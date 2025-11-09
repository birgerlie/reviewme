"""
Widget API Routes
FastAPI endpoints for widget service
Performance critical: < 100ms p95
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import JSONResponse
from typing import Dict, Any

from widget_service.api.models import (
    WidgetDataResponse,
    WidgetConfigCreateRequest,
    WidgetConfigResponse,
    WidgetConfigUpdateRequest,
)
from widget_service.domain.services.widget_service import WidgetService
from widget_service.domain.models.widget_config import WidgetConfig, WidgetLayout, WidgetTheme
from datetime import datetime

router = APIRouter(tags=["widget"])


# Mock dependencies (to be implemented with real services)
async def get_widget_service() -> WidgetService:
    """Dependency: Get widget service"""
    # This would be properly injected in production
    from unittest.mock import Mock, AsyncMock
    mock_repo = Mock()
    mock_repo.get_by_id = AsyncMock()
    mock_client = Mock()
    mock_cache = Mock()
    return WidgetService(mock_repo, mock_client, mock_cache)


@router.get(
    "/widget/{widget_id}",
    response_model=WidgetDataResponse,
    summary="Get widget data (PUBLIC)",
    description="Public endpoint for widget JavaScript. No authentication required. Heavily cached.",
    response_description="Complete widget data including config, reviews, and ratings",
)
async def get_widget_data(
    widget_id: str,
    response: Response,
    service: WidgetService = Depends(get_widget_service),
) -> WidgetDataResponse:
    """
    Get complete widget data for embedding

    **Performance Critical:**
    - Target: < 100ms p95
    - Heavily cached (10 min CDN + 10 min backend)
    - No authentication required
    - CORS enabled

    **CDN Cache Headers:**
    - Cache-Control: public, max-age=600
    - Vary: Accept-Encoding
    """
    try:
        # Set CDN-friendly cache headers
        response.headers["Cache-Control"] = "public, max-age=600"  # 10 minutes
        response.headers["Vary"] = "Accept-Encoding"
        response.headers["X-Content-Type-Options"] = "nosniff"

        widget_data = await service.get_widget_data(widget_id, use_cache=True)

        if widget_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Widget {widget_id} not found",
            )

        return WidgetDataResponse(**widget_data)

    except ValueError as e:
        # Widget disabled
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load widget: {str(e)}",
        )


@router.post(
    "/api/v1/widgets",
    response_model=WidgetConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create widget configuration",
    description="Create a new widget configuration (requires authentication)",
)
async def create_widget(
    request: WidgetConfigCreateRequest,
    service: WidgetService = Depends(get_widget_service),
) -> WidgetConfigResponse:
    """Create a new widget configuration"""
    try:
        # Create widget config
        widget = WidgetConfig(
            id=None,
            merchant_id=request.merchant_id,
            product_id=request.product_id,
            layout=WidgetLayout(request.layout),
            theme=WidgetTheme(request.theme),
            custom_styles=request.custom_styles,
            display_settings=request.display_settings,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        created_widget = await service.create_widget(widget)

        return WidgetConfigResponse(
            id=created_widget.id,
            merchant_id=created_widget.merchant_id,
            product_id=created_widget.product_id,
            layout=created_widget.layout.value,
            theme=created_widget.theme.value,
            enabled=created_widget.enabled,
            custom_styles=created_widget.custom_styles,
            display_settings=created_widget.display_settings,
            created_at=created_widget.created_at,
            updated_at=created_widget.updated_at,
            cdn_url=created_widget.get_cdn_url(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create widget: {str(e)}",
        )


@router.patch(
    "/api/v1/widgets/{widget_id}",
    response_model=WidgetConfigResponse,
    summary="Update widget configuration",
    description="Update widget configuration (requires authentication)",
)
async def update_widget(
    widget_id: str,
    request: WidgetConfigUpdateRequest,
    service: WidgetService = Depends(get_widget_service),
) -> WidgetConfigResponse:
    """Update widget configuration"""
    try:
        # Build updates dictionary
        updates = {}
        if request.enabled is not None:
            updates["enabled"] = request.enabled
        if request.custom_styles is not None:
            updates["custom_styles"] = request.custom_styles
        if request.display_settings is not None:
            updates["display_settings"] = request.display_settings

        updated_widget = await service.update_widget(widget_id, updates)

        return WidgetConfigResponse(
            id=updated_widget.id,
            merchant_id=updated_widget.merchant_id,
            product_id=updated_widget.product_id,
            layout=updated_widget.layout.value,
            theme=updated_widget.theme.value,
            enabled=updated_widget.enabled,
            custom_styles=updated_widget.custom_styles,
            display_settings=updated_widget.display_settings,
            created_at=updated_widget.created_at,
            updated_at=updated_widget.updated_at,
            cdn_url=updated_widget.get_cdn_url(),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update widget: {str(e)}",
        )


@router.delete(
    "/api/v1/widgets/{widget_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete widget configuration",
    description="Delete widget configuration (requires authentication)",
)
async def delete_widget(
    widget_id: str,
    service: WidgetService = Depends(get_widget_service),
) -> None:
    """Delete widget configuration"""
    try:
        deleted = await service.delete_widget(widget_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Widget {widget_id} not found",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete widget: {str(e)}",
        )


@router.get(
    "/api/v1/widgets/merchant/{merchant_id}/product/{product_id}",
    response_model=WidgetConfigResponse,
    summary="Get widget by product",
    description="Get widget configuration for a specific merchant/product",
)
async def get_widget_by_product(
    merchant_id: str,
    product_id: str,
    service: WidgetService = Depends(get_widget_service),
) -> WidgetConfigResponse:
    """Get widget configuration by merchant and product"""
    try:
        widget = await service.get_widget_by_product(merchant_id, product_id)

        if widget is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No widget found for merchant {merchant_id} and product {product_id}",
            )

        return WidgetConfigResponse(
            id=widget.id,
            merchant_id=widget.merchant_id,
            product_id=widget.product_id,
            layout=widget.layout.value,
            theme=widget.theme.value,
            enabled=widget.enabled,
            custom_styles=widget.custom_styles,
            display_settings=widget.display_settings,
            created_at=widget.created_at,
            updated_at=widget.updated_at,
            cdn_url=widget.get_cdn_url(),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get widget: {str(e)}",
        )
