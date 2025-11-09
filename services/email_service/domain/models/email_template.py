"""
Email Template domain model
Represents customizable email templates for review requests
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class TemplateType(Enum):
    """Email template types"""

    REVIEW_REQUEST = "review_request"
    THANK_YOU = "thank_you"
    REMINDER = "reminder"
    INCENTIVE = "incentive"


class TemplateStatus(Enum):
    """Template status"""

    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


@dataclass
class EmailTemplate:
    """
    Email Template domain model

    Represents a customizable email template for review requests
    and other customer communications.

    Business Rules:
    - Templates must be ACTIVE to be used
    - Variables in {{variable}} format
    - Support both HTML and plain text
    - Merchant-specific templates
    """

    # Required fields
    merchant_id: str
    name: str
    template_type: TemplateType
    subject: str
    html_body: str
    status: TemplateStatus
    created_at: datetime
    updated_at: datetime

    # Optional fields
    id: Optional[str] = None
    text_body: Optional[str] = None
    variables: Dict[str, str] = field(default_factory=dict)
    from_name: Optional[str] = None
    from_email: Optional[str] = None

    def activate(self) -> None:
        """
        Activate the template

        Business Rule: Only DRAFT or INACTIVE templates can be activated
        """
        if self.status in [TemplateStatus.DRAFT, TemplateStatus.INACTIVE]:
            self.status = TemplateStatus.ACTIVE
            self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate the template"""
        if self.status == TemplateStatus.ACTIVE:
            self.status = TemplateStatus.INACTIVE
            self.updated_at = datetime.utcnow()

    def archive(self) -> None:
        """Archive the template"""
        self.status = TemplateStatus.ARCHIVED
        self.updated_at = datetime.utcnow()

    def render(self, context: Dict[str, Any]) -> Dict[str, str]:
        """
        Render template with variables

        Args:
            context: Dictionary of variable values

        Returns:
            Dict with rendered subject, html_body, and text_body
        """
        rendered_subject = self._replace_variables(self.subject, context)
        rendered_html = self._replace_variables(self.html_body, context)
        rendered_text = (
            self._replace_variables(self.text_body, context) if self.text_body else None
        )

        return {
            "subject": rendered_subject,
            "html_body": rendered_html,
            "text_body": rendered_text,
        }

    def is_active(self) -> bool:
        """Check if template is active"""
        return self.status == TemplateStatus.ACTIVE

    def _replace_variables(self, text: str, context: Dict[str, Any]) -> str:
        """Replace {{variable}} with values from context"""
        result = text
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        return result

    def __repr__(self) -> str:
        return (
            f"EmailTemplate(id={self.id}, name={self.name}, "
            f"type={self.template_type.value}, status={self.status.value})"
        )
