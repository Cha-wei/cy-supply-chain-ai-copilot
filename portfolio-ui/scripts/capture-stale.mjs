import { chromium } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
const out = "review/stale-v3";
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
        reviewId: document.querySelector("main").dataset.reviewId,
        state: document.querySelector(".design-stage").dataset.demoState,
      }))),
    });
  };
  const simulate = async () => {
    await page.getByRole("button", { name: "查看展示边界" }).click();
    await page.getByRole("button", { name: "模拟输入数据更新" }).click();
  };
  await page.goto("http://127.0.0.1:4190/procurement/M2");
  await page.getByRole("button", { name: "查看展示边界" }).click();
  await capture("demo-controls");
  await page.keyboard.press("Escape");
  await simulate();
  await capture("pending-stale");
  await page.reload();
  await page.getByRole("button", { name: "修改采购数量", exact: true }).click();
  await page.getByLabel("批准数量").fill("120");
  await page.getByLabel("调整原因").fill("上一轮人工选择采购 120 件。");
  await page.getByRole("button", { name: "确认修改并批准" }).click();
  await page.getByRole("button", { name: "查看采购申请草稿" }).click();
  await page.keyboard.press("Escape");
  await simulate();
  await capture("override-stale");
  await page.getByRole("button", { name: "重新审核", exact: true }).click();
  await capture("new-review");
  await page.getByRole("button", { name: "按建议批准", exact: true }).click();
  await page.getByRole("button", { name: "按建议批准 100 件" }).click();
  await page.getByRole("button", { name: "查看采购申请草稿" }).click();
  await capture("new-draft");
  await page.close();
}
await writeFile(
  `${out}/measurements.json`,
  JSON.stringify(measurements, null, 2),
);
await browser.close();
