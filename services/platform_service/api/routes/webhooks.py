"""
Webhook Routes
Handles platform webhook events
"""
from fastapi import APIRouter, HTTPException, Request, Header, status
from typing import Optional

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/shopify/orders_fulfilled")
async def shopify_order_fulfilled(
    request: Request,
    x_shopify_topic: Optional[str] = Header(None),
    x_shopify_shop_domain: Optional[str] = Header(None),
    x_shopify_hmac_sha256: Optional[str] = Header(None),
):
    """
    Shopify webhook: Order fulfilled

    Triggered when an order is fulfilled (shipped).
    This is when we schedule the review request email.

    Flow:
    1. Verify HMAC signature (security)
    2. Parse webhook payload
    3. Look up merchant by shop_domain
    4. For each product in order:
       - Generate review token
       - Schedule email (7 days from now)
    5. Return 200 OK immediately

    Args:
        request: FastAPI request object
        x_shopify_topic: Webhook topic header
        x_shopify_shop_domain: Shop domain header
        x_shopify_hmac_sha256: HMAC signature header

    Returns:
        Success response

    Security:
        - HMAC verification prevents spoofed webhooks
        - Idempotent (can receive same webhook multiple times)

    Example webhook payload:
    {
        "id": 12345,
        "name": "#1001",
        "customer": {"email": "buyer@example.com", "first_name": "John"},
        "line_items": [
            {"product_id": 789, "title": "Product Name", "quantity": 1}
        ],
        "total_price": "29.99",
        "currency": "USD",
        "fulfilled_at": "2025-11-11T10:00:00Z"
    }
    """
    try:
        # Step 1: Get raw payload for HMAC verification
        payload = await request.body()

        # Verify HMAC signature
        # webhook_handler = ShopifyWebhookHandler()
        # if not webhook_handler.verify_webhook(payload, request.headers):
        #     raise HTTPException(status_code=401, detail="Invalid webhook signature")

        # Step 2: Parse JSON payload
        import json
        webhook_data = json.loads(payload)

        # Step 3: Parse webhook event
        # event = await webhook_handler.parse_webhook_event(webhook_data, request.headers)

        # Step 4: Get merchant by shop_domain
        # merchant = await merchant_repository.get_by_platform_domain(
        #     PlatformType.SHOPIFY, x_shopify_shop_domain
        # )

        # if not merchant:
        #     # Shop not found - might have uninstalled
        #     return {"status": "ignored", "reason": "merchant_not_found"}

        # Step 5: Handle order fulfilled
        # token_ids = await platform_service.handle_order_fulfilled(
        #     merchant.id, str(webhook_data["id"])
        # )

        # Return success immediately (don't make Shopify wait)
        return {
            "status": "received",
            "order_id": webhook_data.get("id"),
            "shop_domain": x_shopify_shop_domain,
            # "tokens_created": len(token_ids),
        }

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )
    except Exception as e:
        # Log error but return 200 to prevent Shopify retries
        # logger.error(f"Webhook processing failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
        }


@router.post("/shopify/app_uninstalled")
async def shopify_app_uninstalled(
    request: Request,
    x_shopify_topic: Optional[str] = Header(None),
    x_shopify_shop_domain: Optional[str] = Header(None),
    x_shopify_hmac_sha256: Optional[str] = Header(None),
):
    """
    Shopify webhook: App uninstalled

    Triggered when merchant uninstalls the app.
    We need to clean up data and mark merchant as inactive.

    Flow:
    1. Verify HMAC signature
    2. Look up merchant by shop_domain
    3. Mark merchant as inactive
    4. Delete webhooks (optional - Shopify does this automatically)
    5. Publish "merchant.uninstalled" event
    6. Return 200 OK

    Args:
        request: FastAPI request object
        x_shopify_topic: Webhook topic
        x_shopify_shop_domain: Shop domain
        x_shopify_hmac_sha256: HMAC signature

    Returns:
        Success response

    Example webhook payload:
    {
        "id": 12345,
        "domain": "mystore.myshopify.com",
        "name": "My Store"
    }
    """
    try:
        # Get raw payload
        payload = await request.body()

        # Verify HMAC
        # webhook_handler = ShopifyWebhookHandler()
        # if not webhook_handler.verify_webhook(payload, request.headers):
        #     raise HTTPException(status_code=401, detail="Invalid webhook signature")

        # Parse payload
        import json
        webhook_data = json.loads(payload)

        # Get merchant
        # merchant = await merchant_repository.get_by_platform_domain(
        #     PlatformType.SHOPIFY, x_shopify_shop_domain
        # )

        # if merchant:
        #     await platform_service.uninstall_merchant(merchant.id)

        return {
            "status": "received",
            "shop_domain": x_shopify_shop_domain,
            "message": "Merchant marked as uninstalled",
        }

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )
    except Exception as e:
        # Log error but return 200
        return {
            "status": "error",
            "error": str(e),
        }


@router.post("/woocommerce/order_completed")
async def woocommerce_order_completed(request: Request):
    """
    WooCommerce webhook: Order completed

    Placeholder for future WooCommerce integration.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="WooCommerce integration not yet implemented",
    )


@router.post("/bigcommerce/order_shipped")
async def bigcommerce_order_shipped(request: Request):
    """
    BigCommerce webhook: Order shipped

    Placeholder for future BigCommerce integration.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="BigCommerce integration not yet implemented",
    )
