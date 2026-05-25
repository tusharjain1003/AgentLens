import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig(function (_a) {
    var mode = _a.mode;
    var env = loadEnv(mode, ".", "");
    var backend = env.VITE_BACKEND_URL || "http://127.0.0.1:8765";
    return {
        plugins: [react()],
        server: {
            port: 5174,
            strictPort: true,
            proxy: {
                "/api": { target: backend, changeOrigin: true },
            },
        },
        build: {
            outDir: "dist",
            sourcemap: false,
        },
    };
});
