---
name: Importing a GitHub PR into a diverged local main
description: How to bring a specific GitHub PR's changes into this repo when git apply/merge/checkout are blocked and local main has diverged from GitHub.
---

# Importing a specific GitHub PR's changes

This repo's Replit local `main` has **diverged** from the GitHub `origin/main` (local is typically *ahead* with Replit-side commits; GitHub has its own copilot/codex/PR history). So "import the changes" rarely means a plain pull/merge.

**Constraint:** in the main agent, all mutating git commands are blocked — not just commit/reset/checkout but also `git apply` (it writes to `.git/objects`). So you cannot apply a patch via git.

**Reliable workflow to import one PR (e.g. PR #126):**
1. Identify the PR via the public GitHub API: `GET https://api.github.com/repos/aouggad-web/afcfta-final-002/pulls/<N>` → title, state, head sha, changed_files. (The `listConnections('github')` connector returned 401 in at least one session; the **public** REST API worked unauthenticated since the repo is public.)
2. Download the unified diff: `curl -L -H "Accept: application/vnd.github.v3.diff" .../pulls/<N>` to `/tmp/pr<N>.diff`. Read it fully.
3. **Apply each hunk manually** with the edit/write tools. First read the local target files to confirm they still match the PR's "before" context (they usually do for the touched regions even when the branch overall diverged). Create new files with write.
4. Verify: run the PR's own tests + the surrounding suite, restart the workflow, curl the new endpoints, confirm the frontend hot-updates without compile errors.

**Why manual:** `git fetch origin pull/<N>/head` also came back empty/failed in this environment, and `git apply` is blocked — so the API-diff + manual-edit path is the dependable one.

**Faster path for a full-main sync (not a single PR), e.g. "import the latest changes":** the local Replit checkpoint commits sit on top of the last pushed fork point, and that fork point is the merge-base with `origin/main`. So: `GET /repos/<repo>/compare/<forkpoint-sha>...main` to list changed files, then **overwrite whole files** by fetching raw content (`GET /repos/<repo>/contents/<path>?ref=main` with `Accept: application/vnd.github.raw`) and writing them locally — no hunk-patching needed. This is safe because the local *code* files still match the fork point (only news_cache.json / docs diverge via checkpoints), so a whole-file overwrite == applying the upstream diff. `package.json` unchanged across the range ⇒ no new npm deps; verify new imports resolve anyway. The `listConnections('github')` token works for read/compare/contents but lacks `workflow` scope.

**Backend reload caveat:** `start.sh` runs uvicorn with `--workers 1` and **no `--reload`**, so imported backend route/service changes only take effect after `restart_workflow("Start application")`. Frontend is Vite with HMR (picks up new/changed files live; a new export triggers a full reload, logged as "Could not Fast Refresh (new export)" — that's normal, not an error).

**Note:** `attached_assets/` is the conversation attachment area (untracked); files there are not part of your deliverable — leave them alone.
