import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { reactClickToComponent } from "vite-plugin-react-click-to-component";

export default defineConfig({
  plugins: [react(), tailwindcss(), reactClickToComponent()],
  resolve: {
    alias: {
      "@": "/src",
    },
  },
  server: {
    host: "0.0.0.0",
    port: 8909,
    // https: tls,
    open: true, // 在开发服务器启动时自动在浏览器中打开应用程序
    proxy: {
      "/api/": {
        // 要代理的地址
        target: "http://10.0.87.111:8080/",
        changeOrigin: false,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    }, // 代理
    cors: true, // 为开发服务器配置 CORS
  },
});
