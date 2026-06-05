import os
from celery import Celery

# Läuft lokal ohne externe Dienste (kein Redis nötig)
BROKER_URL = os.getenv("CELERY_BROKER_URL", "sqla+sqlite:///./celery-broker.sqlite")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "db+sqlite:///./celery-results.sqlite")

celery_app = Celery("landseeker", broker=BROKER_URL, backend=RESULT_BACKEND)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.timezone = "Europe/Zurich"
celery_app.conf.task_track_started = True
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.task_acks_late = True
