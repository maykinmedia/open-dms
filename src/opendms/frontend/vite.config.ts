// eslint-disable-next-line import/no-unresolved
import react from "@vitejs/plugin-react";
import path from "path";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
  build: {
    assetsDir: "static", // Make sure Django can pick up assets.
  },
  plugins: [
    react({
      babel: {
        plugins: [["babel-plugin-react-compiler"]],
      },
    }),
  ],
  resolve: {
    alias: {
      "~": path.resolve(__dirname, "src"),
    },
  },
});
