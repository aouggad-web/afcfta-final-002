# AfCFTA Frontend

This frontend is a React/Vite application. Use **npm** as the package manager for reproducible installs.

## Package manager policy

- `package-lock.json` is the canonical dependency lockfile.
- Do not commit Yarn artifacts such as `yarn.lock`, `.yarnrc.yml`, or `.yarn/`.
- Install dependencies with `npm ci` in CI and `npm install` for local updates.

## Available scripts

Run commands from the `frontend/` directory:

### `npm run dev`

Starts the Vite development server on `0.0.0.0`.

### `npm test -- --run`

Runs the Vitest test suite once.

### `npm run build`

Builds the production bundle with Vite.

### `npm run preview`

Serves the built application locally with Vite preview.
