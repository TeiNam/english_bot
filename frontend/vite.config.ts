import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
 const env = loadEnv(mode, '.');

 return {
   plugins: [react()],
   optimizeDeps: {
     exclude: ['lucide-react'],
   },
   server: {
     host: '0.0.0.0',
     port: Number(env.VITE_PORT) || 5174,
     hmr: {
       protocol: 'wss',
       host: env.VITE_WEB_URL || 'localhost:8000',
       clientPort: 443
     },
     proxy: {
       '/api': {
         target: env.VITE_API_URL || 'http://localhost:8000',
         secure: false,
         changeOrigin: true,
         rewrite: (path) => path.replace(/^\/api/, '')
       }
     }
   }
 };
});