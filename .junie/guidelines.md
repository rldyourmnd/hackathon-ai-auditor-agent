# Curestry Project Guidelines for Junie

These guidelines instruct Junie (the autonomous programmer) how to work in this repository. They include a short project overview and concrete rules split by development zones.

## 0) Project Overview
- Name: Curestry — AI prompt analysis and improvement system.
- Stack: FastAPI backend, Next.js frontend, PostgreSQL, optional Redis, Docker Compose.
- LLM policy: Use OpenAI GPT-5 models only
  - cheap tier → gpt-5-nano
  - standard & premium tiers → gpt-5-mini
  - Note: GPT-5 family is treated as provider-managed sampling; temperatures are NOT used or configured anywhere.
- Current API (backend):
  - POST /analyze
  - POST /analyze/apply (temporary; plan calls for POST /apply)
  - POST /analyze/clarify (temporary; plan calls for POST /clarify)
  - GET /healthz

## 1) Repository & Structure
- Root layout:
  - backend/app (FastAPI) — main.py, api/routers, core/, services/, models/
  - frontend/ (Next.js) — app/, components/, etc.
  - infra/ — docker-compose.yml, Dockerfiles, optional nginx
  - scripts/ — utility scripts
  - .env.example — template for env vars (never commit real secrets)
  - AI_Tasks.md — phased development plan
  - Product_info.md — high-level product description
  - CLAUDE.md — guidance for Claude Code
  - .junie/guidelines.md — this document

## 2) Environment & How to Run
- Local development (Windows-friendly):
  - Copy .env.example to .env and set OPENAI_API_KEY (keep private locally).
  - Start stack:
    - Using batch: `dev up` (from repo root)
    - Or via Compose: `cd infra && docker compose up -d`
  - Health checks: http://localhost:8000/healthz and http://localhost:3000
  - Stop services: `dev down` or `docker compose down`
- Important env vars (see .env.example):
  - General: ENV, LOG_LEVEL
  - DB/Cache: POSTGRES_*, DATABASE_URL, REDIS_URL
  - LLM: OPENAI_API_KEY, OPENAI_MODEL_CHEAP=gpt-5-nano, OPENAI_MODEL_STANDARD=gpt-5-mini, OPENAI_MODEL_PREMIUM=gpt-5-mini
  - Analysis: ENTROPY_N (sample count), no temperature variables

## 3) LLM & Models (Zone: LLM Integration)
- Model routing:
  - cheap → gpt-5-nano
  - standard → gpt-5-mini
  - premium → gpt-5-mini
- Do not add temperature parameters; GPT-5 models in this project are used without temperature controls. Remove or ignore any legacy temperature flags.
- Entropy sampling uses n responses (ENTROPY_N). Sampling variability is provider-defined.
- If adding new providers, do so behind a service interface and update .env.example; coordinate with Product_info.md and AI_Tasks.md.

## 4) Backend (Zone: API & Core Services)
- Framework: FastAPI + Pydantic v2 + SQLModel.
- Primary modules:
  - app/main.py — app entry, CORS, healthz
  - app/api/routers/analysis.py — /analyze, apply, clarify
  - app/core/config.py — Pydantic settings; ensure model names per policy
  - app/services/llm.py — OpenAI client, tier routing; ensure no temperature args
  - app/core/database.py & app/models/* — DB setup and models
- Endpoint conventions:
  - Current: /analyze, /analyze/apply, /analyze/clarify
  - Target (per plan): /analyze, /apply, /clarify (align later with minimal breaking changes)
- Async rules:
  - LLM calls currently use a sync OpenAI client inside async funcs; avoid heavy parallel load. If refactoring, prefer async or threadpool wrappers.
- Error handling: Return proper HTTP errors via FastAPI; log exceptions using JSON logging in main.
- Data constraints: Pydantic schemas enforce ranges (e.g., scores 0–10). Keep compatibility.

## 5) Frontend (Zone: Web UI)
- Framework: Next.js (App Router), Tailwind, shadcn/ui, Zustand.
- API base URL: NEXT_PUBLIC_API_BASE in .env (defaults to http://localhost:8000).
- UX goals (per plan): Monaco editor, patch list, clarify Q&A, metrics dashboard, exports.
- Keep types safe and match backend contracts. Use lightweight clients and handle errors gracefully.

## 6) Infra/DevOps (Zone: Infra)
- Docker Compose services: api, web, db, redis.
- Do not expose Postgres externally in dev unless necessary.
- Healthchecks are configured for api, db, redis. Keep them green.
- Never commit secrets. .env.example is the only committed env file.
- When changing model names or envs, update:
  - .env.example, infra/docker-compose.yml environment section, backend/app/core/config.py defaults, and docs (AI_Tasks.md, README.md, Product_info.md).

## 7) Database & Data (Zone: DB)
- ORM: SQLModel. Migrations via Alembic (where present).
- Models include prompts, relations, analysis_results.
- For demos, the backend may run even if DB init fails; log and continue. Avoid data loss in production.

## 8) Testing (Zone: QA)
- Unit tests to cover:
  - Schema validation and serialization
  - LLM service routing logic
  - Basic analysis logic (judge parsing fallbacks, entropy calc)
- E2E smoke path (when implemented): analyze → apply safe → clarify → export.
- Mock LLM in tests. Do not hit real APIs in CI.

## 9) Security & Observability (Zone: Sec/Obs)
- Secrets: Never commit real API keys. Rotate leaked keys immediately.
- CORS: Keep restricted to dev origins; tighten for prod.
- Logging: Use structured JSON; avoid logging raw prompts in prod.
- Basic rate limiting/proxying can be added via Nginx (optional post-MVP).

## 10) Developer Experience (Zone: DX)
- Commands (Windows): use dev.bat — `dev up`, `dev down`, `dev logs`, `dev ps`, `dev health`.
- Docker-based: `cd infra && docker compose up -d`.
- Keep AI_Tasks.md updated when changing scope or endpoints.
- Prefer minimal diffs aligned with the current session’s issue description.

## 11) Coding Style & Conventions
- Python: type annotations, Pydantic v2 models, small cohesive modules.
- JS/TS: strict types where possible; consistent imports and formatting.
- Keep responses small; truncate sample arrays (as done for entropy samples) to keep payloads light.
- Avoid introducing temperature usage or undocumented env vars.

## 12) Definition of Done (DoD) for Junie tasks
- Change scope is minimal and fully addresses the issue description.
- Code and docs are consistent (env keys, model names, routes).
- .env.example and infra configuration remain valid and free of secrets.
- App still starts via docker compose; /healthz returns healthy when configured.

## 13) Junie’s Workflow Expectations
- Always include an <UPDATE> section with plan and next step, then perform tool actions.
- Prefer specialized tools (search_project, get_file_structure, search_replace) instead of raw shell, and never mix them in one call.
- Use Windows-style paths in any commands.
- Do not create files outside the repository; place guidance in .junie/.

## 14) Known Deviations from Plan (to reconcile later)
- /apply and /clarify are currently under /analyze/*.
- Judge rubric is simplified; entropy is basic; NLI and vocabulary modules are stubs.
- These are acceptable for MVP demo; future tasks will align with the product plan.
