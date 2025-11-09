"""
Test Email Template domain model
Following TDD: Write tests first
"""
import pytest
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from email_service.domain.models.email_template import (
    EmailTemplate,
    TemplateType,
    TemplateStatus,
)


class TestEmailTemplateModel:
    """Test Email Template domain model"""

    def test_create_email_template_with_required_fields(self) -> None:
        """GIVEN valid template data WHEN creating EmailTemplate THEN should succeed"""
        template = EmailTemplate(
            id="template_123",
            merchant_id="merchant_456",
            name="Review Request",
            template_type=TemplateType.REVIEW_REQUEST,
            subject="How was your purchase?",
            html_body="<p>Please review your purchase</p>",
            status=TemplateStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert template.merchant_id == "merchant_456"
        assert template.template_type == TemplateType.REVIEW_REQUEST
        assert template.status == TemplateStatus.ACTIVE

    def test_email_template_with_personalization_variables(self) -> None:
        """GIVEN template with variables WHEN created THEN variables are stored"""
        variables = {
            "customer_name": "string",
            "product_name": "string",
            "order_id": "string",
        }

        template = EmailTemplate(
            id="template_123",
            merchant_id="merchant_456",
            name="Review Request",
            template_type=TemplateType.REVIEW_REQUEST,
            subject="Hi {{customer_name}}, review {{product_name}}",
            html_body="<p>Hi {{customer_name}}</p>",
            variables=variables,
            status=TemplateStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert template.variables == variables
        assert "customer_name" in template.variables

    def test_activate_deactivate_template(self) -> None:
        """GIVEN template WHEN activate/deactivate called THEN status changes"""
        template = EmailTemplate(
            id="template_123",
            merchant_id="merchant_456",
            name="Review Request",
            template_type=TemplateType.REVIEW_REQUEST,
            subject="Review",
            html_body="<p>Review</p>",
            status=TemplateStatus.DRAFT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        template.activate()
        assert template.status == TemplateStatus.ACTIVE

        template.deactivate()
        assert template.status == TemplateStatus.INACTIVE

    def test_all_template_types_are_valid(self) -> None:
        """GIVEN all template type enum values WHEN used THEN all are valid"""
        assert TemplateType.REVIEW_REQUEST.value == "review_request"
        assert TemplateType.THANK_YOU.value == "thank_you"
        assert TemplateType.REMINDER.value == "reminder"
        assert TemplateType.INCENTIVE.value == "incentive"

    def test_all_template_statuses_are_valid(self) -> None:
        """GIVEN all status enum values WHEN used THEN all are valid"""
        assert TemplateStatus.DRAFT.value == "draft"
        assert TemplateStatus.ACTIVE.value == "active"
        assert TemplateStatus.INACTIVE.value == "inactive"
        assert TemplateStatus.ARCHIVED.value == "archived"

    def test_template_with_plain_text_body(self) -> None:
        """GIVEN template with plain text WHEN created THEN both bodies stored"""
        template = EmailTemplate(
            id="template_123",
            merchant_id="merchant_456",
            name="Review Request",
            template_type=TemplateType.REVIEW_REQUEST,
            subject="Review",
            html_body="<p>Review</p>",
            text_body="Review",
            status=TemplateStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert template.html_body == "<p>Review</p>"
        assert template.text_body == "Review"

    def test_template_render_with_variables(self) -> None:
        """GIVEN template with variables WHEN render() called THEN replaces variables"""
        template = EmailTemplate(
            id="template_123",
            merchant_id="merchant_456",
            name="Review Request",
            template_type=TemplateType.REVIEW_REQUEST,
            subject="Hi {{customer_name}}",
            html_body="<p>Review {{product_name}}</p>",
            variables={"customer_name": "string", "product_name": "string"},
            status=TemplateStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        context = {"customer_name": "John", "product_name": "Widget"}
        rendered = template.render(context)

        assert "John" in rendered["subject"]
        assert "Widget" in rendered["html_body"]

    def test_template_is_active_check(self) -> None:
        """GIVEN template status WHEN is_active() called THEN returns correct bool"""
        active_template = EmailTemplate(
            id="template_123",
            merchant_id="merchant_456",
            name="Review Request",
            template_type=TemplateType.REVIEW_REQUEST,
            subject="Review",
            html_body="<p>Review</p>",
            status=TemplateStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        inactive_template = EmailTemplate(
            id="template_124",
            merchant_id="merchant_456",
            name="Review Request",
            template_type=TemplateType.REVIEW_REQUEST,
            subject="Review",
            html_body="<p>Review</p>",
            status=TemplateStatus.INACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert active_template.is_active() is True
        assert inactive_template.is_active() is False
