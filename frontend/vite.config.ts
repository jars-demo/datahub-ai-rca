import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

const BACKEND = process.env.RCA_BACKEND_URL ?? 'http://127.0.0.1:8300';

// Proxy the API and its docs so a single forwarded port (5173) is enough.
export default defineConfig({
    plugins: [react()],
    server: {
        host: '127.0.0.1',
        port: 3300,
        strictPort: true,
        proxy: {
            '/api': BACKEND,
            '/docs': BACKEND,
            '/openapi.json': BACKEND,
        },
    },
});
