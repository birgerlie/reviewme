# Project Patterns Reference
## Quick Reference for Claude Code

**READ THIS FIRST before implementing any feature**

---

## Project Structure Convention

```
services/
├── {service_name}_service/
│   ├── api/                    # FastAPI layer
│   │   ├── main.py            # App setup, CORS, error handlers
│   │   ├── routes/            # One file per resource
│   │   │   └── {resource}.py  # e.g., reviews.py
│   │   └── dependencies.py    # Dependency injection
│   │
│   ├── domain/                # Business logic (pure Python)
│   │   ├── entities/          # Domain models (dataclasses)
│   │   ├── repositories/      # Interfaces (ABC)
│   │   └── services/          # Business logic
│   │
│   ├── infrastructure/        # External concerns
│   │   ├── postgres_{}.py     # Repository implementations
│   │   ├── {}_client.py       # External API clients
│   │   └── events/            # Event handlers
│   │
│   └── tests/                 # Mirrors structure exactly
│       ├── domain/
│       ├── infrastructure/
│       └── api/
│
shared/                        # Cross-cutting concerns
├── database.py                # SQLAlchemy setup
├── cache/                     # Caching utilities
├── events/                    # Event bus
└── monitoring/                # Logging, metrics
```

---

## Naming Conventions

### Files
```python
# Entities (domain models)
domain/entities/review.py          # Singular, noun
domain/entities/review_token.py    # Underscore separated

# Repositories (interfaces)
domain/repositories/i_review_repository.py    # Interface prefix: i_

# Implementations
infrastructure/postgres_review_repository.py  # Technology prefix

# Services
domain/services/review_service.py            # {noun}_service.py

# Routes
api/routes/reviews.py                        # Plural, resource name

# Tests
tests/domain/entities/test_review.py         # test_ prefix
```

### Classes
```python
# Entities (dataclasses)
class Review:                    # PascalCase, singular

# Interfaces (ABC)
class IReviewRepository(ABC):    # Prefix: I, PascalCase

# Implementations
class PostgresReviewRepository:  # Technology + Interface name

# Services
class ReviewService:             # PascalCase + Service suffix

# Exceptions
class ReviewNotFoundError:       # PascalCase + Error suffix
```

### Methods
```python
# Repository methods
async def get_by_id(id: str) -> Optional[Review]
async def get_by_product_id(product_id: str) -> List[Review]
async def create(review: Review) -> Review
async def update(review: Review) -> Review
async def delete(id: str) -> bool

# Service methods
async def create_review(data: CreateReviewDTO) -> Review
async def approve_review(review_id: str) -> Review
```

---

## Critical Rules for Claude Code

1. **ALWAYS read this file before starting implementation**
2. **NEVER put business logic in routes** (only in services)
3. **NEVER put database code in domain** (only in infrastructure)
4. **ALWAYS use interfaces** (ABC) for cross-boundary dependencies
5. **ALWAYS write tests first** (TDD)
6. **ALWAYS use type hints**
7. **ALWAYS use async/await**
8. **ALWAYS log errors with context**
9. **ALWAYS validate at domain layer**
10. **ALWAYS follow existing naming conventions EXACTLY**

---

## When in Doubt

1. Find similar feature in codebase
2. Copy its structure exactly
3. Adapt names and logic
4. Keep tests matching

**Example:** "I need to create a new `Widget` entity"
→ Look at `Review` entity
→ Copy structure
→ Adapt for Widget

This ensures consistency!
