import structlog
from zgw_consumers.models import Service

from opendms.api.clients import get_documenten_client
from opendms.api.utils.exceptions import (
    ExternalServiceUnavailable,
)
from opendms.celery import app

from .client import get_elasticsearch_client
from .index import Document

logger = structlog.get_logger(__name__)


@app.task()
def index_all_documents() -> None:
    """
    Fetch all documents from OpenZaak and index them in Elasticsearch.
    """
    services = Service.objects.filter(zgwset_drc_config__isnull=False).distinct()

    if not services.exists():
        raise ExternalServiceUnavailable("No DRC API services configured!")

    last_creatiedatum = ""
    with get_elasticsearch_client() as es_client:
        es_client.get_last_document_creatiedatum()

        for service in services:
            logger.info(
                "fetching_documents",
                service=service.slug,
                creatiedatum_gte=last_creatiedatum,
            )

            with get_documenten_client(service) as doc_client:
                all_documents = doc_client.get_items(
                    params={"creatiedatum__gte": last_creatiedatum}
                    if last_creatiedatum
                    else {}
                )

            logger.info("documents_fetched", count=len(all_documents))
            for doc in all_documents:
                obj = Document(**doc)
                es_client.index_document(obj)

            logger.info("indexing_scheduled", total_documents=len(all_documents))
