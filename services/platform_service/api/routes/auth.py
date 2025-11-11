"""
Authentication Routes
Handles OAuth flows for platform installations
"""
from fastapi import APIRouter, HTTPException, Query, Depends, status
from fastapi.responses import RedirectResponse
from typing import Optional

from platform_service.domain.entities.platform_merchant import PlatformType
from platform_service.domain.services.platform_service import PlatformService
from platform_service.infrastructure.shopify.shopify_auth import ShopifyAuthProvider
from platform_service.api.dependencies import get_platform_service, get_shopify_auth_provider


router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/{platform}/install")
async def install_redirect(
    platform: str,
    shop: str = Query(..., description="Shop domain (e.g., mystore.myshopify.com)"),
    redirect_uri: Optional[str] = Query(None, description="Custom redirect URI"),
    auth_provider: ShopifyAuthProvider = Depends(get_shopify_auth_provider),
):
    """
    Step 1: Redirect merchant to platform OAuth consent screen

    Flow:
    1. Merchant clicks "Install App"
    2. This endpoint generates OAuth URL
    3. Redirects to Shopify/WooCommerce/etc. for approval
    4. Platform redirects back to /auth/{platform}/callback

    Args:
        platform: Platform type (shopify, woocommerce, etc.)
        shop: Shop domain
        redirect_uri: Optional custom redirect URI

    Returns:
        Redirect to platform OAuth URL

    Example:
        GET /auth/shopify/install?shop=mystore.myshopify.com
        → Redirects to Shopify OAuth page
    """
    try:
        # Validate platform
        if platform not in ["shopify", "woocommerce", "bigcommerce"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported platform: {platform}",
            )

        # Get platform-specific auth provider
        # This would be injected via dependency injection in production
        # For now, placeholder logic

        # Generate state for CSRF protection
        import secrets
        state = secrets.token_urlsafe(32)

        # Store state in session/cache for verification
        # cache.set(f"oauth_state:{state}", {"shop": shop, "platform": platform}, ttl=600)

        # Generate OAuth URL
        if platform == "shopify":
            # Shopify-specific OAuth URL
            scopes = ["read_orders", "read_products", "write_products"]
            callback_uri = redirect_uri or f"https://api.yourdomain.com/auth/shopify/callback"

            # Would use ShopifyAuthProvider here
            # oauth_url = auth_provider.get_authorization_url(shop, callback_uri, scopes, state)

            oauth_url = f"https://{shop}/admin/oauth/authorize?client_id=YOUR_API_KEY&scope={','.join(scopes)}&redirect_uri={callback_uri}&state={state}"

        else:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=f"Platform {platform} not yet implemented",
            )

        return RedirectResponse(url=oauth_url, status_code=status.HTTP_302_FOUND)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate OAuth: {str(e)}",
        )


@router.get("/{platform}/callback")
async def oauth_callback(
    platform: str,
    code: str = Query(..., description="OAuth authorization code"),
    shop: str = Query(..., description="Shop domain"),
    state: Optional[str] = Query(None, description="CSRF protection token"),
    hmac: Optional[str] = Query(None, description="HMAC signature (Shopify)"),
    platform_service: PlatformService = Depends(get_platform_service),
    auth_provider: ShopifyAuthProvider = Depends(get_shopify_auth_provider),
):
    """
    Step 2: OAuth callback endpoint

    Platform redirects here after merchant approves installation.

    Flow:
    1. Verify HMAC/signature (security)
    2. Verify state token (CSRF protection)
    3. Exchange code for access token
    4. Get shop info from platform API
    5. Create merchant in database
    6. Register webhooks
    7. Redirect to success page

    Args:
        platform: Platform type
        code: Authorization code from OAuth flow
        shop: Shop domain
        state: CSRF token
        hmac: HMAC signature (for Shopify)

    Returns:
        Redirect to success page

    Example:
        GET /auth/shopify/callback?code=abc123&shop=mystore.myshopify.com&state=xyz789&hmac=...
        → Creates merchant, registers webhooks
        → Redirects to "Installation complete!" page
    """
    try:
        # Validate platform
        if platform not in ["shopify", "woocommerce", "bigcommerce"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported platform: {platform}",
            )

        # Step 1: Verify HMAC (for Shopify)
        if platform == "shopify":
            # Build query params dict for verification
            query_params = {"code": code, "shop": shop, "state": state or "", "hmac": hmac or ""}
            if not auth_provider.verify_request(query_params, hmac or ""):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid HMAC signature",
                )

        # Step 2: Verify state token (CSRF protection)
        # TODO: Implement state verification with cache/session
        # stored_state = cache.get(f"oauth_state:{state}")
        # if not stored_state or stored_state["shop"] != shop:
        #     raise HTTPException(status_code=401, detail="Invalid state token")

        # Step 3-7: Use PlatformService to complete installation
        platform_type = PlatformType(platform)
        merchant = await platform_service.install_merchant(code, shop, platform_type)

        # Success! Redirect to merchant dashboard
        # TODO: Update with actual frontend URL from settings
        return RedirectResponse(
            url=f"https://yourdomain.com/dashboard?merchant_id={merchant.id}&status=installed",
            status_code=status.HTTP_302_FOUND,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth failed: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Installation failed: {str(e)}",
        )


@router.post("/{platform}/uninstall")
async def uninstall(
    platform: str,
    merchant_id: str,
    platform_service: PlatformService = Depends(get_platform_service),
):
    """
    Uninstall app for merchant

    Args:
        platform: Platform type
        merchant_id: Merchant identifier

    Returns:
        Success response
    """
    try:
        # Use PlatformService to handle uninstallation
        await platform_service.uninstall_merchant(merchant_id)

        return {
            "status": "uninstalled",
            "merchant_id": merchant_id,
            "message": "App successfully uninstalled",
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant not found: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Uninstallation failed: {str(e)}",
        )
