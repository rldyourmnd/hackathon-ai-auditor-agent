# Client-First Implementation Plan — AI Auditor

This document is a repo-aware, step-by-step plan to implement the client-only roadmap (browser MV3 + VS Code) described in the epics you provided. It maps work into repository locations under `extensions/` and gives an ordered sequence of tasks, acceptance criteria, and suggested estimates.

Notes about repo context
- Repo root contains `extensions/` subproject that follows a monorepo layout:
  - `extensions/packages/*` — shared libraries
  - `extensions/apps/*` — clients (browser-ext, vscode-ext)
- Use `pnpm` from the `extensions/` folder. Builds are `pnpm -r run build`.

High-level increments
- Increment 1 (offline basics): A1–A3, B1–B4, C1–C3
- Increment 2 (online & UX): A4–A5, B5–B8, C4–C7
- Increment 3 (hardening & release): B9–B12, C8–C11, D–G

Structure of this plan
- For each epic/task: target path, precise steps, acceptance criteria, quick notes.

---

## Increment 1 — Setup & Offline baseline (2–3w)

1) A1 — Shared Types
  - Path: `extensions/packages/shared/src/types.ts`
  - Steps:
    - Add TypeScript interfaces and exports for `Finding`, `Severity`, `Suggestion`, `Provider`, `Model`, `AnalysisRequest`, `AnalysisResponse`.
    - Export types via `packages/shared/src/index.ts`.
    - Add `types.d.ts` for consumers if needed.
  - Acceptance: both `apps/browser-ext` and `apps/vscode-ext` import from `@extensions/shared` types without `any`.

2) A2 — Client SDK (offline stub + API surface)
  - Path: `extensions/packages/core` (or `packages/sdk`)
  - Steps:
    - Implement `client-sdk` with `analyze(text, opts)` and `revise(text, opts)` returning `Promise<AnalysisResponse>`.
    - Provide `OfflineClient` stub implementation that runs local detectors.
    - Add cancellation token support and timeout config.
  - Acceptance: `await analyze(text)` works locally; tests for stub exist.

3) A3 — Storage abstraction
  - Path: `extensions/packages/storage` or `packages/core/storage.ts`
  - Steps:
    - Define `Storage` interface (get/set/remove, migrate(version)).
    - Implement Chrome adapter using `chrome.storage.local` (wrap callbacks into promises).
    - Implement VS Code adapter using `SecretStorage`/`Memento` (in `apps/vscode-ext` code that references the shared interface).
  - Acceptance: flags and saved provider/model persist via shared interface in both clients.

4) B1 — MV3 skeleton & build
  - Path: `extensions/apps/browser-ext`
  - Steps:
    - Ensure `manifest.json` points to `dist/background.js` and `dist/content.js`.
    - Build setup is already present; ensure `pnpm -r run build` produces `dist/`.
  - Acceptance: Load unpacked `apps/browser-ext` in Chrome and open popup.

5) B4 — Local detectors
  - Path: `extensions/packages/core/detectors`
  - Steps:
    - Implement simple detectors: `length`, `pii`, `secretKeyPattern`, `contradictionHeuristic`.
    - Return `Finding[]` with `severity` and `suggestion`.
  - Acceptance: content script calls `analyze()` offline and shows findings in a simple overlay.

6) B2/B3 — Inject UI and capture input
  - Path: `extensions/apps/browser-ext/src/content.ts`
  - Steps:
    - Implement SiteAdapter for ChatGPT selectors; run MutationObserver.
    - Inject a small `Analyze` button next to send; hook click and key events.
    - On trigger, call `client-sdk.analyze()` and render overlay/list.
  - Acceptance: pressing button runs offline analysis and shows UI; button persists on DOM updates.

7) C1 — VS Code skeleton
  - Path: `extensions/apps/vscode-ext`
  - Steps:
    - Confirm `package.json` has `commands` and `activationEvents`.
    - Implement `extension.ts` command `ai-auditor.analyze` that calls `client-sdk` stub.
    - Ensure `tsc` compilation produces `out/extension.js`.
  - Acceptance: open `apps/vscode-ext` in VS Code and press F5 to run Extension Development Host; run command from palette and see results.

8) C3 — Analyze Selection
  - Path: `extensions/apps/vscode-ext/src/commands/analyze.ts`
  - Steps:
    - Implement command to read selection, call `client-sdk.analyze()`, show result in simple webview or quick pick.
  - Acceptance: selection analysis shows findings.

Deliverables for Inc 1
- Shared types implemented and imported by both clients.
- Offline `client-sdk` + detectors with tests.
- Browser MV3 skeleton with injection, Analyze button, overlay with findings.
- VS Code extension with Analyze Selection command.

---

## Increment 2 — Online mode, flags, webview & UX (3–4w)

1) A4 — Feature flags system
  - Path: `extensions/packages/core/flags.ts`
  - Steps:
    - Implement flags store backed by `Storage` (from A3).
    - Flags: `offlineOnly`, `blockOnHighRisk`, `enableJudge`, `provider`, `model`.
    - Add runtime subscription API so UI changes take effect immediately.
  - Acceptance: flags toggled in browser popup immediately change behavior.

2) A5 — i18n
  - Path: `extensions/packages/i18n` + `extensions/apps/*/locales`
  - Steps:
    - Add RU/EN JSON; implement runtime loader and hook to UI components.
    - Add toggle in popup and webview to switch language without rebuild.
  - Acceptance: switching language updates UI instantly.

3) B5 — Online client-sdk integration
  - Path: `extensions/packages/core/client.ts`
  - Steps:
    - Implement HTTP transport client with retries, timeout, cancel token, metadata headers (`x-user-agent`, env).
    - Implement `OnlineClient` that calls backend endpoints `POST /analyze` and `POST /revise`.
    - Use feature flags to choose offline vs online behavior.
  - Acceptance: with `offlineOnly=false`, UI receives backend Findings and suggestions.

4) B6 — Popup/Sidepanel & settings
  - Path: `extensions/apps/browser-ext/src/popup` and `sidepanel`
  - Steps:
    - Add settings page with flags, provider/model pickers, and last X history using `Storage`.
    - Implement panel to show recent analyses and details.
  - Acceptance: settings persist and affect analysis live; history lists recent checks.

5) B7 — UX flow for blocking vs warning
  - Path: content script + popup glue
  - Steps:
    - If `blockOnHighRisk` set, intercept submit and show modal with reason; add Override & Send.
  - Acceptance: in strict mode, send is blocked until override.

6) C4–C7 — VS Code webview, file/folder analysis, status bar
  - Path: `extensions/apps/vscode-ext/src/webview` and commands
  - Steps:
    - Implement webview UI that lists findings, filters, and diffs (use shared `ui` package where possible).
    - Implement commands for file/folder analysis and revise patch apply.
    - Add status bar item showing analysis state.
  - Acceptance: webview shows analysis and clicking highlights document ranges; revise applies patch with single undo checkpoint.

Deliverables for Inc 2
- Flags + i18n implemented and wired to both clients.
- Online client-sdk implemented; toggleable.
- Browser popup/sidepanel full settings & history.
- VS Code webview and file-level analysis.

---

## Increment 3 — Hardening, packaging, tests, docs (3–4w)

1) B9 — Privacy & consent
  - Steps:
    - Add onboarding opt-in for sending content; PII masking preview before send; stored audit of what was sent.
  - Acceptance: user must explicitly opt-in before online calls; audit log visible.

2) B11 / C10 — Tests & CI
  - Path: `extensions/packages/*/tests`, Playwright configs
  - Steps:
    - Unit tests for detectors and core APIs.
    - Integration tests for content↔background messaging.
    - Playwright E2E for browser flow (input → analyze → revise → send override).
    - VS Code extension tests for commands and webview snapshots.
  - Acceptance: CI passes tests for core scenarios.

3) B12 / C11 — Packaging & listing
  - Steps:
    - Create zip for browser and prepare store assets; produce `.vsix` for VS Code using `vsce`.
  - Acceptance: artifacts produced and installable.

4) D/E/F/G — UX polish, diagnostics, adapters, docs
  - Steps:
    - Accessibility audit (contrast, keyboard flows).
    - Diagnostics overlays and VS Code output channels.
    - Implement site-adapter pattern and add at least 1 more adapter test target.
    - Author User & Dev READMEs (see below).
  - Acceptance: accessible UI, diagnostics available, docs enough to onboard a dev in <15m.

---

Repository tasks and immediate next steps (what to run now)
1. From repo root, go to `extensions/` and verify build works:
   ```bash
   cd extensions
   pnpm install
   pnpm -r run build
   ```
2. Create `packages/shared/src/types.ts` and export interfaces.
3. Scaffold `packages/core/client-sdk` and `packages/core/detectors` with tests.
4. Implement a minimal browser flow: inject button, offline analyze, overlay.
5. Scaffold VS Code commands and ensure `F5` loads Extension Host.

Developer notes & conventions
- Keep shared logic under `extensions/packages/*` and thin client code in `extensions/apps/*`.
- Expose types from `@extensions/shared` and import by package name (use path mapping if needed).
- Add unit tests for every detector and a minimal E2E for the browser flow.
- Document any new package in `extensions/README.md` and add usage examples.

Acceptance checklist (for a Pull Request)
- Shared types added and used across clients.
- `client-sdk` stub + online client with config toggles.
- Storage adapters implemented and used for flags.
- Browser extension: installs, popup opens, offline analysis works.
- VS Code extension: runs in dev host; `Analyze Selection` command works.
- Basic tests for detectors and SDK.
- Documentation: `PLAN_CLIENT_ROADMAP.md` (this file) + Updated `extensions/README.md` where needed.

Estimated total: 2–3 months across a small team (2–3 developers), with MVP baseline in 3–4 weeks.

---

If you want, I can now:
- create the `packages/shared/src/types.ts` scaffold and `packages/core` client stub in the repo, or
- open a PR with the initial Increment 1 scaffolding.


