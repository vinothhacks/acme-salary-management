import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  timeout: 90_000,
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  use: {
    baseURL: "http://localhost:5173",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: "python scripts/e2e_api.py",
      cwd: "..",
      url: "http://127.0.0.1:8000/health",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
    {
      command: "npm run dev",
      cwd: "../frontend",
      url: "http://localhost:5173",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
});
