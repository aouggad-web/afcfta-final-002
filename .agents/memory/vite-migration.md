---
name: Vite migration from CRA
description: Why react-scripts was replaced with Vite and what was changed
---

# Vite Migration

## Rule
This project uses Vite (not Create React App / react-scripts).

**Why:** react-scripts pulls in `shell-quote` which is blocked by Replit's security firewall (critical CVE). Vite has no such dependency.

## Key changes made
- `frontend/package.json`: removed react-scripts, craco, added `@vitejs/plugin-react` and `vite`; set `"type": "module"`
- `frontend/vite.config.js`: created with JSX loader for `.js` files, proxy to backend port 8000, port 5000
- `frontend/index.html`: created root HTML entry point (Vite standard)
- `frontend/postcss.config.cjs` / `tailwind.config.cjs`: renamed from `.js` to `.cjs` because `"type": "module"` in package.json
- All `process.env.REACT_APP_BACKEND_URL` → `import.meta.env.VITE_BACKEND_URL`
- `process.env.NODE_ENV === 'production'` → `import.meta.env.PROD`
- TypeScript `interface` syntax removed from `.jsx` files (data-freshness-indicator.jsx)
- `require()` leaflet image imports → ESM `import` statements in LogisticsMap.jsx
- CSS `@import` must come before `@tailwind` directives in index.css

## How to apply
- Always use `npm run start` (calls `vite --host 0.0.0.0 --port 5000`)
- Config files using `module.exports` must have `.cjs` extension
- New `.js` files containing JSX are handled by esbuild loader override in vite.config.js
