# Review Platform

A high-performance, AI-powered review platform that competes with Yotpo, Reviews.io, and Bazaarvoice.

## Features

- **Lightning Fast**: Widget loads in < 50ms, API responses < 100ms (p95)
- **AI-Powered**: LLM-driven style customization and review summarization
- **Scalable**: Handles 10,000+ requests/second
- **Developer-First**: Clean APIs, excellent documentation, easy integration

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy
- **Database**: PostgreSQL 15 with JSONB
- **Cache**: Redis 7
- **Search**: Elasticsearch 8
- **Queue**: RabbitMQ
- **AI**: Anthropic Claude API
- **Frontend**: Next.js, React, Tailwind CSS

## Architecture Principles

- SOLID Principles
- Test-Driven Development (TDD)
- Clean Architecture
- Microservices
- Event-Driven
- API-First

## Getting Started

```bash
# Install dependencies
poetry install

# Start local services (Postgres, Redis, RabbitMQ)
docker-compose up -d

# Run migrations
alembic upgrade head

# Run tests
pytest

# Start development server
uvicorn services.review-service.api.main:app --reload

# Access API docs
open http://localhost:8000/docs
```

## Project Structure

```
review-platform/
├── services/
│   ├── widget-service/          # Public API for widget
│   ├── admin-service/           # Admin dashboard API
│   ├── review-service/          # Core review logic
│   ├── ai-service/              # LLM integrations
│   ├── analytics-service/       # Metrics and insights
│   ├── email-service/           # Review requests
│   ├── media-service/           # Image/video handling
│   └── integration-service/     # Platform integrations
├── shared/                      # Common libraries
├── frontend/
│   ├── widget/                  # Embeddable widget
│   └── admin-dashboard/         # Admin UI
├── k8s/                         # Kubernetes configs
├── terraform/                   # Infrastructure
├── scripts/                     # Utilities
├── docs/                        # Documentation
└── tests/                       # E2E tests
```

## Documentation

- [API Documentation](docs/api.md)
- [Integration Guide](docs/integration.md)
- [Developer Guide](docs/developer.md)
- [Operations Guide](docs/operations.md)

## License

MIT
