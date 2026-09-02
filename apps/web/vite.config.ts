import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  const environment = loadEnv(mode, '', '');

  return {
    plugins: [react()],
    // The internal formula-audit beta can run beside a normal local Vite
    // session. Give that development-only session its own optimizer cache so a
    // stale default server cannot lock the normal `.vite` directory.
    cacheDir: environment.WORKBOOKCARE_VITE_CACHE_DIR || undefined,
    server: {
      port: 5173,
      strictPort: true,
    },
    preview: {
      port: 4173,
      strictPort: true,
    },
    test: {
      environment: 'jsdom',
      setupFiles: './src/test/setup.ts',
      css: true,
    },
  };
});
