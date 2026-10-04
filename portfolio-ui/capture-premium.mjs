import { chromium } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
const phase = process.argv[2] || "initial";
const out = `design-reviews/c3-1/${phase}`;
await mkdir(out, { recursive: true });
const browser = await chromium.launch();
const measurements = [];
for (const width of [1440, 1280, 390]) {
  const p = await browser.newPage({
    viewport: { width, height: 800 },
    deviceScaleFactor: 1,
  });
  const fonts = [];
  p.on("request", (r) => {
    if (/woff|ttf|otf/.test(r.url())) fonts.push(r.url());
  });
  await p.goto("http://127.0.0.1:4184/premium.html?present=1");
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(250);
  await p
    .locator(".design-stage")
    .screenshot({ path: `${out}/C3.1-${width}.png` });
  const values = await p.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    height: document.querySelector(".design-stage").getBoundingClientRect()
      .height,
    font: getComputedStyle(document.querySelector("h1")).fontFamily,
    body: getComputedStyle(document.querySelector(".explanation>p")).fontSize,
  }));
  const c = await p.context().newCDPSession(p);
  await c.send("DOM.enable");
  await c.send("CSS.enable");
  const d = await c.send("DOM.getDocument");
  const n = await c.send("DOM.querySelector", {
    nodeId: d.root.nodeId,
    selector: "h1",
  });
  const actualFonts = await c.send("CSS.getPlatformFontsForNode", {
    nodeId: n.nodeId,
  });
  measurements.push({
    width,
    ...values,
    actualFonts: actualFonts.fonts,
    fontRequests: fonts,
  });
  if (width === 1440) {
    await p.getByRole("button", { name: "预览人工审核", exact: true }).click();
    await p.waitForTimeout(250);
    await p.screenshot({ path: `${out}/C3.1-review-dialog.png` });
    await p.goto("http://127.0.0.1:4184/premium.html");
    await p.getByRole("button", { name: "控件与状态", exact: true }).click();
    await p.waitForTimeout(250);
    await p.screenshot({ path: `${out}/C3.1-controls.png` });
  }
  await p.close();
}
await writeFile(
  `${out}/measurements.json`,
  JSON.stringify(measurements, null, 2),
);
console.log(measurements);
await browser.close();

