# AI Auditor + Revizor (Chat Draft Grabber)

Commands:
- Revizor: Grab Chat Draft (`revizor.grabNow`)
- Revizor: Apply Revised Text (`revizor.applyRevised`)
- Revizor: Open Diagnostics (`revizor.diagnostics.open`)

Settings:
- `revizor.methods.enabled`: ["uia","simCopy","interactiveCopy"]
- `revizor.privacy.noClipboard`: boolean
- `revizor.ui.showPreview`: boolean

Notes:
- Windows uses UI Automation first, then simulated Copy via PowerShell.
- macOS uses simulated Copy via AppleScript (requires Accessibility permission).
- Linux falls back to interactive copy/paste using clipboard.

