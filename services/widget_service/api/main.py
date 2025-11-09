"""
Widget Service FastAPI Application
Ultra-fast public API for widget embedding
Performance target: < 100ms p95
"""
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from shared.config.settings import get_settings
from widget_service.api.routes import widget_routes

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Review Platform Widget Service",
    version="1.0.0",
    description="Ultra-fast public API for embeddable review widgets. < 100ms p95 response time.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware - permissive for public widget embedding
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Public widget can be embedded anywhere
    allow_credentials=False,  # No credentials for public endpoints
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
    expose_headers=["Cache-Control", "X-Content-Type-Options"],
)

# GZip compression for smaller payload sizes
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(widget_routes.router)


@app.get("/", tags=["health"])
async def root():
    """Root endpoint"""
    return {
        "service": "Review Platform Widget Service",
        "version": "1.0.0",
        "status": "running",
        "performance_target": "< 100ms p95",
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "service": "widget-service",
            "version": "1.0.0",
        },
    )


@app.get("/ready", tags=["health"])
async def readiness_check():
    """Readiness check endpoint"""
    # TODO: Check database and cache connections
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "ready",
            "service": "widget-service",
            "version": "1.0.0",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8002,  # Different port from review/AI services
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
