"""
API Models for Email Service
Pydantic schemas for request/response
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime


class SendReviewRequestRequest(BaseModel):
    """Request model for sending a review request email"""

    template_id: str = Field(..., min_length=1, description="Email template ID")
    recipient_email: EmailStr = Field(..., description="Recipient email address")
    recipient_name: Optional[str] = Field(None, description="Recipient name")
    context: Dict[str, Any] = Field(..., description="Template variables")
    delay_hours: Optional[int] = Field(None, ge=0, description="Delay in hours")

    class Config:
        json_schema_extra = {
            "example": {
                "template_id": "template_123",
                "recipient_email": "customer@example.com",
                "recipient_name": "John Doe",
                "context": {
                    "customer_name": "John Doe",
                    "product_name": "Amazing Widget",
                    "order_id": "order_456",
                },
                "delay_hours": 24,
            }
        }


class SendReviewRequestResponse(BaseModel):
    """Response model for sending a review request"""

    success: bool
    scheduled: bool = False
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "scheduled": False,
                "message": "Email sent successfully",
            }
        }


class BulkRecipient(BaseModel):
    """Recipient for bulk email"""

    email: EmailStr
    name: Optional[str] = None
    context: Dict[str, Any]


class SendBulkReviewRequestsRequest(BaseModel):
    """Request model for sending bulk review requests"""

    template_id: str = Field(..., min_length=1)
    recipients: List[BulkRecipient] = Field(..., min_items=1)

    class Config:
        json_schema_extra = {
            "example": {
                "template_id": "template_123",
                "recipients": [
                    {
                        "email": "customer1@example.com",
                        "name": "John",
                        "context": {"customer_name": "John", "product_name": "Widget"},
                    },
                    {
                        "email": "customer2@example.com",
                        "name": "Jane",
                        "context": {"customer_name": "Jane", "product_name": "Gadget"},
                    },
                ],
            }
        }


class SendBulkReviewRequestsResponse(BaseModel):
    """Response model for bulk email sending"""

    sent: int
    failed: int
    success_rate: float

    class Config:
        json_schema_extra = {
            "example": {
                "sent": 48,
                "failed": 2,
                "success_rate": 0.96,
            }
        }


class EmailTemplateCreateRequest(BaseModel):
    """Request model for creating email template"""

    merchant_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    template_type: str = Field(
        ..., pattern="^(review_request|thank_you|reminder|incentive)$"
    )
    subject: str = Field(..., min_length=1)
    html_body: str = Field(..., min_length=1)
    text_body: Optional[str] = None
    variables: Dict[str, str] = Field(default_factory=dict)
    from_name: Optional[str] = None
    from_email: Optional[EmailStr] = None

    class Config:
        json_schema_extra = {
            "example": {
                "merchant_id": "merchant_123",
                "name": "Review Request Template",
                "template_type": "review_request",
                "subject": "How was your {{product_name}}?",
                "html_body": "<p>Hi {{customer_name}}, please review {{product_name}}</p>",
                "variables": {"customer_name": "string", "product_name": "string"},
            }
        }


class EmailTemplateResponse(BaseModel):
    """Response model for email template"""

    id: str
    merchant_id: str
    name: str
    template_type: str
    subject: str
    html_body: str
    text_body: Optional[str]
    variables: Dict[str, str]
    status: str
    from_name: Optional[str]
    from_email: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmailTemplateUpdateRequest(BaseModel):
    """Request model for updating email template"""

    name: Optional[str] = None
    subject: Optional[str] = None
    html_body: Optional[str] = None
    text_body: Optional[str] = None
    variables: Optional[Dict[str, str]] = None
    from_name: Optional[str] = None
    from_email: Optional[EmailStr] = None


class CampaignStatsResponse(BaseModel):
    """Response model for campaign statistics"""

    campaign_id: str
    sent: int
    delivered: int
    opened: int
    clicked: int
    bounce_rate: float
    open_rate: float
    click_rate: float

    class Config:
        json_schema_extra = {
            "example": {
                "campaign_id": "campaign_123",
                "sent": 1000,
                "delivered": 980,
                "opened": 650,
                "clicked": 120,
                "bounce_rate": 0.02,
                "open_rate": 0.66,
                "click_rate": 0.12,
            }
        }


class RunAutomatedCampaignRequest(BaseModel):
    """Request model for running automated campaign"""

    merchant_id: str = Field(..., min_length=1)
    template_type: str = Field(
        ..., pattern="^(review_request|thank_you|reminder|incentive)$"
    )
    days_after_purchase: int = Field(..., ge=1, le=365)

    class Config:
        json_schema_extra = {
            "example": {
                "merchant_id": "merchant_123",
                "template_type": "review_request",
                "days_after_purchase": 7,
            }
        }


class RunAutomatedCampaignResponse(BaseModel):
    """Response model for automated campaign"""

    sent: int
    failed: int
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "sent": 156,
                "failed": 4,
                "message": "Automated campaign completed successfully",
            }
        }
