# DTO Alignment between backend_public and main backend

This note documents alignment decisions and divergences between public DTOs in `backend_public/app/dto/*` and shared schemas in the main backend (e.g., `backend/app/schemas/prompts.py`).

## Requests

- Analyze
  - backend_public: `AnalyzeRequest { prompt: PromptDto, client_info?, save_result }`
  - main backend: `AnalyzeRequest { prompt: PromptInput, include_entropy?, include_clarify?, include_patches? }`
  - Decision: Keep `backend_public` as-is. Fields serve public surface (client_info/save_result). Converters exist in service layer to pipeline payloads.

- Clarify
  - backend_public: `ClarifyRequest { analysis_id, answers[] }`
  - main backend: `ClarifyRequest { prompt_id, answers[] }`
  - Decision: Keep `analysis_id` (maps better to persisted analysis in public flow). Service maps to internal identifiers as needed.

- Apply
  - backend_public: `ApplyRequest { analysis_id, patch_ids[], apply_safe_all? }`
  - main backend: `ApplyPatchesRequest { prompt_id, patch_ids[], apply_safe_all? }`
  - Decision: Keep `analysis_id`. Service resolves prompt linkage.

## Responses

- AnalyzeResponse and MetricReport
  - backend_public: `MetricReport` is a compact report focused on public UI needs; `AnalyzeResponse` includes `analysis_id`, `report`, `patches`, `questions`, timestamps, and pipeline version.
  - main backend: `MetricReport` includes richer fields (prompt_id, analyzed_at, contradictions typed, etc.).
  - Decision: Preserve public shape for stability. Internally, data can be enriched/normalized when exporting.

- ClarifyResponse, ApplyResponse
  - Semantics aligned; field names differ slightly in places (e.g., `updated_report`).
  - Decision: Preserve public names; adapters in `AnalysisService` handle mapping.

## Rationale

- Public API emphasizes stability and minimal surface for browser/app clients.
- Internal schemas may evolve with pipeline; adapters isolate change.

## Action Items

- If in future a shared package is introduced, add lightweight translators between models rather than forcing one side to conform.
- Ensure OpenAPI docs clearly describe public DTOs; avoid leaking internal fields.
