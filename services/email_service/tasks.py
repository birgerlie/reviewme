"""
Email Service Celery Tasks
Background tasks for sending emails
"""
from shared.celery_app import celery_app
from typing import Dict, Any, Optional
import logging
from pathlib import Path
from jinja2 import Template
from datetime import datetime

logger = logging.getLogger(__name__)

# Template directory
TEMPLATE_DIR = Path(__file__).parent / "templates"


def render_template(template_name: str, context: Dict[str, Any]) -> str:
    """
    Render email template with context variables

    Args:
        template_name: Template filename (e.g., "review_request.html")
        context: Dictionary of template variables

    Returns:
        Rendered HTML string
    """
    template_path = TEMPLATE_DIR / template_name
    if not template_path.exists():
        logger.error(f"Template not found: {template_path}")
        raise FileNotFoundError(f"Template {template_name} not found")

    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    template = Template(template_content)
    return template.render(**context)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def send_review_request_email(
    self,
    customer_email: str,
    customer_name: str,
    product_name: str,
    product_image_url: str,
    review_token: str,
    order_number: str,
    store_name: str,
    expiry_days: int = 30,
    expiry_date: Optional[str] = None,
    support_email: Optional[str] = None,
    store_address: Optional[str] = None,
    review_base_url: Optional[str] = None,
):
    """
    Send review request email to customer

    This is the main email sent 7 days after order fulfillment, asking
    customers to leave a review with a unique token link.

    Args:
        customer_email: Customer email address
        customer_name: Customer name
        product_name: Product name
        product_image_url: Product image URL
        review_token: Unique review token
        order_number: Order number
        store_name: Store/merchant name
        expiry_days: Days until token expires
        expiry_date: Formatted expiry date string
        support_email: Support email address
        store_address: Store address
        review_base_url: Base URL for review submission

    This task automatically retries on failure up to 3 times with 5-minute delays.
    """
    try:
        logger.info(f"Sending review request email to {customer_email} for {product_name}")

        # Generate review link
        review_base_url = review_base_url or "https://reviews.yourdomain.com"
        review_link = f"{review_base_url}/public/review/{review_token}"

        # Generate unsubscribe link (TODO: implement proper unsubscribe)
        unsubscribe_link = f"{review_base_url}/unsubscribe?email={customer_email}"

        # Format expiry date if not provided
        if not expiry_date:
            from datetime import datetime, timedelta
            expiry_dt = datetime.utcnow() + timedelta(days=expiry_days)
            expiry_date = expiry_dt.strftime("%B %d, %Y")

        # Render email template
        html_content = render_template(
            "review_request.html",
            {
                "customer_name": customer_name,
                "product_name": product_name,
                "product_image_url": product_image_url,
                "order_number": order_number,
                "store_name": store_name,
                "review_link": review_link,
                "expiry_days": expiry_days,
                "expiry_date": expiry_date,
                "support_email": support_email or f"support@{store_name.lower().replace(' ', '')}.com",
                "store_address": store_address or f"{store_name} · Online Store",
                "unsubscribe_link": unsubscribe_link,
            },
        )

        # TODO: Implement actual email sending via SendGrid/AWS SES/SMTP
        # For now, log the email
        logger.info(f"EMAIL TO: {customer_email}")
        logger.info(f"SUBJECT: Share your experience with {product_name}")
        logger.info(f"REVIEW LINK: {review_link}")
        logger.info(f"HTML LENGTH: {len(html_content)} chars")

        return {
            "status": "sent",
            "email": customer_email,
            "product": product_name,
            "review_link": review_link,
        }

    except Exception as exc:
        logger.error(f"Failed to send review request email: {exc}")
        # Retry with exponential backoff (5min, 10min, 20min)
        raise self.retry(exc=exc, countdown=300 * (2 ** self.request.retries))


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_review_confirmation_email(
    self,
    review_id: str,
    customer_email: str,
    customer_name: str,
    product_name: str,
    product_image_url: str,
    review_title: str,
    review_content: str,
    rating: int,
    store_name: str,
    support_email: Optional[str] = None,
    store_address: Optional[str] = None,
):
    """
    Send confirmation email after review is submitted

    This email thanks the customer and provides a summary of their review.

    Args:
        review_id: Review ID
        customer_email: Customer email address
        customer_name: Customer name
        product_name: Product name
        product_image_url: Product image URL
        review_title: Review title
        review_content: Review content
        rating: Rating (1-5)
        store_name: Store/merchant name
        support_email: Support email address
        store_address: Store address

    This task automatically retries on failure up to 3 times
    """
    try:
        logger.info(f"Sending review confirmation email for review {review_id}")

        # Generate star rating visual
        rating_stars = "⭐" * rating + "☆" * (5 - rating)

        # Render email template
        html_content = render_template(
            "review_confirmation.html",
            {
                "customer_name": customer_name,
                "product_name": product_name,
                "product_image_url": product_image_url,
                "review_id": review_id,
                "review_title": review_title,
                "review_content": review_content[:200] + "..." if len(review_content) > 200 else review_content,
                "rating_stars": rating_stars,
                "store_name": store_name,
                "support_email": support_email or f"support@{store_name.lower().replace(' ', '')}.com",
                "store_address": store_address or f"{store_name} · Online Store",
                "facebook_url": "#",
                "twitter_url": "#",
                "instagram_url": "#",
                "manage_preferences_link": "#",
            },
        )

        # TODO: Implement actual email sending via SendGrid/AWS SES/SMTP
        # For now, log the email
        logger.info(f"EMAIL TO: {customer_email}")
        logger.info(f"SUBJECT: Thank You for Your Review!")
        logger.info(f"HTML LENGTH: {len(html_content)} chars")

        return {
            "status": "sent",
            "review_id": review_id,
            "email": customer_email,
        }

    except Exception as exc:
        logger.error(f"Failed to send confirmation email for review {review_id}: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(bind=True, max_retries=3)
def send_review_approved_email(self, review_id: str, customer_email: str, product_name: str):
    """
    Send email when review is approved

    Args:
        review_id: Review ID
        customer_email: Customer email address
        product_name: Product name
    """
    try:
        logger.info(f"Sending review approved email for review {review_id}")

        email_content = f"""
        Great news! Your review has been approved.

        Your review for {product_name} is now live and visible to other customers.
        Review ID: {review_id}

        Thank you for helping others make informed decisions!

        Best regards,
        Review Platform Team
        """

        logger.info(f"EMAIL TO: {customer_email}")
        logger.info(f"CONTENT: {email_content}")

        return {
            "status": "sent",
            "review_id": review_id,
            "email": customer_email,
        }

    except Exception as exc:
        logger.error(f"Failed to send approval email: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3)
def send_review_rejected_email(self, review_id: str, customer_email: str, reason: str):
    """
    Send email when review is rejected

    Args:
        review_id: Review ID
        customer_email: Customer email address
        reason: Rejection reason
    """
    try:
        logger.info(f"Sending review rejected email for review {review_id}")

        email_content = f"""
        Review Status Update

        Unfortunately, we cannot approve your review at this time.
        Review ID: {review_id}

        Reason: {reason}

        Please feel free to submit a new review following our guidelines.

        Best regards,
        Review Platform Team
        """

        logger.info(f"EMAIL TO: {customer_email}")
        logger.info(f"CONTENT: {email_content}")

        return {
            "status": "sent",
            "review_id": review_id,
            "email": customer_email,
        }

    except Exception as exc:
        logger.error(f"Failed to send rejection email: {exc}")
        raise self.retry(exc=exc)


@celery_app.task
def send_daily_digest(merchant_id: str, stats: Dict[str, Any]):
    """
    Send daily digest email to merchant

    Args:
        merchant_id: Merchant ID
        stats: Daily statistics
    """
    logger.info(f"Sending daily digest to merchant {merchant_id}")

    # TODO: Implement merchant email lookup and digest
    logger.info(f"Daily Stats: {stats}")

    return {"status": "sent", "merchant_id": merchant_id}
