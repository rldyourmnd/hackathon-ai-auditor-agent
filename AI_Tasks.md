# Curestry Development Tasks for AI Agent

## Project Overview
Build "Curestry" - an AI-powered prompt analysis and improvement system using FastAPI backend, Next.js frontend, with Docker deployment.

## Phase 0 - Repository & Framework Setup (Empty but Runnable)

### Repository Initialization
- [ ] Initialize git repository: `git init`, create `LICENSE`, `README.md`
- [ ] Create `.env.example` (without secrets), add `.env` to gitignore
- [ ] Setup basic monorepo structure:
```
curestry/
  backend/
    app/ (FastAPI)
  frontend/
    app/ (Next.js)
  infra/
    docker-compose.yml
    Dockerfile.api
    Dockerfile.web
    nginx/ (optional reverse-proxy)
  scripts/
  .gitignore
  .editorconfig
```

### Development Tools Setup
- [ ] Configure pre-commit hooks: Ruff/Black/Isort/Mypy for Python, ESLint/Prettier for frontend
- [ ] Create Makefile with targets: `make up`, `make down`, `make logs`, `make lint`, `make test`
- [ ] Setup Docker Compose with minimum 3 services: `api`, `web`, `db (Postgres)` (+ optional `redis`)
- [ ] Create backend health-check endpoint `/healthz` and frontend home page `/`
- [ ] Ensure `docker compose up` brings up entire system

### Environment Variables (Minimum Required)
```env
# General
ENV=development|production
LOG_LEVEL=INFO

# Database/Cache
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
DATABASE_URL=postgresql+psycopg://...
REDIS_URL=redis://redis:6379/0

# LLM/Embeddings Providers
OPENAI_API_KEY=
OPENAI_MODEL_CHEAP=gpt-5-nano
OPENAI_MODEL_STANDARD=gpt-5-mini
OPENAI_MODEL_PREMIUM=gpt-5-mini
EMBEDDINGS_PROVIDER=openai

# Frontend
NEXT_PUBLIC_API_BASE=http://api:8000
```

## Phase 1 - Backend Core (FastAPI + Configuration)

### FastAPI Foundation
- [ ] Create FastAPI skeleton: `app/main.py`, `app/api/routers`, `app/core/config.py`
- [ ] Implement Pydantic Settings for reading `.env` configuration
- [ ] Setup structured JSON logging with uvicorn, configure CORS
- [ ] Define Pydantic v2 schemas: `PromptInput`, `MetricReport`, `Patch`, `ClarifyQuestion/Answer`, `PromptImproved`

### Database Setup
- [ ] Configure SQLAlchemy/SQLModel for database ORM
- [ ] Setup Alembic for database migrations
- [ ] Create test database connection
- [ ] Implement database initialization scripts

### LLM Integration
- [ ] Create LLM provider module (`app/services/llm.py`) for OpenAI only (GPT-5 nano for cheap; GPT-5 mini for standard/premium)
- [ ] Implement embeddings service (`app/services/embeddings.py`)
- [ ] Configure feature flags/metric configs (entropy thresholds, etc.) via environment variables:
  - `ENTROPY_N=8`

## Phase 2 - Analysis Pipeline Orchestration (LangGraph, without Temporal)

### Pipeline Nodes Implementation
- [ ] Create pipeline nodes:
  - `detect_lang` → `maybe_translate_to_en`
  - `ensure_format (xml|md)` → `lint_markup (safe fixes)`
  - `vocab_unify (safe lexical replace)`
  - `find_contradictions (intra & inter)`
  - `semantic_entropy (n-samples → embeddings → clustering)`
  - `judge_score (rubric)`
  - `propose_patches (safe/risky)`
  - `build_questions (clarify)`

### Graph Assembly
- [ ] Build `analyze_graph` using LangGraph (linear flow with conditional clarify branch)
- [ ] Define input/output contracts for each node using Pydantic models
- [ ] Implement error handling and retry logic for pipeline nodes

## Phase 3 - Metrics & Logic Modules

### Language & Translation
- [ ] Implement auto-detection of language
- [ ] Create machine translation to English via LLM instructions
- [ ] Add `translated` flag tracking

### Markup Validation
- [ ] Build XML/MD validator with auto-fix capabilities
- [ ] Implement safe markup fixes (closing tags, headers)
- [ ] Track `markup_valid` and `fixes_count` metrics

### Vocabulary & Simplicity (Safe Operations)
- [ ] Analyze word frequencies and generate embeddings
- [ ] Create synonym clusters for term canonization
- [ ] Include tags/sections in vocabulary analysis

### Contradiction Detection
- [ ] Implement LLM-based Natural Language Inference for intra-prompt pairs
- [ ] Add optional inter-document contradiction detection for prompt-base

### Semantic Entropy Analysis
- [ ] Create sampler for n=8-12 responses using cheap LLM
- [ ] Generate embeddings and perform k-means/HDBSCAN clustering
- [ ] Calculate `entropy`, `spread`, and `clusters` metrics

### LLM-as-Judge Scoring
- [ ] Implement rubric-based scoring via LLM
- [ ] Return JSON scores with short rationales (no hidden model thoughts)

### Patch Generation Engine
- [ ] Generate patches categorized as `safe`/`risky`
- [ ] Create diffs/spans with previews for proposed changes

## Phase 4 - Prompt-base (Minimal Consistency)

### Data Model
- [ ] Create database models for `prompts` and `relations` (depends_on|overrides|conflicts_with)
- [ ] Implement CRUD operations: add/update prompt, create relations, retrieve prompts

### Consistency Checking
- [ ] Build inter-prompt conflict detection using pairwise LLM-NLI
- [ ] Generate conflict summaries and propose "unifying" edits

## Phase 5 - Public APIs (REST)

### Core Endpoints
- [ ] `POST /healthz` - system status
- [ ] `POST /analyze` - returns `{report, patches, questions}`
- [ ] `POST /apply` - apply `safe_all` or specific `patch_ids`
- [ ] `POST /clarify` - process clarification answers and return updated report

### Prompt-base Endpoints
- [ ] `POST /prompt-base/add` - add new prompt to knowledge base
- [ ] `POST /prompt-base/check` - check prompt for conflicts

### Export Endpoints
- [ ] `GET /export/{id}.{md|xml}` - export processed prompts
- [ ] `GET /report/{id}.json` - download analysis reports

### Error Handling
- [ ] Implement unified error format (problem+json standard)
- [ ] Add comprehensive input validation

## Phase 6 - Frontend (Next.js) - Landing + Working Interface

### Project Setup
- [ ] Initialize Next.js project with app router
- [ ] Configure Tailwind CSS + shadcn/ui components
- [ ] Setup Zustand for state management

### Landing Page
- [ ] Create hero section with brief product description
- [ ] Add "How it works" section explaining the analysis process
- [ ] Display metric cards showcasing system capabilities
- [ ] Include clear call-to-action "Try it now" button

### Main Application Page (/app)
- [ ] Implement Monaco editor with syntax highlighting for prompt issues
- [ ] Create "Patch List" panel (table: type, position, preview, accept/reject, "Apply Safe Fixes")
- [ ] Build "Clarification Required" block with chat-style Q&A interface
- [ ] Design metrics dashboard showing: Judge scores, Entropy/Spread/Clusters, Markup, Vocabulary, Contradictions, Length
- [ ] Add action buttons: "Export MD", "Export XML", "Save to Prompt-base"

### Prompt-base Interface (/prompt-base)
- [ ] Display prompt list with search/filter capabilities
- [ ] Show consistency checks and conflict warnings
- [ ] Implement basic prompt management (add, edit, delete)

### API Integration
- [ ] Create service client for backend API communication
- [ ] Implement token management (if authentication required)
- [ ] Add loading spinners and toast notifications
- [ ] Handle error states gracefully

## Phase 7 - Testing, Demo Data & Developer Experience

### Demo Content
- [ ] Prepare "dirty" prompt examples (3 use cases): coding agent, FAQ agent, article writing
- [ ] Create seed script to populate prompt-base with demo prompts and relationships

### Testing
- [ ] Write unit tests for metric modules
- [ ] Create mock LLM providers for testing
- [ ] Implement E2E smoke tests: analyze → apply safe → clarify → export
- [ ] Add integration tests for API endpoints

### Development Tools
- [ ] Setup linters/formatters in CI (GitHub Actions)
- [ ] Ensure `make lint` runs all code quality checks
- [ ] Add comprehensive development documentation

## Phase 8 - Infrastructure & Packaging

### Docker Configuration
- [ ] Create `Dockerfile.api` (Python slim, uvicorn, non-root user, env from compose)
- [ ] Create `Dockerfile.web` (Node builder → standalone output)

### Docker Compose Setup
- [ ] Configure `api` service: build from Dockerfile.api, depends on db, env passthrough, dev volume mount
- [ ] Configure `web` service: build from Dockerfile.web, set `NEXT_PUBLIC_API_BASE` to point to api
- [ ] Configure `db` service: Postgres with persistent volume, initialization SQL
- [ ] Optional: Add `redis` service for caching

### Reverse Proxy (Optional)
- [ ] Setup Nginx as reverse proxy: serve `web` on `/:443`, proxy `/api` → `api`
- [ ] Configure SSL termination if needed

### Configuration Validation
- [ ] Implement startup configuration validation
- [ ] Fail fast if required environment variables are missing

## Phase 9 - Security & Observability (MVP Level)

### Security
- [ ] Implement basic rate limiting (Nginx level or middleware)
- [ ] Ensure sensitive data (prompts) are not logged in production
- [ ] Add input sanitization and validation

### API Documentation
- [ ] Generate OpenAPI schema automatically
- [ ] Enable Swagger UI for API exploration
- [ ] Add comprehensive endpoint documentation

### Monitoring
- [ ] Add basic metrics (Prometheus exporter or health probes)
- [ ] Implement request/response logging (without sensitive data)
- [ ] Setup application health monitoring

## Stretch Goals (If Time Permits)

### Advanced Features
- [ ] Visualize prompt-base relationship graph
- [ ] Create template mode: quick deployment of XML/MD frameworks for "Agent/Policy/Tool Spec"
- [ ] Add PDF export for analysis reports
- [ ] Build minimal IDE extension: diagnostics + apply safe fixes

## Definition of Done by Phase

**Phase 0 DoD:** `docker compose up` brings up empty API with `/healthz` and empty frontend landing page

**Phase 2-3 DoD:** `/analyze` endpoint returns valid report with metrics and at least 1-2 types of patches

**Phase 5 DoD:** `/apply`, `/clarify`, `/prompt-base/*` endpoints work with demo data

**Phase 6 DoD:** Web UI displays all metrics, applies safe fixes, includes clarification chat, exports MD/XML

**Phase 8 DoD:** Entire project launches with single command, all credentials from `.env`

## Development Priorities

1. **Minimum Viable Product:** Focus on Phases 0-6 for core functionality
2. **Production Ready:** Complete Phases 7-8 for deployment
3. **Enterprise Features:** Phase 9 for security and monitoring
4. **Advanced Features:** Stretch goals only after MVP completion

## Technical Stack Summary

- **Backend:** FastAPI, SQLAlchemy/SQLModel, Alembic, Pydantic v2
- **Frontend:** Next.js (app router), Tailwind CSS, shadcn/ui, Zustand
- **Database:** PostgreSQL, optional Redis
- **LLM:** OpenAI API (GPT-5 nano for cheap; GPT-5 mini for standard/premium)
- **Pipeline:** LangGraph for orchestration
- **Deployment:** Docker Compose, optional Nginx
- **Testing:** pytest, Jest, mock providers
- **CI/CD:** GitHub Actions, pre-commit hooks
