# Backend Implementation Guidelines for Curestry

This document provides comprehensive guidelines for implementing and maintaining the backend microservices in the Curestry project, with focus on aligning backend_public/ with the main backend/ architecture.

## Architecture Overview

### Microservice Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   frontend/     │    │  backend_public/│    │    backend/     │
│   Next.js 15    │────│   Admin API     │────│  Analysis API   │
│   (Port 3000)   │    │   (Port 8080)   │    │  (Port 8000)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                        │
         └───────────────────────┼────────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │   (Port 5432)   │
                    └─────────────────┘
```

### Service Responsibilities

#### backend/ (Main Analysis Service)
- **Port**: 8000
- **Purpose**: Core AI prompt analysis pipeline
- **Key Features**:
  - LangGraph analysis pipeline (language detection, format validation, contradiction analysis)
  - LLM integration (OpenAI, Anthropic)
  - Semantic entropy analysis with embeddings
  - Prompt-base management with relationship tracking
  - Analysis result export (JSON, Markdown, XML)

#### backend_public/ (Admin & Auth Service)
- **Port**: 8080
- **Purpose**: Authentication, user management, and admin dashboard API
- **Key Features**:
  - Google OAuth authentication
  - User session management
  - Workflow execution tracking
  - Metrics aggregation and reporting
  - Admin dashboard API for frontend integration

## Technology Stack Alignment

### Core Framework Standards
```python
# Standard imports for all backend services
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import SQLModel, Field, Session, select
from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import Optional, List
from datetime import datetime
```

### Database Layer Standards

#### 1. SQLModel Integration
**Use SQLModel for all database models** - provides type safety + ORM integration:

```python
# ✅ CORRECT - SQLModel pattern
from sqlmodel import SQLModel, Field
import uuid

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: str = Field(index=True, unique=True)
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
# ❌ INCORRECT - Pure SQLAlchemy
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
```

#### 2. Primary Key Strategy
**Always use UUID strings** for consistent identification across services:

```python
# Standard UUID primary key pattern
id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)

# Foreign key references
user_id: str = Field(foreign_key="users.id")
```

#### 3. Async Session Management
**Use AsyncSession for all database operations**:

```python
# Database session dependency
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()

# Endpoint usage
async def create_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_async_session)
):
    user = User.model_validate(user_data)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
```

### Configuration Management

#### 1. Pydantic Settings Pattern
**Standardize configuration across all services**:

```python
# config.py - Standard pattern for all services
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal, List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Environment
    env: Literal["development", "production"] = Field(default="development")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")

    # Database (use async connection string)
    database_url: str = Field(
        default="postgresql+asyncpg://curestry:secure_password@db:5432/curestry"
    )

    # Service discovery
    backend_api_url: str = Field(default="http://backend:8000")
    backend_public_url: str = Field(default="http://backend_public:8080")

    # Authentication
    jwt_secret: str = Field(default="dev-secret-change-in-production")
    jwt_expire_minutes: int = Field(default=120)

    @property
    def is_development(self) -> bool:
        return self.env == "development"


settings = Settings()
```

#### 2. Environment Variable Standards
**Use consistent naming across services**:

```bash
# .env - Shared configuration
ENV=development
LOG_LEVEL=INFO

# Database
POSTGRES_USER=curestry
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=curestry
DATABASE_URL=postgresql+asyncpg://curestry:secure_password@db:5432/curestry

# Services
BACKEND_API_URL=http://backend:8000
BACKEND_PUBLIC_URL=http://backend_public:8080

# Authentication
JWT_SECRET=secure-jwt-secret-for-production
JWT_EXPIRE_MINUTES=120

# Google OAuth (backend_public only)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# LLM APIs (backend only)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
```

## Error Handling Standards

### 1. Exception Hierarchy
**Create consistent error handling patterns**:

```python
# errors.py - Shared error types
from fastapi import HTTPException
from typing import Optional

class CurestryException(Exception):
    """Base exception for Curestry services"""
    def __init__(self, message: str, code: str = "GENERAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class ValidationError(CurestryException):
    """Input validation errors"""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, "VALIDATION_ERROR")
        self.field = field

class AuthenticationError(CurestryException):
    """Authentication and authorization errors"""
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, "AUTH_ERROR")

class DatabaseError(CurestryException):
    """Database operation errors"""
    def __init__(self, message: str):
        super().__init__(message, "DATABASE_ERROR")
```

### 2. Error Response Format
**Standardize error responses across all endpoints**:

```python
# Error response schema
class ErrorResponse(BaseModel):
    detail: str
    error_code: str
    timestamp: datetime
    path: Optional[str] = None

# Exception handler
@app.exception_handler(CurestryException)
async def curestry_exception_handler(request: Request, exc: CurestryException):
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            detail=exc.message,
            error_code=exc.code,
            timestamp=datetime.utcnow(),
            path=str(request.url.path)
        ).model_dump()
    )
```

## API Design Standards

### 1. Router Organization
**Organize endpoints by domain with consistent prefixes**:

```python
# backend/app/api/routers/analysis.py
router = APIRouter(prefix="/analyze", tags=["analysis"])

# backend_public/app/routers/auth.py
router = APIRouter(prefix="/auth", tags=["authentication"])

# backend_public/app/routers/admin.py
router = APIRouter(prefix="/admin", tags=["administration"])
```

### 2. Request/Response Models
**Use Pydantic models for all API schemas**:

```python
# schemas.py - Request/Response models
class UserCreate(BaseModel):
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    name: Optional[str] = Field(None, max_length=255)

class UserRead(BaseModel):
    id: str
    email: str
    name: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True  # Enable ORM mode

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    # Don't allow email updates for security
```

### 3. Authentication Middleware
**Implement consistent authentication across services**:

```python
# auth.py - Shared authentication utilities
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
) -> User:
    try:
        payload = jwt.decode(
            credentials.credentials, 
            settings.jwt_secret, 
            algorithms=["HS256"]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return user
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
```

## Service Integration Patterns

### 1. Inter-Service Communication
**Use HTTP clients for service-to-service communication**:

```python
# services/client.py - Service client pattern
import httpx
from typing import Optional

class BackendClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def analyze_prompt(self, prompt_content: str) -> dict:
        """Proxy to main backend analysis endpoint"""
        response = await self.client.post(
            f"{self.base_url}/analyze/",
            json={"prompt": {"content": prompt_content}}
        )
        response.raise_for_status()
        return response.json()
    
    async def get_user_prompts(self, user_id: str) -> List[dict]:
        """Get prompts created by user"""
        response = await self.client.get(
            f"{self.base_url}/prompt-base/prompts",
            params={"user_id": user_id}
        )
        response.raise_for_status()
        return response.json()

# Dependency injection
async def get_backend_client() -> BackendClient:
    return BackendClient(settings.backend_api_url)
```

### 2. Shared Schema Models
**Create shared Pydantic models for cross-service communication**:

```python
# shared/schemas.py - Models used across services
class PromptAnalysisRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=50000)
    user_id: Optional[str] = None
    format_type: Literal["auto", "text", "markdown", "xml"] = "auto"

class AnalysisResult(BaseModel):
    id: str
    overall_score: float
    judge_score: float
    semantic_entropy: float
    length_words: int
    contradictions: List[str]
    patches: List[dict]
    created_at: datetime
```

## Database Migration Strategy

### 1. Unified Migration System
**Use single Alembic instance for all services**:

```python
# backend/alembic/env.py - Include all service models
from app.models.prompts import *  # Main backend models
from backend_public.app.models import *  # Public service models

target_metadata = [
    # All SQLModel metadata
    Prompt.metadata,
    User.metadata,
    WorkflowRun.metadata,
    # ... other models
]
```

### 2. Migration Naming Convention
```bash
# Migration file naming pattern
001_initial_core_tables.py      # Core prompt analysis tables
002_add_user_management.py      # User authentication tables  
003_add_workflow_tracking.py    # Workflow execution tables
004_add_metrics_aggregation.py  # Metrics and reporting tables
```
## Deployment Configuration

### 1. Docker Setup
**Single docker-compose.yml for all services**:

```yaml
# infra/docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: curestry
      POSTGRES_PASSWORD: secure_password
      POSTGRES_DB: curestry
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U curestry"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend:
    build:
      context: ../backend
      dockerfile: Dockerfile
    environment:
      ENV: development
      DATABASE_URL: postgresql+asyncpg://curestry:secure_password@db:5432/curestry
      BACKEND_PUBLIC_URL: http://backend_public:8080
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ../backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  backend_public:
    build:
      context: ../backend_public
      dockerfile: Dockerfile
    environment:
      ENV: development
      DATABASE_URL: postgresql+asyncpg://curestry:secure_password@db:5432/curestry
      BACKEND_API_URL: http://backend:8000
    ports:
      - "8080:8080"
    depends_on:
      db:
        condition: service_healthy
      backend:
        condition: service_started
    volumes:
      - ../backend_public:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

  frontend:
    build:
      context: ../frontend_public
      dockerfile: Dockerfile
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8080
      NEXTAUTH_URL: http://localhost:3000
    ports:
      - "3000:3000"
    depends_on:
      - backend_public
    volumes:
      - ../frontend_public:/app
      - /app/node_modules
    command: npm run dev

volumes:
  postgres_data:

networks:
  default:
    name: curestry-network
```

### 2. Health Check Implementation
**Standardize health checks across services**:

```python
# health.py - Shared health check utilities
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter
import httpx

router = APIRouter()

@router.get("/healthz")
async def health_check(session: AsyncSession = Depends(get_async_session)):
    """Comprehensive health check"""
    health_status = {
        "service": "backend_public",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Database connectivity
    try:
        await session.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {e}"
        health_status["status"] = "degraded"
    
    # Service dependencies
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.backend_api_url}/healthz")
            health_status["checks"]["backend_api"] = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception as e:
        health_status["checks"]["backend_api"] = f"unhealthy: {e}"
        health_status["status"] = "degraded"
    
    return health_status
```

## Security Guidelines

### 1. Authentication Flow
**Implement OAuth + JWT pattern for backend_public**:

```python
# Google OAuth flow with JWT tokens
@router.get("/auth/google/login")
async def google_login():
    """Initiate Google OAuth flow"""
    redirect_uri = settings.google_oauth_redirect
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "scope": "openid email profile",
        "response_type": "code",
        "state": generate_state_token()
    }
    url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"
    return {"auth_url": url}

@router.get("/auth/google/callback")
async def google_callback(
    code: str,
    state: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Handle Google OAuth callback"""
    # Exchange code for tokens
    token_data = await exchange_oauth_code(code)
    user_info = await get_google_user_info(token_data["access_token"])
    
    # Create or update user
    user = await get_or_create_user(session, user_info)
    
    # Generate JWT
    jwt_token = create_jwt_token(user.id)
    
    return {"access_token": jwt_token, "token_type": "bearer"}
```

### 2. Input Validation
**Implement comprehensive input validation**:

```python
# Validation patterns
class PromptContent(BaseModel):
    content: str = Field(
        ..., 
        min_length=1, 
        max_length=50000,
        description="Prompt content to analyze"
    )
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        # Remove dangerous characters
        v = v.strip()
        if not v:
            raise ValueError("Content cannot be empty")
        
        # Check for potential security issues
        if '<script' in v.lower() or 'javascript:' in v.lower():
            raise ValueError("Content contains potentially dangerous code")
        
        return v
```

## Performance Guidelines


### 2. Database Query Optimization
**Use efficient query patterns**:

```python
# Efficient relationship loading
async def get_user_with_prompts(
    user_id: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Get user with their prompts in single query"""
    result = await session.execute(
        select(User)
        .options(selectinload(User.prompts))
        .where(User.id == user_id)
    )
    return result.scalar_one_or_none()

# Pagination with efficient counting
async def list_users_paginated(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_async_session)
):
    """List users with pagination"""
    # Get total count
    count_result = await session.execute(select(func.count(User.id)))
    total = count_result.scalar()
    
    # Get paginated results
    result = await session.execute(
        select(User)
        .offset(skip)
        .limit(limit)
        .order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    
    return {
        "users": [UserRead.model_validate(u) for u in users],
        "total": total,
        "skip": skip,
        "limit": limit
    }
```

## Monitoring and Observability

### 1. Structured Logging
**Implement consistent logging across services**:

```python
# logging_config.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "service": "backend_public",
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add context if available
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
            
        return json.dumps(log_entry)

# Setup logging
def setup_logging():
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
```

### 2. Metrics Collection
**Add Prometheus metrics for monitoring**:

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
REQUEST_COUNT = Counter(
    'http_requests_total', 
    'Total HTTP requests', 
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration'
)

ACTIVE_USERS = Gauge(
    'active_users_total',
    'Number of active users'
)

# Middleware for automatic metrics
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    REQUEST_DURATION.observe(duration)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    return response
```

---

**Last Updated**: 2025-08-17  
**Version**: 1.0  
**Status**: Ready for Implementation

This comprehensive guide provides the foundation for implementing a unified, scalable backend architecture for the Curestry project. Follow these patterns to ensure consistency, maintainability, and performance across all microservices.
