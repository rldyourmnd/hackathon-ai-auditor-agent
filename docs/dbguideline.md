# Database Guidelines - Curestry Platform

Comprehensive database design guide for the Curestry AI prompt analysis platform, covering current implementation and future scalability.

## Architecture Overview

### Database Strategy
Curestry uses a **dual-database microservices architecture**:

1. **Main Backend Database** (`backend/`) - Core AI analysis functionality
2. **Public Backend Database** (`backend_public/`) - User management and metrics
3. **Future: Unified Database** - Single PostgreSQL instance with namespaced schemas

### Technology Stack
- **Database**: PostgreSQL 15+ with JSON/JSONB support
- **ORM**: SQLModel (preferred) + SQLAlchemy 2.0
- **Migrations**: Alembic with auto-generation
- **Drivers**: asyncpg (async) + psycopg (sync)
- **Connection**: Async/await pattern with connection pooling

---

## Current Database Schemas

### Core Schema (Main Backend)

#### 1. Prompts Management

```sql
-- Core prompt storage
CREATE TABLE prompts (
    id VARCHAR PRIMARY KEY,                     -- UUID string
    name VARCHAR(255) NOT NULL,                 -- Display name
    description TEXT,                           -- Optional description
    content TEXT NOT NULL,                      -- Prompt text content
    format_type VARCHAR(50) NOT NULL DEFAULT 'auto',  -- auto|text|markdown|xml
    language VARCHAR(10) NOT NULL DEFAULT 'auto',     -- Language code
    tags JSONB DEFAULT '[]'::jsonb,             -- Categorization tags
    extra_metadata JSONB DEFAULT '{}'::jsonb,  -- Extensible metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Prompt relationships and dependencies
CREATE TABLE prompt_relations (
    id VARCHAR PRIMARY KEY,                     -- UUID string
    source_id VARCHAR NOT NULL REFERENCES prompts(id),
    target_id VARCHAR NOT NULL REFERENCES prompts(id),
    relation_type VARCHAR(50) NOT NULL,         -- depends_on|overrides|conflicts_with
    description TEXT,                           -- Optional description
    extra_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_relation_type CHECK (relation_type IN ('depends_on', 'overrides', 'conflicts_with'))
);

-- Analysis results storage
CREATE TABLE analysis_results (
    id VARCHAR PRIMARY KEY,                     -- UUID string
    prompt_id VARCHAR REFERENCES prompts(id),  -- Optional FK (can analyze without saving prompt)
    prompt_content TEXT NOT NULL,              -- Content that was analyzed

    -- Language and format
    detected_language VARCHAR(10) NOT NULL,
    translated BOOLEAN NOT NULL DEFAULT FALSE,
    format_valid BOOLEAN NOT NULL DEFAULT TRUE,

    -- Core metrics
    overall_score FLOAT NOT NULL CHECK (overall_score >= 0 AND overall_score <= 10),
    judge_score FLOAT NOT NULL CHECK (judge_score >= 0 AND judge_score <= 10),
    semantic_entropy FLOAT NOT NULL,
    complexity_score FLOAT NOT NULL CHECK (complexity_score >= 0 AND complexity_score <= 10),
    length_chars INTEGER NOT NULL CHECK (length_chars >= 0),
    length_words INTEGER NOT NULL CHECK (length_words >= 0),

    -- Analysis data (JSON)
    contradictions JSONB DEFAULT '[]'::jsonb,
    patches JSONB DEFAULT '[]'::jsonb,
    clarify_questions JSONB DEFAULT '[]'::jsonb,
    analysis_extra_metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### 2. User Management Schema (Backend Public)

```sql
-- User accounts
CREATE TABLE users (
    id SERIAL PRIMARY KEY,                      -- Auto-increment ID
    email VARCHAR(255) UNIQUE,                  -- Nullable for anonymous users
    name VARCHAR(255),                          -- Display name
    avatar_url VARCHAR(512),                    -- Profile picture URL
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Authentication sessions
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    jwt_id VARCHAR(64) UNIQUE NOT NULL,         -- JWT token identifier
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

-- OAuth provider accounts
CREATE TABLE auth_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(32) NOT NULL,              -- 'google', 'github', etc.
    provider_account_id VARCHAR(255) NOT NULL,  -- Provider's user ID
    access_token TEXT,                          -- OAuth access token (encrypted)
    refresh_token TEXT,                         -- OAuth refresh token (encrypted)
    raw_profile JSONB,                          -- Provider profile data
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(provider, provider_account_id)
);

-- Workflow execution tracking
CREATE TABLE workflow_runs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),      -- Who initiated the workflow
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,                   -- NULL while running
    status VARCHAR(32) NOT NULL DEFAULT 'running', -- running|success|failed|cancelled
    meta JSONB DEFAULT '{}'::jsonb,             -- Workflow metadata

    CONSTRAINT valid_status CHECK (status IN ('running', 'success', 'failed', 'cancelled'))
);

-- Individual workflow nodes (pipeline steps)
CREATE TABLE workflow_nodes (
    id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
    key VARCHAR(64) NOT NULL,                   -- Node identifier (e.g., 'detect_language')
    status VARCHAR(32) NOT NULL DEFAULT 'pending', -- pending|running|success|failed
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    result JSONB,                               -- Node execution result

    UNIQUE(run_id, key)
);

-- Metrics collection
CREATE TABLE evaluation_metrics (
    id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
    node_key VARCHAR(64),                       -- Which node generated this metric
    metric_name VARCHAR(64) NOT NULL,           -- Metric identifier
    metric_value FLOAT NOT NULL,                -- Numeric value
    metric_meta JSONB,                          -- Additional metric data
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Prevent duplicate metrics per run/node/metric/time
    UNIQUE(run_id, node_key, metric_name, created_at)
);
```

---

## Future Database Architecture (Enterprise Scale)

### Schema Organization Strategy

```sql
-- Operational schemas (current + future)
CREATE SCHEMA IF NOT EXISTS ops;     -- Operational data
CREATE SCHEMA IF NOT EXISTS mart;    -- Analytics/reporting data
CREATE SCHEMA IF NOT EXISTS core;    -- Core business entities (current prompts, etc.)
```

### 1. Multi-tenancy and Access Control

```sql
-- Organizations (teams/companies)
CREATE TABLE ops.organization (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,          -- URL-friendly identifier
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Organization membership
CREATE TABLE ops.organization_user (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES ops.organization(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,                  -- owner|admin|member|viewer
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active|invited|removed
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(organization_id, user_id),
    CONSTRAINT valid_role CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    CONSTRAINT valid_status CHECK (status IN ('active', 'invited', 'removed'))
);

-- API keys for programmatic access
CREATE TABLE ops.api_key (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES ops.organization(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,      -- Hashed API key
    scopes JSONB NOT NULL DEFAULT '[]'::jsonb,  -- Permissions array
    expires_at TIMESTAMPTZ,                     -- NULL = never expires
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Provider credentials (LLM API keys, integrations)
CREATE TABLE ops.provider_credential (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES ops.organization(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,              -- openai|anthropic|slack|github
    credential_ref VARCHAR(255) NOT NULL,       -- External credential ID/reference
    meta JSONB DEFAULT '{}'::jsonb,             -- Provider-specific metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 2. Enhanced Analysis Tracking

```sql
-- Analysis run tracking (replaces simple analysis_results)
CREATE TABLE ops.analysis_run (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES ops.organization(id),
    user_id INTEGER REFERENCES users(id),
    prompt_id VARCHAR REFERENCES prompts(id),   -- Link to existing prompts table
    status VARCHAR(20) NOT NULL DEFAULT 'queued', -- queued|running|succeeded|failed|cancelled
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    meta JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT valid_analysis_status CHECK (status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled'))
);

-- Key-value metrics per analysis
CREATE TABLE ops.analysis_metric (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_run_id UUID NOT NULL REFERENCES ops.analysis_run(id) ON DELETE CASCADE,
    key VARCHAR(100) NOT NULL,                  -- Metric name
    value_num NUMERIC,                          -- Numeric value
    value_text TEXT,                            -- Text value
    value_json JSONB,                           -- Complex value
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- At least one value must be present
    CONSTRAINT has_value CHECK (
        value_num IS NOT NULL OR
        value_text IS NOT NULL OR
        value_json IS NOT NULL
    )
);

-- Pipeline node results
CREATE TABLE ops.analysis_node_result (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_run_id UUID NOT NULL REFERENCES ops.analysis_run(id) ON DELETE CASCADE,
    node VARCHAR(50) NOT NULL,                  -- entropy|llm_judge|rag_oracle|regex_checks
    status VARCHAR(20) NOT NULL,                -- ok|warn|fail|error
    score NUMERIC CHECK (score >= 0 AND score <= 10),
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_node_status CHECK (status IN ('ok', 'warn', 'fail', 'error'))
);
```

### 3. LLM-as-Judge System

```sql
-- Judge rubrics (evaluation criteria)
CREATE TABLE ops.judge_rubric (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES ops.organization(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    meta JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Individual judge criteria
CREATE TABLE ops.judge_criterion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rubric_id UUID NOT NULL REFERENCES ops.judge_rubric(id) ON DELETE CASCADE,
    key VARCHAR(100) NOT NULL,                  -- Unique within rubric
    title VARCHAR(255) NOT NULL,
    description TEXT,
    weight NUMERIC NOT NULL DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(rubric_id, key)
);

-- Judge scores per analysis
CREATE TABLE ops.judge_score (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_run_id UUID NOT NULL REFERENCES ops.analysis_run(id) ON DELETE CASCADE,
    criterion_id UUID NOT NULL REFERENCES ops.judge_criterion(id),
    score NUMERIC NOT NULL CHECK (score >= 0 AND score <= 10),
    comment TEXT,
    evidence JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 4. Analytics and Reporting (mart schema)

```sql
-- Time-series metrics for dashboards
CREATE TABLE mart.metric_timeseries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES ops.organization(id),
    metric_key VARCHAR(100) NOT NULL,
    ts_bucket TIMESTAMPTZ NOT NULL,             -- Aggregated timestamp (hourly/daily)
    value_num NUMERIC,
    value_json JSONB,

    -- Ensure unique metric per time bucket
    UNIQUE(organization_id, metric_key, ts_bucket)
);

-- Daily feature usage
CREATE TABLE mart.feature_daily (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES ops.organization(id),
    day DATE NOT NULL,
    feature_key VARCHAR(100) NOT NULL,
    events INTEGER NOT NULL DEFAULT 0,
    unique_users INTEGER NOT NULL DEFAULT 0,

    UNIQUE(organization_id, day, feature_key)
);

-- Daily analysis quality metrics
CREATE TABLE mart.analysis_daily (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES ops.organization(id),
    day DATE NOT NULL,
    analyses INTEGER NOT NULL DEFAULT 0,
    avg_overall NUMERIC,
    avg_entropy NUMERIC,

    UNIQUE(organization_id, day)
);
```

---

## Database Standards and Conventions

### 1. Naming Conventions

```sql
-- Table names: snake_case, plural
CREATE TABLE user_preferences (...);
CREATE TABLE analysis_results (...);

-- Column names: snake_case
user_id, created_at, api_key_hash

-- Foreign keys: {table}_id
user_id REFERENCES users(id)
organization_id REFERENCES organizations(id)

-- Indexes: idx_{table}_{columns}
CREATE INDEX idx_analysis_results_created_at ON analysis_results(created_at);

-- Constraints: {type}_{table}_{column}
CONSTRAINT chk_analysis_results_score CHECK (score >= 0 AND score <= 10);
CONSTRAINT unq_api_keys_hash UNIQUE (key_hash);
CONSTRAINT fk_sessions_user_id FOREIGN KEY (user_id) REFERENCES users(id);
```

### 2. Data Types Standards

```sql
-- Primary Keys
id UUID PRIMARY KEY DEFAULT gen_random_uuid()           -- Preferred for new tables
id SERIAL PRIMARY KEY                                   -- Existing legacy tables

-- Timestamps (always with timezone)
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()

-- Text fields
name VARCHAR(255)                                       -- Short text with limit
description TEXT                                        -- Long text, unlimited
content TEXT                                            -- Large content

-- JSON fields
metadata JSONB DEFAULT '{}'::jsonb                      -- Use JSONB for performance
tags JSONB DEFAULT '[]'::jsonb                          -- Arrays as JSONB

-- Enums via CHECK constraints
status VARCHAR(20) NOT NULL DEFAULT 'active'
CONSTRAINT valid_status CHECK (status IN ('active', 'inactive', 'pending'))

-- Scores and metrics
score NUMERIC CHECK (score >= 0 AND score <= 10)       -- Use NUMERIC for precision
```

### 3. Index Strategy

```sql
-- Primary indexes (automatic)
-- Foreign key indexes (recommended)
CREATE INDEX idx_analysis_results_prompt_id ON analysis_results(prompt_id);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);

-- Time-based queries
CREATE INDEX idx_analysis_results_created_at ON analysis_results(created_at);
CREATE INDEX idx_workflow_runs_started_at ON workflow_runs(started_at);

-- Organization-scoped queries
CREATE INDEX idx_analysis_run_organization_id ON ops.analysis_run(organization_id);
CREATE INDEX idx_api_key_organization_id ON ops.api_key(organization_id);

-- JSON/JSONB indexes for frequent queries
CREATE INDEX idx_prompts_tags_gin ON prompts USING GIN (tags);
CREATE INDEX idx_analysis_results_metadata_gin ON analysis_results USING GIN (analysis_extra_metadata);

-- Composite indexes for complex queries
CREATE INDEX idx_workflow_runs_user_status ON workflow_runs(user_id, status);
CREATE INDEX idx_evaluation_metrics_run_metric ON evaluation_metrics(run_id, metric_name);
```

---

## Migration Strategy

### Current State to Future Architecture

#### Phase 1: Unification (Keep current tables, add ops schema)
```sql
-- Keep existing tables as-is
-- Add new ops.* tables alongside
-- Migrate data gradually
-- Dual-write during transition
```

#### Phase 2: Schema Migration (Move to unified schema)
```sql
-- Migrate existing tables to core.* schema
ALTER TABLE prompts SET SCHEMA core;
ALTER TABLE analysis_results SET SCHEMA core;

-- Update foreign key references
-- Ensure application code compatibility
```

#### Phase 3: Full Implementation
```sql
-- Implement full ops.* and mart.* schemas
-- Remove legacy tables
-- Optimize indexes and performance
```

### Alembic Configuration

```python
# alembic/env.py configuration for multiple schemas
def run_migrations_online():
    # Include all models from both backends
    from backend.app.models import *
    from backend_public.app.models import *
    from future.app.models import *  # Future models

    # Set target metadata
    target_metadata = [
        Base.metadata,      # Current tables
        SQLModel.metadata,  # Future SQLModel tables
    ]
```

---

## Performance Optimization

### 1. Connection Pooling

```python
# Async engine configuration
async_engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,                    # Connection pool size
    max_overflow=30,                 # Additional connections
    pool_pre_ping=True,              # Verify connections
    pool_recycle=3600,               # Recycle every hour
    echo=False                       # SQL logging (dev only)
)

# Connection with retry logic
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### 2. Query Optimization

```python
# Efficient relationship loading
async def get_prompt_with_relations(prompt_id: str, session: AsyncSession):
    result = await session.execute(
        select(Prompt)
        .options(
            selectinload(Prompt.relations),
            selectinload(Prompt.analyses)
        )
        .where(Prompt.id == prompt_id)
    )
    return result.scalar_one_or_none()

# Pagination with efficient counting
async def list_analyses_paginated(skip: int, limit: int, session: AsyncSession):
    # Get total count efficiently
    count_query = select(func.count(AnalysisResult.id))
    total = await session.scalar(count_query)

    # Get paginated results
    result = await session.execute(
        select(AnalysisResult)
        .offset(skip)
        .limit(limit)
        .order_by(AnalysisResult.created_at.desc())
    )

    return result.scalars().all(), total
```

### 3. JSON Query Optimization

```python
# Efficient JSONB queries
async def find_prompts_by_tags(tags: List[str], session: AsyncSession):
    # Use JSONB containment operator
    result = await session.execute(
        select(Prompt)
        .where(Prompt.tags.op('@>')([tags]))  # Contains any of these tags
    )
    return result.scalars().all()

# JSON path queries
async def find_high_entropy_analyses(threshold: float, session: AsyncSession):
    result = await session.execute(
        select(AnalysisResult)
        .where(
            cast(AnalysisResult.analysis_extra_metadata['semantic_entropy']['entropy'], Float) > threshold
        )
    )
    return result.scalars().all()
```

---

## Security Considerations

### 1. Data Encryption

```sql
-- Sensitive data encryption (at application level)
-- Store encrypted tokens, never plain text
CREATE TABLE ops.provider_credential (
    -- ... other fields ...
    credential_ref VARCHAR(255) NOT NULL,  -- Encrypted credential reference
    encryption_key_id VARCHAR(100),        -- Key management reference
);

-- Use PostgreSQL extensions for additional security
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### 2. Access Control

```python
# Row-level security example (future implementation)
async def apply_organization_filter(query: Select, user_id: int, session: AsyncSession):
    """Apply organization-based filtering to queries"""
    user_orgs = await session.execute(
        select(OrganizationUser.organization_id)
        .where(OrganizationUser.user_id == user_id)
        .where(OrganizationUser.status == 'active')
    )
    org_ids = [row[0] for row in user_orgs]

    return query.where(YourModel.organization_id.in_(org_ids))
```

### 3. Audit Logging

```sql
-- Future audit table
CREATE TABLE ops.audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actor_user_id INTEGER REFERENCES users(id),
    organization_id UUID REFERENCES ops.organization(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(255) NOT NULL,
    before_state JSONB,
    after_state JSONB
);
```

---

## Development Workflow

### 1. Local Development Setup

```bash
# Database setup
docker compose up -d db
cd backend && alembic upgrade head

# Verify setup
psql $DATABASE_URL -c "\dt"  # List tables
psql $DATABASE_URL -c "SELECT version();"  # Check PostgreSQL version
```

### 2. Creating New Migrations

```bash
# Auto-generate migration
cd backend
alembic revision --autogenerate -m "Add organization tables"

# Review generated migration
# Edit if necessary
# Apply migration
alembic upgrade head
```

### 3. Testing Database Changes

```python
# Test database fixture
@pytest.fixture
async def test_db():
    # Create test database
    async_engine = create_async_engine("postgresql+asyncpg://test:test@localhost/test_curestry")

    # Create all tables
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Provide session
    async_session = sessionmaker(async_engine, class_=AsyncSession)
    async with async_session() as session:
        yield session

    # Cleanup
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
```

---

## Monitoring and Maintenance

### 1. Health Checks

```python
async def database_health_check() -> dict:
    """Comprehensive database health check"""
    try:
        async with AsyncSessionLocal() as session:
            # Basic connectivity
            await session.execute(text("SELECT 1"))

            # Check recent activity
            recent_analyses = await session.scalar(
                select(func.count(AnalysisResult.id))
                .where(AnalysisResult.created_at > datetime.utcnow() - timedelta(hours=24))
            )

            return {
                "status": "healthy",
                "recent_analyses_24h": recent_analyses,
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
```

### 2. Performance Monitoring

```sql
-- Monitor slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
WHERE mean_time > 1000  -- Queries taking over 1 second
ORDER BY mean_time DESC;

-- Monitor table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname IN ('public', 'ops', 'mart')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Monitor index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

---

## Backup and Recovery

### 1. Backup Strategy

```bash
# Daily automated backups
pg_dump $DATABASE_URL \
    --format=custom \
    --compress=9 \
    --file="backup_$(date +%Y%m%d_%H%M%S).dump"

# Point-in-time recovery setup
# Enable WAL archiving in postgresql.conf
archive_mode = on
archive_command = 'cp %p /path/to/archive/%f'
```

### 2. Disaster Recovery

```bash
# Restore from backup
pg_restore \
    --dbname=curestry_restored \
    --create \
    --clean \
    backup_20250817_120000.dump

# Verify data integrity
psql curestry_restored -c "
SELECT
    COUNT(*) as total_prompts,
    COUNT(DISTINCT id) as unique_prompts
FROM prompts;
"
```

---

**Last Updated**: 2025-08-17
**Database Version**: PostgreSQL 15+
**Schema Version**: v2.0 (Current + Future Ready)
**Status**: Production Ready + Future Scalable
