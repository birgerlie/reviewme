"""
Auth Provider Interface
Defines the contract for platform OAuth flows
"""
from abc import ABC, abstractmethod
from typing import Tuple, List, Dict, Any


class IAuthProvider(ABC):
    """
    Auth Provider Interface

    Defines methods for OAuth authentication flows with e-commerce platforms.
    Each platform has different OAuth implementations, but this interface
    provides a unified contract.

    OAuth Flow:
    1. get_authorization_url() → User clicks "Install"
    2. Platform redirects to callback with code
    3. exchange_code_for_token() → Get access token
    4. Store token → Use for API calls
    """

    @abstractmethod
    def get_authorization_url(
        self, shop_domain: str, redirect_uri: str, scopes: List[str], state: str = ""
    ) -> str:
        """
        Generate OAuth authorization URL

        User is redirected to this URL to approve app installation

        Args:
            shop_domain: Shop/store domain (e.g., "mystore.myshopify.com")
            redirect_uri: Where platform redirects after approval
            scopes: Permissions requested (e.g., ["read_orders", "write_products"])
            state: CSRF protection token

        Returns:
            Full OAuth authorization URL

        Example:
            https://mystore.myshopify.com/admin/oauth/authorize
            ?client_id=xxx&scope=read_orders,read_products&redirect_uri=xxx
        """
        pass

    @abstractmethod
    async def exchange_code_for_token(
        self, code: str, shop_domain: str
    ) -> Tuple[str, List[str]]:
        """
        Exchange authorization code for access token

        Called after user approves installation

        Args:
            code: Authorization code from OAuth callback
            shop_domain: Shop/store domain

        Returns:
            Tuple of (access_token, granted_scopes)

        Raises:
            ValueError: If code is invalid
            ConnectionError: If API call fails
        """
        pass

    @abstractmethod
    def verify_request(self, params: Dict[str, Any], signature: str) -> bool:
        """
        Verify request authenticity (HMAC/signature check)

        Ensures requests actually come from the platform and haven't been tampered with

        Args:
            params: Query parameters or request body
            signature: Signature/HMAC from request headers

        Returns:
            True if request is authentic, False otherwise
        """
        pass

    @abstractmethod
    async def get_shop_info(self, shop_domain: str, access_token: str) -> Dict[str, Any]:
        """
        Get shop/store information after OAuth

        Used to populate merchant details (name, email, currency, etc.)

        Args:
            shop_domain: Shop/store domain
            access_token: OAuth access token

        Returns:
            Dictionary with shop information

        Raises:
            ConnectionError: If API call fails
        """
        pass
