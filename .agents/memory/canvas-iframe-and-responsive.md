---
name: Canvas preview width & stats-table responsiveness
description: Why "tiny/tangled table" complaints about the Replit canvas preview are usually zoom, not CSS — and why responsive table→card CSS collapses here.
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

# .stats-table sits in a shrink-to-fit ancestor — table→card CSS collapses

The statistics tables (`.stats-table`, e.g. TradeProductsTable "Produits") live
inside an ancestor that is **shrink-to-fit**. A normal `display:table` element
shrink-wraps to its content (so it renders full/fine). But the standard responsive
pattern of converting the table to cards via
`table/tbody/tr/td { display:block; width:100% }` makes the cells **collapse to
~min-content (≈1 char wide)** — labels and product names then wrap one letter per
line. Adding `display:block; width:100%; box-sizing:border-box` to all of
table+tbody+tr+td did **not** fix it; the collapse comes from the shrink-to-fit
ancestor, not the table element.

**Why:** in a shrink-to-fit container, `width:100%` on a block child is circular
and resolves to min-content; a `display:table` child instead shrink-wraps wide.

**How to apply:** don't attempt CSS table→block card conversion for `.stats-table`
without first giving the wrapper a definite width. And remember (above) it wouldn't
help the canvas view anyway. The baseline (table with `overflowX:auto` +
`minWidth:760`) already scrolls cleanly at narrow real widths.
