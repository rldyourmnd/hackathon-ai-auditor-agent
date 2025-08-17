# Backend Tasks - Implementation Plan (According to Roadmap)

Детальный план реализации задач для backend_public согласно roadmap проекта.

## Обзор Фаз

### Phase 1: Реверс-прокси (Задачи 1.1-1.2) - Week 1
**Цель**: Настроить Nginx с TLS и маршрутизацией + базовые оптимизации
**Длительность**: 2-3 дня
**Critical Path**: Да

### Phase 2: Бэкенд-прокси MVP REST (Задачи 2.1-2.4) - Week 1-2
**Цель**: Создать стабильный API-прокси с хранением результатов
**Длительность**: 5-7 дней
**Critical Path**: Да

### Phase 3: Браузерное расширение (Задачи 3.1-3.2) - Week 2
**Цель**: Связать расширение с backend API
**Длительность**: 3-4 дня
**Critical Path**: Да

### Phase 4: Админка (Задачи 6.1-6.3) - Week 3
**Цель**: Базовый UI для управления и аналитики
**Длительность**: 4-5 дней
**Critical Path**: Нет

---

## Phase 1: Реверс-прокси (Задачи 1.1-1.2)

### Task 1.1: Настроить Nginx с TLS и маршрутизацией
**Priority**: 🔴 Critical  
**Estimated Time**: 1.5 дня  
**Assignee**: DevOps Engineer  
**Dependencies**: None

#### Subtask 1.1.1: Поднять Nginx в compose и прокинуть / на веб, /api на бэк (6 часов)

**Создать nginx конфигурацию:**
```nginx
# infra/nginx/nginx.conf
upstream frontend {
    server frontend:3000;
}

upstream backend_public {
    server backend_public:8080;
}

server {
    listen 80;
    server_name localhost;
    
    # Redirect all HTTP to HTTPS (для production)
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name localhost;
    
    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/nginx.crt;
    ssl_certificate_key /etc/nginx/ssl/nginx.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Frontend routes (/) → frontend:3000
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support для Next.js hot reload
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # API routes (/api) → backend_public:8080
    location /api/ {
        proxy_pass http://backend_public/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers для браузерных расширений
        add_header Access-Control-Allow-Origin "*";
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
        
        # Preflight requests
        if ($request_method = OPTIONS) {
            return 204;
        }
    }
    
    # Admin routes (/admin) → backend_public:8080/admin
    location /admin/ {
        proxy_pass http://backend_public/admin/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Обновить docker-compose.yml:**
```yaml
# infra/docker-compose.yml - добавить nginx service
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - backend_public
      - frontend
    networks:
      - curestry-network
    restart: unless-stopped
```

#### Subtask 1.1.2: Включить автогенерацию/подключение сертификатов (dev self-signed) (2 часа)

**Создать скрипт генерации сертификатов:**
```bash
# infra/nginx/generate-ssl.sh
#!/bin/bash
set -e

SSL_DIR="./ssl"
mkdir -p $SSL_DIR

echo "Generating self-signed SSL certificate for development..."

# Generate private key
openssl genrsa -out $SSL_DIR/nginx.key 2048

# Generate certificate signing request
openssl req -new -key $SSL_DIR/nginx.key -out $SSL_DIR/nginx.csr -subj "/C=US/ST=CA/L=SF/O=Curestry/CN=localhost"

# Generate self-signed certificate
openssl x509 -req -days 365 -in $SSL_DIR/nginx.csr -signkey $SSL_DIR/nginx.key -out $SSL_DIR/nginx.crt

# Set proper permissions
chmod 600 $SSL_DIR/nginx.key
chmod 644 $SSL_DIR/nginx.crt

echo "SSL certificate generated successfully!"
echo "Certificate: $SSL_DIR/nginx.crt"
echo "Private key: $SSL_DIR/nginx.key"

# Clean up CSR file
rm $SSL_DIR/nginx.csr
```

**Обновить docker-compose для автогенерации:**
```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
    - ./nginx/ssl:/etc/nginx/ssl
  depends_on:
    - backend_public
    - frontend
  command: |
    sh -c "
    # Generate SSL cert if not exists
    if [ ! -f /etc/nginx/ssl/nginx.crt ]; then
      mkdir -p /etc/nginx/ssl &&
      openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/nginx/ssl/nginx.key \
        -out /etc/nginx/ssl/nginx.crt \
        -subj '/CN=localhost'
    fi &&
    nginx -g 'daemon off;'
    "
```

### Task 1.2: Включить базовые оптимизации
**Priority**: 🟡 Medium  
**Estimated Time**: 0.5 дня  
**Assignee**: DevOps Engineer  
**Dependencies**: Task 1.1

#### Subtask 1.2.1: Включить rate-limit по IP/маршрутам (2 часа)

```nginx
# nginx.conf - добавить rate limiting
http {
    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=general:10m rate=30r/m;
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=analyze:10m rate=2r/s;
    limit_req_zone $binary_remote_addr zone=admin:10m rate=20r/m;
    
    server {
        # General rate limiting
        location / {
            limit_req zone=general burst=50 nodelay;
            proxy_pass http://frontend;
        }
        
        # API rate limiting
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend_public/;
        }
        
        # Strict limiting for analyze endpoint (ресурсоемкий)
        location /api/analyze {
            limit_req zone=analyze burst=5 nodelay;
            proxy_pass http://backend_public/analyze;
        }
        
        # Admin rate limiting
        location /admin/ {
            limit_req zone=admin burst=10 nodelay;
            proxy_pass http://backend_public/admin/;
        }
    }
}
```

#### Subtask 1.2.2: Включить gzip и кэш статики (2 часа)

```nginx
# nginx.conf - performance optimizations
http {
    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/javascript
        text/xml
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    # Buffer sizes
    client_body_buffer_size 128k;
    client_max_body_size 10m;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;
    output_buffers 1 32k;
    postpone_output 1460;
    
    server {
        # Static files caching (для frontend assets)
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            add_header X-Content-Type-Options nosniff;
            proxy_pass http://frontend;
        }
        
        # API responses - no cache
        location /api/ {
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            add_header Pragma "no-cache";
            add_header Expires "0";
            proxy_pass http://backend_public/;
        }
        
        # HTML files - short cache
        location ~ \.html$ {
            expires 5m;
            add_header Cache-Control "public, must-revalidate";
            proxy_pass http://frontend;
        }
    }
}
```

---

## Phase 2: Бэкенд-прокси MVP REST (Задачи 2.1-2.4)

### Task 2.1: Разделить слои и заготовки (app/factory)
**Priority**: 🔴 Critical  
**Estimated Time**: 1 день  
**Assignee**: Backend Developer  
**Dependencies**: None

#### Subtask 2.1.1: Создать app_factory() и точку входа uvicorn (3 часа)

```python
# backend_public/app/factory.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time
import uuid

from .config import settings
from .middleware.error_handler import error_handling_middleware
from .middleware.logging import logging_middleware, request_id_middleware
from .api import analysis, admin, auth, health
from .infra.database import init_database

def create_app() -> FastAPI:
    """Application factory pattern"""
    
    app = FastAPI(
        title="Curestry API Proxy",
        description="AI Prompt Analysis API Gateway & Admin Dashboard",
        version="1.0.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
    )
    
    # Security middleware
    if settings.is_production:
        app.add_middleware(
            TrustedHostMiddleware, 
            allowed_hosts=settings.allowed_hosts
        )
    
    # CORS middleware (для браузерных расширений)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Custom middleware
    app.middleware("http")(request_id_middleware)
    app.middleware("http")(logging_middleware)
    app.middleware("http")(error_handling_middleware)
    
    # Include routers
    app.include_router(health.router)
    app.include_router(analysis.router, prefix="/api")
    app.include_router(admin.router, prefix="/admin")
    app.include_router(auth.router, prefix="/auth")
    
    # Startup/shutdown events
    @app.on_event("startup")
    async def startup_event():
        await init_database()
        print(f"🚀 Curestry API Proxy started (env: {settings.env})")
    
    return app

# backend_public/main.py
from app.factory import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8080, 
        reload=True,
        log_level="info"
    )
```

#### Subtask 2.1.2: Разнести код по слоям (4 часа)

```
backend_public/
├── app/
│   ├── factory.py                    # Application factory
│   ├── config.py                     # Settings configuration
│   ├── infra/                        # Infrastructure layer
│   │   ├── __init__.py
│   │   ├── database.py               # Database connections & sessions
│   │   ├── pipeline_client.py        # HTTP client to main backend
│   │   ├── cache.py                  # Redis/memory cache
│   │   └── event_logger.py           # Event logging service
│   ├── domain/                       # Domain layer
│   │   ├── __init__.py
│   │   ├── models.py                 # Domain models (не DB!)
│   │   ├── events.py                 # Domain events
│   │   ├── services.py               # Domain services
│   │   └── exceptions.py             # Domain exceptions
│   ├── api/                          # API layer (controllers)
│   │   ├── __init__.py
│   │   ├── analysis.py               # POST /analyze, /clarify, /apply
│   │   ├── admin.py                  # GET /analyses, /timeseries, /models
│   │   ├── auth.py                   # Authentication endpoints
│   │   └── health.py                 # Health check & diagnostics
│   ├── services/                     # Application services
│   │   ├── __init__.py
│   │   ├── analysis_service.py       # Analysis orchestration
│   │   ├── admin_service.py          # Admin dashboard logic
│   │   └── auth_service.py           # Authentication logic
│   ├── orm/                          # ORM layer (data access)
│   │   ├── __init__.py
│   │   ├── models.py                 # SQLModel definitions
│   │   └── repositories.py           # Data access repositories
│   ├── dto/                          # Data Transfer Objects
│   │   ├── __init__.py
│   │   ├── requests.py               # Request DTOs
│   │   ├── responses.py              # Response DTOs
│   │   └── common.py                 # Common DTOs (Result, Error)
│   └── middleware/                   # Custom middleware
│       ├── __init__.py
│       ├── error_handler.py          # Global error handling
│       ├── logging.py                # Request logging
│       └── rate_limiting.py          # Application-level rate limiting
├── main.py                           # Entry point
├── pyproject.toml                    # Dependencies
└── alembic/                          # Database migrations
    ├── alembic.ini
    ├── env.py
    └── versions/
```

#### Subtask 2.1.3: Завести общие модели ошибок/ответов в dto/ и Result-тип (1 час)

```python
# app/dto/common.py
from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

T = TypeVar('T')

class Result(BaseModel, Generic[T]):
    """Result pattern для обработки успех/ошибка"""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    metadata: Optional[dict] = None
    
    @classmethod
    def ok(cls, data: T, metadata: Optional[dict] = None) -> "Result[T]":
        return cls(success=True, data=data, metadata=metadata)
    
    @classmethod
    def fail(cls, message: str, code: str = "GENERIC_ERROR", metadata: Optional[dict] = None) -> "Result[T]":
        return cls(success=False, error=message, error_code=code, metadata=metadata)

class ErrorResponse(BaseModel):
    """Стандартный формат ошибки API"""
    message: str
    error_code: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    path: Optional[str] = None
    request_id: Optional[str] = None
    details: Optional[dict] = None

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ClientType(str, Enum):
    BROWSER = "browser"
    IDE = "ide"
    CLI = "cli"
    API = "api"

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=1000)

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    limit: int
    pages: int
    
    @property
    def has_next(self) -> bool:
        return self.page < self.pages
    
    @property
    def has_prev(self) -> bool:
        return self.page > 1
```

### Task 2.2: Описать контракты и стабилизировать API
**Priority**: 🔴 Critical  
**Estimated Time**: 1.5 дня  
**Assignee**: Backend Developer  
**Dependencies**: Task 2.1

#### Subtask 2.2.1: Описать OpenAPI для POST /analyze, POST /analyze/clarify, POST /analyze/apply, GET /export (4 часа)

```python
# app/dto/requests.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from .common import ClientType

class PromptDto(BaseModel):
    content: str = Field(
        ..., 
        min_length=1, 
        max_length=50000,
        description="Prompt text content to analyze",
        example="Write a Python function that calculates fibonacci numbers"
    )
    format_type: str = Field(
        default="auto",
        pattern="^(auto|text|markdown|xml)$",
        description="Prompt format type detection",
        example="auto"
    )
    language: str = Field(
        default="auto",
        description="Prompt language (auto-detected if not specified)",
        example="en"
    )

class ClientInfo(BaseModel):
    type: ClientType = Field(default=ClientType.BROWSER, description="Client type")
    name: str = Field(..., description="Client name/identifier", example="chatgpt-extension")
    version: str = Field(default="1.0.0", description="Client version", example="1.2.3")
    user_agent: Optional[str] = Field(None, description="Browser user agent")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional client metadata")

class AnalyzeRequest(BaseModel):
    """Request для анализа промпта"""
    prompt: PromptDto = Field(..., description="Prompt to analyze")
    client_info: Optional[ClientInfo] = Field(None, description="Client information")
    save_result: bool = Field(default=True, description="Whether to save analysis result")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "prompt": {
                    "content": "Write a Python function that calculates fibonacci numbers",
                    "format_type": "auto",
                    "language": "en"
                },
                "client_info": {
                    "type": "browser",
                    "name": "chatgpt-extension",
                    "version": "1.0.0"
                },
                "save_result": True
            }
        }
    }

class ClarifyAnswer(BaseModel):
    question_id: str = Field(..., description="ID of the question being answered")
    answer: str = Field(..., description="User's answer to the clarification question")

class ClarifyRequest(BaseModel):
    """Request для clarify цикла"""
    analysis_id: str = Field(..., description="ID of the analysis to clarify")
    answers: List[ClarifyAnswer] = Field(..., description="Answers to clarification questions")

class ApplyRequest(BaseModel):
    """Request для применения патчей"""
    analysis_id: str = Field(..., description="ID of the analysis")
    patch_ids: List[str] = Field(..., description="IDs of patches to apply")
    apply_safe_all: bool = Field(default=False, description="Apply all safe patches automatically")
```

```python
# app/dto/responses.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from .common import RiskLevel

class JudgeScore(BaseModel):
    score: float = Field(..., ge=0, le=10, description="Overall judge score (0-10)")
    rationale: str = Field(..., description="Judge reasoning")
    criteria_scores: Dict[str, float] = Field(default_factory=dict, description="Individual criteria scores")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Judge confidence level")

class SemanticEntropy(BaseModel):
    entropy: float = Field(..., description="Semantic entropy value")
    spread: float = Field(..., description="Semantic spread")
    clusters: int = Field(..., description="Number of semantic clusters")
    samples: List[str] = Field(default_factory=list, description="Sample variations")

class MetricReport(BaseModel):
    """Comprehensive analysis metrics"""
    overall_score: float = Field(..., ge=0, le=10, description="Overall quality score")
    judge_score: JudgeScore = Field(..., description="LLM judge evaluation")
    semantic_entropy: SemanticEntropy = Field(..., description="Semantic consistency metrics")
    complexity_score: float = Field(..., ge=0, le=10, description="Vocabulary complexity")
    length_words: int = Field(..., ge=0, description="Word count")
    length_chars: int = Field(..., ge=0, description="Character count")
    risk_level: RiskLevel = Field(..., description="Overall risk assessment")
    contradictions: List[str] = Field(default_factory=list, description="Detected contradictions")
    format_valid: bool = Field(..., description="Format validation result")
    detected_language: str = Field(..., description="Detected language")
    translated: bool = Field(default=False, description="Whether content was translated")

class Patch(BaseModel):
    """Improvement suggestion"""
    id: str = Field(..., description="Unique patch identifier")
    type: str = Field(..., pattern="^(safe|risky)$", description="Patch safety level")
    category: str = Field(..., description="Improvement category")
    title: str = Field(..., description="Short patch description")
    description: str = Field(..., description="Detailed patch description")
    original_text: Optional[str] = Field(None, description="Original text to replace")
    suggested_text: Optional[str] = Field(None, description="Suggested replacement text")
    rationale: str = Field(..., description="Why this improvement is suggested")
    risk_level: RiskLevel = Field(..., description="Risk level of applying this patch")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Confidence in suggestion")

class ClarifyQuestion(BaseModel):
    """Clarification question"""
    id: str = Field(..., description="Question identifier")
    question: str = Field(..., description="Question text")
    category: str = Field(..., description="Question category")
    options: Optional[List[str]] = Field(None, description="Multiple choice options")
    required: bool = Field(default=True, description="Whether answer is required")

class AnalyzeResponse(BaseModel):
    """Response от POST /analyze"""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    prompt_id: Optional[str] = Field(None, description="Prompt identifier")
    report: MetricReport = Field(..., description="Analysis metrics and scores")
    patches: List[Patch] = Field(default_factory=list, description="Improvement suggestions")
    questions: List[ClarifyQuestion] = Field(default_factory=list, description="Clarification questions")
    created_at: datetime = Field(..., description="Analysis timestamp")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    pipeline_version: Optional[str] = Field(None, description="Analysis pipeline version")

class ClarifyResponse(BaseModel):
    """Response от POST /analyze/clarify"""
    analysis_id: str = Field(..., description="Analysis identifier")
    updated_report: MetricReport = Field(..., description="Updated analysis after clarification")
    new_patches: List[Patch] = Field(default_factory=list, description="New improvement suggestions")
    score_delta: float = Field(..., description="Change in overall score")
    processing_time_ms: int = Field(..., description="Processing time for clarification")

class ApplyResponse(BaseModel):
    """Response от POST /analyze/apply"""
    analysis_id: str = Field(..., description="Analysis identifier")
    original_prompt: str = Field(..., description="Original prompt text")
    improved_prompt: str = Field(..., description="Improved prompt text")
    applied_patches: List[str] = Field(..., description="IDs of successfully applied patches")
    failed_patches: List[str] = Field(default_factory=list, description="IDs of patches that failed to apply")
    improvement_summary: str = Field(..., description="Summary of improvements made")
    quality_gain: float = Field(..., description="Estimated quality improvement")
```

#### Subtask 2.2.2: Ввести DTO: Prompt, MetricReport, JudgeScore, RiskLevel, Patch (уже включено выше) (2 часа)

#### Subtask 2.2.3: Включить CORS и /healthz (2 часа)

```python
# app/api/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..infra.database import get_async_session
from ..infra.pipeline_client import PipelineClient, get_pipeline_client
from ..dto.responses import HealthResponse
import httpx
from datetime import datetime

router = APIRouter(tags=["health"])

@router.get("/healthz", response_model=HealthResponse)
async def health_check(
    session: AsyncSession = Depends(get_async_session),
    pipeline: PipelineClient = Depends(get_pipeline_client)
):
    """
    Comprehensive health check endpoint
    
    Checks:
    - Database connectivity
    - Pipeline service availability
    - Application status
    """
    health_data = {
        "service": "backend_public",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "checks": {}
    }
    
    # Database check
    try:
        await session.execute("SELECT 1")
        health_data["checks"]["database"] = "healthy"
    except Exception as e:
        health_data["checks"]["database"] = f"unhealthy: {str(e)}"
        health_data["status"] = "degraded"
    
    # Pipeline service check
    try:
        pipeline_health = await pipeline.health_check()
        health_data["checks"]["pipeline"] = "healthy" if pipeline_health else "unhealthy"
    except Exception as e:
        health_data["checks"]["pipeline"] = f"unhealthy: {str(e)}"
        health_data["status"] = "degraded"
    
    return HealthResponse(**health_data)

@router.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "Curestry API Proxy",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/healthz",
        "endpoints": {
            "analyze": "/api/analyze",
            "admin": "/admin/analyses"
        }
    }
```

### Task 2.3: Подключить хранилище результатов
**Priority**: 🔴 Critical  
**Estimated Time**: 2 дня  
**Assignee**: Backend Developer  
**Dependencies**: Task 2.2

#### Subtask 2.3.1: Подключить ORM/миграции, таблицы prompts, analysis_results, events (6 часов)

```python
# app/orm/models.py
from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# Enums
class ClientType(str, Enum):
    BROWSER = "browser"
    IDE = "ide" 
    CLI = "cli"
    API = "api"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EventType(str, Enum):
    ANALYZE_STARTED = "analyze_started"
    ANALYZE_COMPLETED = "analyze_completed"
    ANALYZE_FAILED = "analyze_failed"
    CLARIFY_REQUESTED = "clarify_requested"
    CLARIFY_COMPLETED = "clarify_completed"
    PATCHES_APPLIED = "patches_applied"
    EXPORT_REQUESTED = "export_requested"

# Models
class Prompt(SQLModel, table=True):
    __tablename__ = "prompts"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    content: str = Field(..., max_length=50000)
    format_type: str = Field(default="auto")
    language: str = Field(default="auto")
    detected_language: Optional[str] = None
    translated: bool = Field(default=False)
    
    # Client info
    client_type: Optional[ClientType] = None
    client_name: Optional[str] = None
    client_version: Optional[str] = None
    client_metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    analyses: List["AnalysisResult"] = Relationship(back_populates="prompt")

class AnalysisResult(SQLModel, table=True):
    __tablename__ = "analysis_results"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    prompt_id: str = Field(foreign_key="prompts.id", index=True)
    
    # Core metrics
    overall_score: float = Field(..., ge=0, le=10)
    judge_score: float = Field(..., ge=0, le=10) 
    semantic_entropy: float = Field(...)
    complexity_score: float = Field(..., ge=0, le=10)
    length_words: int = Field(..., ge=0)
    length_chars: int = Field(..., ge=0)
    risk_level: RiskLevel = Field(...)
    format_valid: bool = Field(...)
    
    # JSON fields for complex data
    judge_details: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    semantic_details: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    contradictions: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    patches: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    questions: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Processing metadata
    processing_time_ms: int = Field(...)
    pipeline_version: Optional[str] = None
    pipeline_metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    # Clarification data
    clarification_answers: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))
    applied_patches: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    prompt: Prompt = Relationship(back_populates="analyses")
    events: List["AnalysisEvent"] = Relationship(back_populates="analysis")

class AnalysisEvent(SQLModel, table=True):
    __tablename__ = "analysis_events"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    analysis_id: Optional[str] = Field(foreign_key="analysis_results.id", index=True)
    prompt_id: Optional[str] = Field(foreign_key="prompts.id", index=True)
    
    event_type: EventType = Field(..., index=True)
    event_data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Performance tracking
    duration_ms: Optional[int] = None
    memory_usage_mb: Optional[float] = None
    
    # Request context
    request_id: Optional[str] = None
    user_ip: Optional[str] = None
    user_agent: Optional[str] = None
    
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    # Relationships
    analysis: Optional[AnalysisResult] = Relationship(back_populates="events")

# Alembic migration setup
# alembic/env.py - добавить import моделей
from app.orm.models import *
target_metadata = SQLModel.metadata
```

**Создать Alembic миграцию:**
```bash
# Команды для создания миграции
cd backend_public
alembic init alembic
alembic revision --autogenerate -m "Initial tables: prompts, analysis_results, events"
alembic upgrade head
```

#### Subtask 2.3.2: Сохранить результат анализа и выдать analysis_id (4 часа)

```python
# app/services/analysis_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from ..orm.models import Prompt, AnalysisResult, AnalysisEvent, EventType
from ..infra.pipeline_client import PipelineClient
from ..infra.event_logger import EventLogger
from ..dto.requests import AnalyzeRequest
from ..dto.responses import AnalyzeResponse, MetricReport, Patch, ClarifyQuestion
from ..dto.common import Result
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AnalysisService:
    def __init__(self, 
                 session: AsyncSession,
                 pipeline_client: PipelineClient,
                 event_logger: EventLogger):
        self.session = session
        self.pipeline = pipeline_client
        self.events = event_logger
    
    async def analyze_prompt(self, request: AnalyzeRequest) -> Result[AnalyzeResponse]:
        """Main analysis workflow with persistence"""
        
        start_time = datetime.utcnow()
        
        # 1. Create and save prompt
        prompt = Prompt(
            content=request.prompt.content,
            format_type=request.prompt.format_type,
            language=request.prompt.language,
            client_type=request.client_info.type if request.client_info else None,
            client_name=request.client_info.name if request.client_info else None,
            client_version=request.client_info.version if request.client_info else None,
            client_metadata=request.client_info.metadata if request.client_info else None
        )
        
        self.session.add(prompt)
        await self.session.commit()
        await self.session.refresh(prompt)
        
        # 2. Log analysis started
        await self.events.log_event(
            event_type=EventType.ANALYZE_STARTED,
            prompt_id=prompt.id,
            event_data={
                "content_length": len(request.prompt.content),
                "format_type": request.prompt.format_type,
                "client_info": request.client_info.model_dump() if request.client_info else None
            }
        )
        
        try:
            # 3. Call pipeline service
            pipeline_response = await self.pipeline.analyze(
                prompt=request.prompt.content,
                format_type=request.prompt.format_type,
                language=request.prompt.language
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # 4. Create analysis result
            analysis = AnalysisResult(
                prompt_id=prompt.id,
                overall_score=pipeline_response["report"]["overall_score"],
                judge_score=pipeline_response["report"]["judge_score"]["score"],
                semantic_entropy=pipeline_response["report"]["semantic_entropy"]["entropy"],
                complexity_score=pipeline_response["report"]["complexity_score"],
                length_words=pipeline_response["report"]["length_words"],
                length_chars=pipeline_response["report"]["length_chars"],
                risk_level=self._calculate_risk_level(pipeline_response["report"]),
                format_valid=pipeline_response["report"]["format_valid"],
                
                # JSON fields
                judge_details=pipeline_response["report"]["judge_score"],
                semantic_details=pipeline_response["report"]["semantic_entropy"],
                contradictions=pipeline_response["report"]["contradictions"],
                patches=pipeline_response["patches"],
                questions=pipeline_response["questions"],
                
                # Metadata
                processing_time_ms=int(processing_time),
                pipeline_version=pipeline_response.get("version", "1.0.0"),
                pipeline_metadata=pipeline_response.get("metadata", {})
            )
            
            # Update prompt with detection results
            prompt.detected_language = pipeline_response["report"]["detected_language"]
            prompt.translated = pipeline_response["report"]["translated"]
            
            self.session.add(analysis)
            await self.session.commit()
            await self.session.refresh(analysis)
            
            # 5. Log success
            await self.events.log_event(
                event_type=EventType.ANALYZE_COMPLETED,
                analysis_id=analysis.id,
                prompt_id=prompt.id,
                event_data={
                    "overall_score": analysis.overall_score,
                    "risk_level": analysis.risk_level,
                    "patches_count": len(analysis.patches),
                    "questions_count": len(analysis.questions)
                },
                duration_ms=int(processing_time)
            )
            
            # 6. Build response
            response = AnalyzeResponse(
                analysis_id=analysis.id,
                prompt_id=prompt.id,
                report=self._build_metric_report(pipeline_response["report"]),
                patches=[Patch(**patch) for patch in pipeline_response["patches"]],
                questions=[ClarifyQuestion(**q) for q in pipeline_response["questions"]],
                created_at=analysis.created_at,
                processing_time_ms=analysis.processing_time_ms,
                pipeline_version=analysis.pipeline_version
            )
            
            logger.info(f"Analysis completed successfully: {analysis.id}")
            return Result.ok(response)
            
        except Exception as e:
            # Log failure
            await self.events.log_event(
                event_type=EventType.ANALYZE_FAILED,
                prompt_id=prompt.id,
                event_data={
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            
            logger.error(f"Analysis failed for prompt {prompt.id}: {e}")
            return Result.fail(f"Analysis failed: {str(e)}", "ANALYSIS_ERROR")
    
    def _calculate_risk_level(self, report: dict) -> str:
        """Calculate overall risk level from metrics"""
        score = report["overall_score"]
        contradictions = len(report.get("contradictions", []))
        
        if score < 3 or contradictions > 5:
            return "critical"
        elif score < 5 or contradictions > 2:
            return "high"
        elif score < 7 or contradictions > 0:
            return "medium"
        else:
            return "low"
    
    def _build_metric_report(self, report_data: dict) -> MetricReport:
        """Convert pipeline response to MetricReport DTO"""
        return MetricReport(
            overall_score=report_data["overall_score"],
            judge_score=JudgeScore(**report_data["judge_score"]),
            semantic_entropy=SemanticEntropy(**report_data["semantic_entropy"]),
            complexity_score=report_data["complexity_score"],
            length_words=report_data["length_words"],
            length_chars=report_data["length_chars"],
            risk_level=self._calculate_risk_level(report_data),
            contradictions=report_data["contradictions"],
            format_valid=report_data["format_valid"],
            detected_language=report_data["detected_language"],
            translated=report_data["translated"]
        )
```

#### Subtask 2.3.3: Добавить GET /analyses/{id} для получения сохранённого отчёта (2 часа)

```python
# app/api/analysis.py - добавить endpoint
@router.get("/analyses/{analysis_id}", response_model=AnalyzeResponse)
async def get_analysis(
    analysis_id: str,
    session: AsyncSession = Depends(get_async_session)
) -> AnalyzeResponse:
    """
    Get saved analysis result by ID
    
    - **analysis_id**: UUID of the analysis to retrieve
    
    Returns complete analysis data including metrics, patches, and questions.
    """
    
    # Find analysis with prompt
    result = await session.execute(
        select(AnalysisResult)
        .options(selectinload(AnalysisResult.prompt))
        .where(AnalysisResult.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(
            status_code=404, 
            detail=f"Analysis {analysis_id} not found"
        )
    
    # Convert to response format
    return AnalyzeResponse(
        analysis_id=analysis.id,
        prompt_id=analysis.prompt_id,
        report=MetricReport(
            overall_score=analysis.overall_score,
            judge_score=JudgeScore(**analysis.judge_details),
            semantic_entropy=SemanticEntropy(**analysis.semantic_details),
            complexity_score=analysis.complexity_score,
            length_words=analysis.length_words,
            length_chars=analysis.length_chars,
            risk_level=analysis.risk_level,
            contradictions=analysis.contradictions,
            format_valid=analysis.format_valid,
            detected_language=analysis.prompt.detected_language,
            translated=analysis.prompt.translated
        ),
        patches=[Patch(**patch) for patch in analysis.patches],
        questions=[ClarifyQuestion(**q) for q in analysis.questions],
        created_at=analysis.created_at,
        processing_time_ms=analysis.processing_time_ms,
        pipeline_version=analysis.pipeline_version
    )
```

### Task 2.4: Соединить прокси с внешними сервисами
**Priority**: 🔴 Critical  
**Estimated Time**: 1.5 дня  
**Assignee**: Backend Developer  
**Dependencies**: Task 2.3

#### Subtask 2.4.1: Прокинуть вызовы в сервис пайплайна (HTTP/RPC) с таймаутами/ретраями (4 часа)

```python
# app/infra/pipeline_client.py
import httpx
import asyncio
from typing import Dict, Any, Optional
from ..config import settings
import logging

logger = logging.getLogger(__name__)

class PipelineError(Exception):
    """Base pipeline service error"""
    pass

class PipelineTimeoutError(PipelineError):
    """Pipeline service timeout error"""
    pass

class PipelineHTTPError(PipelineError):
    """Pipeline service HTTP error"""
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code

class PipelineClient:
    def __init__(self):
        self.base_url = settings.pipeline_service_url  # http://backend:8000
        self.timeout = httpx.Timeout(
            connect=5.0,      # Connection timeout
            read=120.0,       # Read timeout for analysis (2 minutes)
            write=10.0,       # Write timeout  
            pool=5.0          # Pool timeout
        )
        
        # Create persistent HTTP client
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(
                max_connections=20,
                max_keepalive_connections=10
            ),
            headers={
                "User-Agent": "Curestry-Proxy/1.0",
                "Content-Type": "application/json"
            }
        )
    
    async def analyze(self, 
                     prompt: str, 
                     format_type: str = "auto",
                     language: str = "auto") -> Dict[str, Any]:
        """
        Call main backend /analyze endpoint with retries
        
        Implements exponential backoff retry strategy:
        - 3 attempts total
        - Exponential backoff: 1s, 2s, 4s
        - Retry on 5xx errors and timeouts
        - Fail fast on 4xx errors
        """
        
        payload = {
            "prompt": {
                "content": prompt,
                "format_type": format_type,
                "language": language
            }
        }
        
        last_exception = None
        
        for attempt in range(3):
            try:
                logger.info(f"Pipeline analyze attempt {attempt + 1}/3")
                
                response = await self.client.post(
                    f"{self.base_url}/analyze/",
                    json=payload
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"Pipeline analyze successful on attempt {attempt + 1}")
                return result
                
            except httpx.TimeoutException as e:
                last_exception = e
                logger.warning(f"Pipeline timeout on attempt {attempt + 1}: {e}")
                
                if attempt == 2:  # Last attempt
                    raise PipelineTimeoutError(
                        f"Pipeline service timeout after 3 attempts. "
                        f"Analysis taking longer than {self.timeout.read}s."
                    )
                
                # Exponential backoff
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
                
            except httpx.HTTPStatusError as e:
                last_exception = e
                status_code = e.response.status_code
                
                logger.error(f"Pipeline HTTP error {status_code} on attempt {attempt + 1}")
                
                # Don't retry 4xx errors (client errors)
                if 400 <= status_code < 500:
                    raise PipelineHTTPError(
                        f"Pipeline client error {status_code}: {e.response.text}",
                        status_code
                    )
                
                # Retry 5xx errors (server errors)
                if status_code >= 500 and attempt < 2:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying server error in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                
                # Last attempt or non-retryable error
                raise PipelineHTTPError(
                    f"Pipeline server error {status_code}: {e.response.text}",
                    status_code
                )
                
            except Exception as e:
                last_exception = e
                logger.error(f"Pipeline connection error on attempt {attempt + 1}: {e}")
                
                if attempt == 2:  # Last attempt
                    raise PipelineError(f"Pipeline connection failed after 3 attempts: {str(e)}")
                
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
        
        # Should never reach here, but just in case
        raise PipelineError(f"Unexpected error after retries: {last_exception}")
    
    async def clarify(self, analysis_id: str, answers: List[Dict]) -> Dict[str, Any]:
        """Call pipeline /analyze/clarify endpoint"""
        payload = {
            "prompt_id": analysis_id,
            "answers": answers
        }
        
        # Similar retry logic as analyze()
        for attempt in range(3):
            try:
                response = await self.client.post(
                    f"{self.base_url}/analyze/clarify",
                    json=payload
                )
                response.raise_for_status()
                return response.json()
                
            except Exception as e:
                if attempt == 2:
                    raise PipelineError(f"Clarify failed: {str(e)}")
                await asyncio.sleep(2 ** attempt)
    
    async def apply_patches(self, analysis_id: str, patch_ids: List[str]) -> Dict[str, Any]:
        """Call pipeline /analyze/apply endpoint"""
        payload = {
            "prompt_id": analysis_id,
            "patch_ids": patch_ids
        }
        
        # Similar retry logic
        for attempt in range(3):
            try:
                response = await self.client.post(
                    f"{self.base_url}/analyze/apply",
                    json=payload
                )
                response.raise_for_status()
                return response.json()
                
            except Exception as e:
                if attempt == 2:
                    raise PipelineError(f"Apply patches failed: {str(e)}")
                await asyncio.sleep(2 ** attempt)
    
    async def health_check(self) -> bool:
        """Check if pipeline service is healthy"""
        try:
            response = await self.client.get(
                f"{self.base_url}/healthz",
                timeout=httpx.Timeout(5.0)  # Quick health check
            )
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self):
        """Clean up HTTP client"""
        await self.client.aclose()

# Dependency injection
async def get_pipeline_client() -> PipelineClient:
    return PipelineClient()
```

#### Subtask 2.4.2: Нормализовать ошибки пайплайна в единый формат API (2 часа)

```python
# app/middleware/error_handler.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from ..infra.pipeline_client import PipelineError, PipelineTimeoutError, PipelineHTTPError
from ..dto.common import ErrorResponse
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)

async def error_handling_middleware(request: Request, call_next):
    """Global error handling middleware"""
    
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    try:
        response = await call_next(request)
        return response
        
    except PipelineTimeoutError as e:
        logger.error(f"Pipeline timeout [{request_id}]: {e}")
        return JSONResponse(
            status_code=504,
            content=ErrorResponse(
                message="Analysis service is taking longer than expected. Please try again in a few minutes.",
                error_code="PIPELINE_TIMEOUT",
                timestamp=datetime.utcnow(),
                path=str(request.url.path),
                request_id=request_id,
                details={
                    "retry_after": "2-3 minutes",
                    "support_message": "If this persists, contact support with request ID"
                }
            ).model_dump()
        )
        
    except PipelineHTTPError as e:
        logger.error(f"Pipeline HTTP error [{request_id}]: {e}")
        
        # Map pipeline errors to appropriate HTTP status codes
        if e.status_code == 400:
            status_code = 400
            message = "Invalid prompt format or content. Please check your input."
            error_code = "INVALID_PROMPT"
        elif e.status_code == 429:
            status_code = 429
            message = "Analysis service is busy. Please try again in a moment."
            error_code = "RATE_LIMITED"
        else:
            status_code = 502
            message = "Analysis service error. Please try again."
            error_code = "PIPELINE_ERROR"
            
        return JSONResponse(
            status_code=status_code,
            content=ErrorResponse(
                message=message,
                error_code=error_code,
                timestamp=datetime.utcnow(),
                path=str(request.url.path),
                request_id=request_id
            ).model_dump()
        )
        
    except PipelineError as e:
        logger.error(f"Pipeline error [{request_id}]: {e}")
        return JSONResponse(
            status_code=502,
            content=ErrorResponse(
                message="Analysis service temporarily unavailable. Please try again.",
                error_code="PIPELINE_UNAVAILABLE",
                timestamp=datetime.utcnow(),
                path=str(request.url.path),
                request_id=request_id,
                details={
                    "retry_after": "1-2 minutes"
                }
            ).model_dump()
        )
        
    except HTTPException as e:
        # FastAPI HTTPExceptions
        logger.warning(f"HTTP exception [{request_id}]: {e.detail}")
        return JSONResponse(
            status_code=e.status_code,
            content=ErrorResponse(
                message=e.detail,
                error_code="HTTP_ERROR",
                timestamp=datetime.utcnow(),
                path=str(request.url.path),
                request_id=request_id
            ).model_dump()
        )
        
    except RequestValidationError as e:
        # Pydantic validation errors
        logger.warning(f"Validation error [{request_id}]: {e}")
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                message="Invalid request data. Please check your input.",
                error_code="VALIDATION_ERROR",
                timestamp=datetime.utcnow(),
                path=str(request.url.path),
                request_id=request_id,
                details={
                    "validation_errors": [
                        {
                            "field": ".".join(str(x) for x in err["loc"]),
                            "message": err["msg"],
                            "type": err["type"]
                        }
                        for err in e.errors()
                    ]
                }
            ).model_dump()
        )
        
    except Exception as e:
        # Unexpected errors
        logger.exception(f"Unexpected error [{request_id}]: {e}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                message="Internal server error. Please contact support if this persists.",
                error_code="INTERNAL_ERROR",
                timestamp=datetime.utcnow(),
                path=str(request.url.path),
                request_id=request_id,
                details={
                    "support_message": "Include this request ID when contacting support"
                }
            ).model_dump()
        )
```

#### Subtask 2.4.3: Логировать analyze_started/analyze_completed в events (2 часа)

```python
# app/infra/event_logger.py
from sqlalchemy.ext.asyncio import AsyncSession
from ..orm.models import AnalysisEvent, EventType
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EventLogger:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def log_event(self,
                       event_type: EventType,
                       analysis_id: Optional[str] = None,
                       prompt_id: Optional[str] = None,
                       event_data: Optional[Dict[str, Any]] = None,
                       duration_ms: Optional[int] = None,
                       memory_usage_mb: Optional[float] = None,
                       request_id: Optional[str] = None,
                       user_ip: Optional[str] = None,
                       user_agent: Optional[str] = None) -> AnalysisEvent:
        """Log analysis event to database"""
        
        event = AnalysisEvent(
            analysis_id=analysis_id,
            prompt_id=prompt_id,
            event_type=event_type,
            event_data=event_data or {},
            duration_ms=duration_ms,
            memory_usage_mb=memory_usage_mb,
            request_id=request_id,
            user_ip=user_ip,
            user_agent=user_agent,
            timestamp=datetime.utcnow()
        )
        
        self.session.add(event)
        
        try:
            await self.session.commit()
            logger.info(f"Event logged: {event_type} for analysis {analysis_id}")
            return event
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to log event {event_type}: {e}")
            raise

# Usage in analysis service
class AnalysisService:
    async def analyze_prompt(self, request: AnalyzeRequest) -> Result[AnalyzeResponse]:
        # ... existing code ...
        
        # Start event
        await self.events.log_event(
            event_type=EventType.ANALYZE_STARTED,
            prompt_id=prompt.id,
            event_data={
                "content_length": len(request.prompt.content),
                "format_type": request.prompt.format_type,
                "client_info": request.client_info.model_dump() if request.client_info else None
            },
            request_id=getattr(request, 'request_id', None)
        )
        
        try:
            # ... pipeline call ...
            
            # Success event
            await self.events.log_event(
                event_type=EventType.ANALYZE_COMPLETED,
                analysis_id=analysis.id,
                prompt_id=prompt.id,
                event_data={
                    "overall_score": analysis.overall_score,
                    "risk_level": analysis.risk_level,
                    "patches_count": len(analysis.patches),
                    "questions_count": len(analysis.questions),
                    "pipeline_version": analysis.pipeline_version
                },
                duration_ms=int(processing_time)
            )
            
        except Exception as e:
            # Failure event
            await self.events.log_event(
                event_type=EventType.ANALYZE_FAILED,
                prompt_id=prompt.id,
                event_data={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "pipeline_available": await self.pipeline.health_check()
                }
            )
            raise
```

---

## Phase 3: Браузерное расширение (Задачи 3.1-3.2)

### Task 3.1: Добавить HTTP-клиент и конфиг
**Priority**: 🔴 Critical  
**Estimated Time**: 1 день  
**Assignee**: Frontend Developer  
**Dependencies**: Task 2.4

#### Subtask 3.1.1: Встроить типизированный клиент (baseURL, API-key, таймауты) (4 часа)

```typescript
// browser-extension/src/api/types.ts
interface ApiConfig {
  baseURL: string;
  apiKey?: string;
  timeout: number;
  retries: number;
}

interface ClientInfo {
  type: 'browser' | 'ide' | 'cli';
  name: string;
  version: string;
  user_agent?: string;
  metadata?: Record<string, any>;
}

interface AnalyzeRequest {
  prompt: {
    content: string;
    format_type?: 'auto' | 'text' | 'markdown' | 'xml';
    language?: string;
  };
  client_info?: ClientInfo;
  save_result?: boolean;
}

interface AnalyzeResponse {
  analysis_id: string;
  prompt_id?: string;
  report: MetricReport;
  patches: Patch[];
  questions: ClarifyQuestion[];
  created_at: string;
  processing_time_ms: number;
  pipeline_version?: string;
}

interface ApiError {
  message: string;
  error_code: string;
  timestamp: string;
  path?: string;
  request_id?: string;
  details?: Record<string, any>;
}
```

```typescript
// browser-extension/src/api/client.ts
class CurestryApiClient {
  private config: ApiConfig;
  private clientInfo: ClientInfo;
  
  constructor(config: Partial<ApiConfig> = {}) {
    this.config = {
      baseURL: config.baseURL || 'http://localhost:8080',
      apiKey: config.apiKey,
      timeout: config.timeout || 60000, // 1 minute for analysis
      retries: config.retries || 2
    };
    
    this.clientInfo = {
      type: 'browser',
      name: 'chatgpt-extension',
      version: chrome.runtime.getManifest().version,
      user_agent: navigator.userAgent,
      metadata: {
        platform: navigator.platform,
        language: navigator.language,
        url: window.location.href
      }
    };
  }
  
  async analyze(prompt: string): Promise<AnalyzeResponse> {
    const request: AnalyzeRequest = {
      prompt: {
        content: prompt,
        format_type: 'auto'
      },
      client_info: this.clientInfo,
      save_result: true
    };
    
    return this.makeRequest<AnalyzeResponse>('/api/analyze', {
      method: 'POST',
      body: JSON.stringify(request)
    });
  }
  
  async getAnalysis(analysisId: string): Promise<AnalyzeResponse> {
    return this.makeRequest<AnalyzeResponse>(`/api/analyses/${analysisId}`);
  }
  
  async clarify(analysisId: string, answers: Array<{question_id: string, answer: string}>): Promise<any> {
    return this.makeRequest('/api/analyze/clarify', {
      method: 'POST',
      body: JSON.stringify({
        analysis_id: analysisId,
        answers: answers
      })
    });
  }
  
  async applyPatches(analysisId: string, patchIds: string[]): Promise<any> {
    return this.makeRequest('/api/analyze/apply', {
      method: 'POST',
      body: JSON.stringify({
        analysis_id: analysisId,
        patch_ids: patchIds
      })
    });
  }
  
  private async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.config.baseURL}${endpoint}`;
    
    const requestOptions: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` },
        ...options.headers
      }
    };
    
    let lastError: Error;
    
    // Retry logic
    for (let attempt = 0; attempt <= this.config.retries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);
        
        const response = await fetch(url, {
          ...requestOptions,
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
          const errorData: ApiError = await response.json().catch(() => ({
            message: `HTTP ${response.status}: ${response.statusText}`,
            error_code: 'HTTP_ERROR',
            timestamp: new Date().toISOString()
          }));
          
          throw new ApiRequestError(errorData, response.status);
        }
        
        return await response.json();
        
      } catch (error) {
        lastError = error;
        
        if (error.name === 'AbortError') {
          throw new ApiTimeoutError('Request timeout');
        }
        
        if (error instanceof ApiRequestError) {
          // Don't retry 4xx errors
          if (error.status >= 400 && error.status < 500) {
            throw error;
          }
        }
        
        // Retry with exponential backoff
        if (attempt < this.config.retries) {
          const delay = Math.pow(2, attempt) * 1000; // 1s, 2s, 4s
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    
    throw lastError;
  }
}

class ApiRequestError extends Error {
  constructor(public errorData: ApiError, public status: number) {
    super(errorData.message);
    this.name = 'ApiRequestError';
  }
}

class ApiTimeoutError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ApiTimeoutError';
  }
}

// Singleton instance
export const apiClient = new CurestryApiClient({
  baseURL: 'http://localhost:8080', // Will be configurable
  timeout: 60000,
  retries: 2
});
```

#### Subtask 3.1.2: Добавить экран ожидания ответа (минимальный лоадер) (2 часа)

```typescript
// browser-extension/src/components/LoadingSpinner.tsx
import React from 'react';

interface LoadingSpinnerProps {
  message?: string;
  subMessage?: string;
  showProgress?: boolean;
  progress?: number;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  message = "Analyzing prompt...",
  subMessage = "This may take up to 60 seconds",
  showProgress = false,
  progress = 0
}) => (
  <div className="curestry-loading-container">
    <div className="curestry-spinner">
      <div className="curestry-spinner-ring"></div>
      <div className="curestry-spinner-inner">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
        </svg>
      </div>
    </div>
    
    <div className="curestry-loading-text">
      <div className="curestry-loading-message">{message}</div>
      <div className="curestry-loading-submessage">{subMessage}</div>
      
      {showProgress && (
        <div className="curestry-progress-bar">
          <div 
            className="curestry-progress-fill" 
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </div>
  </div>
);

// Loading states hook
export const useLoadingStates = () => {
  const [isLoading, setIsLoading] = React.useState(false);
  const [loadingMessage, setLoadingMessage] = React.useState('');
  const [progress, setProgress] = React.useState(0);
  
  const startLoading = (message: string = 'Processing...') => {
    setIsLoading(true);
    setLoadingMessage(message);
    setProgress(0);
  };
  
  const updateProgress = (newProgress: number, message?: string) => {
    setProgress(newProgress);
    if (message) setLoadingMessage(message);
  };
  
  const stopLoading = () => {
    setIsLoading(false);
    setProgress(0);
  };
  
  return {
    isLoading,
    loadingMessage,
    progress,
    startLoading,
    updateProgress,
    stopLoading
  };
};
```

```css
/* browser-extension/src/styles/loading.css */
.curestry-loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  max-width: 300px;
  text-align: center;
}

.curestry-spinner {
  position: relative;
  width: 48px;
  height: 48px;
  margin-bottom: 16px;
}

.curestry-spinner-ring {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #007bff;
  border-radius: 50%;
  animation: curestry-spin 1s linear infinite;
}

.curestry-spinner-inner {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #007bff;
}

@keyframes curestry-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.curestry-loading-text {
  width: 100%;
}

.curestry-loading-message {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.curestry-loading-submessage {
  font-size: 12px;
  color: #666;
  margin-bottom: 16px;
}

.curestry-progress-bar {
  width: 100%;
  height: 4px;
  background: #f0f0f0;
  border-radius: 2px;
  overflow: hidden;
}

.curestry-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #007bff, #0056b3);
  transition: width 0.3s ease;
}
```

#### Subtask 3.1.3: Обработать 4xx/5xx с коротким сообщением в UI (2 часа)

```typescript
// browser-extension/src/components/ErrorDisplay.tsx
import React from 'react';

interface ErrorDisplayProps {
  error: ApiRequestError | ApiTimeoutError | Error;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ 
  error, 
  onRetry, 
  onDismiss 
}) => {
  const getErrorInfo = () => {
    if (error instanceof ApiTimeoutError) {
      return {
        title: 'Request Timeout',
        message: 'The analysis is taking longer than expected. Please try again.',
        type: 'timeout' as const,
        canRetry: true
      };
    }
    
    if (error instanceof ApiRequestError) {
      const { errorData, status } = error;
      
      if (status === 429) {
        return {
          title: 'Rate Limited',
          message: 'Too many requests. Please wait a moment and try again.',
          type: 'rate_limit' as const,
          canRetry: true
        };
      }
      
      if (status >= 500) {
        return {
          title: 'Service Error',
          message: 'Our analysis service is temporarily unavailable. Please try again.',
          type: 'server_error' as const,
          canRetry: true
        };
      }
      
      if (status === 400) {
        return {
          title: 'Invalid Input',
          message: 'Please check your prompt and try again.',
          type: 'client_error' as const,
          canRetry: false
        };
      }
      
      return {
        title: 'Analysis Error',
        message: errorData.message || 'Something went wrong with the analysis.',
        type: 'general' as const,
        canRetry: true
      };
    }
    
    return {
      title: 'Unexpected Error',
      message: 'An unexpected error occurred. Please try again.',
      type: 'unknown' as const,
      canRetry: true
    };
  };
  
  const errorInfo = getErrorInfo();
  
  return (
    <div className={`curestry-error-container curestry-error-${errorInfo.type}`}>
      <div className="curestry-error-icon">
        {errorInfo.type === 'timeout' && '⏱️'}
        {errorInfo.type === 'rate_limit' && '⚠️'}
        {errorInfo.type === 'server_error' && '🔧'}
        {errorInfo.type === 'client_error' && '❌'}
        {(errorInfo.type === 'general' || errorInfo.type === 'unknown') && '⚠️'}
      </div>
      
      <div className="curestry-error-content">
        <div className="curestry-error-title">{errorInfo.title}</div>
        <div className="curestry-error-message">{errorInfo.message}</div>
        
        {error instanceof ApiRequestError && error.errorData.request_id && (
          <div className="curestry-error-id">
            Request ID: {error.errorData.request_id}
          </div>
        )}
      </div>
      
      <div className="curestry-error-actions">
        {errorInfo.canRetry && onRetry && (
          <button 
            className="curestry-btn curestry-btn-primary"
            onClick={onRetry}
          >
            Try Again
          </button>
        )}
        
        {onDismiss && (
          <button 
            className="curestry-btn curestry-btn-secondary"
            onClick={onDismiss}
          >
            Dismiss
          </button>
        )}
      </div>
    </div>
  );
};

// Error boundary для ловли React ошибок
export class ErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback?: React.ComponentType<{ error: Error }> },
  { hasError: boolean; error?: Error }
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }
  
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }
  
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Curestry extension error:', error, errorInfo);
  }
  
  render() {
    if (this.state.hasError) {
      const FallbackComponent = this.props.fallback || DefaultErrorFallback;
      return <FallbackComponent error={this.state.error!} />;
    }
    
    return this.props.children;
  }
}

const DefaultErrorFallback: React.FC<{ error: Error }> = ({ error }) => (
  <div className="curestry-error-boundary">
    <h3>Something went wrong</h3>
    <p>The Curestry extension encountered an error.</p>
    <details>
      <summary>Error details</summary>
      <pre>{error.message}</pre>
    </details>
  </div>
);
```

### Task 3.2: Подключить контент-скрипт к полю ввода
**Priority**: 🔴 Critical  
**Estimated Time**: 2 дня  
**Assignee**: Frontend Developer  
**Dependencies**: Task 3.1

#### Subtask 3.2.1: Найти и обернуть input ChatGPT, отрисовать кнопку «Analyze» (6 часов)

```typescript
// browser-extension/src/content-scripts/chatgpt.ts
import { apiClient } from '../api/client';
import { AnalysisResults } from '../components/AnalysisResults';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorDisplay } from '../components/ErrorDisplay';

class ChatGPTIntegration {
  private analyzeButton: HTMLElement | null = null;
  private resultsContainer: HTMLElement | null = null;
  private currentAnalysis: any = null;
  private observer: MutationObserver | null = null;
  
  init() {
    console.log('🚀 Curestry: Initializing ChatGPT integration');
    this.setupObserver();
    this.insertAnalyzeButton();
    this.injectStyles();
  }
  
  private setupObserver() {
    this.observer = new MutationObserver((mutations) => {
      let shouldReinitialize = false;
      
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            const element = node as Element;
            
            // Check if new textarea was added
            if (element.matches('textarea') || element.querySelector('textarea')) {
              shouldReinitialize = true;
            }
            
            // Check if submit button area changed
            if (element.matches('[data-testid*="send"]') || 
                element.querySelector('[data-testid*="send"]')) {
              shouldReinitialize = true;
            }
          }
        });
      });
      
      if (shouldReinitialize) {
        this.insertAnalyzeButton();
      }
    });
    
    this.observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }
  
  private insertAnalyzeButton() {
    // Remove existing button if present
    if (this.analyzeButton && document.contains(this.analyzeButton)) {
      this.analyzeButton.remove();
    }
    
    const textarea = this.findTextarea();
    if (!textarea) {
      console.log('🔍 Curestry: Textarea not found, retrying...');
      setTimeout(() => this.insertAnalyzeButton(), 1000);
      return;
    }
    
    // Find the send button container
    const sendButton = this.findSendButton();
    if (!sendButton) {
      console.log('🔍 Curestry: Send button not found');
      return;
    }
    
    const container = sendButton.parentElement;
    if (!container || container.querySelector('.curestry-analyze-btn')) {
      return;
    }
    
    this.analyzeButton = this.createAnalyzeButton();
    container.insertBefore(this.analyzeButton, sendButton);
    
    console.log('✅ Curestry: Analyze button inserted');
  }
  
  private findTextarea(): HTMLTextAreaElement | null {
    // ChatGPT UI selectors (updated for latest UI)
    const selectors = [
      '#prompt-textarea',
      'textarea[data-id]',
      'textarea[placeholder*="Message"]',
      'textarea[placeholder*="Type a message"]',
      '.text-base.resize-none',
      'div[contenteditable="true"]', // Rich text editor
    ];
    
    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element) {
        if (element.tagName === 'TEXTAREA') {
          return element as HTMLTextAreaElement;
        }
        if (element.getAttribute('contenteditable') === 'true') {
          // Convert contenteditable div to work with our code
          return element as any;
        }
      }
    }
    
    return null;
  }
  
  private findSendButton(): HTMLElement | null {
    const selectors = [
      '[data-testid="send-button"]',
      'button[aria-label*="Send"]',
      'button[title*="Send"]',
      'svg[data-testid="send-button"] + ..',
      '.cursor-pointer[role="button"]' // Send button in new UI
    ];
    
    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element) return element as HTMLElement;
    }
    
    return null;
  }
  
  private createAnalyzeButton(): HTMLElement {
    const button = document.createElement('button');
    button.className = 'curestry-analyze-btn';
    button.setAttribute('aria-label', 'Analyze prompt with Curestry');
    button.innerHTML = `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
      </svg>
      <span>Analyze</span>
    `;
    
    button.addEventListener('click', this.handleAnalyzeClick.bind(this));
    
    return button;
  }
  
  private async handleAnalyzeClick(event: Event) {
    event.preventDefault();
    event.stopPropagation();
    
    const textarea = this.findTextarea();
    const prompt = this.getPromptText(textarea);
    
    if (!prompt || prompt.length < 10) {
      this.showMessage('Please enter a prompt to analyze (minimum 10 characters)', 'warning');
      return;
    }
    
    if (prompt.length > 50000) {
      this.showMessage('Prompt is too long (maximum 50,000 characters)', 'error');
      return;
    }
    
    await this.performAnalysis(prompt);
  }
  
  private getPromptText(element: HTMLElement | null): string {
    if (!element) return '';
    
    if (element.tagName === 'TEXTAREA') {
      return (element as HTMLTextAreaElement).value;
    }
    
    if (element.getAttribute('contenteditable') === 'true') {
      return element.innerText || element.textContent || '';
    }
    
    return '';
  }
  
  private async performAnalysis(prompt: string) {
    this.showLoadingState();
    
    try {
      console.log('📊 Curestry: Starting analysis...');
      
      const result = await apiClient.analyze(prompt);
      
      console.log('✅ Curestry: Analysis completed', result);
      this.currentAnalysis = result;
      this.showAnalysisResult(result);
      
    } catch (error) {
      console.error('❌ Curestry: Analysis failed', error);
      this.showErrorState(error);
    }
  }
  
  private showLoadingState() {
    this.hideResults();
    
    const loadingContainer = document.createElement('div');
    loadingContainer.className = 'curestry-loading-overlay';
    loadingContainer.innerHTML = `
      <div class="curestry-loading-content">
        <div class="curestry-spinner">
          <div class="curestry-spinner-ring"></div>
        </div>
        <div class="curestry-loading-text">
          <div>Analyzing prompt...</div>
          <div class="curestry-loading-subtext">This may take up to 60 seconds</div>
        </div>
      </div>
    `;
    
    this.showOverlay(loadingContainer);
  }
  
  private showAnalysisResult(result: any) {
    this.hideResults();
    
    const resultsContainer = document.createElement('div');
    resultsContainer.className = 'curestry-results-overlay';
    resultsContainer.innerHTML = this.buildResultsHTML(result);
    
    this.showOverlay(resultsContainer);
    this.attachResultsEventListeners(resultsContainer);
  }
  
  private showErrorState(error: Error) {
    this.hideResults();
    
    const errorContainer = document.createElement('div');
    errorContainer.className = 'curestry-error-overlay';
    errorContainer.innerHTML = this.buildErrorHTML(error);
    
    this.showOverlay(errorContainer);
    this.attachErrorEventListeners(errorContainer);
  }
  
  private showOverlay(content: HTMLElement) {
    // Remove existing overlay
    const existing = document.querySelector('.curestry-overlay');
    if (existing) existing.remove();
    
    const overlay = document.createElement('div');
    overlay.className = 'curestry-overlay';
    overlay.appendChild(content);
    
    // Close on background click
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        this.hideResults();
      }
    });
    
    document.body.appendChild(overlay);
    
    // Escape key to close
    const escapeHandler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        this.hideResults();
        document.removeEventListener('keydown', escapeHandler);
      }
    };
    
    document.addEventListener('keydown', escapeHandler);
  }
  
  private hideResults() {
    const overlay = document.querySelector('.curestry-overlay');
    if (overlay) overlay.remove();
  }
  
  private buildResultsHTML(result: any): string {
    const { report, patches, questions } = result;
    
    return `
      <div class="curestry-results-container">
        <div class="curestry-results-header">
          <h3>📊 Prompt Analysis Results</h3>
          <button class="curestry-close-btn" aria-label="Close">&times;</button>
        </div>
        
        <div class="curestry-results-content">
          <!-- Score Overview -->
          <div class="curestry-score-overview">
            <div class="curestry-score-main">
              <div class="curestry-score-value">${report.overall_score.toFixed(1)}</div>
              <div class="curestry-score-label">Overall Score</div>
            </div>
            <div class="curestry-score-details">
              <div class="curestry-score-item">
                <span>Judge Score:</span>
                <span>${report.judge_score.score.toFixed(1)}/10</span>
              </div>
              <div class="curestry-score-item">
                <span>Risk Level:</span>
                <span class="curestry-risk-${report.risk_level}">${report.risk_level.toUpperCase()}</span>
              </div>
              <div class="curestry-score-item">
                <span>Entropy:</span>
                <span>${report.semantic_entropy.entropy.toFixed(3)}</span>
              </div>
            </div>
          </div>
          
          <!-- Quick Stats -->
          <div class="curestry-quick-stats">
            <div class="curestry-stat">
              <div class="curestry-stat-value">${report.length_words}</div>
              <div class="curestry-stat-label">Words</div>
            </div>
            <div class="curestry-stat">
              <div class="curestry-stat-value">${patches.length}</div>
              <div class="curestry-stat-label">Improvements</div>
            </div>
            <div class="curestry-stat">
              <div class="curestry-stat-value">${questions.length}</div>
              <div class="curestry-stat-label">Questions</div>
            </div>
          </div>
          
          <!-- Actions -->
          <div class="curestry-actions">
            <button class="curestry-btn curestry-btn-primary" data-action="view-details">
              View Details
            </button>
            <button class="curestry-btn curestry-btn-secondary" data-action="apply-safe">
              Apply Safe Fixes
            </button>
            ${questions.length > 0 ? `
              <button class="curestry-btn curestry-btn-outline" data-action="clarify">
                Answer Questions (${questions.length})
              </button>
            ` : ''}
          </div>
        </div>
      </div>
    `;
  }
  
  private buildErrorHTML(error: Error): string {
    return `
      <div class="curestry-error-container">
        <div class="curestry-error-header">
          <h3>⚠️ Analysis Error</h3>
          <button class="curestry-close-btn" aria-label="Close">&times;</button>
        </div>
        
        <div class="curestry-error-content">
          <p>${error.message}</p>
          
          <div class="curestry-error-actions">
            <button class="curestry-btn curestry-btn-primary" data-action="retry">
              Try Again
            </button>
            <button class="curestry-btn curestry-btn-secondary" data-action="dismiss">
              Dismiss
            </button>
          </div>
        </div>
      </div>
    `;
  }
  
  private attachResultsEventListeners(container: HTMLElement) {
    // Close button
    const closeBtn = container.querySelector('.curestry-close-btn');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.hideResults());
    }
    
    // Action buttons
    container.addEventListener('click', (e) => {
      const target = e.target as HTMLElement;
      const action = target.getAttribute('data-action');
      
      switch (action) {
        case 'view-details':
          this.showDetailedResults();
          break;
        case 'apply-safe':
          this.applySafePatches();
          break;
        case 'clarify':
          this.showClarificationQuestions();
          break;
      }
    });
  }
  
  private attachErrorEventListeners(container: HTMLElement) {
    const closeBtn = container.querySelector('.curestry-close-btn');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.hideResults());
    }
    
    container.addEventListener('click', (e) => {
      const target = e.target as HTMLElement;
      const action = target.getAttribute('data-action');
      
      switch (action) {
        case 'retry':
          this.hideResults();
          const textarea = this.findTextarea();
          const prompt = this.getPromptText(textarea);
          if (prompt) this.performAnalysis(prompt);
          break;
        case 'dismiss':
          this.hideResults();
          break;
      }
    });
  }
  
  private showMessage(message: string, type: 'info' | 'warning' | 'error' = 'info') {
    const notification = document.createElement('div');
    notification.className = `curestry-notification curestry-notification-${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.remove();
    }, 5000);
  }
  
  private async applySafePatches() {
    if (!this.currentAnalysis) return;
    
    const safePatches = this.currentAnalysis.patches.filter((p: any) => p.type === 'safe');
    if (safePatches.length === 0) {
      this.showMessage('No safe patches available to apply', 'info');
      return;
    }
    
    try {
      this.showLoadingState();
      
      const result = await apiClient.applyPatches(
        this.currentAnalysis.analysis_id,
        safePatches.map((p: any) => p.id)
      );
      
      // Replace textarea content with improved prompt
      const textarea = this.findTextarea();
      if (textarea) {
        if (textarea.tagName === 'TEXTAREA') {
          (textarea as HTMLTextAreaElement).value = result.improved_prompt;
        } else if (textarea.getAttribute('contenteditable') === 'true') {
          textarea.innerHTML = result.improved_prompt;
        }
        
        // Trigger input event to notify ChatGPT of the change
        textarea.dispatchEvent(new Event('input', { bubbles: true }));
      }
      
      this.hideResults();
      this.showMessage(`Applied ${result.applied_patches.length} improvements`, 'info');
      
    } catch (error) {
      this.showErrorState(error);
    }
  }
  
  private showDetailedResults() {
    // Implementation for detailed results view
    console.log('📋 Curestry: Showing detailed results');
  }
  
  private showClarificationQuestions() {
    // Implementation for clarification questions
    console.log('❓ Curestry: Showing clarification questions');
  }
  
  private injectStyles() {
    if (document.getElementById('curestry-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'curestry-styles';
    style.textContent = `
      /* Analyze Button */
      .curestry-analyze-btn {
        display: flex !important;
        align-items: center !important;
        gap: 6px !important;
        padding: 8px 12px !important;
        margin-right: 8px !important;
        background: #007bff !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        z-index: 1000 !important;
      }
      
      .curestry-analyze-btn:hover {
        background: #0056b3 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 4px rgba(0, 123, 255, 0.3) !important;
      }
      
      .curestry-analyze-btn:active {
        transform: translateY(0) !important;
      }
      
      .curestry-analyze-btn svg {
        width: 16px !important;
        height: 16px !important;
      }
      
      /* Overlay Styles */
      .curestry-overlay {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        background: rgba(0, 0, 0, 0.5) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        z-index: 10000 !important;
        animation: curestryFadeIn 0.2s ease !important;
      }
      
      @keyframes curestryFadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
      }
      
      /* Results Container */
      .curestry-results-container,
      .curestry-error-container {
        background: white !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15) !important;
        max-width: 500px !important;
        width: 90vw !important;
        max-height: 80vh !important;
        overflow-y: auto !important;
        animation: curestrySlideIn 0.3s ease !important;
      }
      
      @keyframes curestrySlideIn {
        from { 
          opacity: 0;
          transform: translateY(-20px) scale(0.95);
        }
        to { 
          opacity: 1;
          transform: translateY(0) scale(1);
        }
      }
      
      .curestry-results-header,
      .curestry-error-header {
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        padding: 20px 24px 16px !important;
        border-bottom: 1px solid #eee !important;
      }
      
      .curestry-results-header h3,
      .curestry-error-header h3 {
        margin: 0 !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        color: #333 !important;
      }
      
      .curestry-close-btn {
        background: none !important;
        border: none !important;
        font-size: 24px !important;
        color: #666 !important;
        cursor: pointer !important;
        padding: 0 !important;
        width: 32px !important;
        height: 32px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border-radius: 4px !important;
      }
      
      .curestry-close-btn:hover {
        background: #f5f5f5 !important;
        color: #333 !important;
      }
      
      .curestry-results-content,
      .curestry-error-content {
        padding: 20px 24px 24px !important;
      }
      
      /* Score Overview */
      .curestry-score-overview {
        display: flex !important;
        align-items: center !important;
        gap: 20px !important;
        margin-bottom: 20px !important;
        padding: 16px !important;
        background: #f8f9fa !important;
        border-radius: 8px !important;
      }
      
      .curestry-score-main {
        text-align: center !important;
      }
      
      .curestry-score-value {
        font-size: 32px !important;
        font-weight: 700 !important;
        color: #007bff !important;
        line-height: 1 !important;
      }
      
      .curestry-score-label {
        font-size: 12px !important;
        color: #666 !important;
        margin-top: 4px !important;
      }
      
      .curestry-score-details {
        flex: 1 !important;
      }
      
      .curestry-score-item {
        display: flex !important;
        justify-content: space-between !important;
        margin-bottom: 8px !important;
        font-size: 14px !important;
      }
      
      .curestry-score-item:last-child {
        margin-bottom: 0 !important;
      }
      
      .curestry-risk-low { color: #28a745 !important; font-weight: 600 !important; }
      .curestry-risk-medium { color: #ffc107 !important; font-weight: 600 !important; }
      .curestry-risk-high { color: #fd7e14 !important; font-weight: 600 !important; }
      .curestry-risk-critical { color: #dc3545 !important; font-weight: 600 !important; }
      
      /* Quick Stats */
      .curestry-quick-stats {
        display: flex !important;
        justify-content: space-around !important;
        margin-bottom: 24px !important;
        padding: 16px 0 !important;
        border: 1px solid #eee !important;
        border-radius: 8px !important;
      }
      
      .curestry-stat {
        text-align: center !important;
      }
      
      .curestry-stat-value {
        font-size: 20px !important;
        font-weight: 600 !important;
        color: #333 !important;
      }
      
      .curestry-stat-label {
        font-size: 12px !important;
        color: #666 !important;
        margin-top: 4px !important;
      }
      
      /* Buttons */
      .curestry-actions {
        display: flex !important;
        flex-direction: column !important;
        gap: 8px !important;
      }
      
      .curestry-btn {
        padding: 12px 16px !important;
        border: none !important;
        border-radius: 6px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        text-align: center !important;
      }
      
      .curestry-btn-primary {
        background: #007bff !important;
        color: white !important;
      }
      
      .curestry-btn-primary:hover {
        background: #0056b3 !important;
      }
      
      .curestry-btn-secondary {
        background: #6c757d !important;
        color: white !important;
      }
      
      .curestry-btn-secondary:hover {
        background: #545b62 !important;
      }
      
      .curestry-btn-outline {
        background: transparent !important;
        color: #007bff !important;
        border: 1px solid #007bff !important;
      }
      
      .curestry-btn-outline:hover {
        background: #007bff !important;
        color: white !important;
      }
      
      /* Loading Spinner */
      .curestry-loading-content {
        background: white !important;
        padding: 40px !important;
        border-radius: 12px !important;
        text-align: center !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15) !important;
      }
      
      .curestry-spinner {
        width: 40px !important;
        height: 40px !important;
        margin: 0 auto 20px !important;
        position: relative !important;
      }
      
      .curestry-spinner-ring {
        width: 100% !important;
        height: 100% !important;
        border: 3px solid #f3f3f3 !important;
        border-top: 3px solid #007bff !important;
        border-radius: 50% !important;
        animation: curestrySpinnerRotate 1s linear infinite !important;
      }
      
      @keyframes curestrySpinnerRotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
      
      .curestry-loading-text {
        color: #333 !important;
        font-size: 16px !important;
        font-weight: 500 !important;
      }
      
      .curestry-loading-subtext {
        color: #666 !important;
        font-size: 12px !important;
        margin-top: 8px !important;
      }
      
      /* Notifications */
      .curestry-notification {
        position: fixed !important;
        top: 20px !important;
        right: 20px !important;
        padding: 12px 16px !important;
        border-radius: 6px !important;
        color: white !important;
        font-size: 14px !important;
        z-index: 10001 !important;
        animation: curestrySlideInRight 0.3s ease !important;
      }
      
      @keyframes curestrySlideInRight {
        from { 
          opacity: 0;
          transform: translateX(100%);
        }
        to { 
          opacity: 1;
          transform: translateX(0);
        }
      }
      
      .curestry-notification-info {
        background: #17a2b8 !important;
      }
      
      .curestry-notification-warning {
        background: #ffc107 !important;
        color: #333 !important;
      }
      
      .curestry-notification-error {
        background: #dc3545 !important;
      }
    `;
    
    document.head.appendChild(style);
  }
  
  destroy() {
    if (this.observer) {
      this.observer.disconnect();
    }
    
    if (this.analyzeButton) {
      this.analyzeButton.remove();
    }
    
    this.hideResults();
    
    const styles = document.getElementById('curestry-styles');
    if (styles) styles.remove();
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new ChatGPTIntegration().init();
  });
} else {
  new ChatGPTIntegration().init();
}

// Export for potential cleanup
(window as any).curestryIntegration = ChatGPTIntegration;
```

---

## Success Criteria и Timeline

### Phase 1 Complete When:
- ✅ Nginx reverse proxy routing /api → backend_public, / → frontend
- ✅ SSL certificates auto-generated for development
- ✅ Rate limiting implemented (2 req/s for /analyze, 10 req/s for /api)
- ✅ Gzip compression and static file caching enabled

### Phase 2 Complete When:
- ✅ Clean architecture with separated layers (infra/, domain/, api/, services/, orm/, dto/)
- ✅ Comprehensive API documentation with OpenAPI schemas
- ✅ Database persistence (prompts, analysis_results, events tables)
- ✅ Pipeline service integration with retries and error normalization
- ✅ Event logging for all analysis operations

### Phase 3 Complete When:
- ✅ Browser extension HTTP client with timeout/retry logic
- ✅ ChatGPT textarea detection and analyze button integration
- ✅ Loading states and error handling with user-friendly messages
- ✅ Analysis results display with score overview and action buttons

### Phase 4 Complete When:
- ✅ Admin API endpoints (/analyses, /timeseries, /models)
- ✅ Basic admin UI (table, charts, analysis cards)
- ✅ API key management with encryption and masking

## Timeline Summary

**Week 1:**
- Days 1-3: Phase 1 (Nginx setup)
- Days 4-7: Phase 2 начало (Architecture, API)

**Week 2:**
- Days 1-4: Phase 2 завершение (Database, Pipeline)
- Days 5-7: Phase 3 (Browser extension)

**Week 3:**
- Days 1-5: Phase 4 (Admin panel)
- Days 6-7: Testing и cleanup

**Total Estimated Time**: 18-21 дней  
**Team Size**: 1 Backend + 1 Frontend + 1 DevOps  
**Status**: Ready for Implementation

---

**Created**: 2025-08-17  
**Version**: 2.0 (согласно реальному roadmap)  
**Status**: Готово к реализации