from celery import Celery

from opendms.setup import setup_env

setup_env()

app = Celery("opendms-search")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
