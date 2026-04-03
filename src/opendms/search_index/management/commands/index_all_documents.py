from django.core.management import BaseCommand

from ...document_task import index_all_documents


class Command(BaseCommand):
    help = "Index Elastic Search"

    def handle(self, **options):
        index_all_documents()
