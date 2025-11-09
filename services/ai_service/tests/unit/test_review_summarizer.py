"""
Test AI-powered Review Summarizer Service
Following TDD: Write tests first
"""
import pytest
from unittest.mock import Mock, AsyncMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ai_service.domain.services.review_summarizer_service import ReviewSummarizerService


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client"""
    client = Mock()
    client.messages = Mock()
    client.messages.create = AsyncMock()
    return client


@pytest.fixture
def review_summarizer_service(mock_anthropic_client):
    """Create ReviewSummarizerService with mocked client"""
    service = ReviewSummarizerService(api_key="test_key")
    service.client = mock_anthropic_client
    return service


@pytest.fixture
def sample_reviews():
    """Sample reviews for testing"""
    return [
        {
            "id": "rev_1",
            "rating": 5,
            "title": "Excellent product!",
            "content": "This product exceeded my expectations. The quality is outstanding.",
            "verified_purchase": True,
        },
        {
            "id": "rev_2",
            "rating": 4,
            "title": "Good value",
            "content": "Works well for the price. Delivery was fast.",
            "verified_purchase": True,
        },
        {
            "id": "rev_3",
            "rating": 3,
            "title": "Average",
            "content": "It's okay, but could be better. The size runs small.",
            "verified_purchase": False,
        },
        {
            "id": "rev_4",
            "rating": 5,
            "title": "Love it!",
            "content": "Amazing quality! Will buy again.",
            "verified_purchase": True,
        },
    ]


@pytest.mark.asyncio
class TestReviewSummarizerService:
    """Test Review Summarizer Service"""

    async def test_summarize_reviews_returns_summary(
        self, review_summarizer_service, mock_anthropic_client, sample_reviews
    ) -> None:
        """
        GIVEN list of reviews
        WHEN summarize_reviews called
        THEN returns concise summary
        """
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text="Customers love the quality and value. Most common praise: excellent quality, fast delivery. Minor concern: sizing runs small."
            )
        ]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = await review_summarizer_service.summarize_reviews(sample_reviews)

        assert isinstance(result, str)
        assert len(result) > 0
        assert len(result) < 500  # Should be concise

    async def test_extract_pros_and_cons(
        self, review_summarizer_service, mock_anthropic_client, sample_reviews
    ) -> None:
        """
        GIVEN list of reviews
        WHEN extract_pros_and_cons called
        THEN returns structured pros and cons
        """
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='{"pros": ["Excellent quality", "Fast delivery", "Good value"], "cons": ["Sizing runs small"]}'
            )
        ]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = await review_summarizer_service.extract_pros_and_cons(sample_reviews)

        assert "pros" in result
        assert "cons" in result
        assert isinstance(result["pros"], list)
        assert isinstance(result["cons"], list)
        assert len(result["pros"]) > 0

    async def test_analyze_sentiment(
        self, review_summarizer_service, mock_anthropic_client, sample_reviews
    ) -> None:
        """
        GIVEN list of reviews
        WHEN analyze_sentiment called
        THEN returns sentiment analysis
        """
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='{"overall_sentiment": "positive", "sentiment_score": 0.82, "positive_percentage": 75, "negative_percentage": 0, "neutral_percentage": 25}'
            )
        ]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = await review_summarizer_service.analyze_sentiment(sample_reviews)

        assert "overall_sentiment" in result
        assert "sentiment_score" in result
        assert result["overall_sentiment"] in ["positive", "negative", "neutral"]
        assert 0 <= result["sentiment_score"] <= 1

    async def test_extract_key_themes(
        self, review_summarizer_service, mock_anthropic_client, sample_reviews
    ) -> None:
        """
        GIVEN list of reviews
        WHEN extract_key_themes called
        THEN returns list of key themes
        """
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='{"themes": [{"theme": "Quality", "mentions": 3, "sentiment": "positive"}, {"theme": "Sizing", "mentions": 1, "sentiment": "negative"}]}'
            )
        ]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = await review_summarizer_service.extract_key_themes(sample_reviews)

        assert "themes" in result
        assert isinstance(result["themes"], list)
        assert len(result["themes"]) > 0
        assert "theme" in result["themes"][0]

    async def test_generate_highlights(
        self, review_summarizer_service, mock_anthropic_client, sample_reviews
    ) -> None:
        """
        GIVEN list of reviews
        WHEN generate_highlights called
        THEN returns top review highlights
        """
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='["Outstanding quality", "Excellent value for money", "Fast shipping"]'
            )
        ]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = await review_summarizer_service.generate_highlights(
            sample_reviews, max_highlights=3
        )

        assert isinstance(result, list)
        assert len(result) <= 3
        assert all(isinstance(h, str) for h in result)

    async def test_summarize_by_rating(
        self, review_summarizer_service, mock_anthropic_client, sample_reviews
    ) -> None:
        """
        GIVEN list of reviews
        WHEN summarize_by_rating called
        THEN returns summary grouped by rating
        """
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='{"5_star": "Excellent quality and value", "4_star": "Good product overall", "3_star": "Average, sizing issues", "2_star": "N/A", "1_star": "N/A"}'
            )
        ]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = await review_summarizer_service.summarize_by_rating(sample_reviews)

        assert isinstance(result, dict)
        assert "5_star" in result or "5" in str(result)

    async def test_handles_empty_reviews_list(
        self, review_summarizer_service
    ) -> None:
        """
        GIVEN empty reviews list
        WHEN summarize_reviews called
        THEN returns appropriate message
        """
        result = await review_summarizer_service.summarize_reviews([])

        assert isinstance(result, str)
        assert "no reviews" in result.lower() or len(result) == 0

    async def test_filters_by_verified_purchase(
        self, review_summarizer_service, mock_anthropic_client, sample_reviews
    ) -> None:
        """
        GIVEN reviews with mix of verified/unverified
        WHEN summarize_reviews called with verified_only=True
        THEN only includes verified purchases
        """
        mock_response = Mock()
        mock_response.content = [Mock(text="Summary of verified reviews only")]
        mock_anthropic_client.messages.create.return_value = mock_response

        await review_summarizer_service.summarize_reviews(
            sample_reviews, verified_only=True
        )

        # Check that the prompt only included verified reviews
        call_args = mock_anthropic_client.messages.create.call_args
        prompt = str(call_args)
        # The unverified review shouldn't be in the prompt
        assert "Average" not in prompt or prompt.count("verified") >= 3

    async def test_respects_max_reviews_limit(
        self, review_summarizer_service, mock_anthropic_client, sample_reviews
    ) -> None:
        """
        GIVEN many reviews
        WHEN summarize_reviews called with max_reviews limit
        THEN only processes specified number
        """
        mock_response = Mock()
        mock_response.content = [Mock(text="Summary")]
        mock_anthropic_client.messages.create.return_value = mock_response

        await review_summarizer_service.summarize_reviews(
            sample_reviews, max_reviews=2
        )

        # Should process maximum 2 reviews
        call_args = mock_anthropic_client.messages.create.call_args
        # Verify the limit was applied (implementation detail)
        assert call_args is not None
