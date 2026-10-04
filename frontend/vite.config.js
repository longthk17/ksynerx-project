import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const proxy = {
    '/inventory-api': { target: env.INVENTORY_TARGET || 'http://127.0.0.1:8000', changeOrigin: true, rewrite: path => path.replace(/^\/inventory-api/, '/api/v1') },
    '/cdm-api': { target: env.CDM_TARGET || 'http://127.0.0.1:8001', changeOrigin: true, rewrite: path => path.replace(/^\/cdm-api/, '/api/v1') },
  };
  return { plugins: [react()], server: { port: 5173, strictPort: true, proxy }, preview: { proxy } };
});
