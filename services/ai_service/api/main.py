"""
AI Service FastAPI Application
Provides AI-powered features for the review platform
"""
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.config.settings import get_settings
from ai_service.api.routes import ai_routes

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Review Platform AI Service",
    version="1.0.0",
    description="AI-powered features: style generation, review summarization, sentiment analysis",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Include routers
app.include_router(ai_routes.router)


@app.get("/", tags=["health"])
async def root():
    """Root endpoint"""
    return {
        "service": "Review Platform AI Service",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "AI style generation",
            "Review summarization",
            "Sentiment analysis",
            "Key theme extraction",
        ],
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "service": "ai-service",
            "version": "1.0.0",
        },
    )


@app.get("/ready", tags=["health"])
async def readiness_check():
    """Readiness check endpoint"""
    # Check if Anthropic API key is configured
    anthropic_configured = bool(settings.anthropic_api_key)

    if not anthropic_configured:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "service": "ai-service",
                "error": "Anthropic API key not configured",
            },
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "ready",
            "service": "ai-service",
            "version": "1.0.0",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8001,  # Different port from review service
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
