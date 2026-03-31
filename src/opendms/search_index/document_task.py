from datetime import UTC, datetime, timedelta

import structlog
from celery.exceptions import SoftTimeLimitExceeded
from zgw_consumers.models import Service

from opendms.api.clients import get_documenten_client, get_oio_client, get_zaken_client
from opendms.api.utils.exceptions import ExternalServiceUnavailable
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
    doc_services = Service.objects.filter(zgwset_drc_config__isnull=False).distinct()
    zaak_services = Service.objects.filter(zgwset_zrc_config__isnull=False).distinct()

    if not doc_services.exists():
        raise ExternalServiceUnavailable("No DRC API services configured!")
    if not zaak_services.exists():
        raise ExternalServiceUnavailable("No ZRC services configured!")

    with get_elasticsearch_client() as es_client:
        Document.init(using=es_client.client)

        last_creatiedatum = es_client.get_last_document_creatiedatum()

        for doc_service in doc_services:
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
                                    zaak = ZaakReferenties(
                                        **zaak_item, object_type="zaak"
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
                    es_client.index_document(obj)

            logger.info("indexing_scheduled", total_documents=len(all_documents))


@app.task(autoretry_for=(SoftTimeLimitExceeded,))
def validate_expired_documents(batch_size: int = 100):
    """
    For each expired document:
    - If it exists in Open Zaak, extend verloopt_op by 10 days
    - If not, delete it from Elasticsearch
    """

    services = Service.objects.filter(zgwset_drc_config__isnull=False).distinct()
    if not services.exists():
        raise ExternalServiceUnavailable("No DRC API services configured!")

    now = datetime.now(UTC)

    with get_elasticsearch_client() as es_client:
        for service in services:
            # Get the last creation date indexed in Elasticsearch for this service
            last_creatiedatum = es_client.get_last_document_creatiedatum(
                service_slug=service.slug, latest=False
            )

            # Fetch all documents from Open Zaak after last_creatiedatum
            with get_documenten_client(service) as doc_client:
                oz_docs = doc_client.get_items(
                    params={"creatiedatum__gte": last_creatiedatum}
                    if last_creatiedatum
                    else {}
                )

            oz_uuids = {doc["uuid"] for doc in oz_docs}

            # Get expired documents from Elasticsearch
            expired_docs = es_client.get_expired_document(
                now, batch_size, service_slug=service.slug
            )
            if not expired_docs:
                logger.info("no_expired_documents_found", service=service.slug)
                continue

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
