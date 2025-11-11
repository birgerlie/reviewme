"""
Platform Service - Business Logic Layer
Core orchestration for platform integrations
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from platform_service.domain.interfaces.i_platform_client import IPlatformClient
from platform_service.domain.interfaces.i_auth_provider import IAuthProvider
from platform_service.domain.interfaces.i_webhook_handler import IWebhookHandler
from platform_service.domain.entities.platform_merchant import PlatformMerchant, PlatformType
from platform_service.domain.entities.platform_product import PlatformProduct
from platform_service.domain.entities.platform_order import PlatformOrder
from shared.domain.entities.review_token import ReviewToken
from shared.domain.interfaces.review_token_repository_interface import IReviewTokenRepository
from review_service.domain.interfaces.event_bus_interface import IEventBus


class PlatformService:
    """
    Platform Service

    Platform-agnostic business logic for e-commerce integrations.
    This service orchestrates OAuth, webhooks, and review collection
    without knowing about specific platforms (Shopify, WooCommerce, etc.)

    Key Principle: Depend on interfaces, not implementations.
    All platform-specific code is injected via constructor.

    Business Rules:
    - Merchants install via OAuth flow
    - Webhooks trigger review requests (7 days after fulfillment)
    - Review tokens are single-use and expire in 30 days
    - Events published for all state changes
    """

    def __init__(
        self,
        platform_client: IPlatformClient,
        auth_provider: IAuthProvider,
        webhook_handler: IWebhookHandler,
        token_repository: IReviewTokenRepository,
        event_bus: IEventBus,
        platform_merchant_repository=None,  # Will be IMerchantRepository
    ):
        """
        Initialize platform service with dependencies

        Args:
            platform_client: Platform API client (abstracted)
            auth_provider: OAuth provider (abstracted)
            webhook_handler: Webhook handler (abstracted)
            token_repository: Review token repository
            event_bus: Event bus for publishing events
            platform_merchant_repository: Platform merchant repository
        """
        self.platform_client = platform_client
        self.auth_provider = auth_provider
        self.webhook_handler = webhook_handler
        self.token_repository = token_repository
        self.event_bus = event_bus
        self.platform_merchant_repository = platform_merchant_repository

    async def install_merchant(
        self, code: str, shop_domain: str, platform: PlatformType
    ) -> PlatformMerchant:
        """
        Install merchant (complete OAuth flow)

        This method is PLATFORM AGNOSTIC - works for Shopify, WooCommerce, etc.

        Flow:
        1. Exchange authorization code for access token
        2. Get shop/store details from platform API
        3. Create PlatformMerchant entity
        4. Save to repository
        5. Register webhooks
        6. Publish "merchant.installed" event

        Args:
            code: OAuth authorization code
            shop_domain: Shop/store domain
            platform: Platform type

        Returns:
            Created PlatformMerchant

        Raises:
            ValueError: If OAuth fails
            ConnectionError: If API calls fail
        """
        # Step 1: Exchange code for token
        access_token, granted_scopes = await self.auth_provider.exchange_code_for_token(
            code, shop_domain
        )

        # Step 2: Get shop information
        shop_info = await self.auth_provider.get_shop_info(shop_domain, access_token)

        # Step 3: Create merchant entity
        merchant = PlatformMerchant(
            platform=platform,
            platform_domain=shop_domain,
            platform_merchant_id=shop_info["shop_id"],
            access_token=access_token,
            scopes=granted_scopes,
            store_name=shop_info["name"],
            email=shop_info["email"],
            currency=shop_info.get("currency", "USD"),
            timezone=shop_info.get("timezone", "UTC"),
            installed_at=datetime.utcnow(),
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            platform_metadata=shop_info.get("raw", {}),
        )

        # Validate
        merchant.validate()

        # Step 4: Save to repository
        # if self.platform_merchant_repository:
        #     merchant = await self.platform_merchant_repository.create(merchant)

        # Step 5: Register webhooks
        # webhook_url = f"https://api.yourdomain.com/webhooks/{platform.value}"
        # webhook_ids = await self.webhook_handler.register_webhooks(
        #     merchant.id, access_token, webhook_url
        # )

        # Step 6: Publish event
        await self.event_bus.publish(
            "merchant.installed",
            {
                "merchant_id": merchant.id,
                "platform": platform.value,
                "shop_domain": shop_domain,
                "store_name": merchant.store_name,
                "installed_at": merchant.installed_at.isoformat(),
            },
        )

        return merchant

    async def handle_order_fulfilled(
        self, merchant_id: str, order_id: str, schedule_days: int = 7
    ) -> List[str]:
        """
        Handle order fulfilled event

        This method is PLATFORM AGNOSTIC - works for any platform.

        Flow:
        1. Get order details from platform API (abstracted!)
        2. For each product in order:
           - Generate review token
           - Schedule review request email (7 days)
        3. Publish events

        Args:
            merchant_id: Internal merchant ID
            order_id: Platform's order ID
            schedule_days: Days to wait before sending email (default: 7)

        Returns:
            List of token IDs created

        Raises:
            ValueError: If merchant or order not found
        """
        # Step 1: Get order from platform API (abstracted!)
        order = await self.platform_client.get_order(merchant_id, order_id)

        token_ids = []

        # Step 2: For each product, create review token
        for line_item in order.line_items:
            # Generate token
            token = ReviewToken(
                merchant_id=merchant_id,
                product_id=line_item.product_id,
                order_id=order.platform_order_id,
                customer_email=order.customer_email,
                customer_name=order.customer_name,
                token=ReviewToken.generate_token(),
                expires_at=ReviewToken.calculate_expiration(days=30),
                created_at=datetime.utcnow(),
                used=False,
            )

            # Validate and save
            token.validate()
            created_token = await self.token_repository.create(token)
            token_ids.append(created_token.id)

            # Step 3: Publish event to schedule email
            send_at = datetime.utcnow() + timedelta(days=schedule_days)
            await self.event_bus.publish(
                "review.request.scheduled",
                {
                    "token_id": created_token.id,
                    "token": created_token.token,
                    "merchant_id": merchant_id,
                    "product_id": line_item.product_id,
                    "customer_email": order.customer_email,
                    "customer_name": order.customer_name,
                    "order_id": order.platform_order_id,
                    "send_at": send_at.isoformat(),
                },
            )

        return token_ids

    async def uninstall_merchant(self, merchant_id: str) -> None:
        """
        Handle merchant uninstallation

        This method is PLATFORM AGNOSTIC.

        Flow:
        1. Get merchant from repository
        2. Delete webhooks via platform API
        3. Mark merchant as inactive
        4. Publish "merchant.uninstalled" event

        Args:
            merchant_id: Internal merchant ID
        """
        # Step 1: Get merchant
        # if self.platform_merchant_repository:
        #     merchant = await self.platform_merchant_repository.get_by_id(merchant_id)
        #     if not merchant:
        #         raise ValueError(f"Merchant {merchant_id} not found")

        # Step 2: Delete webhooks
        # webhook_ids = merchant.platform_metadata.get("webhook_ids", [])
        # await self.webhook_handler.delete_webhooks(
        #     merchant_id, webhook_ids, merchant.access_token
        # )

        # Step 3: Deactivate merchant
        # merchant.deactivate()
        # await self.platform_merchant_repository.update(merchant)

        # Step 4: Publish event
        await self.event_bus.publish(
            "merchant.uninstalled",
            {
                "merchant_id": merchant_id,
                "uninstalled_at": datetime.utcnow().isoformat(),
            },
        )

    async def get_product_details(
        self, merchant_id: str, product_id: str
    ) -> PlatformProduct:
        """
        Get product details

        This method is PLATFORM AGNOSTIC - works for any platform.

        Args:
            merchant_id: Internal merchant ID
            product_id: Platform's product ID

        Returns:
            Universal PlatformProduct entity

        Raises:
            ValueError: If product not found
        """
        return await self.platform_client.get_product(merchant_id, product_id)

    async def validate_review_token(self, token: str) -> Optional[ReviewToken]:
        """
        Validate review token for submission

        Args:
            token: Token string from email link

        Returns:
            ReviewToken if valid, None otherwise
        """
        review_token = await self.token_repository.get_by_token(token)

        if not review_token:
            return None

        if not review_token.is_valid():
            return None

        return review_token

    async def mark_token_used(self, token: str) -> bool:
        """
        Mark review token as used (after review submission)

        Args:
            token: Token string

        Returns:
            True if marked successfully, False if already used or not found
        """
        return await self.token_repository.mark_as_used(token)
