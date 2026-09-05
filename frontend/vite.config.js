/// <reference types="vitest/config" />
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// Configuration HMR (Hot Module Replacement) — CAUSE DU BUG « l'app revient au
// dashboard / la page se recharge toute seule chaque minute ».
// Derrière un reverse-proxy / ingress Kubernetes (cas Emergent), le websocket
// HMR par défaut tente de se connecter au port INTERNE de Vite (ex. 3000),
// que l'ingress ne route pas : la connexion est coupée au bout de ~60 s et le
// client Vite déclenche un rechargement COMPLET de la page — qui réinitialise
// la SPA sur sa vue par défaut (dashboard).
// Deux échappatoires, pilotées par variable d'environnement :
//   • VITE_HMR=off              → désactive HMR (recommandé en preview/déploiement,
//                                  pas de dev à chaud : supprime la boucle de reload)
//   • VITE_HMR_CLIENT_PORT=443  → HMR passe par l'ingress (avec VITE_HMR_PROTOCOL=wss
//     VITE_HMR_PROTOCOL=wss        et éventuellement VITE_HMR_HOST=<domaine public>)
// Sans aucune de ces variables : comportement Vite par défaut (dev local OK).
const hmr = (() => {
  const flag = (process.env.VITE_HMR || '').toLowerCase();
  if (flag === 'off' || flag === 'false' || flag === '0') return false;
  const clientPort = process.env.VITE_HMR_CLIENT_PORT;
  const host = process.env.VITE_HMR_HOST;
  if (!clientPort && !host) return undefined; // défaut Vite
  return {
    ...(host ? { host } : {}),
    ...(clientPort
      ? { clientPort: Number(clientPort), protocol: process.env.VITE_HMR_PROTOCOL || 'wss' }
      : {}),
  };
})();

// VITE_BACKEND_URL / REACT_APP_BACKEND_URL — DEUX noms pour la même URL backend,
// CAUSE D'UN BUG SILENCIEUX : le code de l'app ne lit que VITE_BACKEND_URL
// (import.meta.env, ~100 usages), mais la synchronisation automatique
// d'environnement d'Emergent ne tient à jour que REACT_APP_BACKEND_URL (nom
// hérité de l'époque Create React App). Les deux dérivent l'une de l'autre
// sans jamais se resynchroniser, laissant VITE_BACKEND_URL figé sur une URL
// de preview périmée après un redéploiement — l'app cible alors un backend
// mort en silence (pas d'erreur de build, juste des requêtes qui échouent).
// On complète ici VITE_BACKEND_URL depuis REACT_APP_BACKEND_URL s'il manque,
// AVANT que Vite ne résolve import.meta.env pour tout le reste du code.
// loadEnv() lit le fichier .env lui-même — process.env, à ce stade, ne
// contient QUE les vraies variables d'environnement du shell (pas encore les
// valeurs du fichier .env, que Vite ne fusionne dans process.env qu'à une
// étape interne ultérieure) ; VITE_BACKEND_URL explicite (shell ou fichier)
// garde donc toujours la priorité sur REACT_APP_BACKEND_URL, qui ne sert que
// de repli. Réaffecter le résultat dans process.env.VITE_BACKEND_URL fait
// que la résolution interne de Vite pour import.meta.env (qui fusionne aussi
// process.env, en lui donnant la priorité) reprend cette même valeur pour
// les ~100 fichiers qui la lisent, sans avoir à les toucher.
const _fileEnv = loadEnv(process.env.NODE_ENV || 'development', process.cwd(), '');
const _resolvedBackendUrl =
  process.env.VITE_BACKEND_URL ||
  _fileEnv.VITE_BACKEND_URL ||
  process.env.REACT_APP_BACKEND_URL ||
  _fileEnv.REACT_APP_BACKEND_URL ||
  '';
// Only assign when something was actually configured: an unset
// VITE_BACKEND_URL means "relative /api/... requests" throughout the app
// code (every `import.meta.env.VITE_BACKEND_URL || ''` fallback), and that
// behavior must survive unchanged — this must not invent a new default.
if (_resolvedBackendUrl) {
  process.env.VITE_BACKEND_URL = _resolvedBackendUrl;
}
// The dev-server proxy target is Node-only config (never exposed to the
// browser bundle), so it keeps its own localhost default independently.
const backendUrl = _resolvedBackendUrl || 'http://localhost:8000';

export default defineConfig({
  plugins: [react()],
  esbuild: {
    loader: 'jsx',
    include: /src\/.*\.[jt]sx?$/,
    exclude: [],
  },
  optimizeDeps: {
    entries: ['src/index.js'],
    esbuildOptions: {
      loader: {
        '.js': 'jsx',
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    host: '0.0.0.0',
    // Port et backend paramétrables par variable d'environnement : chaque
    // environnement (Emergent/K8s, sandbox, poste local) fixe la sienne dans
    // SON environnement (jamais dans ce fichier), pour ne plus jamais avoir
    // à patcher ce fichier après un `git reset`/déploiement. Défauts inchangés
    // (5000 / 8000) si rien n'est défini.
    port: Number(process.env.VITE_PORT || process.env.PORT) || 5000,
    allowedHosts: true,
    hmr,
    proxy: {
      '/api': {
        target: backendUrl,
        changeOrigin: true,
        secure: false,
      },
      '/banking': {
        target: backendUrl,
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    outDir: 'build',
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/setupTests.js',
    css: false,
    include: ['src/**/*.{test,spec}.{js,jsx}'],
  },
});
