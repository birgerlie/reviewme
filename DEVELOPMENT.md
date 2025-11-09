# Development Guide

## Phase 1: Foundation Complete ✅

### What's Been Built

**Core Domain Models** (TDD)
- ✅ Review model with business logic
- ✅ ReviewRating and ReviewStatus enums
- ✅ Complete test coverage (11 tests passing)

**Repository Layer** (Dependency Inversion)
- ✅ IReviewRepository interface
- ✅ PostgreSQL implementation with SQLAlchemy async
- ✅ Complete test coverage (11 tests passing)

**Business Logic** (Service Layer)
- ✅ ReviewService with business rules
- ✅ Auto-approval for verified 4+ star reviews
- ✅ Cache invalidation strategy
- ✅ Event publishing
- ✅ Complete test coverage (9 tests passing)

**API Layer** (FastAPI)
- ✅ RESTful endpoints for reviews
- ✅ Pydantic models for validation
- ✅ API key authentication
- ✅ OpenAPI documentation
- ✅ Health check endpoints

**Infrastructure**
- ✅ PostgreSQL database models
- ✅ Redis cache service
- ✅ Simple event bus
- ✅ Alembic migrations
- ✅ Docker Compose for local development

## Getting Started

### 1. Install Dependencies

```bash
poetry install
```

### 2. Start Services

```bash
# Start PostgreSQL, Redis, and RabbitMQ
docker-compose up -d

# Check service health
docker-compose ps
```

### 3. Run Migrations

```bash
# Apply database migrations
poetry run alembic upgrade head
```

### 4. Run Tests

```bash
# Run all unit tests
poetry run pytest services/review_service/tests/unit/ -v

# With coverage
poetry run pytest services/review_service/tests/unit/ --cov
```

### 5. Start Development Server

```bash
# Start FastAPI server
poetry run uvicorn services.review_service.api.main:app --reload --port 8000

# Or use the main script
cd services/review_service
poetry run python -m api.main
```

### 6. Access API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Test Results

**Total: 31 tests passing**

- Review Model: 11/11 ✅
- Repository Interface: 11/11 ✅
- Review Service: 9/9 ✅

All tests following TDD methodology!

## Architecture

### SOLID Principles Implementation

1. **Single Responsibility**: Each class has one clear purpose
   - `Review`: Domain model with business rules
   - `ReviewService`: Business logic orchestration
   - `PostgresReviewRepository`: Data access only

2. **Open/Closed**: Open for extension, closed for modification
   - Interfaces allow new implementations without changing existing code

3. **Liskov Substitution**: Implementations are interchangeable
   - Any implementation of `IReviewRepository` works with `ReviewService`

4. **Interface Segregation**: Focused interfaces
   - `IReviewRepository`: Data operations
   - `ICacheService`: Cache operations
   - `IEventBus`: Event operations

5. **Dependency Inversion**: Depend on abstractions
   - `ReviewService` depends on interfaces, not concrete classes

### Clean Architecture Layers

```
┌─────────────────────────────────────────────┐
│         API Layer (FastAPI)                 │
│  - Routes, Models, Dependencies             │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│      Domain Layer (Business Logic)          │
│  - Review, ReviewService                    │
│  - Interfaces (IReviewRepository, etc.)     │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│    Infrastructure Layer (Implementation)    │
│  - PostgresReviewRepository                 │
│  - RedisCacheService                        │
│  - SimpleEventBus                           │
└─────────────────────────────────────────────┘
```

## API Endpoints

### Reviews

- `POST /api/v1/reviews/` - Create review
- `GET /api/v1/reviews/products/{product_id}` - List reviews
- `GET /api/v1/reviews/products/{product_id}/rating` - Get rating
- `GET /api/v1/reviews/products/{product_id}/stats` - Get stats
- `POST /api/v1/reviews/{review_id}/helpful` - Mark helpful
- `POST /api/v1/reviews/{review_id}/approve` - Approve (admin)
- `POST /api/v1/reviews/{review_id}/reject` - Reject (admin)
- `POST /api/v1/reviews/{review_id}/flag` - Flag review

### Health Checks

- `GET /health` - Health status
- `GET /ready` - Readiness check

## Business Rules

1. **Auto-Approval**: Verified purchases with 4+ stars are automatically approved
2. **Cache Strategy**:
   - Reviews cached for 5 minutes
   - Ratings cached for 10 minutes
   - Cache invalidated on create/update
3. **Event Publishing**: All state changes publish events
4. **Helpful Count**: Can only increase, never decrease

## Database Schema

```sql
CREATE TABLE reviews (
    id VARCHAR(36) PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL,
    customer_id VARCHAR(255) NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    verified_purchase BOOLEAN DEFAULT FALSE,
    helpful_count INTEGER DEFAULT 0,
    media_urls JSONB DEFAULT '[]',
    attributes JSONB DEFAULT '{}'
);

-- Critical indexes for performance
CREATE INDEX idx_reviews_product_status ON reviews(product_id, status);
CREATE INDEX idx_reviews_created_at ON reviews(created_at);
CREATE INDEX idx_reviews_rating ON reviews(rating);
CREATE INDEX idx_reviews_customer ON reviews(customer_id);
CREATE INDEX idx_reviews_verified ON reviews(verified_purchase);
```

## Next Steps

### Phase 2: AI Service (Weeks 3-4)

- [ ] Style generator service
- [ ] Review summarization
- [ ] Sentiment analysis
- [ ] Integration with Anthropic Claude API

### Phase 3: Widget Service (Weeks 4-5)

- [ ] Ultra-fast public API
- [ ] CDN integration
- [ ] Widget configuration endpoints
- [ ] Performance optimization (< 50ms p95)

### Phase 4: Frontend Widget (Weeks 5-6)

- [ ] React components
- [ ] Bundle optimization (< 50KB)
- [ ] Virtual scrolling
- [ ] Lazy loading

### Phase 5: Additional Services (Weeks 6-8)

- [ ] Email service
- [ ] Media service
- [ ] Analytics service
- [ ] Integration service (Shopify, WooCommerce)

### Phase 6: Production (Weeks 9-12)

- [ ] Kubernetes deployment
- [ ] Terraform infrastructure
- [ ] Monitoring (Prometheus, Grafana)
- [ ] E2E tests
- [ ] Load testing (10,000 req/s)

## Contributing

1. Write tests first (TDD)
2. Follow SOLID principles
3. Keep functions small and focused
4. Document business rules
5. Run tests before committing
6. Update this guide when adding features

## Resources

- [FastAPI Docs](https://fastapi.tiangolo.com)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org)
- [Pydantic Docs](https://docs.pydantic.dev)
- [Alembic Docs](https://alembic.sqlalchemy.org)
