import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1, // all tabs share one real Python Demo session
  use: { baseURL: "http://127.0.0.1:4193", trace: "retain-on-failure" },
  webServer: {
    command: "python -m snapshot_loader.demo_server --port 4193",
    cwd: "..",
    url: "http://127.0.0.1:4193",
    reuseExistingServer: false,
  },
  projects: [
    { name: "desktop", use: { viewport: { width: 1440, height: 800 } } },
    { name: "laptop", use: { viewport: { width: 1280, height: 800 } } },
    { name: "mobile", use: { viewport: { width: 390, height: 844 } } },
  ],
});
