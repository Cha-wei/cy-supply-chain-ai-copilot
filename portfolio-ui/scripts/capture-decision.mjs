import { chromium } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
const out = "review/decision-v2";
await mkdir(out, { recursive: true });
const browser = await chromium.launch();
const measurements = [];
for (const width of [1440, 1280, 390]) {
  const page = await browser.newPage({ viewport: { width, height: 800 } });
  const capture = async (name) => {
    await page.evaluate(() => document.fonts.ready);
    await page.evaluate(() =>
      Promise.allSettled(document.getAnimations().map((a) => a.finished)),
    );
    await page.screenshot({
      path: `${out}/${name}-${width}.png`,
      fullPage: (await page.getByRole("dialog").count()) === 0,
    });
    measurements.push({
      name,
      width,
      ...(await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        height: document.querySelector(".design-stage").getBoundingClientRect()
          .height,
      }))),
    });
  };
  await page.goto("http://127.0.0.1:4190/procurement/M2");
  await capture("pending");
  await page.getByRole("button", { name: "修改采购数量", exact: true }).click();
  await page.getByLabel("批准数量").fill("120");
  await page.getByLabel("调整原因").fill("本次演示选择采购 120 件。");
  await capture("override-dialog");
  await page.getByRole("button", { name: "确认修改并批准" }).click();
  await capture("override-summary");
  await page.getByRole("button", { name: "查看采购申请草稿" }).click();
  await capture("override-draft");
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "重新演示" }).click();
  await page.getByRole("button", { name: "修改采购数量", exact: true }).click();
  await page.getByLabel("批准数量").fill("30");
  await page.getByRole("button", { name: "确认修改并批准" }).click();
  await capture("invalid-override");
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "拒绝建议", exact: true }).click();
  await page.getByLabel("拒绝原因").fill("本次不批准此建议。");
  await capture("reject-dialog");
  await page.getByRole("button", { name: "确认拒绝" }).click();
  await capture("reject-summary");
  await page.getByRole("button", { name: "重新演示" }).click();
  await page.getByRole("button", { name: "按建议批准", exact: true }).click();
  await page.getByRole("button", { name: "按建议批准 100 件" }).click();
  await capture("approve-summary");
  await page.close();
}
await writeFile(
  `${out}/measurements.json`,
  JSON.stringify(measurements, null, 2),
);
await browser.close();
