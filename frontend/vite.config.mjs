// import { defineConfig, loadEnv } from 'vite';
// import react from '@vitejs/plugin-react';

// export default defineConfig(({ mode }) => {
//   // Load environment variables based on the current mode
//   const env = loadEnv(mode, process.cwd());
//   console.log('Loaded VITE_API_URL:', env.VITE_API_URL);
//   console.log('>> mode:', mode);
//   console.log('>> full env object:', env);
//   return {
//     plugins: [react()],
//     server: {
//       port: parseInt(env.VITE_PORT) || 3000,
//       proxy: {
//         '/api': {
//           target: env.VITE_API_URL,
//           changeOrigin: true,
//         },
//       },
//     },
//     define: {
//       __API_URL__: JSON.stringify(env.VITE_API_URL),
//     },
//   };
// });

import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const rootDir = resolve(__dirname, '..');  // Go up one level to project root

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, rootDir);  // ⬅️ this is the key change

  console.log('Loaded VITE_API_URL:', env.VITE_API_URL);

  return {
    plugins: [react()],
    server: {
      port: parseInt(env.VITE_PORT) || 3000,
      proxy: {
        '/api': {
          target: env.VITE_API_URL,
          changeOrigin: true,
          secure: true,
          rewrite: (path) => path.replace(/^\/api/,''),
        },
      },
    },
    define: {
      __API_URL__: JSON.stringify(env.VITE_API_URL),
    },
  };
});