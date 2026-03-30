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
    - If it exists in any Open Zaak service extend verloopt_op by 7 days
    - If not delete it from Elasticsearch
    """
    now = datetime.now(UTC)

    with get_elasticsearch_client() as es_client:
        uuids = es_client.get_expired_document(now, batch_size)

        if not uuids:
            logger.info("no_expired_documents_found")
            return

        services = Service.objects.filter(zgwset_drc_config__isnull=False).distinct()

        if not services.exists():
            raise ExternalServiceUnavailable("No DRC API services configured!")

        for uuid in uuids:
            found = False

            for service in services:
                try:
                    with get_documenten_client(service) as client:
                        client.get_item_by_uuid(uuid)

                    found = True

                    new_expiry = now + timedelta(days=7)
                    updated = es_client.update_verloopt_op(uuid, new_expiry)

                    if updated:
                        logger.info(
                            "document_validated",
                            uuid=uuid,
                            service=service.slug,
                        )
                    else:
                        logger.error(
                            "document_validation_failed_update",
                            uuid=uuid,
                        )
                    break
                except Exception:
                    continue
            if not found:
                es_client.delete_document(uuid)
                logger.info("document_deleted", uuid=uuid)
