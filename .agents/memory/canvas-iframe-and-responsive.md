---
name: Canvas preview width & mobile stats tables
description: Why "tiny/tangled table" canvas complaints are zoom not CSS, and the working mobile pattern for stats tables (separate JSX cards toggled via Tailwind md:hidden, not CSS table→block).
---

# Canvas preview renders at a fixed 1920px width

The running app is embedded on the canvas as a **fixed 1920×1080 artifact iframe**
(confirmed via `getCanvasState`). The app inside therefore always sees
`window.innerWidth ≈ 1920` → it always renders the **desktop** layout, regardless
of how small the user's canvas viewport looks.

**Consequence:** CSS `@media (max-width: …)` breakpoints **never fire** in the
canvas preview. When the user reports a table/page looks "tiny", "tangled",
"illisible/enchevêtré" *in the canvas preview*, the usual cause is that the canvas
is **zoomed out** (the full 1920px-wide app shrunk into a small window), NOT a CSS
overlap bug.

**How to apply:**
- First verify the real layout at desktop width with a direct `app_preview`
  screenshot (it renders ~1280px). If it's clean there, the table is fine.
- The fix is user-side: tell them to click the **Preview button above the frame**
  to view full-size, or zoom in on the canvas. Do not keep shipping invisible CSS.
- Artifact iframes can't be freely resized, so you can't force a narrow render.

# Mobile layout for stats tables: separate JSX cards, NOT CSS table→block

The statistics data tables (`.stats-table`, e.g. TradeProductsTable "Produits") are
unreadable on phones — the wide fixed-layout table just shrinks/scrolls. The
**working** mobile pattern here:

- Render the existing `<table>` AND a **separate JSX card list** built from the same
  data array; toggle with Tailwind — table = `hidden md:block`, cards = `md:hidden`
  (breakpoint 768px, matching `mobile.css`). Cards are plain flex/grid divs styled
  in `statistics.css` (dark-theme tokens). This is the pattern to reuse for the
  other stats tables.
- Do **NOT** use a CSS table→block conversion (the `.mobile-optimized-table`
  `td{display:flex}` pattern in `mobile.css`) for these tables — it's fragile and
  uses light-theme colors.

**Why:** an earlier attempt to collapse `.stats-table` into cards via CSS looked
like a "shrink-to-fit ancestor" bug, but that was an artifact of a temp debug
wrapper — the real table sits in a full-width `.stats-chart-card`. Separate JSX
cards sidestep the whole question and style cleanly for the dark theme.

**How to verify mobile (<768px):** neither `app_preview` (~1280px) nor the canvas
(1920px) can show the mobile breakpoint, and Playwright isn't installed. To see the
cards, temporarily flip the Tailwind toggles to force them visible at desktop width
(and temp-hide `.stats-hero` to bring them above the fold), screenshot, then revert.
