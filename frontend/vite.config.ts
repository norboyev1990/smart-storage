import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // allow opening the dev server through an HTTPS tunnel (ngrok) for testing inside Telegram
  server: { allowedHosts: ['.ngrok-free.app', '.ngrok.app'] },
})
