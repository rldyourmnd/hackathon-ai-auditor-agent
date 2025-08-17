# Auditor Public Backend

FastAPI backend exposing Google OAuth login, workflow reporting, and metrics APIs for the prompt audit pipeline.

## Quick start (Docker)

- Copy `.env.example` to `.env` and set Google OAuth creds (optional for local without auth).
- Run:

```bash
docker compose up --build
```

API at http://localhost:8080

## Endpoints

- `GET /` health
- `GET /auth/google/login` -> redirect to Google
- `GET /auth/google/callback` -> returns `{ access_token }`
- `GET /metrics/{metric_name}` -> series
- `GET /metrics/{metric_name}/cumulative` -> cumulative sum
- `GET /metrics/{metric_name}/sma?window=7` -> moving average
- `POST /workflow/runs` -> create run
- `POST /workflow/runs/{run_id}/nodes/{node_key}` -> report node status/result
- `POST /workflow/runs/{run_id}/metrics` -> report metrics
- `POST /workflow/runs/{run_id}/finish` -> finalize run

## Metrics design (hallucination auditing)

Core metrics mapped to nodes:

- detect_language: `language_detect_confidence` (0-1)
- maybe_translate: `translation_applied` (0/1)
- ensure_format: `format_errors` (count)
- lint_markup: `lint_errors` (count)
- vocab_unify: `vocab_terms_normalized` (count)
- find_contradictions: `contradiction_count` (count)
- analyze_entropy: `semantic_entropy` (float)
- judge_score: `judge_score` (0-1)
- propose_patches: `patch_count` (count)
- build_questions: `question_count` (count)
- finalize: `finalize_pass` (0/1)

Visualization suggestions:

- Per-metric line chart over time
- Cumulative line chart to show progress/volume
- SMA line overlay (window 7/14) to smooth volatility
- Multi-axis if mixing counts and [0-1] scores

## Local development

Install with Poetry, run Uvicorn:

```bash
poetry install
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

Set `DATABASE_URL` to a reachable Postgres (docker compose exposes on 5433).
