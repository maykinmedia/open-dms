from celery import Celery

from opendms.setup import setup_env

setup_env()

app = Celery("opendms")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(
    packages=["opendms.search_index.document_task", "opendms.search_index.zaak_task"]
)
