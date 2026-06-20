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

**Note:** `attached_assets/` is the conversation attachment area (untracked); files there are not part of your deliverable — leave them alone.
