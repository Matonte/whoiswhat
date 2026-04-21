import path from "node:path"
import { defineConfig, loadEnv } from "vite"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"

// Dev mode proxies the three Flask services under /api/*  so the browser
// never hits them cross-origin. In production, set VITE_*_URL to the public
// URLs and enable flask-cors on each service for the portal's origin.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "")
  const WHOISWHAT = env.VITE_WHOISWHAT_URL || "http://127.0.0.1:5000"
  const WHOISHOSS = env.VITE_WHOISHOSS_URL || "http://127.0.0.1:5002"
  const ADVISOR = env.VITE_ADVISOR_URL || "http://127.0.0.1:5003"

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    server: {
      port: 5173,
      host: true,
      proxy: {
        "/api/whoiswhat": {
          target: WHOISWHAT,
          changeOrigin: true,
          rewrite: (p) => p.replace(/^\/api\/whoiswhat/, ""),
        },
        "/api/whoishoss": {
          target: WHOISHOSS,
          changeOrigin: true,
          rewrite: (p) => p.replace(/^\/api\/whoishoss/, ""),
        },
        "/api/advisor": {
          target: ADVISOR,
          changeOrigin: true,
          rewrite: (p) => p.replace(/^\/api\/advisor/, ""),
        },
      },
    },
  }
})
