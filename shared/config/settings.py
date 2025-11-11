"""
Application Settings
Configuration management using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables

    Usage:
        from shared.config.settings import get_settings
        settings = get_settings()
    """

    # API
    api_title: str = "Review Platform API"
    api_version: str = "1.0.0"
    api_description: str = "High-performance, AI-powered review platform"
    debug: bool = False
    environment: str = "development"  # development, staging, production

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/reviews"
    database_pool_size: int = 20
    database_max_overflow: int = 10
    database_pool_timeout: int = 30
    database_pool_recycle: int = 1800  # 30 minutes

    # Redis (with password)
    redis_url: str = "redis://:changeme@localhost:6379/1"
    redis_max_connections: int = 50
    redis_socket_timeout: int = 5
    redis_socket_connect_timeout: int = 5

    # Authentication
    api_key_header: str = "X-API-Key"
    jwt_secret: str = "change-me-in-production-very-secret-key-12345"
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # 1 hour

    # Performance & Caching
    cache_ttl_reviews: int = 300  # 5 minutes - cached review lists
    cache_ttl_ratings: int = 600  # 10 minutes - cached ratings and stats

    # Rate limiting
    rate_limit_requests: int = 1000
    rate_limit_window: int = 60  # seconds

    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:8000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["*"]
    cors_allow_headers: list = ["*"]

    # Pagination
    default_page_size: int = 10
    max_page_size: int = 100

    # Review Settings
    review_title_max_length: int = 500
    review_content_max_length: int = 5000
    review_media_max_files: int = 10

    # AI Service (Anthropic Claude)
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    anthropic_max_tokens: int = 4096

    # Platform Integrations - Shopify
    shopify_api_key: Optional[str] = None
    shopify_api_secret: Optional[str] = None
    shopify_app_url: str = "https://api.yourdomain.com"
    shopify_scopes: list = ["read_orders", "read_products", "write_products"]

    # Celery (Task Queue) - Shares Redis with application (different databases)
    celery_broker_url: str = "redis://:changeme@localhost:6379/2"  # Celery broker
    celery_result_backend: str = "redis://:changeme@localhost:6379/3"  # Results backend
    celery_task_serializer: str = "json"
    celery_result_serializer: str = "json"
    celery_accept_content: list = ["json"]
    celery_timezone: str = "UTC"
    celery_task_track_started: bool = True
    celery_task_time_limit: int = 300  # 5 minutes
    celery_broker_connection_retry_on_startup: bool = True

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json or text

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance

    Returns:
        Settings: Application settings
    """
    return Settings()
