import { chromium } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
const out = "design-reviews/c3-2/final-polish";
await mkdir(out, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 800 } });
const actual = [];
for (const mode of ["system", "noto"]) {
  await page.goto("http://127.0.0.1:4184/rich.html?present=1");
  if (mode === "system")
    await page.addStyleTag({
      content:
        '.material[data-variant="C32"] { --font-sans: -apple-system, BlinkMacSystemFont, "SF Pro Text", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei UI", system-ui, sans-serif; }',
    });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(250);
  await page.screenshot({ path: out + `/typography-${mode}-comparison.png` });
  const c = await page.context().newCDPSession(page);
  await c.send("DOM.enable");
  await c.send("CSS.enable");
  const d = await c.send("DOM.getDocument");
  const n = await c.send("DOM.querySelector", {
    nodeId: d.root.nodeId,
    selector: "h1",
  });
  actual.push({
    mode,
    ...(await c.send("CSS.getPlatformFontsForNode", { nodeId: n.nodeId })),
  });
  await c.detach();
}
await writeFile(
  out + "/typography-comparison-fonts.json",
  JSON.stringify(actual, null, 2),
);
await browser.close();
