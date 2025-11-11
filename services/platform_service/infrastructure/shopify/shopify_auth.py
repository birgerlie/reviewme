"""
Shopify OAuth Authentication Provider
Implements OAuth 2.0 flow for Shopify apps
"""
import hmac
import hashlib
import urllib.parse
from typing import Tuple, List, Dict, Any
import httpx

from platform_service.domain.interfaces.i_auth_provider import IAuthProvider
from shared.config.settings import get_settings


class ShopifyAuthProvider(IAuthProvider):
    """
    Shopify OAuth Provider

    Implements Shopify's OAuth 2.0 flow with HMAC verification.

    Security:
    - All requests verified with HMAC-SHA256
    - State parameter for CSRF protection
    - Secure token exchange over HTTPS

    References:
    https://shopify.dev/docs/apps/auth/oauth
    """

    def __init__(self, api_key: str = None, api_secret: str = None):
        """
        Initialize Shopify auth provider

        Args:
            api_key: Shopify API key (optional, defaults to settings)
            api_secret: Shopify API secret (optional, defaults to settings)
        """
        settings = get_settings()
        self.api_key = api_key or settings.shopify_api_key
        self.api_secret = api_secret or settings.shopify_api_secret
        self.api_version = "2024-01"  # Shopify API version

    def get_authorization_url(
        self, shop_domain: str, redirect_uri: str, scopes: List[str], state: str = ""
    ) -> str:
        """
        Generate Shopify OAuth authorization URL

        Args:
            shop_domain: Shopify shop domain (e.g., "mystore.myshopify.com")
            redirect_uri: Where Shopify redirects after approval
            scopes: Permissions requested
            state: CSRF protection token

        Returns:
            Full OAuth authorization URL

        Example:
            https://mystore.myshopify.com/admin/oauth/authorize
            ?client_id=xxx&scope=read_orders,read_products&redirect_uri=xxx&state=xxx
        """
        # Ensure shop domain has .myshopify.com
        if not shop_domain.endswith(".myshopify.com"):
            shop_domain = f"{shop_domain}.myshopify.com"

        # Build OAuth URL
        params = {
            "client_id": self.api_key,
            "scope": ",".join(scopes),
            "redirect_uri": redirect_uri,
        }

        if state:
            params["state"] = state

        query_string = urllib.parse.urlencode(params)
        return f"https://{shop_domain}/admin/oauth/authorize?{query_string}"

    async def exchange_code_for_token(
        self, code: str, shop_domain: str
    ) -> Tuple[str, List[str]]:
        """
        Exchange authorization code for access token

        Args:
            code: Authorization code from OAuth callback
            shop_domain: Shopify shop domain

        Returns:
            Tuple of (access_token, granted_scopes)

        Raises:
            ValueError: If code is invalid
            ConnectionError: If API call fails
        """
        # Ensure shop domain has .myshopify.com
        if not shop_domain.endswith(".myshopify.com"):
            shop_domain = f"{shop_domain}.myshopify.com"

        # Token exchange endpoint
        url = f"https://{shop_domain}/admin/oauth/access_token"

        # Request body
        data = {
            "client_id": self.api_key,
            "client_secret": self.api_secret,
            "code": code,
        }

        # Make API call
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=data, timeout=10.0)
                response.raise_for_status()

                result = response.json()
                access_token = result["access_token"]
                granted_scopes = result["scope"].split(",")

                return access_token, granted_scopes

            except httpx.HTTPStatusError as e:
                raise ValueError(f"Invalid authorization code: {e.response.text}")
            except httpx.RequestError as e:
                raise ConnectionError(f"Failed to exchange token: {str(e)}")

    def verify_request(self, params: Dict[str, Any], signature: str) -> bool:
        """
        Verify Shopify request HMAC signature

        Shopify signs all requests with HMAC-SHA256.
        This prevents request tampering and verifies authenticity.

        Args:
            params: Query parameters from request
            signature: HMAC signature from 'hmac' query param

        Returns:
            True if signature is valid, False otherwise

        Algorithm:
        1. Remove 'hmac' and 'signature' from params
        2. Sort params alphabetically
        3. Create query string: key1=value1&key2=value2
        4. Compute HMAC-SHA256 with API secret
        5. Compare with provided signature
        """
        # Copy params to avoid mutation
        params_copy = dict(params)

        # Remove hmac and signature params
        params_copy.pop("hmac", None)
        params_copy.pop("signature", None)

        # Sort params alphabetically and build query string
        sorted_params = sorted(params_copy.items())
        query_string = "&".join(f"{key}={value}" for key, value in sorted_params)

        # Compute HMAC-SHA256
        computed_hmac = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(computed_hmac, signature)

    async def get_shop_info(self, shop_domain: str, access_token: str) -> Dict[str, Any]:
        """
        Get shop information from Shopify API

        Args:
            shop_domain: Shopify shop domain
            access_token: OAuth access token

        Returns:
            Dictionary with shop information:
            {
                "shop_id": "12345",
                "name": "My Store",
                "email": "owner@example.com",
                "domain": "mystore.myshopify.com",
                "currency": "USD",
                "timezone": "America/New_York",
                "plan_name": "basic"
            }

        Raises:
            ConnectionError: If API call fails
        """
        # Ensure shop domain has .myshopify.com
        if not shop_domain.endswith(".myshopify.com"):
            shop_domain = f"{shop_domain}.myshopify.com"

        # Shop info endpoint
        url = f"https://{shop_domain}/admin/api/{self.api_version}/shop.json"

        # Headers
        headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json",
        }

        # Make API call
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, timeout=10.0)
                response.raise_for_status()

                shop_data = response.json()["shop"]

                # Transform to universal format
                return {
                    "shop_id": str(shop_data["id"]),
                    "name": shop_data["name"],
                    "email": shop_data["email"],
                    "domain": shop_data["domain"],
                    "currency": shop_data["currency"],
                    "timezone": shop_data["iana_timezone"],
                    "plan_name": shop_data.get("plan_name", "unknown"),
                    "raw": shop_data,  # Full Shopify response
                }

            except httpx.HTTPStatusError as e:
                raise ConnectionError(f"Failed to get shop info: {e.response.text}")
            except httpx.RequestError as e:
                raise ConnectionError(f"Failed to get shop info: {str(e)}")
