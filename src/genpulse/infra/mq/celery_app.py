"""
Celery application configuration for GenPulse.

This module configures the Celery instance used for distributed task processing.
"""
from celery import Celery
from genpulse import config

# Create Celery app
celery_app = Celery(
    "genpulse",
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["genpulse"])
