"""
Event Bus Interface
Defines the contract for event publishing
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class IEventBus(ABC):
    """
    Abstract base class for event bus operations

    Implementations can use RabbitMQ, Kafka, or any other message broker
    """

    @abstractmethod
    async def publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        """
        Publish an event to the event bus

        Args:
            event_type: Type of event (e.g., "review.created", "review.approved")
            payload: Event data dictionary

        Raises:
            EventBusError: If publishing fails
        """
        pass
