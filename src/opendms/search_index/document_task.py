from datetime import datetime

import structlog
from zgw_consumers.models import Service

from opendms.celery import app

from .client import search_last_document_creatiedatum
from .document_client import get_documenten_client
from .tasks import index_document

logger = structlog.get_logger(__name__)


@app.task()
def index_all_documents(service_slug: str) -> None:
    """
    Fetch all documents from OpenZaak and index them in Elasticsearch.
    """
    try:
        service = Service.objects.get(slug=service_slug)
    except Service.DoesNotExist:
        logger.error("Service with slug %s does not exist.", service_slug)
        return

    last_creatiedatum = search_last_document_creatiedatum()
    if last_creatiedatum:
        logger.info(
            "fetching_documents",
            creatiedatum_gte=last_creatiedatum,
        )
    else:
        logger.info(
            "fetching_all_documents",
        )

    client = get_documenten_client(service)
    filters = {"creatiedatum__gte": last_creatiedatum} if last_creatiedatum else None
    all_documents = client.get_items(filters=filters)

    logger.info("documents_fetched", count=len(all_documents))

    for doc in all_documents:
        index_document.delay(
            uuid=str(doc["uuid"]),
            url=doc["link"] or "",
            identificatie=doc["identificatie"],
            bronorganisatie=doc["bronorganisatie"],
            creatiedatum=doc["creatiedatum"],
            titel=doc["titel"],
            auteur=doc.get("auteur"),
            taal=doc.get("taal"),
            begin_registratie=doc.get("begin_registratie") or datetime.now(),
            informatieobjecttype=doc["informatieobjecttype"],
            vertrouwelijkheidaanduiding=doc.get("vertrouwelijkheidaanduiding"),
            status=doc.get("status"),
            formaat=doc.get("formaat"),
            bestandsnaam=doc.get("bestandsnaam"),
            inhoud=doc.get("inhoud") or "",
            link=doc.get("link"),
            beschrijving=doc.get("beschrijving"),
            verschijningsvorm=doc.get("verschijningsvorm"),
        )

    logger.info("indexing_scheduled", total_documents=len(all_documents))
