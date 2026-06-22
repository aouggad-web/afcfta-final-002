---
name: Replit dev preview debugging
description: How to get ground truth when a frontend change "doesn't show" in the Replit preview, and how to inspect rendered layout without devtools.
---

# Diagnosing "my change isn't showing" in the Replit preview

**Rule:** The iframe preview proxy (`$REPLIT_DEV_DOMAIN`) returns an EMPTY body to `curl` / non-browser clients. Do NOT conclude an asset is stale, missing, or lacks a CSS rule from empty proxy-curl output — that is the proxy blocking the request, not the server.

**For ground truth of what the dev server actually serves, curl localhost instead**, e.g. `curl -s http://localhost:5000/src/components/Foo.jsx`. Vite dev serves source modules with `Cache-Control: no-cache`, and HMR reliably reaches the browser for both `.jsx` and `.css` (confirm via `[vite] hot updated: ...` lines in the browser console logs).

**Why:** In a table-layout bug, an empty `$REPLIT_DEV_DOMAIN` curl was misread as "the served CSS doesn't contain my rule," sending the investigation down a wrong "stale cache / service worker" path for a long time. The code was always live; the real bug was a CSS layout issue.

**How to apply when a UI change seems absent:**
1. `curl http://localhost:5000/<path>` to confirm the server serves the new code (NOT the proxy domain).
2. Check browser console logs for `[vite] hot updated` to confirm HMR delivered it.
3. Since you cannot open browser devtools here, inspect *actual rendered geometry* with a screenshot diagnostic: temporarily give the suspect element a bright `background` (and give each child/column a distinct color) and screenshot. This reveals true widths/positions and instantly shows whether the screenshot is live (the colors appear) and which element is collapsing/overflowing. The `app_preview` screenshot browser is separate from the user's HMR preview pane but DOES render live content (verified: a temporary red background appeared immediately).

**Layout note learned alongside this:** inline `table-layout: fixed` + `width:100%` on a `<table>` is not enough to control column distribution when a column has long/greedy content — the reliable fix is an explicit `<colgroup>` with authoritative `<col>` widths, plus letting long-text cells wrap (`white-space: normal; overflow-wrap: anywhere`).

**When a user repeatedly reports "the tables are broken" after you fixed one:** look for a *shared* CSS class and fix it at the source, not one table at a time. Many statistics tables in this app reuse the `.stats-table` class, whose `thead th { white-space: nowrap }` caused header overlap across all of them whenever columns were squeezed; setting headers to wrap (`white-space: normal`) fixed the whole class at once. Grep the class name to find every consumer before concluding a single-component fix is enough.
