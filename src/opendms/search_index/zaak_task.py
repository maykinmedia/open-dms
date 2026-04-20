from datetime import timedelta

from django.utils import timezone

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

CHECK_EXTENSION_DAYS = 10


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


@app.task(autoretry_for=(SoftTimeLimitExceeded,))
def validate_expired_zaken(batch_size: int = 100):
    """
    For each expired zaken:
    - If it exists in Open Zaak, extend verloopt_op by 10 days
    - If not, delete it from Elasticsearch
    """
    groups = ZGWApiGroupConfig.objects.all()

    if not any(group.zrc_service for group in groups):
        raise ExternalServiceUnavailable("No ZRC API services configured!")

    now = timezone.now()

    with get_elasticsearch_client() as es_client:
        seen_zrc_services = set()

        for group in groups:
            service = group.zrc_service

            if not service or service.id in seen_zrc_services:
                continue

            seen_zrc_services.add(service.id)

            logger.info(
                "validating_expired_zaken",
                service=service.slug,
            )

            # Get expired zaken from Elasticsearch
            expired_zaken = es_client.get_expired_zaken(
                now, batch_size, service_slug=service.slug
            )

            if not expired_zaken:
                logger.info("no_expired_zaken_found", service=service.slug)
                continue

            # Get min and max registratiedatum from expired zaken
            registratiedatum = [
                zaak.get("registratiedatum")
                for zaak in expired_zaken
                if zaak.get("registratiedatum")
            ]
            if not registratiedatum:
                continue

            min_registratiedatum = min(registratiedatum)
            max_registratiedatum = max(registratiedatum)

            # Fetch OpenZaak zaken in range
            with get_zaken_client(service) as zaak_client:
                oz_docs = zaak_client.get_items(
                    params={
                        "registratiedatum__gt": min_registratiedatum,
                        "registratiedatum__lt": max_registratiedatum,
                    }
                )
                # Exact min boundary
                oz_min_docs = zaak_client.get_items(
                    params={
                        "registratiedatum": min_registratiedatum,
                    }
                )

                # Exact max boundary
                oz_max_docs = zaak_client.get_items(
                    params={
                        "registratiedatum": max_registratiedatum,
                    }
                )
            oz_uuids = {doc["uuid"] for doc in (oz_docs + oz_min_docs + oz_max_docs)}

            for doc in expired_zaken:
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
                        logger.info("zaak_validated", uuid=uuid, service=service.slug)
                    else:
                        logger.error(
                            "zaak_validation_failed_update",
                            uuid=uuid,
                            service=service.slug,
                        )
                else:
                    es_client.delete_zaak(uuid)
                    logger.info("zaak_deleted", uuid=uuid, service=service.slug)
