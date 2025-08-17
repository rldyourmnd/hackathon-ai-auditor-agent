# Database Guidelines - PostgreSQL

This document provides comprehensive information about the PostgreSQL database used in the Curestry project.

## Overview

The Curestry project uses PostgreSQL 15 as the primary database system for storing prompts, analysis results, and relationship data. The database is containerized using Docker and configured with comprehensive schema management through Alembic migrations.

## Database Configuration

### Connection Details
- **Database Engine**: PostgreSQL 15 (Alpine)
- **Host**: `db` (Docker container name)
- **Port**: `5432` (internal), not exposed externally in production
- **Database Name**: `curestry`
- **Default User**: `curestry`
- **Connection Pool**: SQLAlchemy with connection recycling (300s)

### Environment Variables
```env
POSTGRES_USER=curestry
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=curestry
DATABASE_URL=postgresql+psycopg://curestry:secure_password@db:5432/curestry
```

### Connection Configuration
- **Sync Engine**: `postgresql+psycopg://` (for migrations and setup)
- **Async Engine**: `postgresql+asyncpg://` (for application use)
- **Pool Settings**:
  - `pool_pre_ping=True` - Verify connections before use
  - `pool_recycle=300` - Recycle connections every 5 minutes
  - SQL query logging enabled in development mode

## Database Schema

### Table Structure Overview

The database consists of three main tables that form the core of the prompt analysis system:

1. **prompts** - Core prompt storage and management
2. **prompt_relations** - Inter-prompt relationships and dependencies
3. **analysis_results** - Analysis history and metrics storage

### 1. Prompts Table

**Location**: `backend/alembic/versions/001_initial_tables.py:22-35`

```sql
CREATE TABLE prompts (
    id VARCHAR NOT NULL,                    -- UUID primary key
    name VARCHAR(255) NOT NULL,             -- Prompt name/title
    description VARCHAR,                    -- Optional description
    content TEXT NOT NULL,                  -- The prompt text content
    format_type VARCHAR(50) NOT NULL,       -- Format: auto/xml/markdown
    language VARCHAR(10) NOT NULL,          -- Language code (e.g., 'en')
    tags JSON,                             -- Array of categorization tags
    extra_metadata JSON,                   -- Additional metadata storage
    created_at DATETIME NOT NULL,          -- Creation timestamp
    updated_at DATETIME NOT NULL,          -- Last modification timestamp
    PRIMARY KEY (id)
);
```

**Purpose**: Central storage for all prompts in the prompt-base system.

**Key Fields**:
- `id`: UUID string identifier (auto-generated)
- `content`: Main prompt text stored as TEXT type
- `format_type`: Prompt format detection/validation
- `tags`: JSON array for flexible categorization
- `extra_metadata`: JSON object for extensible metadata

**Model Class**: `backend/app/models/prompts.py:35-56`

### 2. Prompt Relations Table

**Location**: `backend/alembic/versions/001_initial_tables.py:37-49`

```sql
CREATE TABLE prompt_relations (
    id VARCHAR NOT NULL,                    -- UUID primary key
    source_id VARCHAR NOT NULL,             -- Foreign key to prompts.id
    target_id VARCHAR NOT NULL,             -- Foreign key to prompts.id
    relation_type VARCHAR(50) NOT NULL,     -- Relationship type
    description VARCHAR,                    -- Optional description
    extra_metadata JSON,                   -- Additional metadata
    created_at DATETIME NOT NULL,          -- Creation timestamp
    PRIMARY KEY (id),
    FOREIGN KEY(source_id) REFERENCES prompts (id),
    FOREIGN KEY(target_id) REFERENCES prompts (id)
);
```

**Purpose**: Manages relationships between prompts for dependency tracking and conflict detection.

**Relation Types**:
- `depends_on`: Source prompt depends on target prompt
- `overrides`: Source prompt overrides target prompt
- `conflicts_with`: Source prompt conflicts with target prompt

**Model Class**: `backend/app/models/prompts.py:101-121`

### 3. Analysis Results Table

**Location**: `backend/alembic/versions/001_initial_tables.py:51-72`

```sql
CREATE TABLE analysis_results (
    id VARCHAR NOT NULL,                    -- UUID primary key
    prompt_id VARCHAR,                      -- Optional foreign key to prompts.id
    prompt_content TEXT NOT NULL,          -- Content that was analyzed
    detected_language VARCHAR(10) NOT NULL, -- Detected language
    translated BOOLEAN NOT NULL,           -- Whether content was translated
    format_valid BOOLEAN NOT NULL,         -- Format validation result
    overall_score FLOAT NOT NULL,          -- Overall quality score (0-10)
    judge_score FLOAT NOT NULL,            -- LLM judge score (0-10)
    semantic_entropy FLOAT NOT NULL,       -- Semantic entropy measurement
    complexity_score FLOAT NOT NULL,       -- Vocabulary complexity (0-10)
    length_chars INTEGER NOT NULL,         -- Character count
    length_words INTEGER NOT NULL,         -- Word count
    contradictions JSON,                   -- Detected contradictions
    patches JSON,                          -- Improvement suggestions
    clarify_questions JSON,                -- Clarification questions
    analysis_extra_metadata JSON,          -- Additional analysis data
    created_at DATETIME NOT NULL,          -- Analysis timestamp
    PRIMARY KEY (id),
    FOREIGN KEY(prompt_id) REFERENCES prompts (id)
);
```

**Purpose**: Stores comprehensive analysis results and metrics for prompts.

**Key Metrics**:
- `overall_score`: Composite quality score (0-10 scale)
- `judge_score`: LLM-as-Judge evaluation score
- `semantic_entropy`: Consistency measurement across multiple generations
- `complexity_score`: Vocabulary and structural complexity

**JSON Fields**:
- `contradictions`: Array of detected logical contradictions
- `patches`: Array of improvement suggestions (safe/risky categorization)
- `clarify_questions`: Interactive refinement questions

**Model Class**: `backend/app/models/prompts.py:177-191`

## Database Operations

### Connection Management

**Sync Sessions** (for migrations):
```python
from app.core.database import SessionLocal, get_session

with SessionLocal() as session:
    # Perform database operations
    pass

# Or use dependency injection
def my_function(session: Session = Depends(get_session)):
    # Database operations
    pass
```

**Async Sessions** (for application use):
```python
from app.core.database import AsyncSessionLocal, get_async_session

async with AsyncSessionLocal() as session:
    # Perform async database operations
    pass

# Or use dependency injection
async def my_function(session: AsyncSession = Depends(get_async_session)):
    # Async database operations
    pass
```

### Health Monitoring

**Location**: `backend/app/core/database.py:96-149`

The `DatabaseManager` class provides comprehensive health monitoring:

```python
from app.core.database import db_manager

# Basic connection check
is_connected = await check_db_connection()

# Comprehensive health check
health_data = await db_manager.health_check()
# Returns: {
#   "connected": bool,
#   "pool_size": int,
#   "pool_checked_in": int,
#   "pool_checked_out": int,
#   "pool_overflow": int
# }
```

## Migration Management

### Alembic Configuration

**Location**: `backend/alembic.ini`, `backend/alembic/env.py`

The project uses Alembic for database schema migrations:

```bash
# From backend/ directory
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
alembic downgrade -1
```

### Current Migration

**File**: `backend/alembic/versions/001_initial_tables.py`
- **Revision ID**: `001`
- **Description**: Initial tables creation
- **Date**: 2025-08-16 10:30:00

## Data Models and Schemas

### SQLModel Integration

The project uses SQLModel (SQLAlchemy + Pydantic) for type-safe database operations:

**Base Models**: Define database table structure
**Create Models**: Input validation for new records
**Read Models**: Output serialization for API responses
**Update Models**: Partial update validation

Example usage:
```python
from app.models.prompts import Prompt, PromptCreate, PromptRead

# Create new prompt
prompt_data = PromptCreate(
    name="Example Prompt",
    content="This is a test prompt",
    format_type="auto",
    language="en"
)

# Save to database
prompt = Prompt.from_orm(prompt_data)
session.add(prompt)
session.commit()

# Return API response
return PromptRead.from_orm(prompt)
```

## Performance Considerations

### Indexing Strategy

**Primary Keys**: All tables use UUID string primary keys
**Foreign Keys**: Proper indexing on relationship columns
**JSON Fields**: Consider adding GIN indexes for frequent JSON queries

### Connection Pooling

- Default pool size managed by SQLAlchemy
- Connection recycling every 5 minutes prevents stale connections
- Pre-ping verification ensures connection validity

### Query Optimization

- Use async sessions for non-blocking database operations
- Implement proper error handling with rollback mechanisms
- Consider using `selectinload()` for eager loading relationships

## Data Integrity

### Constraints

1. **Foreign Key Constraints**:
   - `prompt_relations.source_id` → `prompts.id`
   - `prompt_relations.target_id` → `prompts.id`
   - `analysis_results.prompt_id` → `prompts.id` (optional)

2. **Field Validation**:
   - All primary keys are non-nullable UUIDs
   - Content fields use appropriate TEXT types for large data
   - Timestamp fields auto-populate with creation/update times

### Data Validation

Pydantic models ensure data integrity at the application level:
- String length limits (e.g., `name` max 255 characters)
- Score ranges (0-10 for quality metrics)
- Required vs. optional field enforcement
- JSON schema validation for structured data

## Backup and Recovery

### Docker Volume Management

Database data is persisted in Docker volumes:
```yaml
volumes:
  postgres_data:  # Persistent storage for PostgreSQL data
```

### Backup Strategy

```bash
# Backup database
docker exec curestry-db pg_dump -U curestry curestry > backup.sql

# Restore database
docker exec -i curestry-db psql -U curestry curestry < backup.sql
```

## Security Considerations

1. **Access Control**:
   - Database not exposed externally (no port mapping in production)
   - Internal Docker network communication only
   - Secure password management via environment variables

2. **SQL Injection Prevention**:
   - SQLAlchemy ORM provides automatic parameterization
   - No raw SQL construction from user input

3. **Connection Security**:
   - TLS encryption can be enabled for production deployments
   - Connection pooling limits prevent resource exhaustion

## Troubleshooting

### Common Issues

1. **Connection Failures**:
   - Check Docker container status: `docker compose ps`
   - Verify environment variables in `.env` file
   - Check database logs: `docker compose logs db`

2. **Migration Issues**:
   - Ensure database is running before migrations
   - Check Alembic revision history: `alembic history`
   - Manual intervention may be needed for complex schema changes

3. **Performance Issues**:
   - Monitor connection pool statistics via health check endpoint
   - Check for long-running queries in PostgreSQL logs
   - Consider adding indexes for frequently queried JSON fields

### Monitoring Commands

```bash
# Check database container status
docker compose ps db

# View database logs
docker compose logs -f db

# Access PostgreSQL shell
docker compose exec db psql -U curestry curestry

# Database size and statistics
docker compose exec db psql -U curestry curestry -c "\l+ curestry"
docker compose exec db psql -U curestry curestry -c "\dt+"
```

## Development Workflow

### Local Development

1. **Start Database**:
   ```bash
   docker compose up -d db
   ```

2. **Run Migrations**:
   ```bash
   cd backend
   alembic upgrade head
   ```

3. **Verify Setup**:
   ```bash
   curl http://localhost:8000/healthz
   ```

### Testing

- Use separate test database for unit tests
- Mock database operations for isolated testing
- Integration tests should use ephemeral database instances

## API Integration

### Health Check Endpoint

**Endpoint**: `GET /healthz`
**Response**: Database connectivity and pool statistics

### Database-Related Endpoints

- `POST /prompt-base/add` - Stores prompts in database
- `POST /analyze` - Creates analysis_results records
- `GET /report/{id}.json` - Retrieves analysis data
- `POST /prompt-base/check` - Queries for conflicts

## Future Enhancements

### Potential Schema Extensions

1. **User Management**: Add user authentication and prompt ownership
2. **Versioning**: Implement prompt version history
3. **Caching**: Add Redis integration for frequently accessed data
4. **Analytics**: Time-series data for usage patterns
5. **Full-text Search**: PostgreSQL full-text search for prompt content

### Performance Optimizations

1. **Read Replicas**: For scaling read operations
2. **Partitioning**: For large analysis_results table
3. **Materialized Views**: For complex analytical queries
4. **Background Jobs**: For heavy analysis operations

---

**Last Updated**: 2025-08-17
**Schema Version**: 001 (Initial Tables)
**PostgreSQL Version**: 15-alpine
