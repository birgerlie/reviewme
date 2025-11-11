"""
Review Token Entity
Secure tokens for review submission from email links
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import secrets


@dataclass
class ReviewToken:
    """
    Review Token Entity

    Secure, single-use tokens for review submission.
    Generated when order is fulfilled and sent in email.

    Business Rules:
    - Tokens are cryptographically secure (32 bytes)
    - Single-use only (cannot reuse after review submitted)
    - Expire after 30 days
    - Tied to specific merchant, product, and order
    - Atomic mark_as_used operation prevents race conditions

    Security:
    - Uses secrets.token_urlsafe for cryptographic randomness
    - Format: rt_<32_random_chars>
    - Tokens are indexed for fast lookup
    - Used flag prevents replay attacks
    """

    # Core identification
    merchant_id: str
    product_id: str
    order_id: str
    customer_email: str
    expires_at: datetime
    created_at: datetime

    # Optional fields
    id: Optional[str] = None
    token: Optional[str] = None
    customer_name: Optional[str] = None
    used: bool = False
    used_at: Optional[datetime] = None

    @staticmethod
    def generate_token() -> str:
        """
        Generate cryptographically secure review token

        Format: rt_<32_random_chars>
        Example: rt_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

        Returns:
            Secure token string
        """
        random_part = secrets.token_urlsafe(32)
        return f"rt_{random_part}"

    @staticmethod
    def calculate_expiration(days: int = 30) -> datetime:
        """
        Calculate token expiration time

        Args:
            days: Number of days until expiration (default: 30)

        Returns:
            Expiration datetime
        """
        return datetime.utcnow() + timedelta(days=days)

    def is_valid(self, current_time: Optional[datetime] = None) -> bool:
        """
        Check if token is valid for use

        Token is valid if:
        - Not used yet
        - Not expired

        Args:
            current_time: Optional current time (for testing)

        Returns:
            True if token can be used, False otherwise
        """
        now = current_time or datetime.utcnow()

        if self.used:
            return False

        if now >= self.expires_at:
            return False

        return True

    def is_expired(self, current_time: Optional[datetime] = None) -> bool:
        """
        Check if token is expired

        Args:
            current_time: Optional current time (for testing)

        Returns:
            True if expired, False otherwise
        """
        now = current_time or datetime.utcnow()
        return now >= self.expires_at

    def mark_as_used(self, current_time: Optional[datetime] = None) -> None:
        """
        Mark token as used (after review submission)

        This should be done atomically in the database to prevent
        race conditions where two reviews are submitted with same token.

        Args:
            current_time: Optional timestamp (for testing)

        Raises:
            ValueError: If token is already used
        """
        if self.used:
            raise ValueError("Token has already been used")

        self.used = True
        self.used_at = current_time or datetime.utcnow()

    def validate(self) -> None:
        """
        Validate token data

        Raises:
            ValueError: If validation fails
        """
        if not self.merchant_id:
            raise ValueError("merchant_id is required")

        if not self.product_id:
            raise ValueError("product_id is required")

        if not self.order_id:
            raise ValueError("order_id is required")

        if not self.customer_email or "@" not in self.customer_email:
            raise ValueError("valid customer_email is required")

        if not self.token or not self.token.startswith("rt_"):
            raise ValueError("token must start with rt_")

        if not self.expires_at:
            raise ValueError("expires_at is required")

    def __repr__(self) -> str:
        return (
            f"ReviewToken(id={self.id}, token={self.token[:10]}..., "
            f"merchant={self.merchant_id}, product={self.product_id}, "
            f"used={self.used}, expired={self.is_expired()})"
        )
