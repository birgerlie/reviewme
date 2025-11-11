"""
Platform Product Entity
Universal product representation across all e-commerce platforms
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class PlatformProduct:
    """
    Platform Product Entity

    Universal representation of a product across different e-commerce platforms.
    Normalized structure allows review collection regardless of platform.
    """

    # Core identification
    id: Optional[str] = None
    merchant_id: str = ""
    platform_product_id: str = ""  # Platform's internal product ID

    # Product Information
    title: str = ""
    description: str = ""
    price: float = 0.0
    currency: str = "USD"

    # Media
    image_url: Optional[str] = None
    images: List[str] = field(default_factory=list)
    url: Optional[str] = None  # Product page URL

    # Variants & Stock
    has_variants: bool = False
    variant_count: int = 0
    in_stock: bool = True

    # Escape hatch for platform-specific data
    platform_metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """
        Validate product data

        Raises:
            ValueError: If validation fails
        """
        if not self.merchant_id:
            raise ValueError("merchant_id is required")

        if not self.platform_product_id:
            raise ValueError("platform_product_id is required")

        if not self.title:
            raise ValueError("title is required")

        if self.price < 0:
            raise ValueError("price must be non-negative")

    def get_primary_image(self) -> Optional[str]:
        """Get primary product image"""
        return self.image_url or (self.images[0] if self.images else None)

    def __repr__(self) -> str:
        return (
            f"PlatformProduct(id={self.id}, merchant_id={self.merchant_id}, "
            f"platform_product_id={self.platform_product_id}, title={self.title})"
        )
