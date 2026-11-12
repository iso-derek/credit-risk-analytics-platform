import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development the React app runs on :5173 and forwards /api to FastAPI on :8000.
// In production FastAPI serves the built files from web/dist on one address.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
});
