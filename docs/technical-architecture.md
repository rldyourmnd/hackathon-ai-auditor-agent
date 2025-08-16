# Technical Architecture

## Overview

Curestry is an AI-powered prompt analysis and improvement system designed to help users optimize LLM prompts through automated analysis, intelligent patch generation, and interactive refinement. The system follows a microservices architecture with clear separation between analysis pipeline, data persistence, and user interface layers.

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   External      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   Services      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Client      │    │   PostgreSQL    │    │  LLM Providers  │
│   State Mgmt    │    │   Database      │    │ (OpenAI/Claude) │
│   (Zustand)     │    │                 │    └─────────────────┘
└─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │     Redis       │
                       │   (Optional)    │
                       └─────────────────┘
```

## Core Components

### 1. Analysis Pipeline (LangGraph)

The heart of the system is a LangGraph-based analysis pipeline that processes prompts through multiple analysis nodes:

```
Input Prompt
     │
     ▼
┌─────────────────┐
│ Language        │
│ Detection       │ → maybe_translate_to_en
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ Format          │
│ Validation      │ → lint_markup
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ Vocabulary      │
│ Analysis        │ → vocab_unify
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ Contradiction   │
│ Detection       │ → find_contradictions
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ Semantic        │
│ Entropy         │ → semantic_entropy
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ LLM Judge       │
│ Scoring         │ → judge_score
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ Patch           │
│ Generation      │ → propose_patches
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ Question        │
│ Generation      │ → build_questions
└─────────────────┘
     │
     ▼
Analysis Report + Patches + Questions
```

### 2. Backend Services

#### API Layer (`app/api/routers/`)
- **Analysis Router**: Core analysis endpoints
- **Prompt-base Router**: Knowledge base management
- **Export Router**: Report and prompt export functionality

#### Business Logic (`app/services/`)
- **LLM Service**: Multi-provider adapter (OpenAI, Anthropic)
- **Embeddings Service**: Vector embeddings for semantic analysis
- **Pipeline Service**: LangGraph orchestration

#### Data Layer (`app/models/`)
- **Prompt Models**: Core prompt entities
- **Analysis Models**: Metrics and reports
- **Relation Models**: Inter-prompt relationships

### 3. Frontend Architecture

#### Page Structure (App Router)
```
app/
├── page.tsx              # Landing/upload page
├── analyze/
│   └── [id]/page.tsx     # Analysis results
├── prompt-base/
│   └── page.tsx          # Knowledge base management
└── export/
    └── [id]/page.tsx     # Export interface
```

#### Component Architecture
```
┌─────────────────────────────────────────────────────┐
│                 Layout                              │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   Editor    │  │   Metrics   │  │   Patches   │  │
│  │   Panel     │  │  Dashboard  │  │    Panel    │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ Questions   │  │   Export    │  │   Actions   │  │
│  │   Block     │  │  Controls   │  │    Bar      │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Analysis Flow
```
User Upload → API Gateway → Pipeline Orchestrator → Analysis Nodes → Database → Frontend
```

### 2. Patch Application Flow
```
Frontend Selection → API Validation → Safe/Risky Classification → Application → Updated Prompt
```

### 3. Clarification Flow
```
Generated Questions → User Answers → Context Enrichment → Re-analysis → Updated Report
```

## Security Architecture

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (User, Admin)
- API key management for LLM providers

### Data Protection
- Input sanitization and validation
- Prompt data encryption at rest
- Rate limiting and abuse prevention
- CORS configuration for frontend

### Privacy Considerations
- Optional prompt anonymization
- Configurable data retention policies
- User consent management

## Scalability Design

### Horizontal Scaling
- Stateless API design
- Redis-based session management
- Database connection pooling
- LLM provider load balancing

### Performance Optimization
- Async/await throughout pipeline
- Streaming responses for large analyses
- Caching layers for embeddings and results
- Background job processing

### Monitoring & Observability
- Health check endpoints
- Structured logging
- Metrics collection (Prometheus)
- Distributed tracing (OpenTelemetry)

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 15+ with SQLAlchemy 2.0
- **Cache**: Redis 7+
- **Migration**: Alembic
- **Validation**: Pydantic v2
- **Pipeline**: LangGraph
- **LLM**: OpenAI GPT-4, Anthropic Claude

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS + shadcn/ui
- **State**: Zustand
- **Editor**: Monaco Editor
- **Charts**: Recharts

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Reverse Proxy**: Nginx
- **Process Management**: PM2 (production)
- **CI/CD**: GitHub Actions

## Development Principles

### Code Quality
- Type safety (TypeScript, Pydantic)
- Comprehensive testing strategy
- Pre-commit hooks (ruff, eslint, prettier)
- Code review requirements

### API Design
- RESTful conventions
- OpenAPI/Swagger documentation
- Consistent error handling
- Versioning strategy

### Database Design
- Normalized schema with proper relationships
- Migration-first development
- Connection pooling and optimization
- Backup and recovery procedures
