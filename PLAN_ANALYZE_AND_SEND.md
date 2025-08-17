# Analyze & Send (Revizor) — implementation plan for Cursor/VS Code

Goal: implement an "Analyze & Send" UX that cannot truly intercept Chat Participant API messages, using an OS-level capture/paste flow for pre-send modifications and an optional post-send audit by tailing `state.vscdb`. Base the work on existing code in `extensions/apps/vscode-ext` (Revizor) and shared logic in `extensions/packages/*`.

Deliverables
- VSIX commands: `cursorAudit.analyzeCurrentDraft`, `cursorAudit.analyzeAndSend`, plus existing `revizor.grabNow`, `revizor.applyRevised`, `revizor.diagnostics.open`.
- Default hotkey: `Ctrl+Enter` on chat input mapped to `Analyze & Send` (UX-level interception).
- OS capture/paste implementations for Windows (UIA + PowerShell SendKeys), macOS (AppleScript), Linux (xdotool or interactive fallback).
- Local analysis pipeline using `@extensions/core` detectors and analyzers (e.g., `runPromptAudit`).
- Optional tailer for `state.vscdb` to provide near-real-time post-send auditing.

---

1) Current repo status (summary)
- `extensions/apps/vscode-ext/revizor` already contains:
  - `grabOrchestrator.ts` — cascaded capture methods: UIA, simulated Copy, interactive copy.
  - `simCopy.ts` — PowerShell/AppleScript wrappers and `applySimPasteFromClipboard()`.
  - `winUia.ts` + `scripts/grab-uia.ps1` — UI Automation capture.
  - `previewPanel.ts` / `diagnosticsPanel.ts` — preview and diagnostics UI.
- Helper HTTP server exists (`helper/index.js`) used as a mock analysis endpoint; we can replace it with direct `@extensions/core` calls.

Conclusion: the repo already implements the main capture and preview capabilities; we need to add the Analyze & Send commands, connect analysis from `@extensions/core`, and add robust paste/send helpers per OS.

---

2) Commands and keybindings
- Add to `extensions/apps/vscode-ext/package.json` (contributes):
  - Commands: `cursorAudit.analyzeCurrentDraft`, `cursorAudit.analyzeAndSend`.
  - Keybinding: map `cursorAudit.analyzeAndSend` to `ctrl+enter` when chat input is focused (see `when` clause).
- Config options:
  - `cursorAudit.sendHotkey` (string, default `ctrl+enter`)
  - `cursorAudit.osMethod` (enum: `auto|uia|applescript|xdotool`, default `auto`)

Acceptance criteria
- Commands appear in the Command Palette.
- The `ctrl+enter` keybinding triggers `cursorAudit.analyzeAndSend` when the chat input or chat view is focused.

---

3) Analysis integration (`@extensions/core`)
- Create `extensions/packages/core/src/analyzers/promptAudit.ts` which aggregates existing detectors:
  - Run `runSelfCheck`, `lengthDetector`, `piiDetector` and produce `AnalysisResponse` with `findings` and a `revised` candidate.
- Export `runPromptAudit` from `packages/core` index.

Acceptance criteria
- Unit tests in `packages/core/test` cover cases: empty input, over‑length, PII detection.
- `runPromptAudit` returns structured `findings` and a revised text candidate.

---

4) Flow: Capture → Analyze → Preview (optional) → Paste → Send
- Implement `runAnalyzeAndMaybeSend(doSend: boolean)` in `extensions/apps/vscode-ext/src/extension.ts`:
  1. Call `grabNow()` to capture current draft (uses UIA / simCopy / interactive fallback).
  2. Run `runPromptAudit(text)` to get `findings` and `revised` text.
 3. If `preview` setting enabled, show `PreviewPanel(original, analysis)` and allow user to finalize revised text.
 4. Write `revised` to clipboard and call `applySimPasteFromClipboard()`; if `doSend` is true, call `applySimSend()` or `applySimPasteAndSend()`.
 5. If simulated paste/send fails, notify user that revised text is in clipboard for manual paste.

Acceptance criteria
- When `Analyze` is invoked, the capture method returns non-empty text or a friendly warning is shown.
- Analysis results are displayed in the PreviewPanel when enabled.
- After user accepts, revised text is placed into the chat input (via simulated paste) and optionally sent.
- On failure, clipboard contains revised text and the user is informed to paste manually.

---

5) Paste and send helpers (per OS)
- Extend `scripts/sim-copy.ps1` and `sim-copy.applescript` with actions: `copy`, `paste`, `send`, `pasteAndSend`.
- Expose `applySimSend()` and `applySimPasteAndSend()` from `simCopy.ts`.
- Linux: add `scripts/sim-copy.sh` that uses `xdotool` or `ydotool` and `wl-clipboard` for Wayland; keep interactive fallback if tools are missing.

Acceptance criteria
- PowerShell/AppleScript scripts accept the new actions and exit 0 on success.
- TypeScript wrappers call scripts and surface errors to the user.

---

6) Optional: near-real-time audit by tailing `state.vscdb`
- Add config flags (disabled by default): `cursorAudit.tailDb.enabled`, `cursorAudit.tailDb.pollIntervalMs`, `cursorAudit.tailDb.pathOverride`.
- Implement `src/tailer/stateDbTailer.ts` in the VSIX that:
  - Locates `state.vscdb` for active workspace (or uses pathOverride).
  - Opens DB in read‑only mode (prefer `better-sqlite3` with `file:...?...mode=ro`) or copies file and parses with `sql.js` to avoid locks.
  - Polls/`fs.watch` the file, queries keys `composerData:%` and `bubbleId:<composerId>:%`, and emits `type === 0` user messages to the Diagnostics/Preview UI.

Constraints
- This is post‑send auditing; it cannot prevent or alter a message before it is delivered.

Acceptance criteria
- When enabled, new user messages written to `state.vscdb` are detected and shown in the Diagnostics panel within a few poll intervals.

---

7) Packaging and builds
- Keep analysis logic in `packages/core` and build it to a CJS bundle consumable by the VSIX. Use `tsup`/`esbuild` or a CJS TS compile option.
- Ensure `extensions/apps/vscode-ext` consumes the workspace package (pnpm workspace) and that the built core bundle is included in the VSIX files.

Acceptance criteria
- `pnpm -w build` produces a VSIX that contains the `@extensions/core` runtime artifacts and the extension runs without module resolution errors.

---

8) UI/UX details
- Status bar: update `overlay.ts` to invoke `cursorAudit.analyzeAndSend` and conditionally show when the chat view is focused.
- PreviewPanel: render `findings` (severity, message) and an editable `Revised` textarea, plus actions `Insert revised` and `Paste & Send`.
- DiagnosticsPanel: include platform help for macOS Accessibility and Windows UIA.

Acceptance criteria
- PreviewPanel shows structured findings and allows the user to insert the revised text into the input.

---

9) Permissions and security
- Document required platform permissions: macOS Accessibility, Windows UIA allowances, Linux tool dependencies.
- Respect `revizor.privacy.noClipboard` setting: if true, avoid using clipboard-based copy/paste.

Acceptance criteria
- README lists required OS permissions and how to enable them.

---

10) Tests and anchors
- Add unit tests to `packages/core/test` for `runPromptAudit` and detectors.
- Add manual E2E test recipes for Windows/macOS/Linux.

Acceptance criteria
- Automated unit tests pass locally in CI for `packages/core`.

---

11) Implementation checklist (detailed tasks)
- Core package
  - [ ] Add `src/analyzers/promptAudit.ts` and export `runPromptAudit`.
  - [ ] Add unit tests for empty, long, and PII cases.
  - [ ] Build core into a CJS artifact for VSIX inclusion.

- VSIX commands & wiring
  - [ ] Add `cursorAudit` commands and keybinding to `package.json`.
  - [ ] Implement `runAnalyzeAndMaybeSend()` in `extension.ts`.
  - [ ] Wire `overlay.ts` status bar to the new commands.

- OS helpers
  - [ ] Extend `sim-copy.ps1` and `sim-copy.applescript` with `send` and `pasteAndSend` actions.
  - [ ] Add `sim-copy.sh` for Linux (xdotool/ydotool) or document fallback.
  - [ ] Expose `applySimSend` and `applySimPasteAndSend` in `simCopy.ts`.

- Optional tailer
  - [ ] Implement `stateDbTailer.ts` with `better-sqlite3` read-only logic and fallback to copy+sql.js.
  - [ ] Add config entries and a toggle UI in Diagnostics.

- Packaging & docs
  - [ ] Ensure VSIX bundling includes built `@extensions/core` artifacts.
  - [ ] Update `extensions/apps/vscode-ext/README.md` with hotkeys, OS permissions, and Linux dependencies.

Acceptance criteria (overall)
- Commands and keybindings are registered and trigger the flow.
- Capture works on at least Windows and macOS via UIA and AppleScript respectively; Linux fallback is documented.
- Analysis returns findings and revised text; preview and apply flows are functional.
- VSIX packaging includes core runtime; extension runs without import errors.

---

Sequence of implementation (recommended sprint sequence)
1. Implement `runPromptAudit` and unit tests in `packages/core` (2–3 days).
2. Extend `sim-copy` scripts (PS1/AppleScript) and `simCopy.ts` TS wrappers (1 day).
3. Add commands & keybinding, implement `runAnalyzeAndMaybeSend()` and wire `overlay.ts` (1–2 days).
4. Hook `runPromptAudit` into the extension flow and wire `PreviewPanel` (1 day).
5. Build & package core into VSIX and test end-to-end across Windows/macOS (1–2 days).
6. Optional: implement `stateDbTailer` + Diagnostics UI (2–3 days).

Exit criteria for feature completion
- All unit tests in `packages/core` pass.
- Manual E2E smoke tests: capture＋analyze＋paste works on Windows and macOS; Linux documented fallback.
- The VSIX contains core runtime and installs without runtime errors.
- UX: Preview/Diagnostics are available and the status bar command works in chat context.

---

Notes
- This design intentionally avoids relying on Chat Participant API to intercept messages; use proxy UX and OS-level automation for pre-send modification, and DB tailing for post-send auditing.


