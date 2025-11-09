"""
Media Service FastAPI Application
Handles media upload, processing, and CDN delivery
"""
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.config.settings import get_settings
from media_service.api.routes import media_routes

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Review Platform Media Service",
    version="1.0.0",
    description="Media upload, processing, and CDN delivery for review images/videos",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(media_routes.router)


@app.get("/", tags=["health"])
async def root():
    """Root endpoint"""
    return {
        "service": "Review Platform Media Service",
        "version": "1.0.0",
        "status": "running",
        "description": "Media upload and CDN delivery",
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "service": "media-service",
            "version": "1.0.0",
        },
    )


@app.get("/ready", tags=["health"])
async def readiness_check():
    """Readiness check endpoint"""
    # TODO: Check storage and CDN connections
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "ready",
            "service": "media-service",
            "version": "1.0.0",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8004,  # Different port from other services
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
