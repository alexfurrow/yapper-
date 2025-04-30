import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { loadEnv } from 'vite'
import { dirname, resolve } from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const rootDir = dirname(__filename)

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, rootDir)
  console.log('FULL ENV:', env);
  console.log('Loaded ENV from:', __dirname);
  console.log('Loaded VITE_API_URL:', env.VITE_API_URL);

  return {
    plugins: [react()],
    server: {
      port: parseInt(env.VITE_PORT) || 3000,
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://127.0.0.1:5000',
          changeOrigin: true,
          secure: true,
        },
      },
    },
    define: {
      __API_URL__: JSON.stringify(env.VITE_API_URL || 'http://127.0.0.1:5000'),
    },
  };
});