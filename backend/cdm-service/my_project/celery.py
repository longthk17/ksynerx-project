# config/celery.py
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_project.settings")

app = Celery("cdm_service")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
