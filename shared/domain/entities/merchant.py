"""
Merchant domain model
Represents a merchant/store in the multi-tenant system
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import secrets
import hashlib


class MerchantPlan(Enum):
    """Merchant subscription plans"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class Merchant:
    """
    Merchant domain model

    Represents a merchant account in the system.
    Merchants own reviews and have API keys for authentication.

    Business Rules:
    - Each merchant has a unique email
    - API keys must be unique and secure
    - Active status determines API access
    - Settings stored as flexible JSON
    """

    # Required fields
    email: str
    company_name: str
    created_at: datetime
    updated_at: datetime

    # Optional fields
    id: Optional[str] = None
    api_key: Optional[str] = None
    active: bool = True
    plan: MerchantPlan = MerchantPlan.FREE
    settings: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def generate_api_key() -> str:
        """
        Generate a cryptographically secure API key

        Format: mk_live_<32_random_chars>
        Example: mk_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

        Returns:
            Secure API key string
        """
        random_part = secrets.token_urlsafe(32)
        return f"mk_live_{random_part}"

    def generate_new_api_key(self, current_time: Optional[datetime] = None) -> None:
        """
        Regenerate API key (for security rotation)

        Args:
            current_time: Optional timestamp (for testing)
        """
        self.api_key = self.generate_api_key()
        self.updated_at = current_time or datetime.utcnow()

    def deactivate(self, current_time: Optional[datetime] = None) -> None:
        """
        Deactivate merchant account

        Prevents API access and review collection

        Args:
            current_time: Optional timestamp (for testing)
        """
        self.active = False
        self.updated_at = current_time or datetime.utcnow()

    def activate(self, current_time: Optional[datetime] = None) -> None:
        """
        Activate merchant account

        Args:
            current_time: Optional timestamp (for testing)
        """
        self.active = True
        self.updated_at = current_time or datetime.utcnow()

    def upgrade_plan(self, plan: MerchantPlan, current_time: Optional[datetime] = None) -> None:
        """
        Upgrade/change merchant plan

        Args:
            plan: New plan to upgrade to
            current_time: Optional timestamp (for testing)
        """
        self.plan = plan
        self.updated_at = current_time or datetime.utcnow()

    def update_settings(self, settings: Dict[str, Any], current_time: Optional[datetime] = None) -> None:
        """
        Update merchant settings

        Args:
            settings: New settings dictionary
            current_time: Optional timestamp (for testing)
        """
        self.settings.update(settings)
        self.updated_at = current_time or datetime.utcnow()

    def validate(self) -> None:
        """
        Validate merchant data

        Raises:
            ValueError: If validation fails
        """
        if not self.email or not self.email.strip():
            raise ValueError("email is required")

        if "@" not in self.email:
            raise ValueError("email must be valid")

        if not self.company_name or not self.company_name.strip():
            raise ValueError("company_name is required")

        if len(self.company_name) > 255:
            raise ValueError("company_name must be 255 characters or less")

        if self.api_key and not self.api_key.startswith("mk_live_"):
            raise ValueError("api_key must start with mk_live_")

    def is_active(self) -> bool:
        """Check if merchant is active"""
        return self.active

    def has_feature(self, feature: str) -> bool:
        """
        Check if merchant's plan includes a feature

        Args:
            feature: Feature name to check

        Returns:
            True if feature is available in current plan
        """
        features_by_plan = {
            MerchantPlan.FREE: ["basic_reviews", "widget"],
            MerchantPlan.BASIC: ["basic_reviews", "widget", "ai_moderation", "email_campaigns"],
            MerchantPlan.PRO: ["basic_reviews", "widget", "ai_moderation", "email_campaigns", "advanced_analytics", "custom_branding"],
            MerchantPlan.ENTERPRISE: ["basic_reviews", "widget", "ai_moderation", "email_campaigns", "advanced_analytics", "custom_branding", "priority_support", "custom_integrations"]
        }

        plan_features = features_by_plan.get(self.plan, [])
        return feature in plan_features

    def __repr__(self) -> str:
        return (
            f"Merchant(id={self.id}, email={self.email}, "
            f"company={self.company_name}, plan={self.plan.value}, active={self.active})"
        )
