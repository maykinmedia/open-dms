import logging
from datetime import date, datetime

from django.conf import settings

from opendms.celery import app

from .client import get_elasticsearch_client
from .constants import DOCUMENT_ATTACHMENT_PIPELINE_ID
from .index import Document

logger = logging.getLogger(__name__)


@app.task()
def index_document(
    *,
    uuid: str,
    url: str,
    identificatie: str,
    bronorganisatie: str,
    creatiedatum: date,
    titel: str,
    auteur: str,
    taal: str,
    begin_registratie: datetime,
    informatieobjecttype: str,
    vertrouwelijkheidaanduiding: str | None,
    status: str | None,
    formaat: str | None,
    bestandsnaam: str | None,
    inhoud: str = "",
    link: str | None,
    beschrijving: str | None,
    verschijningsvorm: str | None,
    bestandsomvang: int | None = None,
):
    document = Document(
        _id=uuid,
        uuid=uuid,
        url=url,
        identificatie=identificatie,
        bronorganisatie=bronorganisatie,
        creatiedatum=creatiedatum,
        titel=titel,
        auteur=auteur,
        taal=taal,
        begin_registratie=begin_registratie,
        informatieobjecttype=informatieobjecttype,
        vertrouwelijkheidaanduiding=vertrouwelijkheidaanduiding,
        status=status,
        formaat=formaat,
        bestandsnaam=bestandsnaam,
        link=link,
        beschrijving=beschrijving,
        verschijningsvorm=verschijningsvorm,
    )

    if (
        inhoud
        and bestandsomvang
        and bestandsomvang <= settings.SEARCH_INDEX["MAX_INDEX_FILE_SIZE"]
    ):
        document.document_data = _download_document(document_url=inhoud)

    with get_elasticsearch_client() as client:
        document.save(
            using=client,
            refresh=settings.SEARCH_INDEX["REFRESH"],
            pipeline=DOCUMENT_ATTACHMENT_PIPELINE_ID,
        )
