from datetime import timedelta

from django.utils import timezone

import structlog
from celery.exceptions import SoftTimeLimitExceeded

from opendms.api.clients import get_documenten_client, get_oio_client, get_zaken_client
from opendms.api.models import ZGWApiGroupConfig
from opendms.api.utils.exceptions import ExternalServiceUnavailable
from opendms.api.utils.validators import extract_uuid
from opendms.celery import app

from .client import get_elasticsearch_client
from .index import Document, ZaakReferenties

logger = structlog.get_logger(__name__)

CHECK_EXTENSION_DAYS = 10


@app.task(autoretry_for=(SoftTimeLimitExceeded,))
def index_all_documents() -> None:
    """
    Fetch all documents from OpenZaak, add connected 'zaak' information
    (via ObjectInformatieObjecten), and index them in Elasticsearch.
    """
    groups = ZGWApiGroupConfig.objects.all()

    if not any(group.drc_service for group in groups):
        raise ExternalServiceUnavailable("No DRC API services configured!")

    if not any(group.zrc_service for group in groups):
        raise ExternalServiceUnavailable("No ZRC services configured!")

    zaak_services = set()
    for group in groups:
        if group.zrc_service:
            zaak_services.add(group.zrc_service)

    with get_elasticsearch_client() as es_client:
        # TODO: add to docker compose
        Document.init(using=es_client.client)

        last_creatiedatum = es_client.get_last_document_creatiedatum()

        seen_doc_services = set()

        for group in groups:
            doc_service = group.drc_service
            ztc_service_slug = group.ztc_service.slug if group.ztc_service else None

            if not doc_service or doc_service.id in seen_doc_services:
                continue
            seen_doc_services.add(doc_service.id)

            logger.info(
                "fetching_documents",
                service=doc_service.slug,
                creatiedatum_gte=last_creatiedatum,
            )

            with (
                get_documenten_client(doc_service) as doc_client,
                get_oio_client(doc_service) as oio_client,
            ):
                all_documents = doc_client.get_items(
                    params={"creatiedatum__gte": last_creatiedatum}
                    if last_creatiedatum
                    else {}
                )

                for doc in all_documents:
                    oios = [
                        oio
                        for oio in oio_client.get_by_informatieobject(doc["url"])
                        if oio.get("objectType") == "zaak" and oio.get("object")
                    ]

                    zaak_refs = []

                    for oio in oios:
                        url = oio["object"]
                        uuid = url.split("/")[-1]
                        zaak = None

                        for zaak_service in zaak_services:
                            try:
                                with get_zaken_client(zaak_service) as zaken_client:
                                    zaak_item = zaken_client.get_item_by_uuid(uuid)
                                    logger.debug(
                                        "Fetched zaak",
                                        uuid=uuid,
                                        service=zaak_service.slug,
                                    )
                                    ztc_uuid = extract_uuid(zaak_item.get("zaaktype"))
                                    startjaar = zaak_item.get("startdatum", "")[:4]
                                    zaak = ZaakReferenties(
                                        **zaak_item,
                                        object_type="zaak",
                                        service_slug=zaak_service.slug,
                                        ztc_service_slug=ztc_service_slug,
                                        ztc_uuid=ztc_uuid,
                                        startjaar=startjaar,
                                    )
                                    break
                            except Exception as e:
                                logger.warning(
                                    "Failed to fetch zaak",
                                    uuid=uuid,
                                    service=zaak_service.slug,
                                    error=str(e),
                                )
                                continue

                        if zaak:
                            zaak_refs.append(zaak)
                        else:
                            logger.warning("No zaak found for OIO", uuid=uuid, url=url)

                    obj = Document(**doc, zaak_referenties=zaak_refs)
                    es_client.index_document(
                        obj, service=doc_service.slug, group_slug=group.identifier
                    )

            logger.info("indexing_scheduled", total_documents=len(all_documents))


@app.task(autoretry_for=(SoftTimeLimitExceeded,))
def validate_expired_documents(batch_size: int = 100):
    """
    For each expired document:
    - If it exists in Open Zaak, extend verloopt_op by 10 days
    - If not, delete it from Elasticsearch
    """
    groups = ZGWApiGroupConfig.objects.all()

    if not any(group.drc_service for group in groups):
        raise ExternalServiceUnavailable("No DRC API services configured!")

    now = timezone.now()

    with get_elasticsearch_client() as es_client:
        seen_drc_services = set()

        for group in groups:
            service = group.drc_service

            if not service or service.id in seen_drc_services:
                continue

            seen_drc_services.add(service.id)

            logger.info(
                "validating_expired_documents",
                service=service.slug,
            )

            # Get expired documents from Elasticsearch
            expired_docs = es_client.get_expired_documents(
                now, batch_size, service_slug=service.slug
            )

            if not expired_docs:
                logger.info("no_expired_documents_found", service=service.slug)
                continue

            # Get min and max creatiedatum from expired documents
            creatiedata = [
                doc.get("creatiedatum")
                for doc in expired_docs
                if doc.get("creatiedatum")
            ]
            if not creatiedata:
                continue

            min_creatiedatum = min(creatiedata)
            max_creatiedatum = max(creatiedata)

            # Fetch OpenZaak documents in range
            with get_documenten_client(service) as doc_client:
                oz_docs = doc_client.get_items(
                    params={
                        "creatiedatum__gte": min_creatiedatum,
                        "creatiedatum__lte": max_creatiedatum,
                    }
                )
            oz_uuids = {doc["uuid"] for doc in oz_docs}

            for doc in expired_docs:
                uuid = doc.get("uuid")
                if not uuid:
                    continue

                if uuid in oz_uuids:
                    last_checked_at = now
                    next_check_at = now + timedelta(days=CHECK_EXTENSION_DAYS)
                    updated = es_client.update_check_times(
                        uuid,
                        last_checked_at=last_checked_at,
                        next_check_at=next_check_at,
                    )
                    if updated:
                        logger.info(
                            "document_validated", uuid=uuid, service=service.slug
                        )
                    else:
                        logger.error(
                            "document_validation_failed_update",
                            uuid=uuid,
                            service=service.slug,
                        )
                else:
                    es_client.delete_document(uuid)
                    logger.info("document_deleted", uuid=uuid, service=service.slug)
