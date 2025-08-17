# Curestry — UI Elements (Draft)

A quick set of basic components and patterns for the hackathon. Written in Markdown for easy copy-paste of texts and states. Style: minimal, calm colors, emphasis on readability and speed.

---

## 1) Brand Basics

**Colors (Design Tokens):**

- `--text`: #ffffff

- `--background`: #1a1a1a

- `--primary`: #2AC8AA

- `--secondary`: #b9d1cc

- `--accent`: #27c7fb

- `--info`: #3F51B5

- `--success`: #43A047

- `--warning`: #FFC107

- `--error`: #EF4444

- `--border`: #333333

- `--muted`: #888888

**Typography (updated):**

- Headings — `Montserrat`
- Body/UI — `Open Sans`

**Headings — Montserrat**

- **H1** — Bold, 48px, line-height 58px, letter-spacing -0.3px

- **Subtitle 1** — Regular, 48px, line-height 58px, letter-spacing -0.3px

- **H2** — Bold, 40px, line-height 48px, letter-spacing -0.3px

- **Subtitle 2** — Regular, 40px, line-height 48px, letter-spacing -0.3px

- **H3** — Bold, 32px, line-height 40px, letter-spacing -0.3px

- **Subtitle 3** — Regular, 32px, line-height 40px, letter-spacing -0.3px

- **H4** — Bold, 28px, line-height 34px, letter-spacing -0.1px

- **Subtitle 4** — Regular, 28px, line-height 34px, letter-spacing -0.1px

- **H5** — Bold, 24px, line-height 28px, letter-spacing -0.1px

- **Subtitle 5** — Regular, 24px, line-height 28px, letter-spacing -0.1px

**Body — Open Sans**

- **Text L Bold** — Bold, 20px, line-height 24px, letter-spacing -0.3px

- **Text L** — Regular, 20px, line-height 24px, letter-spacing -0.3px

- **Text M SemiBold** — SemiBold, 16px, line-height 22px, letter-spacing 0

- **Text M** — Medium, 16px, line-height 22px, letter-spacing 0

- **Text S SemiBold** — SemiBold, 14px, line-height 20px, letter-spacing 0

- **Text S** — Medium, 14px, line-height 20px, letter-spacing 0

- **Text XS SemiBold** — SemiBold, 12px, line-height 16px, letter-spacing 0

- **Text XS** — Medium, 12px, line-height 16px, letter-spacing 0

**Design Tokens — fonts**

```
--font-heading: 'Montserrat', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
--font-body: 'Open Sans', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
```

**CSS cheatsheet (utilities/mixins)**

```
.h1{font-family:var(--font-heading);font-weight:700;font-size:48px;line-height:58px;letter-spacing:-0.3px}
.subtitle1{font-family:var(--font-heading);font-weight:400;font-size:48px;line-height:58px;letter-spacing:-0.3px}
.h2{font-family:var(--font-heading);font-weight:700;font-size:40px;line-height:48px;letter-spacing:-0.3px}
.subtitle2{font-family:var(--font-heading);font-weight:400;font-size:40px;line-height:48px;letter-spacing:-0.3px}
.h3{font-family:var(--font-heading);font-weight:700;font-size:32px;line-height:40px;letter-spacing:-0.3px}
.subtitle3{font-family:var(--font-heading);font-weight:400;font-size:32px;line-height:40px;letter-spacing:-0.3px}
.h4{font-family:var(--font-heading);font-weight:700;font-size:28px;line-height:34px;letter-spacing:-0.1px}
.subtitle4{font-family:var(--font-heading);font-weight:400;font-size:28px;line-height:34px;letter-spacing:-0.1px}
.h5{font-family:var(--font-heading);font-weight:700;font-size:24px;line-height:28px;letter-spacing:-0.1px}
.subtitle5{font-family:var(--font-heading);font-weight:400;font-size:24px;line-height:28px;letter-spacing:-0.1px}

.text-l-bold{font-family:var(--font-body);font-weight:700;font-size:20px;line-height:24px;letter-spacing:-0.3px}
.text-l{font-family:var(--font-body);font-weight:400;font-size:20px;line-height:24px;letter-spacing:-0.3px}
.text-m-sb{font-family:var(--font-body);font-weight:600;font-size:16px;line-height:22px;letter-spacing:0}
.text-m{font-family:var(--font-body);font-weight:500;font-size:16px;line-height:22px;letter-spacing:0}
.text-s-sb{font-family:var(--font-body);font-weight:600;font-size:14px;line-height:20px;letter-spacing:0}
.text-s{font-family:var(--font-body);font-weight:500;font-size:14px;line-height:20px;letter-spacing:0}
.text-xs-sb{font-family:var(--font-body);font-weight:600;font-size:12px;line-height:16px;letter-spacing:0}
.text-xs{font-family:var(--font-body);font-weight:500;font-size:12px;line-height:16px;letter-spacing:0}
```

**Spacing:** 4 / 8 / 12 / 16 / 24 / 32 / 48

**Radius:** 10–16 (large elements 16, small 10)

---

## 2) Buttons

**Variants:**

- `Primary` — main action (e.g. “Check”)
- `Secondary` — secondary (“Preview”, “Show details”)
- `Tertiary`/ghost — no fill (“Help”, “Cancel”)
- `Danger` — destructive (“Revert change”)
- `Success` — confirmative (“Apply all”)

**States:** `default`, `hover`, `pressed`, `loading`, `disabled`.

**Sizes:** `S (28)`, `M (36)`, `L (44)` height; icon left 16px.

**Microcopy:**

- Primary: *Check*, *Apply*, *Run tests*
- Secondary: *Compare versions*, *Show risks*
- Danger: *Revert*, *Delete fix*

**Examples (Markdown):**

```
[Check] [Apply all] [Compare versions] [Revert]
```

---

## 3) Inputs

**Types:** text, textarea (prompt), select, combobox (tool search), toggle, checkbox, radio.

**States:** `default`, `focus`, `error`, `success`, `disabled`.

**Placeholders:** “Describe the agent goal…”, “Add a fact source (URL)…”

**Inline help / validation:**

- error: “At least one fact source required”
- hint: “Use imperative and explicit length limits”

---

## 4) Tags & Badges

- `risk-high` (danger): “Hallucination risk”
- `risk-medium` (warning): “Ambiguous phrasing”
- `risk-low` (muted): “Minor style”
- Suggestion statuses: `Accepted`, `Rejected`, `Waiting for input`

Example: `🏷️ Risk: high`, `✅ Accepted`, `❓ More data needed`

---

## 5) Toasts & Notifications

- Success: “Check complete. 3 improvements found”
- Warning: “Not enough context. Please specify answer style”
- Error: “Simulation failed. Try again”
- Info: “New reviewer rules available”

Lifecycle: 4–6 sec, pause on hover, `Cancel` button for revert.

---

## 6) Modals & Side Panels

**Confirmation modal:**

- Title: “Apply 5 fixes?”
- Text: “Quick regression check passed.”
- Buttons: `Apply` (primary), `Cancel` (ghost)

**Side panel “Analysis details”:**

- Tabs: *Risks*, *Suggestions*, *Simulation logs*
- Sticky-footer: `Apply all` · `Revert` · `Export diff`

---

## 7) Inline Annotations

- Wavy underline for risky spots.
- Hover hint: short reason + CTA: `Fix` · `Show example` · `Hide`.
- Colors: high risk — danger; medium — warning; low — muted.

Hint card format:

```
[ID]: PROMPT-12
Reason: Ambiguity in phrase “describe in detail”.
Solution: Specify length and answer format.
[Fix] [Add constraint] [Ignore]
```

---

## 8) Suggestions List

**Row structure:**

- checkbox | title | reason | tags (risk, type) | actions (Accept / Reject)

**Types of suggestions:**

- “Clarify fact source” (context)
- “Add test for contextual error” (quality)
- “Normalize answer style” (tone)

**Bulk actions:** `Accept selected`, `Reject`, `Export patch`.

---

## 9) Diff Viewer

- Modes: `Unified` / `Split`
- Highlight: additions (`--diff-add`) / deletions (`--diff-del`)
- Toggle: “Show only significant changes”
- CTA: `Apply`, `Revert`, `Create branch`

Example title: `Prompt v14 → v15 · 5 changes · simulation: pass`.

---

## 10) Progress & Loading

- `Progress bar` for analysis: steps `Parsing → Risks → Suggestions → Simulation → Done`
- `Skeleton` for suggestions list (3–6 rows)
- `Spinner` inside buttons in `loading` state

Progress text: “Step 3/5: simulation (12 scenarios)”

---

## 11) Tables & Test Results

**Bench table:**

- Columns: `Scenario`, `Metric`, `Threshold`, `Result`, `Logs` (link)
- Filters: `All / Failed / Warn`
- Status chip pattern: `Pass` (success), `Warn` (warning), `Fail` (danger)

**Empty states:**

- “No tests yet. [Create base bench]”

---

## 12) Navigation

- Top bar: logo · search · `Check` button · icons: history, notifications, help
- Left column: `Projects`, `Prompts`, `Rules`, `Tests`, `History`
- Breadcrumbs: Project / Prompt / Version v15
- Command palette (⌘K): “Check”, “Open diff”, “Create test”

---

## 13) Versioning

- Version card: `v15 • 17:42 • 5 fixes • author: Agent-Fix`
- Actions: `View diff` · `Revert` · `Mark stable`
- Filter: `All / Regression-pass / Drafts`

---

## 14) Clarifying Questions

Component `Prompt`: small modal/banner with a question and quick answers.

**Examples:**

- “Specify answer style: *formal / friendly / brief*.”
- “Is there a reliable fact source (URL)?”
- “Max answer length (chars)?”

Buttons: quick chips + free input field.

---

## 15) Alerts

- Danger: “Conflict detected between system and user prompt.”
- Warning: “Semantic entropy above threshold in 3 scenarios.”
- Info: “New detector `RAG-oracle` added. Check settings.”

Alert includes “Fix now” link → opens side panel.

---

## 16) Icons & Shortcuts

- Icons: Lucide/Feather-like, 16/20px
- Hotkeys: `⌘K` palette, `⌘Enter` — Check, `A` — Accept suggestion, `D` — Reject, `V` — View diff

---

## 17) Accessibility (A11y)

- Contrast ≥ 4.5 for text
- Focus outline: 2px `--primary`
- ARIA roles: `alert`, `status`, `dialog`
- Clear button texts (not “Ok”, but “Apply”)

---

## 18) Curestry-Specific Patterns

**Main flow:**

1. User writes prompt → `Check`
2. Progress + inline highlights appear
3. Side panel “Analysis details”: default tab *Suggestions*
4. `Apply all` or selective → `Revert` available
5. Tests auto-run (can repeat)

**Quick actions (action bar):** `Check` · `Compare versions` · `Create test` · `Export` (JSON/patch)

---

## 19) Text Templates

- Buttons: “Check”, “Apply all”, “Run tests”, “Revert”, “Compare versions”, “Export diff”
- Placeholders: “Describe the agent goal…”, “Add URL source…”, “Specify answer style…”
- Toasts: “Check complete”, “Need clarifications”, “Revert applied”
- Hints: “Add explicit answer format (JSON/table/text)”

---

## 20) README Component Section Example

```
### Button — Primary
Purpose: main action.
States: default / hover / loading / disabled
Text: verb in imperative (≤ 2 words)
Hotkey: ⌘Enter (if action is “Check”)
```

---

## 21) Optional Cuts (if no time)

- Empty states → replace with short phrase
- Log table → link “Download logs”
- Unified diff mode → keep only Split

---

## 22) UI Readiness Checklist

-

---

**Done.** This file covers the minimum for Curestry hackathon demo. Add screenshots/links as they appear.
