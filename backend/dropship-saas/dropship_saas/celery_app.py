"""Celery application for async background tasks."""

from celery import Celery
from kombu import Queue

# Celery configuration
celery_app = Celery("dropship_saas")

celery_app.conf.update(
    # Broker
    broker_url="redis://localhost:6379/0",
    result_backend="redis://localhost:6379/0",
    
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Queue configuration
    task_queues=[
        Queue("default", routing_key="default"),
        Queue("scraping", routing_key="scraping"),
        Queue("sync", routing_key="sync"),
        Queue("fulfillment", routing_key="fulfillment"),
    ],
    task_routes={
        "dropship_saas.tasks.scraping.*": {"queue": "scraping"},
        "dropship_saas.tasks.sync.*": {"queue": "sync"},
        "dropship_saas.tasks.fulfillment.*": {"queue": "fulfillment"},
    },
    
    # Worker settings
    worker_prefetch_multiplier=4,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Beat schedule (periodic tasks)
    beat_schedule={
        "sync-prices-every-30-min": {
            "task": "dropship_saas.tasks.sync.sync_all_prices",
            "schedule": 1800.0,  # 30 minutes
        },
        "sync-inventory-every-hour": {
            "task": "dropship_saas.tasks.sync.sync_all_inventory",
            "schedule": 3600.0,  # 1 hour
        },
        "health-check-every-15-min": {
            "task": "dropship_saas.tasks.monitoring.health_check_all",
            "schedule": 900.0,  # 15 minutes
        },
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["dropship_saas.tasks"])