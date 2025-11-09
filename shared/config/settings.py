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

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50
    redis_socket_timeout: int = 5
    redis_socket_connect_timeout: int = 5

    # Authentication
    api_key_header: str = "X-API-Key"
    jwt_secret: str = "change-me-in-production-very-secret-key-12345"
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # 1 hour

    # Performance
    cache_ttl_reviews: int = 300  # 5 minutes
    cache_ttl_ratings: int = 600  # 10 minutes

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

    # Event Bus (RabbitMQ)
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    rabbitmq_exchange: str = "review-platform"

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json or text

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance

    Returns:
        Settings: Application settings
    """
    return Settings()
