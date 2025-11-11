"""
Celery Event Bus Implementation
Publishes events as Celery tasks for async processing
"""
from typing import Dict, Any
from review_service.domain.interfaces.event_bus_interface import IEventBus
from shared.celery_app import celery_app


class CeleryEventBus(IEventBus):
    """
    Celery-based event bus

    Events are published as Celery tasks that can be consumed
    by workers in any service.

    Benefits over SimpleEventBus:
    - Persistence (Redis-backed)
    - Distributed processing
    - Automatic retries
    - Load balancing across workers
    """

    async def publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        """
        Publish an event via Celery

        Args:
            event_type: Type of event (e.g., "review.created")
            payload: Event data
        """
        # Send event as Celery task
        # Using .delay() for async execution
        celery_app.send_task(
            "process_event",  # Generic event processor task
            args=[event_type, payload],
            queue="events",  # Dedicated events queue
            retry=True,
            retry_policy={
                "max_retries": 3,
                "interval_start": 1,
                "interval_step": 2,
                "interval_max": 10,
            },
        )

        # Log for debugging
        print(f"[CELERY EVENT] {event_type}: {payload}")
