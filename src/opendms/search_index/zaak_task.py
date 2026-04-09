import structlog
from zgw_consumers.models import Service

from opendms.api.clients import get_zaken_client
from opendms.api.utils.exceptions import (
    ExternalServiceUnavailable,
)
from opendms.celery import app

from .client import get_elasticsearch_client
from .index import Zaak

logger = structlog.get_logger(__name__)


@app.task()
def index_all_zaken() -> None:
    """
    Fetch all zaken from OpenZaak and index them in Elasticsearch.
    """
    services = Service.objects.filter(zgwset_zrc_config__isnull=False).distinct()

    if not services.exists():
        raise ExternalServiceUnavailable("No ZRC API services configured!")

    last_registratiedatum = ""
    with get_elasticsearch_client() as es_client:
        Zaak.init(using=es_client.client)
        last_registratiedatum = es_client.get_last_zaak_registratiedatum()

        for service in services:
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
                obj = Zaak(**zaak)
                es_client.index_zaken(obj)

            logger.info("indexing_scheduled", total_zaken=len(all_zaken))
