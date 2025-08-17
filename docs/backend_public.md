# Backend_public Implementation Plan

Этот документ описывает план реализации backend_public как основного API-прокси для системы анализа промптов, согласно roadmap проекта.

## Обзор Архитектуры

### Роль backend_public в общей системе
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Browser Ext   │    │  backend_public │    │   Pipeline      │
│   IDE Clients   │────│   (API Proxy)   │────│   Service       │
│   CLI Tools     │    │   Port 8080     │    │   Port 8000     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                        │
         │              ┌─────────────────┐               │
         └──────────────│     Nginx       │───────────────┘
                        │  Reverse Proxy  │
                        │   Port 80/443   │
                        └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │   + Events DB   │
                    └─────────────────┘
```

**backend_public** является центральным API-прокси, который:
- Предоставляет стабильный REST API для всех клиентов
- Управляет аутентификацией и авторизацией
- Сохраняет результаты анализа и события
- Проксирует запросы к pipeline service
- Обслуживает админку и аналитику

## Фаза 1: Реверс-прокси (Задачи 1.1-1.2)

### 1.1 Настройка Nginx с TLS и маршрутизацией

#### 1.1.1 Поднять Nginx в compose и настроить маршрутизацию
```yaml
# infra/nginx/nginx.conf
server {
    listen 80;
    server_name localhost;

    # Frontend routes
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # API routes → backend_public
    location /api/ {
        proxy_pass http://backend_public:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Admin panel API
    location /admin/ {
        proxy_pass http://backend_public:8080/admin/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 1.1.2 Автогенерация сертификатов (dev self-signed)
```yaml
# docker-compose.yml - добавить nginx service
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./infra/nginx/nginx.conf:/etc/nginx/conf.d/default.conf
    - ./infra/nginx/ssl:/etc/nginx/ssl
  depends_on:
    - backend_public
    - frontend
  command: |
    sh -c "
    # Generate self-signed cert for development
    mkdir -p /etc/nginx/ssl &&
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
      -keyout /etc/nginx/ssl/nginx.key \
      -out /etc/nginx/ssl/nginx.crt \
      -subj '/CN=localhost' &&
    nginx -g 'daemon off;'
    "
```

### 1.2 Базовые оптимизации

#### 1.2.1 Rate limiting по IP/маршрутам
```nginx
# nginx.conf - добавить rate limiting
http {
    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=analyze:10m rate=2r/s;

    server {
        # API rate limiting
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend_public:8080/;
        }

        # Strict limiting for analyze endpoint
        location /api/analyze {
            limit_req zone=analyze burst=5 nodelay;
            proxy_pass http://backend_public:8080/analyze;
        }
    }
}
```

#### 1.2.2 Gzip и кэш статики
```nginx
# nginx.conf - оптимизации
server {
    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    # Static files caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API responses - no cache
    location /api/ {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        proxy_pass http://backend_public:8080/;
    }
}
```

## Фаза 2: Бэкенд-прокси (MVP REST) (Задачи 2.1-2.4)

### 2.1 Разделение слоев и заготовки

#### 2.1.1 Создать app_factory() и точку входа uvicorn
```python
# backend_public/app/factory.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .api import analysis, admin, auth
from .middleware import error_handler, logging_middleware

def create_app() -> FastAPI:
    """Application factory pattern"""
    app = FastAPI(
        title="Curestry API Proxy",
        description="AI Prompt Analysis API Gateway",
        version="1.0.0",
        docs_url="/docs" if settings.is_development else None,
    )

    # Middleware
    app.add_middleware(CORSMiddleware, allow_origins=["*"])
    app.add_middleware(error_handler)
    app.add_middleware(logging_middleware)

    # Routers
    app.include_router(analysis.router, prefix="/api")
    app.include_router(admin.router, prefix="/admin")
    app.include_router(auth.router, prefix="/auth")

    return app

# backend_public/main.py
from app.factory import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
```

#### 2.1.2 Разнести код по слоям
```
backend_public/
├── app/
│   ├── factory.py           # Application factory
│   ├── infra/               # Infrastructure layer
│   │   ├── database.py      # Database connections
│   │   ├── pipeline_client.py # HTTP client to pipeline
│   │   └── cache.py         # Redis/memory cache
│   ├── domain/              # Domain layer
│   │   ├── models.py        # Domain models
│   │   ├── events.py        # Domain events
│   │   └── services.py      # Domain services
│   ├── api/                 # API layer
│   │   ├── analysis.py      # Analysis endpoints
│   │   ├── admin.py         # Admin endpoints
│   │   └── auth.py          # Auth endpoints
│   ├── services/            # Application services
│   │   ├── analysis_service.py
│   │   ├── admin_service.py
│   │   └── auth_service.py
│   ├── orm/                 # ORM layer
│   │   ├── models.py        # SQLModel definitions
│   │   └── repositories.py  # Data access
│   └── dto/                 # Data Transfer Objects
│       ├── requests.py      # Request DTOs
│       ├── responses.py     # Response DTOs
│       └── common.py        # Common DTOs
```

#### 2.1.3 Общие модели ошибок и Result-тип
```python
# app/dto/common.py
from typing import Generic, TypeVar, Optional, Union
from pydantic import BaseModel

T = TypeVar('T')

class Result(BaseModel, Generic[T]):
    """Result type for handling success/error states"""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    error_code: Optional[str] = None

    @classmethod
    def success(cls, data: T) -> "Result[T]":
        return cls(success=True, data=data)

    @classmethod
    def error(cls, message: str, code: str = "GENERIC_ERROR") -> "Result[T]":
        return cls(success=False, error=message, error_code=code)

class ErrorResponse(BaseModel):
    """Standard error response format"""
    message: str
    error_code: str
    timestamp: str
    path: Optional[str] = None
    request_id: Optional[str] = None
```

### 2.2 Описать контракты и стабилизировать API

#### 2.2.1 Описать OpenAPI для основных endpoints
```python
# app/api/analysis.py
from fastapi import APIRouter, Depends, HTTPException
from ..dto.requests import AnalyzeRequest, ClarifyRequest, ApplyRequest
from ..dto.responses import AnalyzeResponse, ClarifyResponse, ApplyResponse
from ..services.analysis_service import AnalysisService

router = APIRouter(tags=["analysis"])

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_prompt(
    request: AnalyzeRequest,
    service: AnalysisService = Depends()
) -> AnalyzeResponse:
    """
    Analyze prompt for quality, consistency, and improvement opportunities.

    - **prompt**: Text content to analyze (1-50000 chars)
    - **format_type**: auto|text|markdown|xml
    - **client_info**: Browser extension or IDE client info

    Returns analysis with metrics, patches, and clarification questions.
    """
    result = await service.analyze_prompt(request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return result.data

@router.post("/analyze/clarify", response_model=ClarifyResponse)
async def clarify_analysis(
    request: ClarifyRequest,
    service: AnalysisService = Depends()
) -> ClarifyResponse:
    """Process clarification answers and update analysis."""
    pass

@router.post("/analyze/apply", response_model=ApplyResponse)
async def apply_patches(
    request: ApplyRequest,
    service: AnalysisService = Depends()
) -> ApplyResponse:
    """Apply selected improvement patches to prompt."""
    pass

@router.get("/export/{analysis_id}")
async def export_analysis(
    analysis_id: str,
    format: str = "md"  # md|xml|json
):
    """Export analysis results in specified format."""
    pass
```

#### 2.2.2 Ввести DTO: Prompt, MetricReport, JudgeScore, RiskLevel, Patch
```python
# app/dto/requests.py
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

class PromptDto(BaseModel):
    content: str = Field(..., min_length=1, max_length=50000)
    format_type: Literal["auto", "text", "markdown", "xml"] = "auto"
    language: Optional[str] = "auto"

class ClientInfo(BaseModel):
    type: Literal["browser", "ide", "cli"] = "browser"
    name: str = Field(..., examples=["chrome-extension", "cursor", "claude-code"])
    version: str = "1.0.0"
    user_agent: Optional[str] = None

class AnalyzeRequest(BaseModel):
    prompt: PromptDto
    client_info: Optional[ClientInfo] = None
    save_result: bool = True

# app/dto/responses.py
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class JudgeScore(BaseModel):
    score: float = Field(..., ge=0, le=10)
    rationale: str
    criteria_scores: dict = Field(default_factory=dict)

class MetricReport(BaseModel):
    overall_score: float = Field(..., ge=0, le=10)
    judge_score: JudgeScore
    semantic_entropy: float
    complexity_score: float
    length_words: int
    length_chars: int
    risk_level: RiskLevel
    contradictions: List[str] = Field(default_factory=list)

class Patch(BaseModel):
    id: str
    type: Literal["safe", "risky"] = "safe"
    category: str  # "clarity", "structure", "specificity", etc.
    description: str
    original_text: Optional[str] = None
    suggested_text: Optional[str] = None
    rationale: str
    risk_level: RiskLevel = RiskLevel.LOW

class AnalyzeResponse(BaseModel):
    analysis_id: str
    prompt_id: Optional[str] = None
    report: MetricReport
    patches: List[Patch] = Field(default_factory=list)
    questions: List[dict] = Field(default_factory=list)
    created_at: datetime
    processing_time_ms: int
```

### 2.3 Подключить хранилище результатов

#### 2.3.1 ORM/миграции, таблицы prompts, analysis_results, events
```python
# app/orm/models.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
import uuid

class Prompt(SQLModel, table=True):
    __tablename__ = "prompts"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    content: str = Field(..., max_length=50000)
    format_type: str = Field(default="auto")
    language: str = Field(default="auto")
    client_type: Optional[str] = None
    client_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    analyses: List["AnalysisResult"] = Relationship(back_populates="prompt")

class AnalysisResult(SQLModel, table=True):
    __tablename__ = "analysis_results"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    prompt_id: str = Field(foreign_key="prompts.id")

    # Analysis metrics
    overall_score: float
    judge_score: float
    semantic_entropy: float
    complexity_score: float
    length_words: int
    length_chars: int
    risk_level: str

    # JSON fields
    judge_details: dict = Field(default_factory=dict, sa_column_kwargs={"type_": JSON})
    contradictions: List[str] = Field(default_factory=list, sa_column_kwargs={"type_": JSON})
    patches: List[dict] = Field(default_factory=list, sa_column_kwargs={"type_": JSON})
    questions: List[dict] = Field(default_factory=list, sa_column_kwargs={"type_": JSON})

    # Metadata
    processing_time_ms: int
    pipeline_version: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    prompt: Prompt = Relationship(back_populates="analyses")
    events: List["AnalysisEvent"] = Relationship(back_populates="analysis")

class AnalysisEvent(SQLModel, table=True):
    __tablename__ = "analysis_events"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    analysis_id: str = Field(foreign_key="analysis_results.id")
    event_type: str  # "analyze_started", "analyze_completed", "clarify_requested", etc.
    event_data: dict = Field(default_factory=dict, sa_column_kwargs={"type_": JSON})
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    analysis: AnalysisResult = Relationship(back_populates="events")
```

#### 2.3.2 Сохранить результат анализа и выдать analysis_id
```python
# app/services/analysis_service.py
from ..orm.models import Prompt, AnalysisResult, AnalysisEvent
from ..infra.pipeline_client import PipelineClient
from ..dto.requests import AnalyzeRequest
from ..dto.responses import AnalyzeResponse, Result

class AnalysisService:
    def __init__(self,
                 db: AsyncSession,
                 pipeline_client: PipelineClient,
                 event_logger: EventLogger):
        self.db = db
        self.pipeline_client = pipeline_client
        self.event_logger = event_logger

    async def analyze_prompt(self, request: AnalyzeRequest) -> Result[AnalyzeResponse]:
        """Main analysis flow with persistence"""

        # 1. Save prompt
        prompt = Prompt(
            content=request.prompt.content,
            format_type=request.prompt.format_type,
            language=request.prompt.language,
            client_type=request.client_info.type if request.client_info else None,
            client_name=request.client_info.name if request.client_info else None
        )
        self.db.add(prompt)
        await self.db.commit()

        # 2. Log analysis started
        await self.event_logger.log_event(
            analysis_id=None,  # Will be set after analysis
            event_type="analyze_started",
            event_data={"prompt_id": prompt.id, "client_info": request.client_info}
        )

        try:
            # 3. Call pipeline service
            start_time = datetime.utcnow()
            pipeline_response = await self.pipeline_client.analyze(
                prompt=request.prompt.content,
                format_type=request.prompt.format_type
            )
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # 4. Save analysis result
            analysis = AnalysisResult(
                prompt_id=prompt.id,
                overall_score=pipeline_response["report"]["overall_score"],
                judge_score=pipeline_response["report"]["judge_score"]["score"],
                semantic_entropy=pipeline_response["report"]["semantic_entropy"]["entropy"],
                complexity_score=pipeline_response["report"]["complexity_score"],
                length_words=pipeline_response["report"]["length_words"],
                length_chars=pipeline_response["report"]["length_chars"],
                risk_level=self._calculate_risk_level(pipeline_response["report"]),
                judge_details=pipeline_response["report"]["judge_score"],
                contradictions=pipeline_response["report"]["contradictions"],
                patches=pipeline_response["patches"],
                questions=pipeline_response["questions"],
                processing_time_ms=int(processing_time),
                pipeline_version=pipeline_response.get("version", "1.0.0")
            )
            self.db.add(analysis)
            await self.db.commit()

            # 5. Log analysis completed
            await self.event_logger.log_event(
                analysis_id=analysis.id,
                event_type="analyze_completed",
                event_data={
                    "overall_score": analysis.overall_score,
                    "processing_time_ms": analysis.processing_time_ms
                }
            )

            # 6. Build response
            response = AnalyzeResponse(
                analysis_id=analysis.id,
                prompt_id=prompt.id,
                report=MetricReport(**pipeline_response["report"]),
                patches=[Patch(**patch) for patch in pipeline_response["patches"]],
                questions=pipeline_response["questions"],
                created_at=analysis.created_at,
                processing_time_ms=analysis.processing_time_ms
            )

            return Result.success(response)

        except Exception as e:
            await self.event_logger.log_event(
                analysis_id=None,
                event_type="analyze_failed",
                event_data={"error": str(e), "prompt_id": prompt.id}
            )
            return Result.error(f"Analysis failed: {str(e)}", "ANALYSIS_ERROR")
```

### 2.4 Соединить прокси с внешними сервисами

#### 2.4.1 Прокинуть вызовы в сервис пайплайна с таймаутами/ретраями
```python
# app/infra/pipeline_client.py
import httpx
import asyncio
from typing import Dict, Any, Optional
from ..config import settings

class PipelineClient:
    def __init__(self):
        self.base_url = settings.pipeline_service_url  # http://backend:8000
        self.timeout = httpx.Timeout(
            connect=5.0,  # Connection timeout
            read=60.0,    # Read timeout for analysis
            write=10.0,   # Write timeout
            pool=5.0      # Pool timeout
        )
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )

    async def analyze(self, prompt: str, format_type: str = "auto") -> Dict[str, Any]:
        """Call pipeline /analyze endpoint with retries"""
        payload = {
            "prompt": {
                "content": prompt,
                "format_type": format_type
            }
        }

        for attempt in range(3):  # 3 retry attempts
            try:
                response = await self.client.post(
                    f"{self.base_url}/analyze/",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                return response.json()

            except httpx.TimeoutException:
                if attempt == 2:  # Last attempt
                    raise PipelineTimeoutError("Pipeline service timeout after 3 attempts")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500 and attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise PipelineHTTPError(f"Pipeline HTTP error: {e.response.status_code}")

            except Exception as e:
                if attempt == 2:
                    raise PipelineConnectionError(f"Pipeline connection error: {str(e)}")
                await asyncio.sleep(2 ** attempt)

    async def clarify(self, analysis_id: str, answers: List[Dict]) -> Dict[str, Any]:
        """Call pipeline /analyze/clarify endpoint"""
        payload = {
            "prompt_id": analysis_id,
            "answers": answers
        }
        # Similar retry logic...

    async def apply_patches(self, analysis_id: str, patch_ids: List[str]) -> Dict[str, Any]:
        """Call pipeline /analyze/apply endpoint"""
        payload = {
            "prompt_id": analysis_id,
            "patch_ids": patch_ids
        }
        # Similar retry logic...

# Custom exceptions
class PipelineError(Exception):
    pass

class PipelineTimeoutError(PipelineError):
    pass

class PipelineHTTPError(PipelineError):
    pass

class PipelineConnectionError(PipelineError):
    pass
```

#### 2.4.2 Нормализовать ошибки пайплайна в единый формат API
```python
# app/middleware/error_handler.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from ..infra.pipeline_client import PipelineError, PipelineTimeoutError
from ..dto.common import ErrorResponse
from datetime import datetime

async def error_handling_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except PipelineTimeoutError as e:
        return JSONResponse(
            status_code=504,
            content=ErrorResponse(
                message="Analysis service temporarily unavailable. Please try again.",
                error_code="PIPELINE_TIMEOUT",
                timestamp=datetime.utcnow().isoformat(),
                path=str(request.url.path)
            ).model_dump()
        )
    except PipelineError as e:
        return JSONResponse(
            status_code=502,
            content=ErrorResponse(
                message="Analysis service error. Please contact support if this persists.",
                error_code="PIPELINE_ERROR",
                timestamp=datetime.utcnow().isoformat(),
                path=str(request.url.path)
            ).model_dump()
        )
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=ErrorResponse(
                message=e.detail,
                error_code="HTTP_ERROR",
                timestamp=datetime.utcnow().isoformat(),
                path=str(request.url.path)
            ).model_dump()
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                message="Internal server error",
                error_code="INTERNAL_ERROR",
                timestamp=datetime.utcnow().isoformat(),
                path=str(request.url.path)
            ).model_dump()
        )
```

## Фаза 3: Браузерное расширение (Задачи 3.1-3.2)

### 3.1 HTTP-клиент и конфиг для расширения

#### 3.1.1 Типизированный клиент (baseURL, API-key, таймауты)
```typescript
// browser-extension/src/api/client.ts
interface ApiConfig {
  baseURL: string;
  apiKey?: string;
  timeout: number;
}

class CurestryApiClient {
  private config: ApiConfig;

  constructor(config: Partial<ApiConfig> = {}) {
    this.config = {
      baseURL: config.baseURL || 'http://localhost:8080',
      apiKey: config.apiKey,
      timeout: config.timeout || 30000
    };
  }

  async analyze(prompt: string, clientInfo: ClientInfo): Promise<AnalyzeResponse> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

    try {
      const response = await fetch(`${this.config.baseURL}/api/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` })
        },
        body: JSON.stringify({
          prompt: { content: prompt, format_type: 'auto' },
          client_info: clientInfo
        }),
        signal: controller.signal
      });

      if (!response.ok) {
        throw new ApiError(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } finally {
      clearTimeout(timeoutId);
    }
  }
}

export const apiClient = new CurestryApiClient();
```

#### 3.1.2 Экран ожидания ответа (минимальный лоадер)
```typescript
// browser-extension/src/components/LoadingSpinner.tsx
export const LoadingSpinner: React.FC<{ message?: string }> = ({
  message = "Analyzing prompt..."
}) => (
  <div className="loading-container">
    <div className="spinner"></div>
    <p>{message}</p>
    <small>This may take up to 30 seconds</small>
  </div>
);

// CSS
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  text-align: center;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
```

### 3.2 Подключение контент-скрипта к полю ввода

#### 3.2.1 Найти и обернуть input ChatGPT, отрисовать кнопку «Analyze»
```typescript
// browser-extension/src/content-scripts/chatgpt.ts
class ChatGPTIntegration {
  private analyzeButton: HTMLElement | null = null;

  init() {
    this.observeDOM();
    this.insertAnalyzeButton();
  }

  private observeDOM() {
    const observer = new MutationObserver(() => {
      if (!this.analyzeButton || !document.contains(this.analyzeButton)) {
        this.insertAnalyzeButton();
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  private insertAnalyzeButton() {
    // ChatGPT input selectors (may change with updates)
    const inputSelectors = [
      'textarea[data-id]',
      'textarea[placeholder*="Message"]',
      '#prompt-textarea',
      '.text-base.resize-none'
    ];

    const textarea = this.findTextarea(inputSelectors);
    if (!textarea) return;

    const container = textarea.closest('[data-testid="send-button-container"]')
                   || textarea.parentElement;

    if (!container || container.querySelector('.curestry-analyze-btn')) return;

    this.analyzeButton = this.createAnalyzeButton();
    container.appendChild(this.analyzeButton);
  }

  private findTextarea(selectors: string[]): HTMLTextAreaElement | null {
    for (const selector of selectors) {
      const element = document.querySelector(selector) as HTMLTextAreaElement;
      if (element) return element;
    }
    return null;
  }

  private createAnalyzeButton(): HTMLElement {
    const button = document.createElement('button');
    button.className = 'curestry-analyze-btn';
    button.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
        <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
      </svg>
      Analyze
    `;
    button.onclick = this.handleAnalyzeClick.bind(this);
    return button;
  }

  private async handleAnalyzeClick() {
    const textarea = this.findTextarea([/* selectors */]);
    const prompt = textarea?.value.trim();

    if (!prompt) {
      this.showMessage('Please enter a prompt to analyze', 'warning');
      return;
    }

    this.showLoadingState();

    try {
      const result = await apiClient.analyze(prompt, {
        type: 'browser',
        name: 'chatgpt-extension',
        version: '1.0.0',
        user_agent: navigator.userAgent
      });

      this.showAnalysisResult(result);

    } catch (error) {
      this.showMessage(
        error instanceof ApiError ? error.message : 'Analysis failed. Please try again.',
        'error'
      );
    } finally {
      this.hideLoadingState();
    }
  }
}

new ChatGPTIntegration().init();
```

## Фаза 4: Админка (задачи 6.1-6.3)

### 6.1 API для агрегатов

#### 6.1.1 GET /analyses с фильтрами дата/клиент/модель
```python
# app/api/admin.py
@router.get("/analyses", response_model=AnalysesListResponse)
async def list_analyses(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    client_type: Optional[str] = None,
    client_name: Optional[str] = None,
    risk_level: Optional[RiskLevel] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    page: int = 1,
    limit: int = 50,
    session: AsyncSession = Depends(get_async_session)
):
    """List analyses with filtering and pagination"""
    query = select(AnalysisResult).join(Prompt)

    # Apply filters
    if date_from:
        query = query.where(AnalysisResult.created_at >= date_from)
    if date_to:
        query = query.where(AnalysisResult.created_at <= date_to)
    if client_type:
        query = query.where(Prompt.client_type == client_type)
    if client_name:
        query = query.where(Prompt.client_name == client_name)
    if risk_level:
        query = query.where(AnalysisResult.risk_level == risk_level)
    if min_score:
        query = query.where(AnalysisResult.overall_score >= min_score)
    if max_score:
        query = query.where(AnalysisResult.overall_score <= max_score)

    # Pagination
    total_query = select(func.count(AnalysisResult.id)).select_from(query.subquery())
    total = await session.execute(total_query)
    total_count = total.scalar()

    query = query.offset((page - 1) * limit).limit(limit)
    query = query.order_by(AnalysisResult.created_at.desc())

    result = await session.execute(query)
    analyses = result.scalars().all()

    return AnalysesListResponse(
        analyses=[AnalysisSummary.from_orm(a) for a in analyses],
        total=total_count,
        page=page,
        limit=limit,
        pages=math.ceil(total_count / limit)
    )
```

## Предстоящие фазы (краткий обзор)

### Фаза 5: Расширенный пайплайн (Задачи 5.1-5.4)
- Улучшение детекции галлюцинаций (цель >50% recall)
- Добавление новых детекторов: source-need, границы знаний, конфликты
- Калибровка порогов и self-consistency

### Фаза 6: IDE-клиенты (Задачи 7.1-7.3)
- Поддержка Cursor, VS Code Copilot, Windsurf
- Сканирование проектных промптов (.md, .mdc files)
- Анализ конфликтов и дублей

### Фаза 7: CLI-инструменты (Задачи 10.1-10.2)
- Shims для claude-code, gemini, cursor-cli
- Установщик в PATH с YAML конфигом
- --scan режим для каталогов промптов

### Фаза 8: Enterprise-функции (Задачи 8.1-8.3, 9.1-9.2)
- Проектная энтропия и метрики по репозиторию
- Совместимость с кукбуками провайдеров (OpenAI/Gemini/Claude/Grok)
- Time-series аналитика и алертинг

## Техническая архитектура - финальное состояние

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Browser Ext   │    │     Nginx       │    │   Pipeline      │
│   IDE Clients   │────│  (Port 80/443)  │────│   Service       │
│   CLI Tools     │    │   Rate Limit    │    │   (Enhanced)    │
└─────────────────┘    │   TLS/Gzip      │    └─────────────────┘
                       └─────────────────┘             │
                                │                       │
                    ┌─────────────────┐    ┌─────────────────┐
                    │ backend_public  │    │   PostgreSQL    │
                    │  (API Gateway)  │────│  + Events DB    │
                    │   Port 8080     │    │  + Analytics    │
                    └─────────────────┘    └─────────────────┘
                                │
                    ┌─────────────────┐
                    │    Admin UI     │
                    │ (Next.js SPA)   │
                    │   Port 3000     │
                    └─────────────────┘
```

## Итоги реализации

По завершении всех фаз backend_public станет:

1. **API Gateway** - Стабильный REST API для всех клиентов
2. **Authentication Hub** - JWT-авторизация и управление ключами
3. **Data Persistence Layer** - Сохранение анализов, событий, метрик
4. **Analytics Engine** - Агрегация данных для админки и дашбордов
5. **Monitoring & Observability** - Логирование, метрики, алертинг

Архитектура обеспечит:
- **Scalability** - Горизонтальное масштабирование через nginx
- **Reliability** - Таймауты, ретраи, circuit breakers
- **Security** - Rate limiting, TLS, input validation
- **Observability** - Структурированные логи, метрики, трейсинг
- **Maintainability** - Четкое разделение слоев, типизация, тесты

---

**Создано**: 2025-08-17
**Версия**: 1.0 (согласно roadmap)
**Статус**: Готово к реализации
