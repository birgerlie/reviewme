"""
AI Service API Routes
FastAPI endpoints for AI-powered features
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from ai_service.api.models import (
    StyleGenerationRequest,
    StyleGenerationResponse,
    CSSGenerationRequest,
    CSSGenerationResponse,
    ReviewSummaryRequest,
    ReviewSummaryResponse,
    ProsConsRequest,
    ProsConsResponse,
    SentimentAnalysisRequest,
    SentimentAnalysisResponse,
    KeyThemesRequest,
    KeyThemesResponse,
    HighlightsRequest,
    HighlightsResponse,
)
from ai_service.domain.services.style_generator_service import StyleGeneratorService
from ai_service.domain.services.review_summarizer_service import (
    ReviewSummarizerService,
)
from shared.config.settings import get_settings

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])
settings = get_settings()


def get_style_generator() -> StyleGeneratorService:
    """Dependency: Get style generator service"""
    return StyleGeneratorService()


def get_review_summarizer() -> ReviewSummarizerService:
    """Dependency: Get review summarizer service"""
    return ReviewSummarizerService()


@router.post(
    "/style/generate",
    response_model=StyleGenerationResponse,
    summary="Generate widget style",
    description="AI-powered widget style generation based on brand website",
)
async def generate_widget_style(
    request: StyleGenerationRequest,
    service: StyleGeneratorService = Depends(get_style_generator),
) -> StyleGenerationResponse:
    """Generate widget style configuration"""
    try:
        style_config = await service.generate_widget_style(
            brand_website_url=str(request.brand_website_url),
            brand_colors=request.brand_colors,
            preferences=request.preferences,
            include_responsive=request.include_responsive,
        )

        return StyleGenerationResponse(style_config=style_config)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Style generation failed: {str(e)}",
        )


@router.post(
    "/style/css",
    response_model=CSSGenerationResponse,
    summary="Generate CSS from config",
    description="Generate production-ready CSS from style configuration",
)
async def generate_css(
    request: CSSGenerationRequest,
    service: StyleGeneratorService = Depends(get_style_generator),
) -> CSSGenerationResponse:
    """Generate CSS from style configuration"""
    try:
        css = await service.generate_css_from_config(request.style_config)

        return CSSGenerationResponse(css=css)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CSS generation failed: {str(e)}",
        )


@router.post(
    "/reviews/summarize",
    response_model=ReviewSummaryResponse,
    summary="Summarize reviews",
    description="AI-powered review summarization",
)
async def summarize_reviews(
    request: ReviewSummaryRequest,
    service: ReviewSummarizerService = Depends(get_review_summarizer),
) -> ReviewSummaryResponse:
    """Summarize customer reviews"""
    try:
        summary = await service.summarize_reviews(
            reviews=request.reviews,
            max_reviews=request.max_reviews,
            verified_only=request.verified_only,
        )

        return ReviewSummaryResponse(summary=summary)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summarization failed: {str(e)}",
        )


@router.post(
    "/reviews/pros-cons",
    response_model=ProsConsResponse,
    summary="Extract pros and cons",
    description="Extract pros and cons from reviews using AI",
)
async def extract_pros_cons(
    request: ProsConsRequest,
    service: ReviewSummarizerService = Depends(get_review_summarizer),
) -> ProsConsResponse:
    """Extract pros and cons from reviews"""
    try:
        result = await service.extract_pros_and_cons(
            reviews=request.reviews,
            max_reviews=request.max_reviews,
            verified_only=request.verified_only,
        )

        return ProsConsResponse(pros=result["pros"], cons=result["cons"])

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pros/cons extraction failed: {str(e)}",
        )


@router.post(
    "/reviews/sentiment",
    response_model=SentimentAnalysisResponse,
    summary="Analyze sentiment",
    description="Analyze overall sentiment of reviews",
)
async def analyze_sentiment(
    request: SentimentAnalysisRequest,
    service: ReviewSummarizerService = Depends(get_review_summarizer),
) -> SentimentAnalysisResponse:
    """Analyze review sentiment"""
    try:
        result = await service.analyze_sentiment(reviews=request.reviews)

        return SentimentAnalysisResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sentiment analysis failed: {str(e)}",
        )


@router.post(
    "/reviews/themes",
    response_model=KeyThemesResponse,
    summary="Extract key themes",
    description="Extract key themes and topics from reviews",
)
async def extract_key_themes(
    request: KeyThemesRequest,
    service: ReviewSummarizerService = Depends(get_review_summarizer),
) -> KeyThemesResponse:
    """Extract key themes from reviews"""
    try:
        result = await service.extract_key_themes(
            reviews=request.reviews, max_themes=request.max_themes
        )

        return KeyThemesResponse(themes=result["themes"])

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Theme extraction failed: {str(e)}",
        )


@router.post(
    "/reviews/highlights",
    response_model=HighlightsResponse,
    summary="Generate highlights",
    description="Generate top review highlights",
)
async def generate_highlights(
    request: HighlightsRequest,
    service: ReviewSummarizerService = Depends(get_review_summarizer),
) -> HighlightsResponse:
    """Generate review highlights"""
    try:
        highlights = await service.generate_highlights(
            reviews=request.reviews, max_highlights=request.max_highlights
        )

        return HighlightsResponse(highlights=highlights)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Highlights generation failed: {str(e)}",
        )
