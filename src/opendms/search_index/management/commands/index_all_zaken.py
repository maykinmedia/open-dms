from django.core.management import BaseCommand

from ...zaak_task import index_all_zaken


class Command(BaseCommand):
    help = "Index Elastic Search"

    def handle(self, **options):
        index_all_zaken()
