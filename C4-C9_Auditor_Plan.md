## C4–C9 Auditor: Plan, Tasks, Criteria, and Root Checklist

This document defines an implementation plan (tasks, acceptance criteria, configs, APIs, data models, UX) for C4 — Analyze File/Folder (Cursor + docs) through C9 — Provider/Model selection. It includes defaults and a checklist to add to repository root.

---

## Goals (high level)
- Detect and collect prompt artifacts across the workspace (files + JSON fields).
- Collect supporting documentation (.md) to cross-check and contextualize prompts.
- Normalize and stream/push data to analysis backend in bounded batches.
- Surface findings in a webview panel, provide revise/patch flow with safe/risky patches and apply via WorkspaceEdit.
- Provide editor diagnostics, code actions, status bar, provider/model selection, cancellation and caching.

## Config keys & defaults
Defaults should be overridable in workspace settings.

```json
{
  "auditor.cursorPrompt.searchFolders": [
    ".cursor/rules/",
    ".cursor/prompts/",
    ".cursor/agents/",
    ".cursor/policies/",
    "cursor/prompts/",
    "cursor/agents/",
    "prompts/",
    "_prompts/",
    ".prompts/"
  ],
  "auditor.cursorPrompt.extensions": [".prompt",".cprompt",".txt",".md"],
  "auditor.cursorPrompt.filenameIncludes": ["prompt","system","persona","agent","policy"],
  "auditor.cursorPrompt.jsonPromptFields": ["systemPrompt","userPrompt","prompt","instructions","policy"],
  "auditor.cursorPrompt.excludeGlobs": [],

  "auditor.docs.searchFolders": ["docs/","documentation/","handbook/","knowledge/","wiki/",""],
  "auditor.docs.excludeGlobs": [],

  "auditor.ui.statusBarMinimal": false,
  "auditor.ui.notifications": "all"
}
```

Note: `""` in docs searchFolders indicates root README.md and top-level files are included.

## File patterns considered prompt artifacts
- File extensions: `.prompt`, `.cprompt`, `.txt`, `.md` (configurable).
- Filename includes (case-insensitive): `prompt`, `system`, `persona`, `agent`, `policy` (configurable).
- Prioritized folders (search order):
  - `.cursor/prompts/`, `.cursor/agents/`, `.cursor/policies/`
  - `cursor/prompts/`, `cursor/agents/`
  - `prompts/`, `_prompts/`, `.prompts/`
  - Any subdirectory whose name contains both `cursor` and `prompt` (case-insensitive)

### JSON artifacts
- Files: `.cursor/**/*.json`, `cursor/**/*.json` (configurable via searchFolders + extensions).
- If JSON contains any of the configured `jsonPromptFields` (default: `systemPrompt,userPrompt,prompt,instructions,policy`) — extract those string fields as prompt sections.

## Where to take documentation (.md)
- File extension: `.md` only (configurable).
- Default folders: `docs/`, `documentation/`, `handbook/`, `knowledge/`, `wiki/`, plus `README.md` top-level and nested.
- Whitelist/blacklist via `auditor.docs.searchFolders` and `auditor.docs.excludeGlobs`.

## Collection algorithm (workspace-aware)
1. Resolve scope: current file | selected folder | workspace roots.
2. Build prioritized start directories: merge (user scope) + default prioritized folders (above).
3. Recursively walk start directories in priority order.
4. For each file:
   - Skip if matches `excludeGlobs`.
   - If extension/filename matches prompt rules: add to promptCandidates.
   - If `.json`: inspect fields, extract matching string fields (each becomes a PromptSource section).
   - If `.md` and in docs searchFolders: add to docCandidates.
5. Deduplicate by URI; compute `contentHash` (default SHA1) for caching and change detection.
6. Enforce limits: prompts ≤ 500, docs ≤ 2000 (configurable). If exceeded, abort and prompt user to narrow scope.

### Outputs during collection
- `promptCandidates[]` — array of raw string sources (file sections).
- `docCandidates[]` — array of markdown documents.

## Data models (client-side)
PromptSource:
```ts
type PromptSource = {
  id: string; // stable: hash(fileUri + sectionKey)
  fileUri: string;
  fileRelPath: string;
  kind: "file" | "json";
  section?: string; // e.g. "systemPrompt"
  title: string; // basename or basename#section
  content: string;
  contentHash: string;
  tags: string[]; // e.g. ["system","persona","policy"]
}
```

DocSource:
```ts
type DocSource = {
  id: string; // hash(fileUri)
  fileUri: string;
  fileRelPath: string;
  title: string; // H1 or basename
  content: string; // markdown as-is
  contentHash: string;
}
```

AnalysisManifest (sent before large content batches):
```ts
type AnalysisManifest = {
  workspaceRoot: string;
  generatedAt: string; // ISO
  provider: string;
  model: string;
  riskThreshold: number;
  prompts: Array<{ id:string; fileRelPath:string; kind:string; section?:string; contentHash:string }>;
  docs: Array<{ id:string; fileRelPath:string; contentHash:string }>;
  stats: { promptCount:number; docCount:number; totalChars:number };
}
```

## Transport and server API
- Preferred: streaming batch upload if server supports it. Otherwise paged JSON.

Sequence (recommended):
- POST /analyze/manifest  — body = AnalysisManifest
- POST /analyze/prompts   — body = array of PromptSource (batches)
- POST /analyze/docs      — body = array of DocSource (batches)
- POST /analyze/run       — triggers server-side calculations (overlap, entropy, conflicts)

Fallback single-request:
- POST /analyze { manifest, prompts[], docs[] } — client must chunk to respect size limits.

Client responsibilities before send:
- Normalize line endings to `\n`.
- Strip binary attachments / large images from markdown; keep code blocks and text.
- Optionally chunk large `.md` into chunks by H2/H3 headings or by token/char counts (e.g., 1–2k tokens) while retaining `sourceId` and `chunkIndex`.

## Normalization & chunking rules
- Normalize whitespace and line endings.
- Remove embedded base64 blobs and large images; replace with placeholder `[image removed size=...].`
- For JSON prompts: trim and collapse repeated whitespace; preserve newline structure in content.
- For chunking: prefer semantic chunk boundaries (H2/H3). If absent, chunk by ~2000 characters preserving sentence boundaries when possible.

## Caching & deduplication
- Cache by key: `{workspaceRoot}:{fileUri}:{contentHash}` in `globalState` with configurable TTL.
- Skip unchanged sources by comparing contentHash.

## Limits & failure modes
- Reasonable defaults: maxPrompts=500, maxDocs=2000, maxBatchSizeChars=1_000_000.
- If server unreachable: show partial/offline results and mark cross-checks as `partial`.
- Provide clear user errors for oversized payloads and offer scope narrowing suggestions.

## Client UX
- Command: `Analyze prompts (Cursor) & docs in workspace` (exposed in Command Palette).
- UI: progress bar / spinner with message `Analyzing X prompt files + Y docs…` and `Cancel` button.
- On completion open Findings webview (C7). Status bar updates (C6).

## C5 — Revise Prompt (flow)
1. Trigger from Findings item or editor command `Revise Prompt`.
2. Client selects one `PromptSource` (or selection within file) and assembles context: top-k related docs (server-provided) or nearest docs by path heuristics.
3. POST /revise { source: PromptSource, context: DocSource[], provider, model, riskThreshold }
4. Server returns `Patch[]`:
   ```ts
   type Patch = {
     kind: "safe" | "risky";
     title: string;
     description?: string;
     edits: Array<{ range: RangeAbs | RangeLC; newText: string }>;
     rationale?: string;
   }
   ```
5. Show diff preview with toggles `Safe only / All`, checkboxes per patch.
6. Apply → build a `WorkspaceEdit` applying all selected edits as a single undoable operation.
7. If ranges conflict or doc versions changed: offer rebase (contextual fuzzy apply) or uncheck conflicting patches. Warn user before apply.

Client-side protections:
- Check `document.version` before applying; if changed, require user confirmation or re-run revise.
- Record `lastAppliedPatchSet` for quick rollback.

## C6 — Status bar & notifications
- States: `Idle: Auditor`, `Running: Analyzing (X/Y)…`, `Done: Found Z issues` (click opens Findings).
- Errors surface via `vscode.window.showErrorMessage` and also logged to extension Output channel.
- Settings: `auditor.ui.statusBarMinimal` and `auditor.ui.notifications`.

## C7 — Findings Webview (React)
Payload from client to webview:
```ts
type FindingsPayload = {
  summary: { prompts:number; docs:number; total:number; bySeverity: Record<string,number> };
  files: Array<{ fileRelPath:string; sourceKind: 'prompt'|'doc'|'cross'; findings: FindingUI[] }>
}
```

Features:
- Filters: severity / rule / sourceKind / filename search.
- Grouping: by file (default), by rule, by source type.
- Actions: `Open at range`, `Copy advice`, `Apply safe fixes in this file`, `Run Revise Prompt for this file/selection`.
- IPC: `postMessage` ⇄ `onDidReceiveMessage` with typed messages.

## C8 — Inline decorations & Code Actions
- Create `DiagnosticCollection` from findings: each Diagnostic includes `range`, `message`, `severity`, `code` (ruleId), `source = 'Auditor'`.
- Provide at least two CodeActions per applicable finding:
  1. Safe automatic edit (WorkspaceEdit) — e.g., unify terminology or small markup corrections.
  2. Suggest full revise (opens panel) for risky changes.
- Handle document changes and dispose/recompute decorations in batches to avoid flicker.

## C9 — Provider & model selection
- QuickPick for provider (OpenAI/Anthropic/etc.) and then model quick pick.
- Persist `auditor.provider` and `auditor.model` in settings; sensitive keys/endpoint in `SecretStorage`.
- All network calls read latest provider/model values before request; if missing credentials show quick link to settings.

## Cross-cutting: Cancellation, Telemetry, Tests
- Cancellation: single CancellationTokenSource per analysis job; respect tokens in long ops.
- Telemetry (local): scan time, counts found, percent safe fixes applied — opt-in.
- Unit tests: detectors, chunking logic, manifest builder, patch application. Integration tests: mock server with sample prompts/docs.

## DoD Checklist (place in repository root)
- [ ] C4: Prompt discovery implemented for default + configurable rules.
- [ ] C4: JSON prompt field extraction implemented and tested.
- [ ] C4: Docs collection implemented and chunking behavior validated.
- [ ] C4: Manifest + batching APIs implemented with retries and size limits.
- [ ] C4: Collection caching and contentHash skip logic implemented.
- [ ] C5: Revise endpoint integration + patch UI + WorkspaceEdit apply with single-undo implemented.
- [ ] C5: Conflict detection & rebase or manual resolution UI.
- [ ] C6: Status bar states + clickable open panel + notifications implemented.
- [ ] C7: Findings webview with filtering, grouping, and actions implemented and IPC secured.
- [ ] C8: DiagnosticCollection created; >=2 CodeActions implemented (safe fixes + panel open for risky).
- [ ] C9: Provider/model picker implemented; keys/endpoint check with SecretStorage.
- [ ] Cross-cutting: Cancellation support, caching, limits, and offline fallback implemented.
- [ ] Tests: unit and integration tests for each block; CI builds green.
- [ ] Docs: this plan file added to repo root and referenced in `extensions/README.md`.

## Acceptance criteria (per block — short)
- C4: When user runs analyze on workspace root, client returns <= limits, manifest posted, server returns analysis or graceful offline partial results with status. UI shows progress and results.
- C5: Patch preview shows diffs; applying patches modifies files in one undo; if file changed mid-flow, user is warned.
- C6: Status bar shows counts; clicking opens Findings; errors surface to Output and message boxes.
- C7: Webview lists findings grouped and filterable; clicking item opens editor at the right range.
- C8: Diagnostics appear inline and CodeActions either apply safe edits or route to panel for risky edits.
- C9: Provider/model selection persists and used for subsequent requests; missing credentials produce actionable prompt.

---

Place this file at repository root as `C4-C9_Auditor_Plan.md` and reference it from extension docs/README where appropriate.


