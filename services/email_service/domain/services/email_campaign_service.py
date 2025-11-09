"""
Email Campaign Service
Business logic for email campaigns and automated review requests
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from email_service.domain.models.email_template import EmailTemplate, TemplateType


class EmailCampaignService:
    """
    Email Campaign Service

    Manages email campaigns for review requests, thank you emails,
    reminders, and incentive offers.

    Business Rules:
    - Only ACTIVE templates can be used
    - Respect email frequency limits (avoid spam)
    - Auto-send review requests after purchase completion
    - Track campaign statistics
    """

    def __init__(
        self,
        template_repository,
        email_sender,
        order_service_client,
    ):
        """
        Initialize Email Campaign Service

        Args:
            template_repository: Repository for email templates
            email_sender: Service for sending emails
            order_service_client: Client for order service
        """
        self.template_repository = template_repository
        self.email_sender = email_sender
        self.order_service_client = order_service_client
        # In-memory tracking for frequency limits (would be Redis in production)
        self._email_tracking: Dict[str, datetime] = {}

    async def send_review_request(
        self,
        template_id: str,
        recipient: Dict[str, str],
        context: Dict[str, Any],
        delay_hours: Optional[int] = None,
    ) -> bool:
        """
        Send a review request email

        Args:
            template_id: ID of the email template
            recipient: Recipient info {"email": str, "name": str}
            context: Template variables for personalization
            delay_hours: Optional delay in hours before sending

        Returns:
            True if sent successfully, False otherwise

        Raises:
            ValueError: If template not found or not active
        """
        # Get template
        template = await self.template_repository.get_by_id(template_id)

        if template is None:
            raise ValueError(f"Template {template_id} not found")

        # Business Rule: Only ACTIVE templates can be used
        if not template.is_active():
            raise ValueError(f"Template {template_id} is not active")

        # Render template with context
        rendered = template.render(context)

        # If delayed, schedule for future (would use task queue in production)
        if delay_hours:
            # For now, return a placeholder indicating it was scheduled
            return {"scheduled": True, "delay_hours": delay_hours}

        # Send email
        result = await self.email_sender.send_email(
            to_email=recipient["email"],
            to_name=recipient.get("name"),
            subject=rendered["subject"],
            html_body=rendered["html_body"],
            text_body=rendered.get("text_body"),
        )

        return result

    async def send_bulk_review_requests(
        self,
        template_id: str,
        recipients: List[Dict[str, Any]],
    ) -> Dict[str, int]:
        """
        Send review requests to multiple recipients

        Args:
            template_id: ID of the email template
            recipients: List of recipient info with email and context

        Returns:
            Dict with sent and failed counts
        """
        sent = 0
        failed = 0

        for recipient_data in recipients:
            try:
                recipient = {
                    "email": recipient_data["email"],
                    "name": recipient_data.get("name"),
                }
                context = recipient_data["context"]

                await self.send_review_request(
                    template_id=template_id,
                    recipient=recipient,
                    context=context,
                )
                sent += 1
            except Exception:
                failed += 1

        return {
            "sent": sent,
            "failed": failed,
        }

    async def run_automated_campaign(
        self,
        merchant_id: str,
        template_type: TemplateType,
        days_after_purchase: int,
    ) -> Dict[str, int]:
        """
        Run automated email campaign for recent orders

        Business Rule: Automatically send review requests N days after purchase

        Args:
            merchant_id: Merchant ID
            template_type: Type of template to use
            days_after_purchase: Days after purchase to send email

        Returns:
            Dict with sent and failed counts
        """
        # Get active template for this merchant and type
        template = await self.template_repository.get_active_by_type(template_type)

        if template is None:
            return {"sent": 0, "failed": 0}

        # Business Rule: Only ACTIVE templates can be used
        if not template.is_active():
            return {"sent": 0, "failed": 0}

        # Get recent orders that match the criteria
        target_date = datetime.utcnow() - timedelta(days=days_after_purchase)
        recent_orders = await self.order_service_client.get_recent_orders(
            merchant_id=merchant_id,
            completed_after=target_date - timedelta(hours=12),  # 12-hour window
            completed_before=target_date + timedelta(hours=12),
        )

        sent = 0
        failed = 0

        for order in recent_orders:
            try:
                recipient = {
                    "email": order["customer_email"],
                    "name": order.get("customer_name"),
                }

                context = {
                    "customer_name": order.get("customer_name", "Valued Customer"),
                    "product_name": order.get("product_name", "your purchase"),
                    "order_id": order["order_id"],
                }

                # Render template directly instead of calling send_review_request
                # to avoid fetching the template again
                rendered = template.render(context)

                # Send email
                await self.email_sender.send_email(
                    to_email=recipient["email"],
                    to_name=recipient.get("name"),
                    subject=rendered["subject"],
                    html_body=rendered["html_body"],
                    text_body=rendered.get("text_body"),
                )
                sent += 1
            except Exception:
                failed += 1

        return {
            "sent": sent,
            "failed": failed,
        }

    async def can_send_email(
        self,
        recipient_email: str,
        min_hours_between: int = 24,
    ) -> bool:
        """
        Check if we can send email to recipient

        Business Rule: Don't spam customers with too many emails

        Args:
            recipient_email: Recipient email address
            min_hours_between: Minimum hours between emails

        Returns:
            True if can send, False if too soon
        """
        # Check when we last sent to this recipient
        last_sent = self._email_tracking.get(recipient_email)

        if last_sent is None:
            # Never sent before, OK to send
            self._email_tracking[recipient_email] = datetime.utcnow()
            return True

        # Check if enough time has passed
        time_since_last = datetime.utcnow() - last_sent
        min_timedelta = timedelta(hours=min_hours_between)

        if time_since_last >= min_timedelta:
            # Enough time has passed, OK to send
            self._email_tracking[recipient_email] = datetime.utcnow()
            return True

        # Too soon
        return False

    async def get_campaign_statistics(
        self,
        campaign_id: str,
    ) -> Dict[str, Any]:
        """
        Get campaign statistics

        Args:
            campaign_id: Campaign ID

        Returns:
            Dict with campaign stats (sent, delivered, opened, clicked)
        """
        # In production, this would query a campaign tracking database
        # For now, return mock structure
        return {
            "campaign_id": campaign_id,
            "sent": 0,
            "delivered": 0,
            "opened": 0,
            "clicked": 0,
            "bounce_rate": 0.0,
            "open_rate": 0.0,
            "click_rate": 0.0,
        }
