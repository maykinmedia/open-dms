from django.core.management import BaseCommand

from ...zaak_task import validate_expired_zaken


class Command(BaseCommand):
    help = "Validate expired zaken in Elasticsearch"

    def handle(self, **options):
        validate_expired_zaken()
