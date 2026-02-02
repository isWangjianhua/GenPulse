"""
Celery application configuration for GenPulse.

This module configures the Celery instance used for distributed task processing.
"""
from celery import Celery
from kombu import Queue, Exchange
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
    task_reject_on_worker_lost=True,  # Re-queue tasks if worker dies
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    
    # DLQ Configuration
    task_queues=(
        Queue(config.MAIN_QUEUE_NAME, Exchange('default'), routing_key='default',
              task_arguments={'x-dead-letter-exchange': 'dlq', 'x-dead-letter-routing-key': 'dead_letter'}),
        Queue(config.DLQ_QUEUE_NAME, Exchange('dlq'), routing_key='dead_letter'),
    ),
    task_default_queue=config.MAIN_QUEUE_NAME,
    task_default_exchange='default',
    task_default_routing_key='default',
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["genpulse"])
