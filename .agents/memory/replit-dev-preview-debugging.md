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

## Preview "unstable / reloads on every interaction" = orphaned dev servers, not CSS/HMR

**Symptom:** the full-page preview flickers and reloads constantly; browser console shows repeated `[vite] connecting... / connected` and `server connection lost. Polling for restart...` cycles.

**Root cause seen here:** workflow restarts left ORPHANED process trees (old `vite --port 5000` and `uvicorn server:app`) alive — they survive `restart_workflow` because they're outside the new workflow's process group. The stale Vite keeps port 5000, so the new Vite falls back to **5001** ("Port 5000 is in use, trying another one...") and the new backend fails with **`[Errno 98] address already in use`** on 8000. The preview pane (always 5000) is then served by the *stale* server while the live code runs on 5001 → reload loop.

**How to diagnose:** `ps aux | grep -E "uvicorn server:app|vite --host"` — more than ONE of each = orphans. Check the workflow log for `Port 5000 is in use` / `localhost:5001` / `address already in use`. (Note: `lsof`, `fuser`, `ss` are all absent in this NixOS env; use `ps` + `pkill -f`.)

**Fix (durable):** `start.sh` must (1) `pkill -9 -f` the stale `uvicorn server:app` and `vite --host 0.0.0.0 --port 5000` BEFORE launching, and (2) `trap cleanup TERM INT EXIT` to kill its own children on shutdown so they don't orphan next time. Verify after restart: exactly one uvicorn + one vite, both ports return 200, and the log shows `Local: http://localhost:5000/` (NOT 5001) with no "address already in use".
