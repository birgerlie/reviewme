"""
Test Widget Service
Following TDD: Write tests first
"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from widget_service.domain.services.widget_service import WidgetService
from widget_service.domain.models.widget_config import (
    WidgetConfig,
    WidgetLayout,
    WidgetTheme,
)


@pytest.fixture
def mock_widget_repo():
    """Mock widget repository"""
    repo = Mock()
    repo.get_by_id = AsyncMock()
    repo.get_by_merchant_and_product = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def mock_review_service_client():
    """Mock review service client"""
    client = Mock()
    client.get_reviews = AsyncMock()
    client.get_rating = AsyncMock()
    return client


@pytest.fixture
def mock_cache():
    """Mock cache service"""
    cache = Mock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    cache.delete = AsyncMock()
    return cache


@pytest.fixture
def widget_service(mock_widget_repo, mock_review_service_client, mock_cache):
    """Create WidgetService with mocked dependencies"""
    return WidgetService(
        widget_repository=mock_widget_repo,
        review_service_client=mock_review_service_client,
        cache_service=mock_cache,
    )


@pytest.fixture
def sample_widget_config():
    """Sample widget configuration"""
    return WidgetConfig(
        id="widget_123",
        merchant_id="merchant_456",
        product_id="prod_789",
        layout=WidgetLayout.GRID,
        theme=WidgetTheme.LIGHT,
        enabled=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.mark.asyncio
class TestWidgetService:
    """Test Widget Service business logic"""

    async def test_get_widget_data_returns_complete_payload(
        self,
        widget_service,
        mock_widget_repo,
        mock_review_service_client,
        sample_widget_config,
    ) -> None:
        """
        GIVEN valid widget ID
        WHEN get_widget_data called
        THEN returns complete widget payload with config and reviews
        """
        mock_widget_repo.get_by_id.return_value = sample_widget_config
        mock_review_service_client.get_reviews.return_value = [
            {"id": "rev_1", "rating": 5, "content": "Great!"}
        ]
        mock_review_service_client.get_rating.return_value = {
            "average_rating": 4.5,
            "total_reviews": 10,
        }

        result = await widget_service.get_widget_data("widget_123")

        assert "config" in result
        assert "reviews" in result
        assert "rating" in result
        assert result["config"]["id"] == "widget_123"
        assert len(result["reviews"]) == 1
        assert result["rating"]["average_rating"] == 4.5

    async def test_get_widget_data_uses_cache(
        self, widget_service, mock_cache, mock_widget_repo
    ) -> None:
        """
        Performance: Use cache when available
        GIVEN widget data in cache
        WHEN get_widget_data called
        THEN returns cached data without DB/API calls
        """
        cached_data = {
            "config": {"id": "widget_123"},
            "reviews": [],
            "rating": {"average_rating": 4.5},
        }
        mock_cache.get.return_value = cached_data

        result = await widget_service.get_widget_data("widget_123", use_cache=True)

        assert result == cached_data
        mock_widget_repo.get_by_id.assert_not_called()

    async def test_get_widget_data_caches_results(
        self,
        widget_service,
        mock_cache,
        mock_widget_repo,
        mock_review_service_client,
        sample_widget_config,
    ) -> None:
        """
        Performance: Cache results for fast subsequent requests
        GIVEN widget data not in cache
        WHEN get_widget_data called
        THEN caches the result
        """
        mock_cache.get.return_value = None
        mock_widget_repo.get_by_id.return_value = sample_widget_config
        mock_review_service_client.get_reviews.return_value = []
        mock_review_service_client.get_rating.return_value = {
            "average_rating": 0.0,
            "total_reviews": 0,
        }

        await widget_service.get_widget_data("widget_123")

        mock_cache.set.assert_called_once()
        # Verify cache TTL is set for performance (10 minutes = 600s)
        call_args = mock_cache.set.call_args
        assert call_args[0][2] == 600  # TTL

    async def test_get_widget_data_disabled_widget_returns_error(
        self, widget_service, mock_widget_repo
    ) -> None:
        """
        GIVEN disabled widget
        WHEN get_widget_data called
        THEN raises ValueError
        """
        disabled_widget = WidgetConfig(
            id="widget_123",
            merchant_id="merchant_456",
            product_id="prod_789",
            layout=WidgetLayout.GRID,
            theme=WidgetTheme.LIGHT,
            enabled=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_widget_repo.get_by_id.return_value = disabled_widget

        with pytest.raises(ValueError, match="disabled"):
            await widget_service.get_widget_data("widget_123")

    async def test_get_widget_data_not_found_returns_none(
        self, widget_service, mock_widget_repo
    ) -> None:
        """
        GIVEN non-existent widget ID
        WHEN get_widget_data called
        THEN returns None
        """
        mock_widget_repo.get_by_id.return_value = None

        result = await widget_service.get_widget_data("nonexistent")

        assert result is None

    async def test_create_widget_config(
        self, widget_service, mock_widget_repo
    ) -> None:
        """
        GIVEN valid widget configuration
        WHEN create_widget called
        THEN creates and returns widget config
        """
        new_config = WidgetConfig(
            id=None,
            merchant_id="merchant_456",
            product_id="prod_789",
            layout=WidgetLayout.LIST,
            theme=WidgetTheme.DARK,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        created_config = WidgetConfig(**{**new_config.__dict__, "id": "widget_new"})
        mock_widget_repo.create.return_value = created_config

        result = await widget_service.create_widget(new_config)

        assert result.id == "widget_new"
        assert result.merchant_id == "merchant_456"

    async def test_update_widget_invalidates_cache(
        self, widget_service, mock_cache, mock_widget_repo, sample_widget_config
    ) -> None:
        """
        GIVEN widget update
        WHEN update_widget called
        THEN invalidates cache for that widget
        """
        mock_widget_repo.get_by_id.return_value = sample_widget_config
        mock_widget_repo.update.return_value = sample_widget_config

        await widget_service.update_widget("widget_123", {"enabled": False})

        mock_cache.delete.assert_called_with("widget:data:widget_123")

    async def test_get_widget_by_product_returns_config(
        self, widget_service, mock_widget_repo, sample_widget_config
    ) -> None:
        """
        GIVEN merchant and product IDs
        WHEN get_widget_by_product called
        THEN returns widget configuration
        """
        mock_widget_repo.get_by_merchant_and_product.return_value = sample_widget_config

        result = await widget_service.get_widget_by_product(
            "merchant_456", "prod_789"
        )

        assert result.id == "widget_123"
        assert result.product_id == "prod_789"

    async def test_performance_get_widget_data_response_time(
        self,
        widget_service,
        mock_widget_repo,
        mock_review_service_client,
        sample_widget_config,
    ) -> None:
        """
        Performance test: Ensure fast response (< 100ms without network)
        GIVEN widget request
        WHEN get_widget_data called
        THEN completes quickly
        """
        import time

        mock_widget_repo.get_by_id.return_value = sample_widget_config
        mock_review_service_client.get_reviews.return_value = []
        mock_review_service_client.get_rating.return_value = {
            "average_rating": 4.5,
            "total_reviews": 10,
        }

        start_time = time.time()
        await widget_service.get_widget_data("widget_123", use_cache=False)
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms

        # Without network latency, should be very fast (< 10ms)
        assert elapsed_time < 10, f"Response time {elapsed_time}ms too slow"
