# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Curestry is an AI-powered prompt analysis and improvement system built with FastAPI backend and Next.js frontend. The system analyzes LLM prompts across multiple dimensions (semantic consistency, markup validation, vocabulary optimization, contradiction detection) and provides automated improvement suggestions.

## Development Commands

```bash
# Core development workflow (from infra/ directory)
docker compose up -d        # Start all services in background
docker compose down         # Stop all services
docker compose logs -f      # View all service logs
docker compose ps          # Check container status

# Windows batch commands (from project root)
dev up          # Start all services
dev down        # Stop all services
dev logs        # View service logs
dev ps          # Check status
dev help        # Show all commands
```

## Architecture Overview

### Monorepo Structure
```
curestry/
├── backend/app/           # FastAPI application
│   ├── main.py           # FastAPI entry point
│   ├── api/routers/      # API route definitions
│   ├── core/config.py    # Pydantic Settings configuration
│   ├── services/         # Business logic modules
│   │   ├── llm.py        # LLM provider adapters (OpenAI/Anthropic)
│   │   └── embeddings.py # Embedding services
│   └── models/           # SQLAlchemy/SQLModel database models
├── frontend/app/         # Next.js application (App Router)
├── infra/               # Docker and deployment configuration
└── scripts/             # Utility scripts
```

### Key Technologies
- **Backend**: FastAPI + SQLAlchemy/SQLModel + Alembic + Pydantic v2
- **Frontend**: Next.js 14 (App Router) + Tailwind CSS + shadcn/ui + Zustand
- **Database**: PostgreSQL with optional Redis caching
- **Orchestration**: LangGraph for analysis pipeline management
- **LLM Integration**: Multi-provider adapters (OpenAI, Anthropic)

## Core Analysis Pipeline

The system implements a LangGraph-based pipeline with these key nodes:
1. **Language Detection & Translation** → `detect_lang` → `maybe_translate_to_en`
2. **Markup Validation** → `ensure_format` → `lint_markup` (safe fixes)
3. **Vocabulary Analysis** → `vocab_unify` (safe lexical replacements)
4. **Contradiction Detection** → `find_contradictions` (intra & inter-prompt)
5. **Semantic Entropy Analysis** → `semantic_entropy` (n-samples → embeddings → clustering)
6. **LLM-as-Judge Scoring** → `judge_score` (rubric-based evaluation)
7. **Patch Generation** → `propose_patches` (safe/risky categorization)
8. **Clarification Questions** → `build_questions` (interactive refinement)

## API Endpoints

### Core Analysis Endpoints
- `POST /analyze` - Returns `{report, patches, questions}`
- `POST /apply` - Apply `safe_all` or specific `patch_ids`
- `POST /clarify` - Process clarification answers, return updated report
- `GET /export/{id}.{md|xml}` - Export processed prompts
- `GET /report/{id}.json` - Download analysis reports

### Prompt-base Management
- `POST /prompt-base/add` - Add prompt to knowledge base
- `POST /prompt-base/check` - Check for conflicts with existing prompts

### System
- `GET /healthz` - Health check endpoint

## Environment Configuration

Required environment variables (see .env.example):

```env
# Core settings
ENV=development|production
LOG_LEVEL=INFO

# Database
POSTGRES_USER=curestry
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=curestry
DATABASE_URL=postgresql+psycopg://user:pass@db:5432/curestry
REDIS_URL=redis://redis:6379/0

# LLM providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
EMBEDDINGS_PROVIDER=openai
DEFAULT_MODEL=gpt-4o-mini

# Analysis configuration
ENTROPY_N=8              # Number of samples for semantic entropy

# Frontend
NEXT_PUBLIC_API_BASE=http://api:8000
```

## Key Data Models

### Core Pydantic Schemas
- `PromptInput` - Input prompt with metadata
- `MetricReport` - Comprehensive analysis results
- `Patch` - Improvement suggestions (safe/risky)
- `ClarifyQuestion/Answer` - Interactive refinement
- `PromptImproved` - Final processed output

### Database Models
- `prompts` - Stored prompts in prompt-base
- `relations` - Inter-prompt relationships (depends_on|overrides|conflicts_with)

## Frontend Architecture

### Key Components
- **Monaco Editor** - Code editing with syntax highlighting for prompt issues
- **Patch List Panel** - Table showing type, position, preview, accept/reject actions
- **Clarification Block** - Chat-style Q&A interface
- **Metrics Dashboard** - Judge scores, Entropy/Spread/Clusters, Markup quality, Vocabulary analysis, Contradictions, Length metrics
- **Export Controls** - "Export MD", "Export XML", "Save to Prompt-base" buttons

### State Management
- **Zustand** for global state management
- API service client for backend communication
- Toast notifications and loading states

## Development Workflow

### Project Initialization
The project follows a phased development approach as outlined in AI_Tasks.md:
- Phase 0: Repository & Framework Setup
- Phase 1-3: Backend Core & Analysis Pipeline
- Phase 4-5: Prompt-base & APIs
- Phase 6: Frontend Interface
- Phase 7-8: Testing & Infrastructure
- Phase 9: Security & Observability

### Testing Strategy
- Unit tests for metric modules
- Mock LLM providers for testing
- E2E smoke tests: analyze → apply safe → clarify → export
- Integration tests for API endpoints

### Code Quality
- Pre-commit hooks: Ruff/Black/Isort/Mypy for Python, ESLint/Prettier for frontend
- Linting enforced via `make lint`
- Type checking with Pydantic v2 and TypeScript

## Demo Data

The system includes three demo prompt categories:
1. **Coding Agent** - Software development assistance prompts
2. **FAQ Agent** - Customer support automation prompts
3. **Article Writing** - Content generation prompts

Each demonstrates different quality issues and improvement opportunities.
