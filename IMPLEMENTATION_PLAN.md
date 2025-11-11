# Review Platform MVP - Implementation Plan v2.0
## Claude Code Edition with Platform Abstraction

**Project:** Multi-Platform Review Platform MVP  
**Timeline:** 4 weeks  
**Development Method:** TDD, SOLID principles, Clean Architecture  
**AI Assistant:** Claude Code for implementation  
**Primary Platform:** Shopify (with abstraction for future platforms)  
**Infrastructure:** Railway (PostgreSQL + Redis), Cloudflare R2 (storage)  
**Version:** 2.0  
**Date:** November 11, 2025

---

## Key Architectural Decisions

### ✅ Decisions Made

1. **Platform Abstraction from Day 1**
   - Build `IPlatformClient`, `IAuthProvider`, `IWebhookHandler` interfaces
   - Implement Shopify first, but properly abstracted
   - Cost: 2 extra hours (negligible with Claude Code)
   - Benefit: 3-day platform additions vs 6-week retrofits

2. **Railway for Infrastructure**
   - PostgreSQL + Redis in one place
   - Private networking (fast service communication)
   - Already familiar, proven in other projects
   - ~$35/mo for MVP, ~$135/mo at scale

3. **Cloudflare R2 for Storage**
   - S3-compatible API (standard boto3)
   - $0.015/GB storage, free egress
   - Not locked to any database provider

4. **Direct GTM with Partner Readiness**
   - Launch on Shopify (fastest validation)
   - Platform abstraction enables quick pivots
   - Enterprise partners can request new platforms (3-day turnaround)

### 🎯 Success Targets

**Technical:**
- Widget API: < 100ms p95
- Cache hit rate: > 90%
- Test coverage: > 95%
- Uptime: > 99.9%

**Business:**
- Week 4: 5 active merchants
- Month 2: 10 merchants, 5 paying ($75 MRR)
- Month 4: 25 merchants, 10 paying ($150 MRR)

---

## Table of Contents

1. [Claude Code Usage Guidelines](#claude-code-usage-guidelines)
2. [Week 1: Foundation & Platform Abstraction](#week-1-foundation--platform-abstraction)
3. [Week 2: Review Collection & Moderation](#week-2-review-collection--moderation)
4. [Week 3: Widget Implementation](#week-3-widget-implementation)
5. [Week 4: Polish & Launch](#week-4-polish--launch)
6. [Deployment & Operations](#deployment--operations)

---

## Claude Code Usage Guidelines

### How to Work with Claude Code

**General Pattern:**
```
1. Point Claude Code to existing codebase patterns
2. Specify interfaces and contracts first
3. Request tests before implementation
4. Review generated code
5. Iterate on edge cases
6. Run full test suite
```

### Example Prompt Structure

```
CONTEXT: Read services/review_service/ structure and understand the patterns.

TASK: Create platform abstraction layer with:
- Domain interfaces (IPlatformClient, IAuthProvider)
- Universal entities (PlatformMerchant, PlatformProduct)
- Follow existing Clean Architecture patterns exactly

REQUIREMENTS:
- Write tests first (TDD)
- 100% test coverage
- Type hints everywhere
- Docstrings for all public methods
- Follow existing naming conventions

TEST: All tests must pass before moving to next task.
```

### Time Estimates with Claude Code

**Traditional Development** → **With Claude Code**
- Platform abstraction: 1 week → 4 hours
- Shopify OAuth: 2 days → 2 hours
- Database migrations: 4 hours → 30 minutes
- Widget JavaScript: 1 week → 6 hours
- Testing: 30% of dev time → 10% of dev time

**Your role:**
- Make architectural decisions (30% of time)
- Review/validate Claude Code output (50% of time)
- Handle edge cases and integration (20% of time)

---

## Week 1: Foundation & Platform Abstraction

### Day 1: Infrastructure Setup

#### Task 1.1: Railway Infrastructure (30 minutes)

**Setup:**
```bash
# Initialize Railway project
railway init

# Add managed services
railway add postgresql
railway add redis

# Link to project
railway link
```

**Environment Variables (auto-provided by Railway):**
```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
```

**Claude Code Task:**
```
Update infrastructure configuration:

1. Update shared/database.py:
   - Use Railway DATABASE_URL
   - Connection pooling: pool_size=5, max_overflow=10
   - Add health check function

2. Update shared/cache/redis_cache_service.py:
   - Use Railway REDIS_URL
   - Connection pool: max_connections=50
   - Add reconnection logic

3. Create alembic.ini updates for Railway

4. Test connections with health checks

All tests must pass.
```

**Success Criteria:**
- ✅ Railway project created
- ✅ PostgreSQL and Redis accessible
- ✅ Connection pooling configured
- ✅ Health checks passing

---

#### Task 1.2: Cloudflare R2 Storage Setup (30 minutes)

**Cloudflare R2 Setup:**
1. Create R2 bucket: `review-platform-media`
2. Generate API token with R2 permissions
3. Get account ID and endpoint URL

**Environment Variables:**
```bash
R2_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=xxx
R2_SECRET_ACCESS_KEY=xxx
R2_BUCKET_NAME=review-platform-media
R2_PUBLIC_URL=https://media.yourdomain.com
```

**Claude Code Task:**
```
Create R2 storage service following existing patterns:

FILE: shared/storage/r2_storage.py

INTERFACE: Create IStorageService interface with:
- upload_image(file_bytes: bytes, filename: str) -> str
- delete_image(filename: str) -> bool
- get_image_url(filename: str) -> str

IMPLEMENTATION: R2StorageService using boto3:
- S3-compatible API
- Image validation (type, size)
- Unique filename generation (UUID)
- Error handling with logging
- Public URL generation

TESTS: shared/storage/test_r2_storage.py
- Mock boto3 S3 client
- Test upload success/failure
- Test file validation
- Test URL generation
- 100% coverage

Follow existing repository patterns in infrastructure layer.
```

**Success Criteria:**
- ✅ Can upload images to R2
- ✅ Public URLs work
- ✅ Validation prevents bad files
- ✅ All tests pass

---

### Day 2-3: Platform Abstraction Layer

#### Task 1.3: Platform Domain Layer (4 hours)

**Goal:** Create platform-agnostic interfaces and entities

**Claude Code Task:**
```
CONTEXT: Analyze services/review_service/domain/ structure.

CREATE: services/platform_service/ with Clean Architecture:

1. Domain Entities (domain/entities/):

   FILE: platform_merchant.py
   - PlatformType enum (SHOPIFY, WOOCOMMERCE, BIGCOMMERCE, CUSTOM)
   - PlatformMerchant dataclass:
     * id, platform, platform_domain, platform_merchant_id
     * access_token, scopes, token_expires_at
     * store_name, email, currency, timezone
     * installed_at, active, widget_config
     * platform_metadata (dict - escape hatch)
   - Validation methods
   
   FILE: platform_product.py
   - PlatformProduct dataclass:
     * id, merchant_id, platform_product_id
     * title, description, price, currency
     * image_url, images, url
     * has_variants, variant_count, in_stock
     * platform_metadata (dict - escape hatch)
   
   FILE: platform_order.py
   - PlatformOrderLineItem dataclass
   - PlatformOrder dataclass:
     * id, merchant_id, platform_order_id, platform_order_number
     * customer_email, customer_name
     * line_items, total, currency
     * fulfilled, fulfilled_at
     * platform_metadata (dict - escape hatch)

2. Domain Interfaces (domain/interfaces/):

   FILE: i_platform_client.py
   - IPlatformClient ABC with methods:
     * get_product(merchant_id, product_id) -> PlatformProduct
     * get_order(merchant_id, order_id) -> PlatformOrder
     * list_products(merchant_id, limit) -> List[PlatformProduct]
     * verify_webhook(payload, headers) -> bool
   
   FILE: i_auth_provider.py
   - IAuthProvider ABC with methods:
     * get_authorization_url(shop_domain, redirect_uri, scopes) -> str
     * exchange_code_for_token(code, shop_domain) -> Tuple[str, List[str]]
     * verify_request(params, signature) -> bool
   
   FILE: i_webhook_handler.py
   - IWebhookHandler ABC with methods:
     * register_webhooks(merchant_id, access_token, webhook_url) -> List[str]
     * parse_webhook_event(payload, headers) -> Dict
     * delete_webhooks(merchant_id, webhook_ids) -> bool

3. Domain Repositories (domain/repositories/):

   FILE: i_merchant_repository.py
   - IMerchantRepository ABC with methods:
     * create(merchant: PlatformMerchant) -> PlatformMerchant
     * get_by_id(merchant_id: str) -> Optional[PlatformMerchant]
     * get_by_platform_domain(platform: PlatformType, domain: str) -> Optional[PlatformMerchant]
     * update(merchant: PlatformMerchant) -> PlatformMerchant
     * delete(merchant_id: str) -> bool

4. Tests (tests/domain/):
   - Test entity validation
   - Test interface contracts (using mocks)
   - Test edge cases
   - 100% coverage

FOLLOW: Existing patterns in services/review_service/domain/
STYLE: Match existing naming conventions exactly
QUALITY: All docstrings, type hints, validation
```

**Success Criteria:**
- ✅ All entities defined with validation
- ✅ All interfaces defined with clear contracts
- ✅ All tests pass (100% coverage)
- ✅ No implementation yet (pure domain layer)

---

#### Task 1.4: Shopify Platform Implementation (4 hours)

**Goal:** Implement platform interfaces for Shopify

**Database Migration:**
```sql
-- Create merchants table
CREATE TABLE merchants (
    id VARCHAR(36) PRIMARY KEY,
    platform VARCHAR(50) NOT NULL DEFAULT 'shopify',
    platform_domain VARCHAR(255) NOT NULL,
    platform_merchant_id VARCHAR(255) NOT NULL,
    access_token TEXT NOT NULL,
    scopes TEXT[] NOT NULL,
    token_expires_at TIMESTAMP WITH TIME ZONE,
    store_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    installed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    active BOOLEAN DEFAULT TRUE,
    widget_config JSONB DEFAULT '{}',
    platform_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(platform, platform_domain)
);

CREATE INDEX idx_merchants_platform_domain ON merchants(platform, platform_domain);
CREATE INDEX idx_merchants_active ON merchants(active) WHERE active = true;
```

**Claude Code Task:**
```
CONTEXT: Study domain interfaces in services/platform_service/domain/interfaces/

CREATE: services/platform_service/infrastructure/shopify/

1. FILE: shopify_client.py
   
   CLASS: ShopifyClient(IPlatformClient)
   
   METHODS:
   - __init__(api_key, api_secret)
   - get_product() -> PlatformProduct
     * Call Shopify Admin API
     * Transform to universal PlatformProduct
     * Store raw data in platform_metadata
   - get_order() -> PlatformOrder
     * Call Shopify Admin API
     * Transform to universal PlatformOrder
     * Handle line items mapping
   - list_products() -> List[PlatformProduct]
     * Pagination handling
     * Rate limiting
   - verify_webhook() -> bool
     * HMAC verification
     * Shopify-specific validation
   
   ERROR HANDLING:
   - Retry logic (3 attempts)
   - Rate limiting (429 handling)
   - Clear error messages
   - Logging

2. FILE: shopify_auth.py
   
   CLASS: ShopifyAuthProvider(IAuthProvider)
   
   METHODS:
   - get_authorization_url()
     * Generate Shopify OAuth URL
     * Include nonce for security
     * Required scopes
   - exchange_code_for_token()
     * Exchange code for access token
     * Validate HMAC
     * Return token and granted scopes
   - verify_request()
     * HMAC verification
     * Timestamp validation

3. FILE: shopify_webhooks.py
   
   CLASS: ShopifyWebhookHandler(IWebhookHandler)
   
   METHODS:
   - register_webhooks()
     * Create webhooks: orders/fulfilled, app/uninstalled
     * Store webhook IDs
     * Error handling
   - parse_webhook_event()
     * Verify HMAC
     * Transform to universal format
     * Map event types
   - delete_webhooks()
     * Remove all webhooks
     * Handle errors gracefully

4. FILE: postgres_merchant_repository.py
   
   CLASS: PostgresMerchantRepository(IMerchantRepository)
   
   IMPLEMENTATION:
   - Use async SQLAlchemy
   - Follow existing repository patterns
   - Connection pooling
   - Error handling

5. TESTS: tests/infrastructure/shopify/
   - Mock Shopify API responses
   - Test success and error scenarios
   - Test rate limiting
   - Test HMAC verification
   - Integration tests with database
   - 100% coverage

REQUIREMENTS:
- All async methods
- Type hints everywhere
- Comprehensive error handling
- Logging at appropriate levels
- Follow existing infrastructure patterns exactly
```

**Success Criteria:**
- ✅ Shopify client implements all interfaces
- ✅ HMAC verification works correctly
- ✅ Can authenticate with Shopify
- ✅ Can register webhooks
- ✅ All tests pass (100% coverage)

---

#### Task 1.5: Platform Service Layer (2 hours)

**Goal:** Create platform-agnostic business logic

**Claude Code Task:**
```
CREATE: services/platform_service/domain/services/

FILE: platform_service.py

CLASS: PlatformService

CONSTRUCTOR:
- platform_client: IPlatformClient (injected)
- auth_provider: IAuthProvider (injected)
- webhook_handler: IWebhookHandler (injected)
- merchant_repo: IMerchantRepository (injected)
- event_bus: IEventBus (injected)

METHODS:

1. install_merchant(code: str, shop_domain: str, platform: PlatformType) -> PlatformMerchant
   - Exchange code for token
   - Get shop details
   - Create merchant entity
   - Save to repository
   - Register webhooks
   - Publish "merchant.installed" event
   - PLATFORM AGNOSTIC (works for any platform)

2. handle_order_fulfilled(merchant_id: str, order_id: str) -> None
   - Get merchant from repo
   - Get order via platform client (abstracted!)
   - For each line item:
     * Publish "review.request.scheduled" event
     * Include all order data
   - PLATFORM AGNOSTIC

3. uninstall_merchant(merchant_id: str) -> None
   - Get merchant from repo
   - Delete webhooks via platform client
   - Mark merchant as inactive
   - Publish "merchant.uninstalled" event
   - PLATFORM AGNOSTIC

4. get_product_details(merchant_id: str, product_id: str) -> PlatformProduct
   - Get merchant from repo
   - Get product via platform client
   - Return universal product entity
   - PLATFORM AGNOSTIC

TESTS: tests/domain/services/test_platform_service.py
- Mock all dependencies
- Test each method in isolation
- Test error handling
- Test event publishing
- Verify platform abstraction (no Shopify-specific code)
- 100% coverage

CRITICAL: This service must have ZERO platform-specific code.
It only knows about interfaces, not implementations.
```

**Success Criteria:**
- ✅ Service has zero platform-specific code
- ✅ All logic is platform-agnostic
- ✅ Events published correctly
- ✅ All tests pass with mocked dependencies

---

#### Task 1.6: Platform API Routes (2 hours)

**Goal:** Create FastAPI routes for platform operations

**Claude Code Task:**
```
CREATE: services/platform_service/api/

1. FILE: main.py
   - FastAPI app setup
   - CORS configuration
   - Health check endpoint
   - Error handlers
   - Follow review_service/api/main.py pattern

2. FILE: dependencies.py
   - get_platform_service() dependency
   - Inject correct platform client based on merchant
   - Database session management
   - Follow existing dependency injection patterns

3. FILE: routes/auth.py
   
   ENDPOINTS:
   
   GET /auth/{platform}/install
   - Query params: shop_domain
   - Generate OAuth URL
   - Return authorization URL
   
   GET /auth/{platform}/callback
   - Query params: code, shop, state
   - Verify HMAC
   - Install merchant
   - Redirect to success page
   
   POST /auth/{merchant_id}/uninstall
   - Verify authentication
   - Uninstall merchant
   - Clean up resources

4. FILE: routes/webhooks.py
   
   POST /webhooks/{platform}/orders/fulfilled
   - Verify webhook signature
   - Parse webhook payload
   - Handle order fulfilled event
   - Return 200 immediately
   
   POST /webhooks/{platform}/app/uninstalled
   - Verify webhook signature
   - Handle app uninstall
   - Return 200 immediately

5. TESTS: tests/api/
   - Test all endpoints
   - Mock dependencies
   - Test error cases
   - Test authentication
   - 100% coverage

SECURITY:
- HMAC verification on all webhooks
- Request validation (Pydantic)
- Rate limiting
- CORS properly configured
```

**Success Criteria:**
- ✅ Can complete OAuth flow
- ✅ Webhooks verified correctly
- ✅ All routes have tests
- ✅ API follows existing patterns

---

### Day 4: Caching Layer

#### Task 1.7: Redis Caching Implementation (3 hours)

**Claude Code Task:**
```
ENHANCE: shared/cache/

1. FILE: cache_service.py
   
   INTERFACE: ICacheService (ABC)
   - get(key: str) -> Optional[Any]
   - set(key: str, value: Any, ttl: int) -> bool
   - delete(key: str) -> bool
   - delete_pattern(pattern: str) -> int
   - exists(key: str) -> bool
   
   CLASS: RedisCacheService(ICacheService)
   - Use Railway REDIS_URL
   - JSON serialization
   - Error handling (log, don't crash)
   - Connection pooling

2. FILE: decorators.py
   
   DECORATOR: @cached
   - Cache function results
   - Key pattern with formatting
   - Configurable TTL
   - Async support
   - Preserve function metadata
   
   Usage:
   @cached(key_pattern="product:reviews:{product_id}", ttl=300)
   async def get_product_reviews(product_id: str):
       ...

3. UPDATE: services/review_service/domain/service.py
   
   ADD: ICacheService injection
   
   ADD CACHING:
   - get_approved_reviews() -> cache 5 min
   - get_product_rating() -> cache 10 min
   - get_rating_distribution() -> cache 10 min
   
   INVALIDATE ON:
   - create_review()
   - approve_review()
   - reject_review()

4. TESTS:
   - Test cache hit/miss
   - Test TTL expiration
   - Test pattern deletion
   - Test decorator
   - Integration tests with Redis
   - 100% coverage

CACHE KEY PATTERNS:
- product:reviews:{product_id} (list of reviews)
- product:rating:{product_id} (average rating)
- product:stats:{product_id} (distribution)
- widget:config:{merchant_id} (widget settings)
```

**Success Criteria:**
- ✅ Cache service working with Railway Redis
- ✅ Decorator caches function results
- ✅ Cache invalidation works
- ✅ Performance improvement measurable
- ✅ All tests pass

---

### Day 5: Review Token System & Email Setup

#### Task 1.8: Review Token System (2 hours)

**Goal:** Secure token system for review submissions

**Database Migration:**
```sql
CREATE TABLE review_tokens (
    id VARCHAR(36) PRIMARY KEY,
    token VARCHAR(255) UNIQUE NOT NULL,
    merchant_id VARCHAR(36) NOT NULL REFERENCES merchants(id),
    product_id VARCHAR(255) NOT NULL,
    order_id VARCHAR(255) NOT NULL,
    customer_email VARCHAR(255) NOT NULL,
    customer_name VARCHAR(255),
    used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (merchant_id) REFERENCES merchants(id) ON DELETE CASCADE
);

CREATE INDEX idx_review_tokens_token ON review_tokens(token);
CREATE INDEX idx_review_tokens_unused ON review_tokens(used, expires_at) WHERE used = false;
CREATE INDEX idx_review_tokens_merchant_product ON review_tokens(merchant_id, product_id);
```

**Claude Code Task:**
```
CREATE: services/review_service/domain/entities/review_token.py

ENTITY: ReviewToken
- id, token, merchant_id, product_id, order_id
- customer_email, customer_name
- used, used_at, expires_at, created_at

METHODS:
- generate_token() -> str
  * Use secrets.token_urlsafe(32)
  * Cryptographically secure
- is_valid() -> bool
  * Not used
  * Not expired
- mark_as_used() -> None
  * Atomic operation

CREATE: services/review_service/infrastructure/postgres_review_token_repository.py

IMPLEMENTATION: IReviewTokenRepository
- create(token: ReviewToken) -> ReviewToken
- get_by_token(token: str) -> Optional[ReviewToken]
- mark_as_used(token: str) -> bool (atomic!)
- delete_expired() -> int
- Follow existing repository patterns

TESTS:
- Test token generation (uniqueness)
- Test validation logic
- Test expiration
- Test atomic mark_as_used
- 100% coverage
```

**Success Criteria:**
- ✅ Tokens are cryptographically secure
- ✅ Cannot reuse tokens
- ✅ Expiration works correctly
- ✅ All tests pass

---

#### Task 1.9: Email Service Foundation (2 hours)

**Goal:** Email sending infrastructure

**Claude Code Task:**
```
CREATE: services/email_service/

CHOOSE EMAIL PROVIDER: Resend (recommended)
- Simple API
- Good deliverability
- Generous free tier (100 emails/day)
- Easy setup

1. FILE: infrastructure/email_client.py
   
   CLASS: IEmailClient (ABC)
   - send_email(to, subject, html, text) -> bool
   
   CLASS: ResendEmailClient(IEmailClient)
   - Use Resend API
   - Error handling
   - Retry logic
   - Logging

2. FILE: templates/review_request.py
   
   FUNCTION: render_review_request_email(data: dict) -> Tuple[str, str]
   - Use Jinja2
   - HTML version
   - Plain text version
   - Mobile responsive
   - Variables: customer_name, product_title, review_url, shop_name

3. FILE: tasks/send_review_request.py
   
   CELERY TASK: send_review_request_email
   - @celery_app.task(queue='emails', max_retries=3)
   - Get product from platform service
   - Generate review token (7 day expiration)
   - Render email template
   - Send via email client
   - Log result
   - Handle errors with retry

4. FILE: tasks/send_review_confirmation.py
   
   CELERY TASK: send_review_confirmation_email
   - Sent after review submission
   - Thank customer
   - Set expectations

5. TESTS:
   - Mock email client
   - Test template rendering
   - Test Celery task
   - Test retry logic
   - 100% coverage

ENV VARS:
- RESEND_API_KEY=re_xxx
- FROM_EMAIL=reviews@yourdomain.com
```

**Success Criteria:**
- ✅ Can send emails via Resend
- ✅ Templates render correctly
- ✅ Celery tasks queue properly
- ✅ Retries work on failure
- ✅ All tests pass

---

### Week 1 Summary

**What we built:**
- ✅ Railway infrastructure (PostgreSQL + Redis)
- ✅ Cloudflare R2 storage
- ✅ Platform abstraction layer (interfaces)
- ✅ Shopify implementation (first platform)
- ✅ Platform service (business logic)
- ✅ OAuth and webhook endpoints
- ✅ Caching layer with Redis
- ✅ Review token system
- ✅ Email service foundation

**Tests:** ~100 tests, 100% coverage on new code

**Deployment:** All services deployed to Railway

**Time spent:** ~25-30 hours (with Claude Code assistance)

---

## Week 2: Review Collection & Moderation

### Day 6-7: Public Review Submission

#### Task 2.1: Review Entity Enhancements (1 hour)

**Database Migration:**
```sql
ALTER TABLE reviews ADD COLUMN merchant_id VARCHAR(36) REFERENCES merchants(id);
ALTER TABLE reviews ADD COLUMN verified_purchase BOOLEAN DEFAULT FALSE;
ALTER TABLE reviews ADD COLUMN media_urls TEXT[] DEFAULT '{}';
ALTER TABLE reviews ADD COLUMN platform_metadata JSONB DEFAULT '{}';

CREATE INDEX idx_reviews_merchant_product ON reviews(merchant_id, product_id, status);
```

**Claude Code Task:**
```
UPDATE: services/review_service/domain/entities/review.py

ADD FIELDS:
- merchant_id: str
- verified_purchase: bool
- media_urls: List[str]
- platform_metadata: dict

UPDATE: Validation logic
UPDATE: Existing tests
ADD: Tests for new fields

UPDATE: services/review_service/infrastructure/postgres_review_repository.py
- Handle new fields
- Update queries
- Migration
```

---

#### Task 2.2: Image Upload Endpoint (2 hours)

**Claude Code Task:**
```
CREATE: services/review_service/api/routes/public.py

ENDPOINT: POST /public/upload-image
- Accept multipart/form-data
- Validate file:
  * Type: image/jpeg, image/png, image/webp
  * Size: < 5MB
  * Dimensions: min 200x200, max 4000x4000
- Upload to R2 via IStorageService
- Return public URL
- No authentication needed
- Rate limit: 10 uploads per IP per minute

ENDPOINT: GET /public/review/{token}
- Validate token (not used, not expired)
- Get product details from platform service
- Return: product info + token validity
- Frontend uses this to render form

TESTS:
- Test file validation (type, size)
- Test upload success
- Test upload failure
- Test token validation
- Test rate limiting
```

**Success Criteria:**
- ✅ Images upload to R2
- ✅ Validation prevents bad files
- ✅ Rate limiting works
- ✅ All tests pass

---

#### Task 2.3: Review Submission Endpoint (3 hours)

**Claude Code Task:**
```
ADD TO: services/review_service/api/routes/public.py

ENDPOINT: POST /public/review/{token}

REQUEST BODY (Pydantic):
{
  "rating": 1-5,
  "title": "string (max 200)",
  "content": "string (max 2000)",
  "media_urls": ["url1", "url2"] (optional, max 5)
}

LOGIC:
1. Validate token (not used, not expired)
2. Get merchant + product from token
3. Validate request body
4. Verify media_urls are from our R2 bucket
5. Create review (status: "pending")
   - Include merchant_id
   - verified_purchase: true (came from order)
   - media_urls from request
6. Mark token as used (atomic!)
7. Publish "review.created" event
8. Queue confirmation email
9. Return success

ERROR HANDLING:
- Token expired -> 410 Gone
- Token used -> 409 Conflict
- Validation error -> 400 Bad Request
- Server error -> 500 (log to Sentry)

TESTS:
- Test valid submission
- Test with/without images
- Test token reuse prevention
- Test validation errors
- Test expired token
- Test concurrent submissions
- 100% coverage
```

**Success Criteria:**
- ✅ Customers can submit reviews
- ✅ Images attach correctly
- ✅ Token reuse impossible
- ✅ All edge cases handled
- ✅ All tests pass

---

### Day 8-9: Admin Dashboard API

#### Task 2.4: Authentication Middleware (1 hour)

**Claude Code Task:**
```
CREATE: services/review_service/api/auth.py

FUNCTION: verify_shopify_session_token(token: str) -> Dict
- Decode Shopify session token JWT
- Verify signature
- Extract shop_domain
- Return merchant data or raise 401

DEPENDENCY: get_authenticated_merchant() -> PlatformMerchant
- Extract token from Authorization header
- Verify token
- Get merchant from repository
- Raise 401 if invalid

TESTS:
- Test with valid token
- Test with invalid token
- Test with expired token
- Test missing token
```

---

#### Task 2.5: Admin Review Endpoints (3 hours)

**Claude Code Task:**
```
CREATE: services/review_service/api/routes/admin.py

ENDPOINT: GET /admin/reviews
- Require authentication
- Query params: status (pending/approved/rejected), limit, offset
- Filter by merchant_id from auth
- Pagination
- Return: reviews list + total count

ENDPOINT: GET /admin/reviews/{review_id}
- Require authentication
- Verify ownership (review.merchant_id == auth.merchant_id)
- Return full review details

ENDPOINT: POST /admin/reviews/{review_id}/approve
- Require authentication
- Verify ownership
- Update status to "approved"
- Invalidate cache (product:reviews:{product_id})
- Publish "review.approved" event
- Queue approval email to customer
- Return updated review

ENDPOINT: POST /admin/reviews/{review_id}/reject
- Require authentication
- Verify ownership
- Body: { "reason": "string" }
- Update status to "rejected"
- Store rejection_reason
- Publish "review.rejected" event
- Optional: Queue rejection email
- Return updated review

ENDPOINT: GET /admin/stats
- Require authentication
- Return stats for merchant:
  * total_reviews
  * pending_count
  * approved_count
  * rejected_count
  * average_rating
  * recent_reviews (last 7 days)
- Cache 5 minutes

TESTS:
- Test all endpoints
- Test authentication
- Test authorization (wrong merchant)
- Test pagination
- Test caching
- 100% coverage

SECURITY:
- Always verify merchant ownership
- Never expose other merchants' data
- Log all admin actions
```

**Success Criteria:**
- ✅ Merchants can list reviews
- ✅ Merchants can approve/reject
- ✅ Stats calculate correctly
- ✅ Authorization works
- ✅ All tests pass

---

### Day 10: AI Auto-Moderation

#### Task 2.6: AI Moderation Service (4 hours)

**Claude Code Task:**
```
CREATE: services/ai_service/domain/services/moderation_service.py

CLASS: ModerationService

METHOD: moderate_review(content: str) -> Dict

LOGIC:
1. Call Claude API with moderation prompt
2. Detect:
   - is_spam (boolean)
   - has_profanity (boolean)
   - is_genuine (boolean)
   - confidence (0.0-1.0)
   - reason (string)
3. Return structured JSON

PROMPT ENGINEERING:
"""
Analyze this product review for moderation:

"{content}"

Return JSON:
{
  "is_spam": boolean,
  "has_profanity": boolean,
  "is_genuine": boolean,
  "confidence": 0.0-1.0,
  "reason": "explanation"
}

Consider:
- Spam: Generic text, promotional content, unrelated
- Profanity: Offensive language
- Genuine: Real customer experience, specific details
"""

ERROR HANDLING:
- API timeout -> retry 2 times
- Rate limit -> exponential backoff
- Parse error -> log and return safe default

CREATE: services/ai_service/domain/services/sentiment_service.py

CLASS: SentimentService

METHOD: analyze_sentiment(content: str) -> Dict

RETURN:
{
  "sentiment_score": -1.0 to 1.0,
  "positive_points": ["point1", "point2"],
  "negative_points": ["point1", "point2"],
  "topics": ["topic1", "topic2"]
}

CREATE: services/ai_service/tasks/auto_moderate.py

CELERY TASK: auto_moderate_review

LOGIC:
1. Get review from review service
2. Run moderation check
3. Run sentiment analysis
4. Store results in review.ai_moderation, review.ai_sentiment
5. Auto-approve if:
   - not spam
   - not profanity
   - is_genuine
   - confidence > 0.8
   - rating >= 4
6. Otherwise: Leave as pending
7. Log decision

TESTS:
- Mock Claude API
- Test with spam review
- Test with profanity
- Test with genuine review
- Test auto-approval logic
- Test error handling
- 100% coverage

ENV VARS:
- ANTHROPIC_API_KEY=sk-xxx
- ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

**Success Criteria:**
- ✅ AI moderation works
- ✅ Sentiment analysis works
- ✅ Safe reviews auto-approve
- ✅ Suspicious reviews flagged
- ✅ Errors handled gracefully
- ✅ All tests pass

---

#### Task 2.7: Connect Auto-Moderation to Review Flow (1 hour)

**Claude Code Task:**
```
UPDATE: services/review_service/domain/service.py

IN: create_review() method

AFTER: Review saved to database
ADD: Publish event "review.needs_moderation"

CREATE: Event handler in AI service
SUBSCRIBE TO: "review.needs_moderation"
TRIGGER: auto_moderate_review Celery task

UPDATE: Review entity to store AI results
ADD FIELDS:
- ai_moderation: dict (JSONB)
- ai_sentiment: dict (JSONB)
- auto_approved: bool

TESTS:
- Test event published
- Test AI service receives event
- Integration test: submission -> auto-moderation
```

---

### Week 2 Summary

**What we built:**
- ✅ Public review submission with images
- ✅ Review token security system
- ✅ Admin dashboard API (list, approve, reject)
- ✅ Authentication & authorization
- ✅ AI auto-moderation with Claude
- ✅ Sentiment analysis

**Tests:** ~80 new tests, maintaining 100% coverage

**Deployment:** Updated all services on Railway

**Time spent:** ~25-30 hours

---

## Week 3: Widget Implementation

### Day 11-12: Widget API Service

#### Task 3.1: Widget Service Setup (2 hours)

**Claude Code Task:**
```
CREATE: services/widget_service/

STRUCTURE:
├── api/
│   ├── main.py
│   ├── routes/
│   │   └── widget.py
│   └── dependencies.py
├── domain/
│   └── services/
│       └── widget_service.py
└── tests/

FILE: api/main.py
- FastAPI app
- CORS: Allow all origins (public widget)
- Cache-Control headers
- Compression enabled
- Health check

FILE: domain/services/widget_service.py

CLASS: WidgetService

METHOD: get_widget_data(merchant_id, product_id) -> Dict

LOGIC:
1. Check cache (Redis): widget:data:{merchant_id}:{product_id}
2. If hit: return cached (TTL: 5 min)
3. If miss:
   - Call review service: get approved reviews
   - Call review service: get rating summary
   - Get widget config from merchant
   - Format for widget consumption
   - Cache result
   - Return

RESPONSE FORMAT:
{
  "rating": {
    "average": 4.5,
    "count": 123,
    "distribution": {1: 2, 2: 3, 3: 10, 4: 30, 5: 78}
  },
  "reviews": [
    {
      "id": "...",
      "rating": 5,
      "title": "Great!",
      "content": "...",
      "customer_name": "John D.",
      "created_at": "2025-11-01",
      "verified_purchase": true,
      "media_urls": ["url1"],
      "helpful_count": 5
    }
  ],
  "config": {
    "theme": "light",
    "primary_color": "#000000",
    "show_photos": true,
    "show_verified_badge": true
  }
}

TESTS:
- Test cache hit (fast path)
- Test cache miss
- Test with no reviews
- Test performance (<50ms target)
```

---

#### Task 3.2: Widget Endpoints (2 hours)

**Claude Code Task:**
```
CREATE: services/widget_service/api/routes/widget.py

ENDPOINT: GET /widget/{merchant_id}/{product_id}

HEADERS:
- Cache-Control: public, max-age=300
- ETag: {hash of content}
- Access-Control-Allow-Origin: *

QUERY PARAMS:
- limit: int = 10 (reviews per page)
- page: int = 1
- sort: "recent" | "helpful" | "highest" | "lowest"

RESPONSE:
- Widget data JSON
- Gzip compressed
- < 100ms p95

ENDPOINT: GET /widget/{merchant_id}/{product_id}/rating

PURPOSE: Ultra-fast rating badge
CACHE: 10 minutes
RESPONSE: { "average": 4.5, "count": 123 }
TARGET: < 20ms p95

ENDPOINT: PUT /widget/{merchant_id}/config
- Require authentication
- Update widget configuration
- Clear cache

TESTS:
- Test all endpoints
- Test caching headers
- Test performance
- Test pagination
- Test sorting
- 100% coverage
```

**Success Criteria:**
- ✅ Widget API < 50ms p95
- ✅ Rating badge < 20ms p95
- ✅ Caching works correctly
- ✅ CORS configured
- ✅ All tests pass

---

### Day 13-14: Widget JavaScript

#### Task 3.3: Widget JavaScript Core (6 hours)

**Manual Implementation (not Claude Code - needs careful UI work)**

**Files to Create:**

```
public/
├── widget.js (main widget)
├── rating-badge.js (lightweight badge)
└── styles/
    └── widget.css (embedded in JS)
```

**widget.js Requirements:**

```javascript
// Core Features:
// 1. Async data fetching
// 2. Render reviews with stars
// 3. Photo gallery with lightbox
// 4. Pagination
// 5. Sorting dropdown
// 6. Responsive design
// 7. Accessibility (ARIA labels)
// 8. Theme customization
// 9. Auto-init from data attributes
// 10. Error handling

// Usage:
<div id="review-widget" 
     data-merchant-id="abc123"
     data-product-id="prod_xyz">
</div>
<script src="https://widget.yourdomain.com/widget.js"></script>

// Performance:
// - Vanilla JS (no framework)
// - < 10KB gzipped
// - No jQuery or dependencies
// - Lazy load images
// - IntersectionObserver for lazy reviews

// Browser Support:
// - Chrome/Edge (last 2 versions)
// - Firefox (last 2 versions)
// - Safari (last 2 versions)
// - Mobile browsers
```

**rating-badge.js Requirements:**

```javascript
// Ultra-lightweight rating display
// < 2KB gzipped
// Shows: ★★★★★ 4.5 (123 reviews)
// Links to full widget

// Usage:
<span class="review-rating-badge"
      data-merchant-id="abc123"
      data-product-id="prod_xyz">
</span>
<script src="https://widget.yourdomain.com/rating-badge.js"></script>
```

**Testing:**
- Manual testing on various themes
- Mobile responsiveness
- Performance testing (Lighthouse)
- Accessibility audit (WAVE)

---

#### Task 3.4: Widget Customization (2 hours)

**Claude Code Task:**
```
CREATE: Widget configuration entity and endpoints

UPDATE: services/platform_service/domain/entities/platform_merchant.py

ENHANCE: widget_config with defaults:
{
  "theme": "auto",  // "light", "dark", "auto"
  "primary_color": "#000000",
  "star_color": "#FFD700",
  "font_family": "inherit",
  "show_photos": true,
  "show_verified_badge": true,
  "show_date": true,
  "reviews_per_page": 10,
  "default_sort": "recent",
  "enable_helpful_button": true,
  "custom_css": ""
}

CREATE: Admin endpoint to update config

ENDPOINT: PUT /admin/widget/config
- Update widget_config
- Validate colors (hex format)
- Clear widget cache
- Return updated config

CREATE: Preview endpoint

ENDPOINT: GET /admin/widget/preview
- Return HTML preview with current config
- Used in admin dashboard

TESTS:
- Test config validation
- Test cache invalidation
- Test defaults
```

---

### Day 15: Installation System

#### Task 3.5: Theme Installer (4 hours)

**Claude Code Task:**
```
CREATE: services/platform_service/domain/services/theme_installer.py

CLASS: ShopifyThemeInstaller

METHOD: detect_theme(merchant_id) -> str
- Call Shopify Theme API
- Detect theme type (Dawn, Debut, custom)
- Return theme name

METHOD: generate_installation_code(merchant_id) -> str
- Generate Liquid snippet
- Include merchant_id and API endpoint
- Return code snippet

METHOD: auto_install(merchant_id) -> bool
- Get active theme
- Find product template
- Inject widget code via Theme API
- Backup before modification
- Rollback on error
- Return success/failure

METHOD: verify_installation(merchant_id, product_url) -> bool
- Fetch product page
- Check for widget div
- Verify widget loads
- Return true/false

TESTS:
- Mock Shopify Theme API
- Test various theme types
- Test error scenarios
- Test rollback logic
```

---

#### Task 3.6: Installation Dashboard (2 hours)

**Create admin UI for installation (HTML/JS)**

**Features:**
1. Installation status indicator
2. One-click auto-install button
3. Manual code snippet (fallback)
4. Theme detection
5. Installation verification
6. Troubleshooting tips

---

### Week 3 Summary

**What we built:**
- ✅ Widget Service with caching
- ✅ Widget JavaScript (responsive, accessible)
- ✅ Rating badge widget
- ✅ Widget customization API
- ✅ Theme installer (auto + manual)
- ✅ Installation dashboard

**Performance:**
- Widget API: < 50ms p95 ✅
- Rating badge: < 20ms p95 ✅
- JavaScript: < 10KB gzipped ✅

**Tests:** ~50 new tests

**Time spent:** ~30 hours

---

## Week 4: Polish & Launch

### Day 16-17: End-to-End Testing

#### Task 4.1: Complete Flow Testing (6 hours)

**Create comprehensive integration tests:**

```
tests/integration/test_complete_flow.py

TEST: Happy Path
1. Merchant installs app (OAuth)
2. Webhooks registered
3. Customer places order
4. Order fulfilled webhook
5. Review request email queued (7 days)
6. Customer receives email
7. Customer submits review with photos
8. AI auto-moderates
9. Review auto-approved (if safe)
10. Review appears in admin
11. Review appears on widget
12. Cache invalidated correctly

TEST: Error Scenarios
- Token expired
- Token reused
- Invalid image
- Shopify API error
- Claude API error
- Database error
- Redis error
- Email failure

TEST: Edge Cases
- Concurrent review submissions
- Product deleted
- Very long review
- Many images
- App uninstalled mid-process
- Network timeouts
```

**Run with real services:**
- Real Shopify test store
- Real emails (catch-all address)
- Real Claude API
- Real Railway services

---

### Day 18: Performance Optimization

#### Task 4.2: Database Optimization (3 hours)

**Claude Code Task:**
```
CREATE: alembic/versions/xxx_performance_indexes.py

ADD INDEXES:
- (merchant_id, product_id, status, created_at DESC)
  For: Fast review queries by merchant/product
- (product_id, status) WHERE status = 'approved'
  For: Widget queries (only approved reviews)
- (merchant_id, status, created_at DESC)
  For: Admin dashboard queries
- (customer_email, merchant_id)
  For: Customer review history

RUN EXPLAIN ANALYZE:
- Verify indexes are used
- Check query plans
- Measure before/after performance

TARGET:
- All queries < 20ms
- Index usage: 100%
```

---

#### Task 4.3: Cache Optimization (2 hours)

**Optimize cache strategy:**

```
Widget Cache:
- TTL: 5 minutes
- Pre-warm on review approval
- Separate cache for rating badge (10 min TTL)

Review List Cache:
- TTL: 5 minutes per page
- Invalidate on approval/rejection

Stats Cache:
- TTL: 5 minutes
- Invalidate on any review state change

Implement cache warming:
- After review approval
- Pre-fetch popular products
```

---

### Day 19: Monitoring & Operations

#### Task 4.4: Monitoring Setup (4 hours)

**Claude Code Task:**
```
CREATE: shared/monitoring/

1. FILE: sentry.py
   - Initialize Sentry
   - Capture exceptions
   - Add context (merchant, request)
   - Filter sensitive data

2. FILE: logger.py
   - Structured JSON logging
   - Log levels
   - Context (request_id, merchant_id)
   - Performance metrics

3. FILE: metrics.py
   - Track key metrics:
     * Request rate per endpoint
     * Response time (p50, p95, p99)
     * Error rate
     * Cache hit rate
     * Reviews created per day
     * Active merchants
   - Export for Prometheus

4. FILE: health.py
   - Health check endpoints
   - Check database connection
   - Check Redis connection
   - Check Celery workers
   - Disk space, memory

ADD TO ALL SERVICES:
- Sentry integration
- Structured logging
- Health check endpoints
- Metrics export

ENV VARS:
- SENTRY_DSN=https://xxx@sentry.io/xxx
- LOG_LEVEL=INFO
```

---

#### Task 4.5: Alerting Setup (2 hours)

**Setup BetterUptime or similar:**

Alerts for:
- Any service down (> 1 minute)
- Error rate > 1%
- Response time p95 > 500ms
- Database connections > 80%
- Redis memory > 80%
- Disk space > 90%
- Celery queue length > 100

**Notification channels:**
- Email
- Slack (optional)
- SMS for critical (optional)

---

### Day 20: Documentation & Launch Prep

#### Task 4.6: Documentation (4 hours)

**For Merchants:**

```
docs/
├── installation.md
│   - Shopify app store link
│   - Installation steps (auto + manual)
│   - Widget setup
│   - Customization guide
│   - Troubleshooting
│
├── configuration.md
│   - Theme customization
│   - Email timing
│   - Auto-moderation settings
│   - Widget appearance
│
├── faq.md
│   - Common questions
│   - Known issues
│   - Feature requests
│
└── video-tutorials/
    - Installation (2 min)
    - First review (3 min)
    - Customization (4 min)
```

**For Developers:**

```
docs/dev/
├── architecture.md (update with new decisions)
├── setup.md (local development)
├── testing.md (running tests)
├── deployment.md (Railway deployment)
├── contributing.md
└── api/
    - OpenAPI spec (auto-generated)
    - Authentication
    - Rate limits
```

---

#### Task 4.7: Security Audit (2 hours)

**Security Checklist:**

```
✓ Authentication
  - Shopify HMAC verified
  - Session tokens validated
  - No credentials in code

✓ Authorization
  - Merchants can only access own data
  - Review tokens are single-use
  - Token expiration works

✓ Input Validation
  - All inputs validated (Pydantic)
  - File upload validation
  - SQL injection prevented (ORM)
  - XSS prevention

✓ Data Protection
  - HTTPS only (Railway provides)
  - Sensitive data encrypted
  - No PII in logs
  - Secure headers set

✓ Dependencies
  - All packages up to date
  - Run: poetry update
  - No known vulnerabilities

✓ Rate Limiting
  - Widget: 1000 req/min per IP
  - API: 100 req/min per merchant
  - Upload: 10 per minute per IP
```

**Run security test suite:**
```bash
poetry run pytest tests/security/ -v
```

---

#### Task 4.8: Launch Preparation (2 hours)

**Pre-Launch Checklist:**

```
✓ Code Quality
  - All tests pass (300+ tests)
  - No linting errors
  - No type errors (MyPy)
  - Code reviewed

✓ Infrastructure (Railway)
  - PostgreSQL: Pro plan
  - Redis: Pro plan
  - All services deployed
  - SSL certificates active
  - Backups enabled (Railway automatic)
  - Monitoring enabled

✓ Shopify
  - App created in Partners
  - App Store listing draft ready
  - Screenshots captured
  - Demo video recorded
  - Pricing tiers set ($15/month)

✓ Operations
  - Support email active
  - Incident response plan
  - Rollback procedure documented
  - Monitoring alerts set
  - On-call schedule (you!)

✓ Legal
  - Privacy policy
  - Terms of service
  - GDPR compliance checked
```

---

### Launch Day Strategy

**Day 1: Soft Launch**
```
Hour 1: Deploy to production
Hour 2: Verify all services running
Hour 3: Run smoke tests
Hour 4: Install on YOUR test store
Hour 5: Complete full flow (order -> review)
Hour 6-10: Monitor closely
End of day: Fix any critical issues
```

**Day 2-3: Private Beta**
```
- Set app to "Unlisted"
- Share link with 5 beta testers
- Monitor closely
- Gather feedback
- Fix reported issues
- Monitor for 48 hours
```

**Day 4: Public Launch**
```
- Set app to "Public"
- Submit to Shopify App Store
- Post launch announcement (Twitter, Reddit, etc.)
- Monitor metrics
- Respond to feedback
- Celebrate! 🎉
```

---

### Week 4 Summary

**What we built:**
- ✅ End-to-end integration tests
- ✅ Performance optimizations
- ✅ Monitoring and alerting
- ✅ Complete documentation
- ✅ Security hardening
- ✅ Launch preparation

**Final Statistics:**
- Total tests: 300+
- Test coverage: > 95%
- Services: 5 (Review, AI, Widget, Platform, Email)
- API endpoints: 25+
- Performance: All targets met
- Ready for customers: YES

---

## Deployment & Operations

### Railway Configuration

**Project Structure:**
```
railway-project/
├── PostgreSQL (Pro - $20/mo)
│   - Storage: 10GB
│   - Connections: 100
│   - Backups: Automatic
│
├── Redis (Pro - $15/mo)
│   - Memory: 1GB
│   - Persistence: Yes
│
├── review-service
│   - Command: uvicorn services.review_service.api.main:app --host 0.0.0.0 --port $PORT
│   - Health: /health
│   - Replicas: 1 (scale to 2-3 later)
│
├── ai-service
│   - Command: uvicorn services.ai_service.api.main:app --host 0.0.0.0 --port $PORT
│   - Health: /health
│   - Replicas: 1
│
├── widget-service
│   - Command: uvicorn services.widget_service.api.main:app --host 0.0.0.0 --port $PORT
│   - Health: /health
│   - Replicas: 2 (public-facing, needs redundancy)
│
├── platform-service
│   - Command: uvicorn services.platform_service.api.main:app --host 0.0.0.0 --port $PORT
│   - Health: /health
│   - Replicas: 1
│
└── celery-worker
    - Command: celery -A shared.celery_app worker --loglevel=info --concurrency=2
    - Type: Worker (not web service)
    - Replicas: 1 (scale to 2-3 later)
```

**Environment Variables (shared across services):**
```bash
# Database
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis
REDIS_URL=${{Redis.REDIS_URL}}

# Celery
CELERY_BROKER_URL=${{Redis.REDIS_URL}}/2
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}/3

# Cloudflare R2
R2_ENDPOINT=https://xxx.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=xxx
R2_SECRET_ACCESS_KEY=xxx
R2_BUCKET_NAME=review-platform-media
R2_PUBLIC_URL=https://media.yourdomain.com

# Shopify
SHOPIFY_API_KEY=xxx
SHOPIFY_API_SECRET=xxx
SHOPIFY_APP_URL=https://platform-service.railway.app

# AI
ANTHROPIC_API_KEY=sk-xxx
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Email
RESEND_API_KEY=re_xxx
FROM_EMAIL=reviews@yourdomain.com

# Monitoring
SENTRY_DSN=https://xxx@sentry.io/xxx
LOG_LEVEL=INFO

# App
ENVIRONMENT=production
SECRET_KEY=xxx
```

---

### Deployment Commands

**Initial Deployment:**
```bash
# Link to Railway
railway link

# Deploy all services
railway up

# Run migrations
railway run poetry run alembic upgrade head

# Verify
railway status
```

**Updates:**
```bash
# Push to GitHub
git push origin main

# Railway auto-deploys
# Watch logs
railway logs
```

---

### Monitoring Dashboards

**Railway Dashboard:**
- Service health
- Resource usage (CPU, memory)
- Logs (real-time)
- Deployments

**Sentry:**
- Error tracking
- Performance monitoring
- Release tracking

**BetterUptime:**
- Uptime monitoring
- Response time tracking
- Incident management

**Custom Metrics (Future):**
- Grafana dashboard
- Reviews per day
- Active merchants
- Widget performance

---

### Backup & Recovery

**Database Backups (Railway Automatic):**
- Daily snapshots
- 7-day retention
- Point-in-time recovery

**Manual Backup:**
```bash
# Export database
railway run pg_dump $DATABASE_URL > backup.sql

# Upload to S3/R2 for long-term storage
```

**Disaster Recovery Plan:**
1. Check Railway status page
2. View service logs
3. Rollback deployment if needed: `railway rollback`
4. Restore from backup if needed
5. Notify customers (status page)

---

### Scaling Strategy

**Month 1-3 (0-50 merchants):**
```
Current setup sufficient
Cost: ~$35/mo
```

**Month 3-6 (50-200 merchants):**
```
- Scale review-service: 2 replicas
- Scale widget-service: 3 replicas
- Scale celery-workers: 2 replicas
- Upgrade PostgreSQL: 20GB storage
Cost: ~$100/mo
```

**Month 6-12 (200-1000 merchants):**
```
- All services: 2-3 replicas
- PostgreSQL: Read replicas
- Redis: 2GB memory
- Add CDN (Cloudflare)
Cost: ~$250/mo
```

**Month 12+ (1000+ merchants):**
```
Consider migration to:
- Render (more control)
- AWS (enterprise features)
Cost: $500-1000/mo
```

---

## Success Metrics & KPIs

### Technical Metrics

**Performance (measured via Sentry):**
- Widget API p95: < 100ms ✅
- Admin API p95: < 200ms ✅
- Cache hit rate: > 90% ✅
- Uptime: > 99.9% ✅
- Error rate: < 0.1% ✅

**Quality:**
- Test coverage: > 95% ✅
- Code duplication: < 3% ✅
- Tech debt ratio: < 5% ✅

### Business Metrics

**Week 1-4 (MVP Launch):**
- [ ] 5 active merchants
- [ ] 50+ reviews collected
- [ ] 0 critical bugs

**Month 2:**
- [ ] 10 active merchants
- [ ] 5 paying ($75 MRR)
- [ ] 500+ reviews collected
- [ ] < 2 hour support response time

**Month 3:**
- [ ] 25 active merchants
- [ ] 10 paying ($150 MRR)
- [ ] 2,000+ reviews collected
- [ ] Net Promoter Score: > 50

**Month 6:**
- [ ] 100 active merchants
- [ ] 50 paying ($750 MRR)
- [ ] 10,000+ reviews collected
- [ ] First enterprise partner discussion

---

## Future Platform Additions

### When Enterprise Partner Requests New Platform

**Example: BigCommerce Request**

**Timeline: 3 Days**

**Day 1: Implementation (4 hours with Claude Code)**
```
Claude Code Prompt:

"Create BigCommerce platform implementation:

1. Study Shopify implementation in infrastructure/shopify/
2. Create infrastructure/bigcommerce/ with same structure
3. Implement:
   - BigCommerceClient(IPlatformClient)
   - BigCommerceAuthProvider(IAuthProvider)
   - BigCommerceWebhookHandler(IWebhookHandler)

4. Follow OAuth flow for BigCommerce
5. Map BigCommerce webhooks to our events
6. Transform BigCommerce data to our universal entities

7. Write comprehensive tests
8. 100% coverage

Reference BigCommerce API docs: https://developer.bigcommerce.com/
```

**Day 2: Testing & Integration (3 hours)**
- Set up BigCommerce test store
- Test OAuth flow
- Test webhook processing
- Test product/order data
- End-to-end testing

**Day 3: Deployment & Documentation (2 hours)**
- Deploy to Railway
- Update documentation
- Create BigCommerce installation guide
- Notify partner: Ready!

**Cost to Add Platform:**
- Development: 9 hours total (Claude Code makes it fast)
- Testing: Minimal (interfaces already tested)
- Deployment: Zero (Railway handles it)

**This is only possible because we built the abstraction layer in Week 1!**

---

## Appendix: Key Decisions Rationale

### Why Platform Abstraction Day 1?

**Traditional Thinking:** "YAGNI - You Ain't Gonna Need It"
- Don't build abstractions until you need them
- Focus on Shopify, retrofit later

**AI-Assisted Reality:** "Abstractions are cheap, retrofits are expensive"
- Claude Code makes abstraction cost trivial (2 hours)
- Enables 3-day platform additions vs 6-week retrofits
- Better code organization helps Claude Code help you
- Zero technical debt from start

**Decision:** Build abstraction layer Week 1 ✅

---

### Why Railway over Supabase?

**Supabase Pros:**
- Managed PostgreSQL ✅
- Storage solution ✅
- Trendy, modern ✅

**Supabase Cons:**
- No Redis (need separate) ❌
- Connection pooling complex ❌
- Optimized for Firebase-style apps ❌
- We don't use Auth/Realtime/Edge Functions ❌

**Railway Pros:**
- PostgreSQL + Redis in one place ✅
- Already familiar ✅
- Perfect for microservices ✅
- Private networking ✅
- Simple deployment ✅

**Decision:** Railway + Cloudflare R2 ✅

---

### Why Cloudflare R2?

**vs Supabase Storage:**
- S3-compatible (standard API) ✅
- Cheaper ($0.015/GB vs Supabase) ✅
- Free egress (matters for images) ✅
- Not locked to Supabase ✅

**vs AWS S3:**
- Much cheaper ($0.015/GB vs $0.023/GB) ✅
- Free egress vs S3's $0.09/GB ✅
- Same API compatibility ✅

**Decision:** Cloudflare R2 ✅

---

### Why Not Build WooCommerce Support Yet?

**Traditional Startup Wisdom:** "Validate with one market first"

**Our Approach:** "Build abstraction, implement on demand"
- Shopify validates product-market fit fastest
- Enterprise partners will request platforms they need
- They'll often co-fund development ($25-50k)
- Proves demand before we build

**Decision:** Shopify only in MVP, others on demand ✅

---

## Final Checklist

**Before calling it "done":**

```
✓ All 300+ tests pass
✓ Test coverage > 95%
✓ All services deployed to Railway
✓ Health checks working
✓ Monitoring active (Sentry + BetterUptime)
✓ Documentation complete
✓ Security audit passed
✓ Performance targets met
✓ Can install on test store successfully
✓ Can submit review end-to-end
✓ Widget displays correctly
✓ Email sending works
✓ AI moderation works
✓ Backups configured
✓ Support email active
✓ Incident response plan ready
```

**Then and only then:**

🚀 **LAUNCH!**

---

**Document Version:** 2.0  
**Last Updated:** November 11, 2025  
**Next Review:** After Week 1 completion

---

## Getting Started

**First command to Claude Code:**

```
Analyze the existing codebase:
1. Read ARCHITECTURE.md thoroughly
2. Study services/review_service/ structure
3. Read all test files in tests/
4. Understand shared/ utilities
5. Study the Clean Architecture patterns used
6. Report back what you learned about the patterns

Then we'll start with Week 1, Task 1.1: Railway Infrastructure Setup
```

**For each task, use this pattern:**

```
1. Tell me what existing patterns you found
2. Show me the test structure you'll create
3. Write tests first (TDD)
4. Implement to pass tests
5. Refactor if needed
6. Confirm all tests pass
7. Move to next task
```

**Remember:**
- Make it work, make it right, make it fast (in that order)
- Follow existing patterns religiously
- Tests first, always
- Simple is better than clever
- Consistency is king

**Good luck! 🚀**