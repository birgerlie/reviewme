"""
Email API Routes
FastAPI endpoints for email service
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Any

from email_service.api.models import (
    SendReviewRequestRequest,
    SendReviewRequestResponse,
    SendBulkReviewRequestsRequest,
    SendBulkReviewRequestsResponse,
    EmailTemplateCreateRequest,
    EmailTemplateResponse,
    EmailTemplateUpdateRequest,
    CampaignStatsResponse,
    RunAutomatedCampaignRequest,
    RunAutomatedCampaignResponse,
)
from email_service.domain.services.email_campaign_service import EmailCampaignService
from email_service.domain.models.email_template import (
    EmailTemplate,
    TemplateType,
    TemplateStatus,
)
from datetime import datetime

router = APIRouter(tags=["email"])


# Mock dependencies (to be implemented with real services)
async def get_email_campaign_service() -> EmailCampaignService:
    """Dependency: Get email campaign service"""
    # This would be properly injected in production
    from unittest.mock import Mock, AsyncMock

    mock_repo = Mock()
    mock_repo.get_by_id = AsyncMock()
    mock_repo.get_active_by_type = AsyncMock()
    mock_sender = Mock()
    mock_sender.send_email = AsyncMock()
    mock_client = Mock()
    mock_client.get_recent_orders = AsyncMock()
    return EmailCampaignService(mock_repo, mock_sender, mock_client)


@router.post(
    "/api/v1/emails/review-request",
    response_model=SendReviewRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Send review request email",
    description="Send a personalized review request email to a customer",
)
async def send_review_request(
    request: SendReviewRequestRequest,
    service: EmailCampaignService = Depends(get_email_campaign_service),
) -> SendReviewRequestResponse:
    """
    Send a review request email

    **Use Cases:**
    - Post-purchase review requests
    - Follow-up emails for completed orders
    - Scheduled review reminders

    **Business Rules:**
    - Template must be ACTIVE
    - Respects email frequency limits
    - Supports delayed sending
    """
    try:
        recipient = {
            "email": request.recipient_email,
            "name": request.recipient_name,
        }

        result = await service.send_review_request(
            template_id=request.template_id,
            recipient=recipient,
            context=request.context,
            delay_hours=request.delay_hours,
        )

        # Check if scheduled
        scheduled = isinstance(result, dict) and result.get("scheduled", False)

        return SendReviewRequestResponse(
            success=True,
            scheduled=scheduled,
            message="Email scheduled successfully"
            if scheduled
            else "Email sent successfully",
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}",
        )


@router.post(
    "/api/v1/emails/review-request/bulk",
    response_model=SendBulkReviewRequestsResponse,
    status_code=status.HTTP_200_OK,
    summary="Send bulk review request emails",
    description="Send review request emails to multiple recipients",
)
async def send_bulk_review_requests(
    request: SendBulkReviewRequestsRequest,
    service: EmailCampaignService = Depends(get_email_campaign_service),
) -> SendBulkReviewRequestsResponse:
    """
    Send bulk review request emails

    **Use Cases:**
    - Batch processing of recent orders
    - Campaign emails to multiple customers
    - Automated review collection

    **Performance:**
    - Processes recipients concurrently
    - Returns summary statistics
    """
    try:
        # Convert Pydantic models to dicts
        recipients = [
            {
                "email": r.email,
                "name": r.name,
                "context": r.context,
            }
            for r in request.recipients
        ]

        results = await service.send_bulk_review_requests(
            template_id=request.template_id,
            recipients=recipients,
        )

        total = results["sent"] + results["failed"]
        success_rate = results["sent"] / total if total > 0 else 0.0

        return SendBulkReviewRequestsResponse(
            sent=results["sent"],
            failed=results["failed"],
            success_rate=success_rate,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send bulk emails: {str(e)}",
        )


@router.post(
    "/api/v1/emails/campaigns/automated",
    response_model=RunAutomatedCampaignResponse,
    status_code=status.HTTP_200_OK,
    summary="Run automated email campaign",
    description="Automatically send review requests for recent orders",
)
async def run_automated_campaign(
    request: RunAutomatedCampaignRequest,
    service: EmailCampaignService = Depends(get_email_campaign_service),
) -> RunAutomatedCampaignResponse:
    """
    Run automated email campaign

    **Business Rule:** Automatically send review requests N days after purchase

    **Use Cases:**
    - Daily batch job for review requests
    - Scheduled campaigns
    - Post-purchase automation

    **Parameters:**
    - days_after_purchase: Send emails to orders completed N days ago
    """
    try:
        template_type = TemplateType(request.template_type)

        results = await service.run_automated_campaign(
            merchant_id=request.merchant_id,
            template_type=template_type,
            days_after_purchase=request.days_after_purchase,
        )

        return RunAutomatedCampaignResponse(
            sent=results["sent"],
            failed=results["failed"],
            message=f"Automated campaign completed: {results['sent']} sent, {results['failed']} failed",
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run automated campaign: {str(e)}",
        )


@router.get(
    "/api/v1/emails/campaigns/{campaign_id}/stats",
    response_model=CampaignStatsResponse,
    summary="Get campaign statistics",
    description="Get detailed statistics for an email campaign",
)
async def get_campaign_stats(
    campaign_id: str,
    service: EmailCampaignService = Depends(get_email_campaign_service),
) -> CampaignStatsResponse:
    """
    Get campaign statistics

    **Metrics:**
    - Sent: Total emails sent
    - Delivered: Successfully delivered
    - Opened: Email opens (requires tracking pixel)
    - Clicked: Link clicks (requires tracking links)
    - Bounce Rate: Failed deliveries
    - Open Rate: Opens / Delivered
    - Click Rate: Clicks / Delivered
    """
    try:
        stats = await service.get_campaign_statistics(campaign_id=campaign_id)

        return CampaignStatsResponse(**stats)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get campaign stats: {str(e)}",
        )


@router.post(
    "/api/v1/emails/templates",
    response_model=EmailTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create email template",
    description="Create a new email template",
)
async def create_email_template(
    request: EmailTemplateCreateRequest,
) -> EmailTemplateResponse:
    """
    Create a new email template

    **Template Variables:**
    - Use {{variable_name}} syntax
    - Example: "Hi {{customer_name}}, please review {{product_name}}"

    **Template Types:**
    - review_request: Request for product review
    - thank_you: Thank you for review
    - reminder: Review reminder
    - incentive: Review with incentive offer
    """
    try:
        # Create template (would use repository in production)
        template = EmailTemplate(
            id=f"template_{datetime.utcnow().timestamp()}",
            merchant_id=request.merchant_id,
            name=request.name,
            template_type=TemplateType(request.template_type),
            subject=request.subject,
            html_body=request.html_body,
            text_body=request.text_body,
            variables=request.variables,
            status=TemplateStatus.DRAFT,
            from_name=request.from_name,
            from_email=request.from_email,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        return EmailTemplateResponse(
            id=template.id,
            merchant_id=template.merchant_id,
            name=template.name,
            template_type=template.template_type.value,
            subject=template.subject,
            html_body=template.html_body,
            text_body=template.text_body,
            variables=template.variables,
            status=template.status.value,
            from_name=template.from_name,
            from_email=template.from_email,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}",
        )


@router.patch(
    "/api/v1/emails/templates/{template_id}",
    response_model=EmailTemplateResponse,
    summary="Update email template",
    description="Update an existing email template",
)
async def update_email_template(
    template_id: str,
    request: EmailTemplateUpdateRequest,
) -> EmailTemplateResponse:
    """
    Update email template

    **Note:** Only DRAFT and INACTIVE templates can be fully edited.
    ACTIVE templates require deactivation first.
    """
    # Would use repository in production
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Template update not yet implemented",
    )


@router.post(
    "/api/v1/emails/templates/{template_id}/activate",
    response_model=EmailTemplateResponse,
    summary="Activate email template",
    description="Activate an email template for use",
)
async def activate_template(template_id: str) -> EmailTemplateResponse:
    """
    Activate email template

    **Business Rule:** Only DRAFT or INACTIVE templates can be activated
    """
    # Would use repository in production
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Template activation not yet implemented",
    )


@router.post(
    "/api/v1/emails/templates/{template_id}/deactivate",
    response_model=EmailTemplateResponse,
    summary="Deactivate email template",
    description="Deactivate an email template",
)
async def deactivate_template(template_id: str) -> EmailTemplateResponse:
    """
    Deactivate email template

    Prevents the template from being used in new campaigns.
    """
    # Would use repository in production
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Template deactivation not yet implemented",
    )


@router.delete(
    "/api/v1/emails/templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete email template",
    description="Delete (archive) an email template",
)
async def delete_template(template_id: str) -> None:
    """
    Delete (archive) email template

    **Note:** Templates are archived, not permanently deleted,
    to maintain audit trail.
    """
    # Would use repository in production
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Template deletion not yet implemented",
    )
