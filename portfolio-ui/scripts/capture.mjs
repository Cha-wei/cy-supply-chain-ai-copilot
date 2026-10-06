import { chromium } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
const out = "review/screenshots";
await mkdir(out, { recursive: true });
const browser = await chromium.launch();
const measurements = [];
for (const width of [1440, 1280, 390]) {
  const page = await browser.newPage({ viewport: { width, height: 800 } });
  await page.goto("http://127.0.0.1:4190/procurement/M2");
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(250);
  const shot = async (name) => {
    await page.waitForTimeout(250);
    return page.screenshot({
      path: `${out}/${name}-${width}.png`,
      fullPage: width === 390 && ["ready", "approved"].includes(name),
    });
  };
  await shot("ready");
  measurements.push(
    await page.evaluate(() => ({
      width: innerWidth,
      scrollWidth: document.documentElement.scrollWidth,
      height: document.querySelector(".design-stage").getBoundingClientRect()
        .height,
    })),
  );
  await page.getByRole("button", { name: "查看完整依据" }).click();
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "查看 AI 解释" }).click();
  if (width === 1440) await shot("explanation");
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "按建议批准", exact: true }).click();
  if (width === 1440) await shot("review");
  await page.getByRole("button", { name: "按建议批准 100 件" }).click();
  await page.waitForTimeout(250);
  await shot("approved");
  await page.getByRole("button", { name: "查看采购申请草稿" }).click();
  await page.waitForTimeout(250);
  await shot("draft");
  await page.close();
}
await writeFile(
  "review/measurements.json",
  JSON.stringify(measurements, null, 2),
);
await browser.close();
