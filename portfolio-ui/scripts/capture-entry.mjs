import { chromium } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
const out = "review/entry-v1";
await mkdir(out, { recursive: true });
const browser = await chromium.launch();
const measurements = [];
for (const width of [1440, 1280, 390]) {
  const page = await browser.newPage({ viewport: { width, height: 800 } });
  await page.goto("http://127.0.0.1:4190/");
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(250);
  await page.screenshot({
    path: `${out}/workspace-${width}.png`,
    fullPage: width === 390,
  });
  measurements.push({
    view: "workspace",
    ...(await page.evaluate(() => ({
      width: innerWidth,
      scrollWidth: document.documentElement.scrollWidth,
      height: document.querySelector(".design-stage").getBoundingClientRect()
        .height,
    }))),
  });
  await page.getByRole("link", { name: "查看建议" }).click();
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(250);
  await page.screenshot({
    path: `${out}/detail-${width}.png`,
    fullPage: width === 390,
  });
  measurements.push({
    view: "detail",
    ...(await page.evaluate(() => ({
      width: innerWidth,
      scrollWidth: document.documentElement.scrollWidth,
      height: document.querySelector(".design-stage").getBoundingClientRect()
        .height,
    }))),
  });
  await page.close();
}
await writeFile(
  `${out}/measurements.json`,
  JSON.stringify(measurements, null, 2),
);
await browser.close();
