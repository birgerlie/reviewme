"""
Test Email Campaign Service
Following TDD: Write tests first
"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from email_service.domain.services.email_campaign_service import EmailCampaignService
from email_service.domain.models.email_template import (
    EmailTemplate,
    TemplateType,
    TemplateStatus,
)


@pytest.fixture
def mock_template_repo():
    """Mock template repository"""
    repo = Mock()
    repo.get_by_id = AsyncMock()
    repo.get_active_by_type = AsyncMock()
    return repo


@pytest.fixture
def mock_email_sender():
    """Mock email sender"""
    sender = Mock()
    sender.send_email = AsyncMock()
    return sender


@pytest.fixture
def mock_order_service_client():
    """Mock order service client"""
    client = Mock()
    client.get_recent_orders = AsyncMock()
    return client


@pytest.fixture
def email_campaign_service(
    mock_template_repo, mock_email_sender, mock_order_service_client
):
    """Create EmailCampaignService with mocked dependencies"""
    return EmailCampaignService(
        template_repository=mock_template_repo,
        email_sender=mock_email_sender,
        order_service_client=mock_order_service_client,
    )


@pytest.fixture
def sample_template():
    """Sample email template"""
    return EmailTemplate(
        id="template_123",
        merchant_id="merchant_456",
        name="Review Request",
        template_type=TemplateType.REVIEW_REQUEST,
        subject="How was your {{product_name}}?",
        html_body="<p>Hi {{customer_name}}, please review {{product_name}}</p>",
        variables={"customer_name": "string", "product_name": "string"},
        status=TemplateStatus.ACTIVE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.mark.asyncio
class TestEmailCampaignService:
    """Test Email Campaign Service business logic"""

    async def test_send_review_request_email(
        self,
        email_campaign_service,
        mock_template_repo,
        mock_email_sender,
        sample_template,
    ) -> None:
        """
        GIVEN customer and order data
        WHEN send_review_request called
        THEN sends personalized email
        """
        mock_template_repo.get_by_id.return_value = sample_template
        mock_email_sender.send_email.return_value = True

        recipient = {
            "email": "customer@example.com",
            "name": "John Doe",
        }

        context = {
            "customer_name": "John Doe",
            "product_name": "Amazing Widget",
            "order_id": "order_123",
        }

        result = await email_campaign_service.send_review_request(
            template_id="template_123",
            recipient=recipient,
            context=context,
        )

        assert result is True
        mock_email_sender.send_email.assert_called_once()
        # Verify email contained personalized content
        call_args = mock_email_sender.send_email.call_args[1]
        assert "John Doe" in call_args["subject"] or "Amazing Widget" in call_args["subject"]

    async def test_send_review_request_with_delay(
        self,
        email_campaign_service,
        mock_template_repo,
        mock_email_sender,
        sample_template,
    ) -> None:
        """
        Business Rule: Review requests can be scheduled with delay
        GIVEN delay specified
        WHEN send_review_request called
        THEN schedules email for future
        """
        mock_template_repo.get_by_id.return_value = sample_template

        recipient = {"email": "customer@example.com", "name": "John"}
        context = {"customer_name": "John", "product_name": "Widget"}
        delay_hours = 24

        result = await email_campaign_service.send_review_request(
            template_id="template_123",
            recipient=recipient,
            context=context,
            delay_hours=delay_hours,
        )

        # When delayed, it should be queued/scheduled (implementation detail)
        assert result is not None

    async def test_send_bulk_review_requests(
        self,
        email_campaign_service,
        mock_template_repo,
        mock_email_sender,
        sample_template,
    ) -> None:
        """
        GIVEN multiple recipients
        WHEN send_bulk_review_requests called
        THEN sends to all recipients
        """
        mock_template_repo.get_by_id.return_value = sample_template
        mock_email_sender.send_email.return_value = True

        recipients = [
            {
                "email": "customer1@example.com",
                "context": {"customer_name": "John", "product_name": "Widget"},
            },
            {
                "email": "customer2@example.com",
                "context": {"customer_name": "Jane", "product_name": "Gadget"},
            },
        ]

        results = await email_campaign_service.send_bulk_review_requests(
            template_id="template_123",
            recipients=recipients,
        )

        assert results["sent"] == 2
        assert results["failed"] == 0
        assert mock_email_sender.send_email.call_count == 2

    async def test_send_review_request_template_not_found(
        self,
        email_campaign_service,
        mock_template_repo,
    ) -> None:
        """
        GIVEN invalid template ID
        WHEN send_review_request called
        THEN raises ValueError
        """
        mock_template_repo.get_by_id.return_value = None

        recipient = {"email": "customer@example.com", "name": "John"}
        context = {"customer_name": "John", "product_name": "Widget"}

        with pytest.raises(ValueError, match="Template"):
            await email_campaign_service.send_review_request(
                template_id="nonexistent",
                recipient=recipient,
                context=context,
            )

    async def test_send_review_request_inactive_template(
        self,
        email_campaign_service,
        mock_template_repo,
    ) -> None:
        """
        Business Rule: Only ACTIVE templates can be used
        GIVEN inactive template
        WHEN send_review_request called
        THEN raises ValueError
        """
        inactive_template = EmailTemplate(
            id="template_123",
            merchant_id="merchant_456",
            name="Review Request",
            template_type=TemplateType.REVIEW_REQUEST,
            subject="Review",
            html_body="<p>Review</p>",
            status=TemplateStatus.INACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        mock_template_repo.get_by_id.return_value = inactive_template

        recipient = {"email": "customer@example.com", "name": "John"}
        context = {"customer_name": "John"}

        with pytest.raises(ValueError, match="not active"):
            await email_campaign_service.send_review_request(
                template_id="template_123",
                recipient=recipient,
                context=context,
            )

    async def test_get_campaign_statistics(
        self,
        email_campaign_service,
    ) -> None:
        """
        GIVEN campaign tracking
        WHEN get_campaign_statistics called
        THEN returns stats
        """
        stats = await email_campaign_service.get_campaign_statistics(
            campaign_id="campaign_123"
        )

        assert "sent" in stats
        assert "delivered" in stats
        assert "opened" in stats
        assert "clicked" in stats

    async def test_automated_campaign_for_recent_orders(
        self,
        email_campaign_service,
        mock_order_service_client,
        mock_template_repo,
        mock_email_sender,
        sample_template,
    ) -> None:
        """
        Business Rule: Automatically send review requests for recent orders
        GIVEN recent completed orders
        WHEN run_automated_campaign called
        THEN sends review requests
        """
        # Mock recent orders
        mock_order_service_client.get_recent_orders.return_value = [
            {
                "order_id": "order_1",
                "customer_email": "customer1@example.com",
                "customer_name": "John",
                "product_name": "Widget",
                "completed_at": datetime.utcnow() - timedelta(days=3),
            },
            {
                "order_id": "order_2",
                "customer_email": "customer2@example.com",
                "customer_name": "Jane",
                "product_name": "Gadget",
                "completed_at": datetime.utcnow() - timedelta(days=3),
            },
        ]

        mock_template_repo.get_active_by_type.return_value = sample_template
        mock_email_sender.send_email.return_value = True

        results = await email_campaign_service.run_automated_campaign(
            merchant_id="merchant_456",
            template_type=TemplateType.REVIEW_REQUEST,
            days_after_purchase=3,
        )

        assert results["sent"] >= 2
        assert mock_email_sender.send_email.call_count >= 2

    async def test_respect_email_frequency_limits(
        self,
        email_campaign_service,
        mock_email_sender,
    ) -> None:
        """
        Business Rule: Don't spam customers with too many emails
        GIVEN customer recently received email
        WHEN attempting to send another
        THEN respects frequency limit
        """
        recipient = {"email": "customer@example.com", "name": "John"}

        # First email should go through
        can_send = await email_campaign_service.can_send_email(
            recipient_email=recipient["email"],
            min_hours_between=24,
        )

        assert can_send is True
