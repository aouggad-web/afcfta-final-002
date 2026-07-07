/// <reference types="vitest/config" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

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
