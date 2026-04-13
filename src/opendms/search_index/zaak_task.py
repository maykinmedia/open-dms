import structlog
from celery.exceptions import SoftTimeLimitExceeded

from opendms.api.clients import get_zaken_client
from opendms.api.models import ZGWApiGroupConfig
from opendms.api.utils.exceptions import (
    ExternalServiceUnavailable,
)
from opendms.api.utils.validators import extract_uuid
from opendms.celery import app

from .client import get_elasticsearch_client
from .index import Zaak

logger = structlog.get_logger(__name__)


@app.task(autoretry_for=(SoftTimeLimitExceeded,))
def index_all_zaken() -> None:
    """
    Fetch all zaken from OpenZaak and index them in Elasticsearch.
    """
    groups = ZGWApiGroupConfig.objects.all()

    if not any(group.zrc_service for group in groups):
        raise ExternalServiceUnavailable("No ZRC API services configured!")

    last_registratiedatum = ""
    with get_elasticsearch_client() as es_client:
        Zaak.init(using=es_client.client)
        last_registratiedatum = es_client.get_last_zaak_registratiedatum()

        seen_zaak_services = set()

        for group in groups:
            service = group.zrc_service
            ztc_service_slug = group.ztc_service.slug if group.ztc_service else None

            if not group.zrc_service:
                continue

            if not service or service.id in seen_zaak_services:
                continue
            seen_zaak_services.add(service.id)

            logger.info(
                "fetching_zaken",
                service=service.slug,
                registratiedatum=last_registratiedatum,
            )

            with get_zaken_client(service) as zaak_client:
                all_zaken = zaak_client.get_zaken_for_elasticsearch(
                    params={"registratiedatum__gt": last_registratiedatum}
                    if last_registratiedatum
                    else {}
                )

            logger.info("zaken_fetched", count=len(all_zaken))
            for zaak in all_zaken:
                ztc_uuid = extract_uuid(zaak.get("zaaktype"))
                startjaar = zaak.get("startdatum", "")[:4]

                obj = Zaak(
                    **zaak,
                    ztc_uuid=ztc_uuid,
                    startjaar=startjaar,
                    ztc_service_slug=ztc_service_slug,
                )
                es_client.index_zaken(
                    obj, service_slug=service.slug, group_slug=group.identifier
                )

            logger.info("indexing_scheduled", total_zaken=len(all_zaken))
