# AI Auditor VS Code Extension - Release Notes

This file documents releases for the `ai-auditor-vscode` extension. Each section contains the version, release date, and a short summary of changes. Where possible, a diff-style summary of changed files is included.

## v0.1.0 - (unreleased)

- **Bumped version**: `0.0.1` -> `0.1.0`
- **Added**: `description` field to `package.json`.
- **Added**: `RELEASE_NOTES.md` (this file).

Diff summary:

```diff
--- a/extensions/apps/vscode-ext/package.json
+++ b/extensions/apps/vscode-ext/package.json
@@
-  "version": "0.0.1",
+  "version": "0.1.0",
+  "description": "Analyze and suggest improvements to selected text using local or remote helpers.",
```

---

## v0.0.1 - initial

- Initial scaffolding and command `ai-auditor.analyze`.


