"""
Shared Celery Application
Central Celery configuration for all services
"""
from celery import Celery
from shared.config.settings import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "review_platform",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "services.email_service.tasks",
        "services.review_service.tasks",
        "services.ai_service.tasks",
    ],
)

# Configure Celery
celery_app.conf.update(
    task_serializer=settings.celery_task_serializer,
    result_serializer=settings.celery_result_serializer,
    accept_content=settings.celery_accept_content,
    timezone=settings.celery_timezone,
    task_track_started=settings.celery_task_track_started,
    task_time_limit=settings.celery_task_time_limit,
    broker_connection_retry_on_startup=settings.celery_broker_connection_retry_on_startup,
    # Additional useful settings
    task_acks_late=True,  # Task acknowledged after execution (safer)
    worker_prefetch_multiplier=1,  # One task at a time per worker
    task_reject_on_worker_lost=True,  # Requeue task if worker dies
    result_expires=3600,  # Results expire after 1 hour
)

# Optional: Configure task routes (for advanced routing)
celery_app.conf.task_routes = {
    "services.email_service.tasks.*": {"queue": "emails"},
    "services.ai_service.tasks.*": {"queue": "ai"},
    "services.review_service.tasks.*": {"queue": "reviews"},
}

# Optional: Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Example: Daily cleanup task
    # "cleanup-old-results": {
    #     "task": "services.review_service.tasks.cleanup_old_reviews",
    #     "schedule": crontab(hour=2, minute=0),  # Run at 2 AM daily
    # },
}


if __name__ == "__main__":
    celery_app.start()
