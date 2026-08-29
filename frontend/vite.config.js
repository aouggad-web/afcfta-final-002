/// <reference types="vitest/config" />
import { defineConfig } from 'vite';
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
        target: process.env.VITE_BACKEND_URL || 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/banking': {
        target: process.env.VITE_BACKEND_URL || 'http://localhost:8000',
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
