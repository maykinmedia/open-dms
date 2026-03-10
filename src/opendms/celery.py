from celery import Celery
from celery.schedules import crontab

from opendms.setup import setup_env

setup_env()

app = Celery("opendms")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # Index all documents from OpenZaak every hour
    "update_documents_hourly": {
        "task": "tasks.index_all_documents.index_all_documents",
        "schedule": crontab(minute=0),
        "args": ("openzaak-documenten",),
    },
}
