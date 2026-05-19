import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
      },
    },
    server: {
      host: '0.0.0.0',
      port: Number(env.PORT || 3000),
    },
    define: {
      'process.env': {
        NODE_ENV: mode === 'production' ? 'production' : 'development',
        REACT_APP_API_KEY: env.REACT_APP_API_KEY || '',
        REACT_APP_BACKEND_URL: env.REACT_APP_BACKEND_URL || '',
      },
    },
  };
});
