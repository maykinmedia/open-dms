from django.core.management import BaseCommand

from ...document_task import validate_expired_documents


class Command(BaseCommand):
    help = "Validate expired documents in Elasticsearch"

    def handle(self, **options):
        validate_expired_documents()
