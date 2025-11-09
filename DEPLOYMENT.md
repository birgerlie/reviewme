# Review Platform - Deployment Guide

This guide explains different ways to spin up and run the Review Platform.

## Table of Contents

1. [Quick Start (Docker Compose)](#quick-start-docker-compose)
2. [Local Development](#local-development)
3. [Production Deployment](#production-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Service Architecture](#service-architecture)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start (Docker Compose)

**⚡ Fastest way to get the entire platform running!**

This method spins up all services and dependencies (PostgreSQL, Redis, RabbitMQ) in Docker containers.

### Prerequisites

- Docker Desktop or Docker Engine (20.10+)
- Docker Compose (2.0+)
- 4GB+ RAM available
- Ports 5432, 6379, 5672, 8000-8004, 15672 available

### Steps

```bash
# 1. Clone the repository
git clone <repository-url>
cd reviewme

# 2. Create environment file
cp .env.example .env

# 3. Edit .env and add your API keys
# Required:
#   - ANTHROPIC_API_KEY=your-key-here
# Optional (for full functionality):
#   - SMTP_USER, SMTP_PASSWORD (for email service)
#   - AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY (for media service)

# 4. Start all services
docker-compose -f docker-compose.dev.yml up --build

# 5. Wait for services to be healthy (30-60 seconds)
# You'll see logs from all services

# 6. Run database migrations (in a new terminal)
docker-compose -f docker-compose.dev.yml exec review-service \
    poetry run alembic upgrade head

# 7. Access the services
# Review Service API:  http://localhost:8000/docs
# AI Service API:      http://localhost:8001/docs
# Widget Service API:  http://localhost:8002/docs
# Email Service API:   http://localhost:8003/docs
# Media Service API:   http://localhost:8004/docs
# RabbitMQ UI:         http://localhost:15672 (guest/guest)
```

### Stopping Services

```bash
# Stop all services
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes (clean slate)
docker-compose -f docker-compose.dev.yml down -v
```

### Viewing Logs

```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Specific service
docker-compose -f docker-compose.dev.yml logs -f review-service
docker-compose -f docker-compose.dev.yml logs -f ai-service
```

---

## Local Development

**👨‍💻 Best for active development and debugging**

Run services locally with hot-reload for faster iteration.

### Prerequisites

- Python 3.11+
- Poetry 1.7+
- PostgreSQL 15+
- Redis 7+
- RabbitMQ 3+ (optional, for events)

### Steps

#### 1. Install Dependencies

```bash
# Install Python dependencies
poetry install

# Verify installation
poetry run python --version  # Should be 3.11+
```

#### 2. Start Infrastructure (Option A: Docker)

```bash
# Start only infrastructure services
docker-compose -f docker-compose.dev.yml up postgres redis rabbitmq -d

# Wait for health checks
docker-compose -f docker-compose.dev.yml ps
```

#### 2. Start Infrastructure (Option B: Local)

```bash
# Start PostgreSQL (macOS with Homebrew)
brew services start postgresql@15

# Start Redis
brew services start redis

# Start RabbitMQ (optional)
brew services start rabbitmq
```

#### 3. Configure Environment

```bash
# Create .env file
cp .env.example .env

# Edit .env for local development
# Change service URLs to localhost:
DATABASE_URL=postgresql+asyncpg://reviewplatform:devpassword@localhost:5432/reviews
REDIS_URL=redis://localhost:6379/0
RABBITMQ_URL=amqp://reviewplatform:devpassword@localhost:5672/
```

#### 4. Run Database Migrations

```bash
poetry run alembic upgrade head
```

#### 5. Start Services (Each in separate terminal)

```bash
# Terminal 1: Review Service
poetry run uvicorn services.review_service.api.main:app --reload --port 8000

# Terminal 2: AI Service
poetry run uvicorn services.ai_service.api.main:app --reload --port 8001

# Terminal 3: Widget Service
poetry run uvicorn services.widget_service.api.main:app --reload --port 8002

# Terminal 4: Email Service
poetry run uvicorn services.email_service.api.main:app --reload --port 8003

# Terminal 5: Media Service
poetry run uvicorn services.media_service.api.main:app --reload --port 8004
```

#### 6. Run Tests

```bash
# Run all tests
poetry run pytest services/ -v

# Run specific service tests
poetry run pytest services/review_service/tests/ -v
poetry run pytest services/ai_service/tests/ -v

# Run with coverage
poetry run pytest services/ --cov=services --cov-report=html
open htmlcov/index.html
```

---

## Production Deployment

### Deployment Options

#### Option 1: Docker Compose (Small Scale)

Suitable for:
- Small to medium workloads (< 10,000 requests/day)
- Single server deployments
- Testing/staging environments

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Configure external PostgreSQL/Redis for better reliability
# Use environment variables for production secrets
# Enable SSL/TLS for all endpoints
# Set up reverse proxy (Nginx/Traefik) with rate limiting
```

#### Option 2: Kubernetes (Recommended for Production)

Suitable for:
- High availability requirements
- Auto-scaling needs
- Multi-region deployments
- Enterprise workloads

**Coming Soon**: Kubernetes manifests and Helm charts

#### Option 3: Cloud Platforms

##### AWS Deployment

```
- ECS/Fargate for containers
- RDS for PostgreSQL
- ElastiCache for Redis
- S3 for media storage
- CloudFront for CDN
- ALB for load balancing
- Route53 for DNS
```

##### Google Cloud Platform

```
- Cloud Run for services
- Cloud SQL for PostgreSQL
- Memorystore for Redis
- Cloud Storage for media
- Cloud CDN
- Cloud Load Balancing
```

##### Azure

```
- Azure Container Apps
- Azure Database for PostgreSQL
- Azure Cache for Redis
- Azure Blob Storage
- Azure CDN
- Azure Load Balancer
```

### Production Checklist

- [ ] Environment variables secured (use secrets management)
- [ ] Database connection pooling configured
- [ ] Redis persistence enabled
- [ ] SSL/TLS certificates installed
- [ ] CORS origins restricted
- [ ] Rate limiting enabled
- [ ] Monitoring/alerting configured (Prometheus, Grafana)
- [ ] Logging aggregation setup (ELK, CloudWatch, etc.)
- [ ] Backup strategy implemented
- [ ] CDN configured for media service
- [ ] Health checks configured in load balancer
- [ ] Auto-scaling policies defined
- [ ] Security headers configured
- [ ] API authentication/authorization enabled

---

## Environment Configuration

### Required Variables

```bash
# Anthropic AI (Required for AI Service)
ANTHROPIC_API_KEY=sk-ant-...

# Database (Required)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/reviews

# Redis (Required)
REDIS_URL=redis://host:6379/0
```

### Optional Variables

```bash
# Email Service (Optional - needed for email campaigns)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Media Service (Optional - needed for image/video uploads)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET=your-bucket-name
CDN_URL=https://cdn.yourplatform.com

# RabbitMQ (Optional - needed for events)
RABBITMQ_URL=amqp://user:pass@host:5672/
```

### Environment-Specific Configuration

```bash
# Development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Staging
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO

# Production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
```

---

## Service Architecture

### Port Allocation

| Service          | Port  | Purpose                                    |
|------------------|-------|--------------------------------------------|
| Review Service   | 8000  | Core review management API                 |
| AI Service       | 8001  | AI-powered features (style gen, summaries) |
| Widget Service   | 8002  | Ultra-fast public widget API               |
| Email Service    | 8003  | Email campaigns and templates              |
| Media Service    | 8004  | Image/video upload and CDN                 |
| PostgreSQL       | 5432  | Primary database                           |
| Redis            | 6379  | Caching layer                              |
| RabbitMQ         | 5672  | Message broker                             |
| RabbitMQ UI      | 15672 | Management interface                       |

### Service Dependencies

```
┌─────────────────────────────────────────────────┐
│                 Load Balancer                   │
└─────────────────────────────────────────────────┘
          │           │           │
    ┌─────┴─────┬────┴────┬──────┴──────┐
    │           │         │             │
┌───▼───┐  ┌───▼────┐  ┌▼────┐  ┌──────▼─────┐
│Review │  │Widget  │  │Email│  │   Media    │
│Service│  │Service │  │Svc  │  │  Service   │
└───┬───┘  └───┬────┘  └─┬───┘  └──────┬─────┘
    │          │         │             │
    │      ┌───▼─────────▼─────────────▼───┐
    │      │       AI Service                │
    │      │  (Anthropic Claude API)         │
    │      └─────────────────────────────────┘
    │
┌───▼──────────────┬──────────────┬────────────┐
│   PostgreSQL     │    Redis     │  RabbitMQ  │
│  (Primary DB)    │  (Cache)     │  (Events)  │
└──────────────────┴──────────────┴────────────┘
```

### Health Checks

All services expose health check endpoints:

```bash
# Check if service is running
curl http://localhost:8000/health

# Check if service is ready to accept traffic
curl http://localhost:8000/ready

# Response format:
{
  "status": "healthy",
  "service": "review-service",
  "version": "1.0.0"
}
```

---

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

```bash
# Error: "Address already in use"

# Find process using the port
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn services.review_service.api.main:app --port 8010
```

#### 2. Database Connection Failed

```bash
# Check PostgreSQL is running
docker-compose -f docker-compose.dev.yml ps postgres

# Check connection manually
psql postgresql://reviewplatform:devpassword@localhost:5432/reviews

# Reset database
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up postgres -d
poetry run alembic upgrade head
```

#### 3. Redis Connection Failed

```bash
# Check Redis is running
docker-compose -f docker-compose.dev.yml ps redis

# Test connection
redis-cli -h localhost -p 6379 ping
# Expected: PONG

# Clear Redis cache
redis-cli -h localhost -p 6379 FLUSHALL
```

#### 4. Anthropic API Key Not Working

```bash
# Verify API key is set
echo $ANTHROPIC_API_KEY

# Test API key with curl
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 10,
    "messages": [{"role": "user", "content": "hi"}]
  }'
```

#### 5. Docker Build Fails

```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose -f docker-compose.dev.yml build --no-cache

# Check disk space
df -h
```

#### 6. Tests Failing

```bash
# Make sure dependencies are installed
poetry install

# Run tests with verbose output
poetry run pytest services/ -v -s

# Run specific failing test
poetry run pytest services/review_service/tests/unit/test_review_model.py::test_can_approve -v

# Check Python version
python --version  # Must be 3.11+
```

### Getting Help

1. Check logs: `docker-compose logs -f <service-name>`
2. Verify health endpoints: `curl http://localhost:8000/health`
3. Review environment variables: `docker-compose config`
4. Check service connectivity: `docker-compose exec review-service ping postgres`

### Performance Optimization

#### Database

```bash
# Increase connection pool size in .env
DATABASE_POOL_SIZE=50

# Enable query logging for debugging
LOG_LEVEL=DEBUG
```

#### Redis

```bash
# Increase cache TTL for better hit rate (in service config)
CACHE_TTL=600  # 10 minutes

# Monitor Redis memory usage
redis-cli INFO memory
```

#### Application

```bash
# Increase worker processes (production)
uvicorn app:main --workers 4

# Enable uvloop for better async performance
poetry add uvloop
```

---

## Next Steps

1. **Run the platform**: Choose Docker Compose or local development
2. **Test the APIs**: Visit http://localhost:8000/docs
3. **Try the AI features**:
   - Generate widget styles from a domain
   - Summarize reviews
   - Create email campaigns
4. **Read the docs**:
   - [README.md](./README.md) - Project overview
   - [DEVELOPMENT.md](./DEVELOPMENT.md) - Development guide
   - [PROGRESS.md](./PROGRESS.md) - Implementation status

---

**Need help?** Check the troubleshooting section or review the service logs.

**Ready for production?** Review the production checklist and deployment options.
