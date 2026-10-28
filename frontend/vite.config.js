import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// In development, forward API and admin requests to Django so the session
// and CSRF cookies stay on the same origin as the React page.
const DJANGO = process.env.DJANGO_URL || 'http://127.0.0.1:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': DJANGO,
      '/manage': DJANGO,
      '/static': DJANGO,
    },
  },
});
