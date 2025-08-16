# Extensions: Minimal plan to make `extensions/` buildable

This document lists concrete steps to turn the current `extensions/` scaffold into two buildable artifacts:
- a minimal Chrome (Manifest V3) extension
- a minimal VS Code extension

Goal: be able to run local builds and load the browser extension as "unpacked" and run the VS Code extension in the Extension Development Host (F5).

1) Add workspace + tooling
- Create `extensions/package.json` with workspace config (npm or pnpm) and root scripts:
  - `install`/`bootstrap` (install workspace deps)
  - `build` to run per-package builds: e.g. `pnpm -w -r run build` or `npm run -w ...`
- Add `extensions/tsconfig.base.json` with shared `compilerOptions`.

2) Browser extension (apps/browser-ext)
- Required files:
  - `package.json` with build scripts and devDependencies (`typescript`, optional bundler)
  - `tsconfig.json` for compilation target (ES2020+)
  - source: `src/content.ts`, optional `src/background.ts`, optional `src/popup/*`
  - `dist/` folder with compiled JS referenced by `manifest.json`
- Update `manifest.json` to reference compiled files (example):
  - `"background": { "service_worker": "dist/background.js" }`
  - add `content_scripts` that include `dist/content.js` or use `action.default_popup` for a popup HTML
- Minimal build flow:
  - `npx tsc -p .` to compile TS into `dist/`
  - for React UI use Vite/Rollup to emit `dist/popup/*` and a `popup.html`
- Dev test: load the folder containing `manifest.json` and the compiled `dist/` into `chrome://extensions` → Load unpacked

3) VS Code extension (apps/vscode-ext)
- Required changes to `package.json`:
  - add `publisher`, `contributes.commands`, `activationEvents` (e.g. `onCommand:ai-auditor.analyze`)
  - add devDependencies: `typescript`, `@types/node`, `@types/vscode` (or use `vscode` devDependency) and build script `tsc -p .`
- Add `tsconfig.json` configured for `module: commonjs`, `target: es2020`, `outDir: out` (or `dist`)
- Ensure `src/extension.ts` compiles to `out/extension.js` and `main` in package.json points to `out/extension.js`
- Dev test: open `apps/vscode-ext` in VS Code and press F5 (Extension Development Host)

4) Basic CI / checks (optional but recommended)
- Add a simple `build` GitHub Action that runs `pnpm install` (or `npm ci`) and `pnpm -w -r run build`
- Lint/type-check steps for TS packages

5) Packaging
- Browser: when ready, pack the directory or use a build pipeline to zip `manifest.json` + `dist/` + `popup/` as the release artifact
- VS Code: use `vsce package` to create a `.vsix` (requires `publisher` in `package.json`)

6) Minimal files I recommend adding now (these are the smallest changes to make both buildable):
- `extensions/package.json` (workspaces + root build script)
- `extensions/tsconfig.base.json`
- `extensions/apps/browser-ext/package.json` + `tsconfig.json` + `src/background.ts` -> compiles to `dist/background.js`
- fix `manifest.json` to point to `dist/background.js` and add `content_scripts` that point to `dist/content.js`
- `extensions/apps/vscode-ext/tsconfig.json` + update `package.json` with `contributes` and devDependencies

7) Example commands
```bash
# build browser extension only
cd extensions/apps/browser-ext
npx tsc -p .

# build vscode extension only
cd extensions/apps/vscode-ext
npx tsc -p .

# workspace-wide build (if using pnpm workspace)
cd extensions
pnpm install
pnpm -w -r run build
```

8) Verification checklist
- After building, verify `dist/` exists and contains JS files referenced by `manifest.json`.
- For Chrome: Load unpacked extension from `extensions/apps/browser-ext` (make sure `manifest.json` and `dist/` are present).
- For VS Code: open `extensions/apps/vscode-ext` in VS Code and press F5; check that extension activates and the command `ai-auditor.analyze` appears in the command palette.

If you want, I can now apply the minimal changes automatically: create `extensions/package.json`, `tsconfig.base.json`, `apps/*/tsconfig.json`, add `background.ts`, and update `manifest.json` & `apps/vscode-ext/package.json` `contributes`/`activationEvents`. Say "do it" and I'll implement the edits.


