---
name: GitHub Actions npm "Exit handler never called!"
description: Why the afcfta CI frontend-build kept failing and why it was switched to yarn
---

On the GitHub Actions Ubuntu runner, `npm ci` (frontend job) crashes instantly with
`npm error Exit handler never called!`. The crash is intrinsic to the runner's npm —
it happens with the bundled npm AND with any `npm install -g npm@X` pin (10.8.2,
10.9.2 all reproduce). `npm config set ...` works fine; only `npm ci` dies.

**The dangerous part:** the crash exits 0 (the exit handler that would set the error
code never runs), so the install step is marked SUCCESS while `node_modules` stays
empty. The failure only surfaces later as `sh: 1: vite: not found` (exit 127) in the
build step, because `vite` is a devDependency that never got installed.

**Why:** pinning/reinstalling npm does NOT fix it — the bug is in the runner's npm
itself, not the self-reinstall. Chasing npm versions wastes iterations.

**How to apply / the fix that worked:** switch the frontend job from npm to yarn.
yarn 1.22 is preinstalled on the runner and `frontend/yarn.lock` exists, so:
`yarn install --frozen-lockfile || yarn install` then `yarn build`. Drop the
`cache: npm` setup-node option (or switch to `cache: yarn`). yarn installs
devDependencies by default, so vite is present and the build passes.

**Constraint:** the GitHub connection OAuth token lacks the `workflow` scope, so
`.github/workflows/*` cannot be edited by the agent — the user must paste/commit
ci.yml changes in the GitHub web UI (full-file replace is the most reliable; Copilot
auto-fix PRs repeatedly failed to remove the offending step).
