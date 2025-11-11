"""
Platform Service FastAPI Application
Handles OAuth flows and webhooks for e-commerce platforms
"""
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.config.settings import get_settings

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Platform Service API",
    version="1.0.0",
    description="E-commerce platform integration service (OAuth, webhooks)",
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
from platform_service.api.routes import auth, webhooks

app.include_router(auth.router)
app.include_router(webhooks.router)


@app.get("/", tags=["health"])
async def root():
    """Root endpoint"""
    return {
        "service": "Platform Service API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "service": "platform-service",
            "version": "1.0.0",
        },
    )


@app.get("/ready", tags=["health"])
async def readiness_check():
    """Readiness check endpoint"""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "ready",
            "service": "platform-service",
            "version": "1.0.0",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8005,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
