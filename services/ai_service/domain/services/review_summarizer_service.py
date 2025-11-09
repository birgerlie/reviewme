"""
AI-Powered Review Summarizer Service
Uses Anthropic Claude to analyze and summarize reviews
Provides insights similar to Yotpo's AI features
"""
import json
from typing import List, Dict, Any, Optional
from anthropic import AsyncAnthropic

from shared.config.settings import get_settings


class ReviewSummarizerService:
    """
    AI-Powered Review Summarizer

    Analyzes customer reviews to extract:
    - Summary of overall sentiment
    - Pros and cons
    - Key themes and topics
    - Sentiment analysis
    - Review highlights

    Business Value:
    - Helps customers make informed decisions
    - Surfaces common themes automatically
    - Reduces time to understand product quality
    - Competitive feature matching Yotpo
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        """
        Initialize service with Anthropic API key

        Args:
            api_key: Anthropic API key (optional, uses settings if not provided)
        """
        settings = get_settings()
        self.api_key = api_key or settings.anthropic_api_key
        self.model = settings.anthropic_model
        self.max_tokens = settings.anthropic_max_tokens

        if not self.api_key:
            raise ValueError("Anthropic API key is required")

        self.client = AsyncAnthropic(api_key=self.api_key)

    async def summarize_reviews(
        self,
        reviews: List[Dict[str, Any]],
        max_reviews: Optional[int] = None,
        verified_only: bool = False,
    ) -> str:
        """
        Generate a concise summary of reviews

        Args:
            reviews: List of review dictionaries
            max_reviews: Maximum number of reviews to process
            verified_only: Only include verified purchases

        Returns:
            str: Concise summary of reviews
        """
        if not reviews:
            return "No reviews available"

        # Filter and limit reviews
        filtered_reviews = self._filter_reviews(reviews, verified_only, max_reviews)

        if not filtered_reviews:
            return "No reviews available"

        # Build prompt
        prompt = self._build_summary_prompt(filtered_reviews)

        # Call Claude API
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=512,  # Summaries should be concise
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text.strip()

    async def extract_pros_and_cons(
        self,
        reviews: List[Dict[str, Any]],
        max_reviews: Optional[int] = None,
        verified_only: bool = False,
    ) -> Dict[str, List[str]]:
        """
        Extract pros and cons from reviews

        Args:
            reviews: List of review dictionaries
            max_reviews: Maximum number of reviews to process
            verified_only: Only include verified purchases

        Returns:
            Dict with 'pros' and 'cons' lists
        """
        if not reviews:
            return {"pros": [], "cons": []}

        filtered_reviews = self._filter_reviews(reviews, verified_only, max_reviews)

        prompt = f"""Analyze these customer reviews and extract the main PROS and CONS:

Reviews:
{self._format_reviews_for_prompt(filtered_reviews)}

Return ONLY a JSON object with this structure:
{{
  "pros": ["list of positive points"],
  "cons": ["list of negative points"]
}}

Focus on the most frequently mentioned points. Be concise and specific."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            return json.loads(response.content[0].text)
        except json.JSONDecodeError:
            return {"pros": [], "cons": []}

    async def analyze_sentiment(
        self, reviews: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze overall sentiment of reviews

        Args:
            reviews: List of review dictionaries

        Returns:
            Dict with sentiment analysis
        """
        if not reviews:
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.5,
                "positive_percentage": 0,
                "negative_percentage": 0,
                "neutral_percentage": 100,
            }

        prompt = f"""Analyze the sentiment of these customer reviews:

Reviews:
{self._format_reviews_for_prompt(reviews[:50])}  # Limit to avoid token limits

Return ONLY a JSON object:
{{
  "overall_sentiment": "positive|negative|neutral",
  "sentiment_score": 0.0-1.0,
  "positive_percentage": 0-100,
  "negative_percentage": 0-100,
  "neutral_percentage": 0-100
}}

Be objective and data-driven."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            return json.loads(response.content[0].text)
        except json.JSONDecodeError:
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.5,
                "positive_percentage": 33,
                "negative_percentage": 33,
                "neutral_percentage": 34,
            }

    async def extract_key_themes(
        self, reviews: List[Dict[str, Any]], max_themes: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract key themes/topics from reviews

        Args:
            reviews: List of review dictionaries
            max_themes: Maximum number of themes to extract

        Returns:
            Dict with themes list
        """
        if not reviews:
            return {"themes": []}

        prompt = f"""Identify the top {max_themes} themes mentioned in these reviews:

Reviews:
{self._format_reviews_for_prompt(reviews[:50])}

Return ONLY a JSON object:
{{
  "themes": [
    {{
      "theme": "theme name",
      "mentions": count,
      "sentiment": "positive|negative|neutral"
    }}
  ]
}}

Focus on product features, quality, shipping, customer service, etc."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            return json.loads(response.content[0].text)
        except json.JSONDecodeError:
            return {"themes": []}

    async def generate_highlights(
        self, reviews: List[Dict[str, Any]], max_highlights: int = 3
    ) -> List[str]:
        """
        Generate top review highlights

        Args:
            reviews: List of review dictionaries
            max_highlights: Maximum number of highlights

        Returns:
            List of highlight strings
        """
        if not reviews:
            return []

        # Focus on 5-star reviews for highlights
        top_reviews = [r for r in reviews if r.get("rating", 0) >= 4][:20]

        if not top_reviews:
            top_reviews = reviews[:10]

        prompt = f"""Extract the top {max_highlights} most compelling positive highlights from these reviews:

Reviews:
{self._format_reviews_for_prompt(top_reviews)}

Return ONLY a JSON array of strings:
["highlight 1", "highlight 2", "highlight 3"]

Make them concise, specific, and impactful."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            return json.loads(response.content[0].text)
        except json.JSONDecodeError:
            return []

    async def summarize_by_rating(
        self, reviews: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Summarize reviews grouped by rating

        Args:
            reviews: List of review dictionaries

        Returns:
            Dict with summaries for each rating level
        """
        if not reviews:
            return {}

        prompt = f"""Summarize what customers are saying at each rating level:

Reviews:
{self._format_reviews_for_prompt(reviews[:100])}

Return ONLY a JSON object:
{{
  "5_star": "summary of 5-star reviews",
  "4_star": "summary of 4-star reviews",
  "3_star": "summary of 3-star reviews",
  "2_star": "summary of 2-star reviews",
  "1_star": "summary of 1-star reviews"
}}

Use "N/A" if no reviews for that rating. Be concise."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            return json.loads(response.content[0].text)
        except json.JSONDecodeError:
            return {}

    def _filter_reviews(
        self,
        reviews: List[Dict[str, Any]],
        verified_only: bool,
        max_reviews: Optional[int],
    ) -> List[Dict[str, Any]]:
        """Filter reviews based on criteria"""
        filtered = reviews

        if verified_only:
            filtered = [r for r in filtered if r.get("verified_purchase", False)]

        if max_reviews:
            filtered = filtered[:max_reviews]

        return filtered

    def _format_reviews_for_prompt(self, reviews: List[Dict[str, Any]]) -> str:
        """Format reviews for Claude prompt"""
        formatted = []
        for i, review in enumerate(reviews, 1):
            rating = review.get("rating", "N/A")
            title = review.get("title", "")
            content = review.get("content", "")
            verified = " [Verified]" if review.get("verified_purchase") else ""

            formatted.append(
                f"{i}. Rating: {rating}/5{verified}\n   Title: {title}\n   Review: {content}\n"
            )

        return "\n".join(formatted)

    def _build_summary_prompt(self, reviews: List[Dict[str, Any]]) -> str:
        """Build prompt for review summarization"""
        return f"""Summarize these customer reviews in 2-3 concise sentences:

{self._format_reviews_for_prompt(reviews)}

Focus on:
- Overall sentiment
- Most common praise
- Main concerns (if any)
- Key product features mentioned

Be objective and balanced. Keep it under 100 words."""
