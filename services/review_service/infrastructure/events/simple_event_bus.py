"""
Simple Event Bus Implementation
For development/testing purposes
Production should use RabbitMQ or Kafka
"""
from typing import Dict, Any
from review_service.domain.interfaces.event_bus_interface import IEventBus


class SimpleEventBus(IEventBus):
    """
    Simple in-memory event bus

    This is a minimal implementation for development and testing.
    In production, replace with RabbitMQ, Kafka, or AWS SNS/SQS.

    Events are just logged for now.
    """

    def __init__(self) -> None:
        """Initialize event bus"""
        self.events: list = []

    async def publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        """
        Publish an event

        Args:
            event_type: Type of event
            payload: Event data
        """
        event = {"type": event_type, "payload": payload}
        self.events.append(event)

        # For development, just log the event
        print(f"[EVENT] {event_type}: {payload}")

    def get_events(self) -> list:
        """Get all published events (for testing)"""
        return self.events

    def clear_events(self) -> None:
        """Clear all events (for testing)"""
        self.events.clear()
