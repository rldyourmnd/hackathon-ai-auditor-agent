# API Implementation Guidelines

This document provides comprehensive guidelines for the Curestry API implementation, covering architecture, endpoints, error handling, authentication, and development practices.

## API Architecture Overview

### Framework and Technologies
- **Framework**: FastAPI 0.104+ with async/await support
- **Documentation**: Auto-generated OpenAPI 3.0 (Swagger) docs at `/docs` (dev only)
- **CORS**: Configured for frontend at `localhost:3000`
- **Logging**: Structured JSON logging with custom formatter
- **Database**: SQLAlchemy/SQLModel integration with async support
- **Response Models**: Pydantic v2 models for type safety and validation

### Application Structure
```
backend/app/
├── main.py                 # FastAPI application entry point
├── api/routers/           # API route handlers
│   ├── analysis.py        # Analysis pipeline endpoints
│   └── prompt_base.py     # Prompt management endpoints
├── core/                  # Core configuration and database
├── models/                # SQLModel database models
├── schemas/               # Pydantic request/response models
├── services/              # Business logic services
└── pipeline/              # Analysis pipeline implementation
```

## Core Application Configuration

### FastAPI Application Setup
**Location**: `backend/app/main.py:64-84`

```python
app = FastAPI(
    title="Curestry API",
    description="AI Prompt Analysis & Optimization Platform",
    version="0.1.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)
```

**Key Features**:
- Auto-documentation disabled in production for security
- CORS middleware configured for frontend integration
- Structured JSON logging with custom formatter
- Environment-based configuration via Pydantic Settings

### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Startup Event Handler
**Location**: `backend/app/main.py:86-106`

The startup event initializes:
1. Database connections and schema
2. Logging configuration
3. Service dependencies
4. Health check capabilities

## API Endpoints Documentation

### 1. Analysis Pipeline API

**Router**: `backend/app/api/routers/analysis.py`
**Prefix**: `/analyze`
**Tags**: `["analysis"]`

#### POST /analyze
**Purpose**: Comprehensive prompt analysis across multiple dimensions

**Request Model**: `AnalyzeRequest`
```json
{
  "prompt": {
    "content": "string",        // Required: prompt text
    "format_type": "auto"       // Optional: auto|text|markdown|xml
  }
}
```

**Response Model**: `AnalyzeResponse`
```json
{
  "report": {
    "prompt_id": "uuid-string",
    "detected_language": "en",
    "translated": false,
    "format_valid": true,
    "overall_score": 7.5,
    "improvement_priority": "medium",
    "judge_score": {
      "score": 7.5,
      "rationale": "Analysis feedback...",
      "details": {}
    },
    "semantic_entropy": {
      "entropy": 0.23,
      "spread": 0.45,
      "clusters": 3,
      "samples": ["sample1", "sample2", "sample3"]
    },
    "contradictions": [],
    "length_words": 150,
    "length_chars": 800,
    "complexity_score": 6.2
  },
  "patches": [...],
  "questions": [...]
}
```

**Processing Pipeline**:
1. Language Detection → Translation (if needed)
2. Format Validation → Markup Linting
3. Vocabulary Analysis → Contradiction Detection
4. Semantic Entropy Analysis (8-sample embeddings + clustering)
5. LLM Judge Scoring → Patch Generation → Clarification Questions

**Implementation Details**:
- **Location**: `backend/app/api/routers/analysis.py:30-157`
- **Pipeline Integration**: Uses `get_analysis_pipeline()` from LangGraph
- **Caching**: Analysis results stored in `analysis_cache` dict (replace with Redis in production)
- **Error Handling**: Comprehensive try-catch with detailed error logging
- **Performance**: 35-40 seconds for complete analysis

#### POST /analyze/apply
**Purpose**: Apply selected improvement patches to prompts

**Request Model**: `ApplyPatchesRequest`
```json
{
  "prompt_id": "uuid-string",      // Required: analysis ID
  "patch_ids": ["patch1", "patch2"],  // Optional: specific patches
  "apply_safe_all": false          // Optional: apply all safe patches
}
```

**Response Model**: `PromptImproved`
```json
{
  "original_prompt": "original text...",
  "improved_prompt": "improved text...",
  "applied_patches": ["patch1", "patch2"],
  "improvement_summary": "Applied 2 patches: clarity, structure",
  "quality_gain": 1.0
}
```

**Patch Application Logic**:
- **Safe Patches**: Automatic vocabulary and markup fixes
- **Risky Patches**: LLM-generated improvements requiring review
- **String Replacement**: Exact matching for targeted improvements
- **Fallback Handling**: Graceful degradation for non-matching patches

#### POST /analyze/clarify
**Purpose**: Process clarification answers and re-analyze with enhanced context

**Request Model**: `ClarifyRequest`
```json
{
  "prompt_id": "uuid-string",
  "answers": [
    {
      "question_id": "q_1",
      "answer": "Yes, handle negative inputs by returning 0"
    }
  ]
}
```

**Response**: Same as `/analyze` with updated metrics and patches

**Implementation**:
- Builds clarification context from answers
- Enhances original prompt with Q&A context
- Re-runs complete analysis pipeline
- Updates cached results with new analysis

#### GET /analyze/export/{prompt_id}.{format}
**Purpose**: Export analyzed prompts in structured formats

**Supported Formats**:
- `.md` - Markdown with metrics, patches, and judge feedback
- `.xml` - Structured XML with CDATA sections for safe content

**Response**: File download with appropriate MIME type and filename

**Implementation Details**:
- **Markdown Export**: Human-readable report with sections for metrics, contradictions, improvements
- **XML Export**: Machine-readable structured data with metadata and analysis results
- **Error Handling**: 404 for non-existent analyses, 400 for invalid formats

#### GET /analyze/report/{prompt_id}.json
**Purpose**: Download complete analysis report as JSON

**Response**: Complete analysis data including report, patches, questions, and export timestamp

### 2. Prompt-Base Management API

**Router**: `backend/app/api/routers/prompt_base.py`
**Prefix**: `/prompt-base`
**Tags**: `["prompt-base"]`

#### POST /prompt-base/add
**Purpose**: Add new prompts to the knowledge base

**Request Model**: `PromptCreate`
```json
{
  "name": "Python Fibonacci Function",
  "description": "Template for recursive fibonacci implementation",
  "content": "Write a Python function using recursion...",
  "format_type": "text",
  "language": "en",
  "tags": ["python", "recursion", "algorithms"],
  "extra_metadata": {}
}
```

**Response Model**: `PromptRead` with generated UUID and timestamps

**Validation**:
- Content length limits
- Format type validation
- Language code validation
- Tag structure validation

#### GET /prompt-base/prompts
**Purpose**: List prompts with filtering and pagination

**Query Parameters**:
- `skip`: Pagination offset (default: 0)
- `limit`: Results per page (1-1000, default: 100)
- `tags`: Comma-separated tag filter
- `language`: Language code filter
- `format_type`: Format filter

**Response**: Array of `PromptRead` objects

#### GET /prompt-base/search
**Purpose**: Full-text search across prompt content, names, and descriptions

**Query Parameters**:
- `q`: Search query (min 2 characters)
- `limit`: Max results (1-100, default: 50)

**Implementation**: Uses service layer for database queries with search indexing

#### POST /prompt-base/check
**Purpose**: Analyze prompt for conflicts with existing prompts

**Request**: `PromptCreate` object
**Response**: Conflict analysis with suggestions

```json
{
  "conflicts": [
    {
      "type": "potential_duplicate",
      "severity": "medium",
      "message": "Found 3 similar prompts",
      "related_prompts": ["id1", "id2", "id3"]
    }
  ],
  "suggestions": [
    {
      "action": "review_existing",
      "message": "Consider reviewing existing similar prompts",
      "prompt_ids": ["id1", "id2"]
    }
  ],
  "analysis": {
    "total_existing_prompts": 3,
    "conflict_score": 0.3,
    "recommendation": "review_recommended"
  }
}
```

#### Prompt Relations API
**Endpoints**:
- `POST /prompt-base/relations` - Create prompt relationships
- `GET /prompt-base/prompts/{id}/relations` - Get prompt relationships
- `DELETE /prompt-base/relations/{id}` - Delete relationships

**Relation Types**:
- `depends_on`: Source prompt depends on target
- `overrides`: Source overrides target
- `conflicts_with`: Source conflicts with target

### 3. System Health API

#### GET /healthz
**Purpose**: Comprehensive health check with service connectivity

**Response Model**: `HealthResponse`
```json
{
  "status": "healthy",
  "message": "Curestry API is running",
  "version": "0.1.0",
  "environment": "development",
  "openai_configured": true
}
```

**Health Checks**:
- Database connectivity via `db_manager.health_check()`
- OpenAI API connectivity (development only)
- Service configuration validation

#### GET /
**Purpose**: API root with basic information and navigation

## Error Handling Standards

### HTTP Status Codes
- `200`: Success
- `400`: Bad Request (validation errors)
- `404`: Resource Not Found
- `422`: Unprocessable Entity (Pydantic validation)
- `500`: Internal Server Error

### Error Response Format
```json
{
  "detail": "Detailed error description",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2025-08-17T10:30:00Z"
}
```

### Implementation Pattern
**Location**: Throughout routers with consistent try-catch blocks

```python
try:
    # Business logic
    result = await service.operation()
    return result
except ValueError as e:
    logger.warning(f"Validation error: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(status_code=500, detail="Operation failed")
```

## Request/Response Models

### Schema Organization
**Location**: `backend/app/schemas/`

**Key Schema Categories**:
1. **Request Models**: Input validation (`AnalyzeRequest`, `PromptCreate`)
2. **Response Models**: Output serialization (`AnalyzeResponse`, `PromptRead`)
3. **Domain Models**: Business logic entities (`Patch`, `MetricReport`)

### Validation Features
- **Pydantic v2**: Advanced validation with custom validators
- **Field Constraints**: Min/max lengths, ranges, patterns
- **Optional Fields**: Proper default handling
- **Type Safety**: Full TypeScript-compatible type annotations

### Example Schema Design
```python
class AnalyzeRequest(BaseModel):
    prompt: PromptInput = Field(..., description="Prompt to analyze")

class PromptInput(BaseModel):
    content: str = Field(..., min_length=1, max_length=50000)
    format_type: Optional[str] = Field(default="auto")
```

## Service Layer Integration

### Service Pattern
**Location**: `backend/app/services/`

Services provide business logic abstraction:
- **LLM Service**: OpenAI/Anthropic API integration
- **Embedding Service**: Vector embeddings for semantic analysis
- **Prompt Base Service**: Database operations with caching

### Dependency Injection
```python
from app.services.prompt_base import get_prompt_base_service

async def endpoint_handler():
    service = get_prompt_base_service()
    return await service.operation()
```

## Database Integration

### Session Management
**Location**: `backend/app/core/database.py`

**Async Sessions**: Primary pattern for all database operations
```python
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()
```

**Dependency Pattern**:
```python
async def endpoint(session: AsyncSession = Depends(get_async_session)):
    # Database operations
    pass
```

## Performance Considerations

### Async Processing
- **All endpoints**: Async/await pattern for non-blocking operations
- **Database**: Async SQLAlchemy sessions
- **LLM calls**: Async HTTP client integration
- **Concurrent requests**: FastAPI handles multiple requests efficiently

### Caching Strategy
- **Analysis Results**: In-memory cache (migrate to Redis for production)
- **Database Queries**: SQLAlchemy query caching
- **LLM Responses**: Service-level caching for repeated queries

### Rate Limiting
- **OpenAI API**: Respect 3 requests/second limit
- **Analysis Pipeline**: Consider queueing for high load
- **Database**: Connection pooling with limits

## Security Implementation

### Input Validation
- **Pydantic Models**: Automatic input sanitization
- **Content Length**: Limits on prompt content size
- **SQL Injection**: SQLAlchemy ORM prevents raw SQL
- **XSS Prevention**: Content escaping in XML/HTML export

### Development vs Production
- **Debug Mode**: Automatic docs disabled in production
- **Logging**: Structured logging without sensitive data
- **CORS**: Restricted origins in production
- **Error Details**: Limited error information in production

## Testing Guidelines

### Unit Testing
- **Router Testing**: FastAPI TestClient for endpoint testing
- **Service Testing**: Mock dependencies for isolated testing
- **Schema Testing**: Pydantic model validation testing

### Integration Testing
- **Database**: Use test database for integration tests
- **LLM Mocking**: Mock external API calls for predictable testing
- **End-to-End**: Full pipeline testing with sample data

### Example Test Structure
```python
async def test_analyze_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/analyze/", json={
            "prompt": {"content": "test prompt"}
        })
    assert response.status_code == 200
    assert "report" in response.json()
```

## Deployment and Configuration

### Environment Configuration
**Location**: `backend/app/core/config.py`

**Key Settings**:
- `ENV`: development|production
- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: LLM service authentication
- `LOG_LEVEL`: Structured logging verbosity

### Docker Integration
**Location**: `infra/Dockerfile.api`, `infra/docker-compose.yml`

**Container Configuration**:
- **Multi-stage build**: Optimized for production
- **Health checks**: Container-level health monitoring
- **Volume mounts**: Development hot-reloading
- **Network isolation**: Internal service communication

### Production Deployment
- **Reverse Proxy**: nginx for SSL termination and static files
- **Process Management**: Multiple uvicorn workers
- **Database Migrations**: Alembic integration
- **Monitoring**: Structured logging + observability tools

## API Usage Examples

### Quick Start Commands
```bash
# Health check
curl http://localhost:8000/healthz

# Analyze prompt
curl -X POST http://localhost:8000/analyze/ \
  -H "Content-Type: application/json" \
  -d '{"prompt": {"content": "Write Python code", "format_type": "auto"}}'

# Apply safe improvements
curl -X POST http://localhost:8000/analyze/apply \
  -H "Content-Type: application/json" \
  -d '{"prompt_id": "uuid", "apply_safe_all": true}'

# Add to prompt-base
curl -X POST http://localhost:8000/prompt-base/add \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python Function Template",
    "content": "Write a Python function...",
    "tags": ["python", "template"]
  }'
```

### Client Integration
```typescript
// TypeScript client example
interface AnalyzeRequest {
  prompt: {
    content: string;
    format_type?: "auto" | "text" | "markdown" | "xml";
  };
}

const analyzePrompt = async (prompt: string): Promise<AnalyzeResponse> => {
  const response = await fetch("/analyze/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt: { content: prompt } }),
  });
  return response.json();
};
```

## Development Workflow

### Local Development Setup
```bash
# Start services
cd infra && docker compose up -d

# Run API in development mode
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Access API documentation
open http://localhost:8000/docs
```

### Code Quality Standards
- **Type Hints**: Full type annotation coverage
- **Docstrings**: Comprehensive endpoint documentation
- **Error Handling**: Consistent error response patterns
- **Logging**: Structured logging with context
- **Testing**: Unit and integration test coverage

### API Versioning Strategy
- **Current**: v0.1.0 in FastAPI metadata
- **Future**: URL-based versioning (`/v1/`, `/v2/`)
- **Backwards Compatibility**: Deprecation warnings before breaking changes

## Migration and Maintenance

### Database Migrations
```bash
# Generate migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### API Evolution
- **Breaking Changes**: New major version
- **New Features**: Minor version increment
- **Bug Fixes**: Patch version increment
- **Deprecation**: Advance notice via response headers

### Performance Monitoring
- **Response Times**: Log request duration
- **Error Rates**: Track 4xx/5xx responses
- **Database Performance**: Monitor query execution times
- **Resource Usage**: Memory and CPU utilization

---

**Last Updated**: 2025-08-17
**API Version**: 0.1.0
**Implementation Status**: Production Ready (Phase 6 Complete)
