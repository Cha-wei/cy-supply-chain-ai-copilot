import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
import { scenario, recommendationPath } from "../src/fixture";

test("material identity follows existing fixture; display label is separate", () => {
  const canonicalFixture = readFileSync(
    new URL("../../tests/test_shortage_calculation.py", import.meta.url),
    "utf8",
  );
  expect(canonicalFixture.match(/^DEMAND = "([^"]+)"/m)?.[1]).toBe(
    scenario.material_code,
  );
  expect(scenario.material_code).toBe("M2");
  expect(scenario.display_name).toBeTruthy();
});

test("workspace discovers one task and continues the accepted detail path", async ({
  page,
}) => {
  const businessRequests: string[] = [];
  page.on("request", (r) => {
    if (["fetch", "xhr"].includes(r.resourceType()) || r.method() !== "GET")
      businessRequests.push(r.url());
  });
  await page.goto("/");
  await page.evaluate(() => document.fonts.ready);
  await expect(
    page.getByRole("heading", { name: "采购决策工作台", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "待审核采购建议 · 1" }),
  ).toBeVisible();
  await expect(page.getByRole("article")).toHaveCount(1);
  await expect(
    page.getByRole("heading", { name: scenario.display_name, exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("article")).toContainText(
    `物料编码：${scenario.material_code}`,
  );
  await expect(page.getByRole("article")).toContainText("模拟展示名称");
  await expect(
    page.locator(".entry-facts>div").filter({ hasText: "当前缺口" }),
  ).toContainText("30件");
  await expect(
    page.locator(".entry-facts>div").filter({ hasText: "建议采购量" }),
  ).toContainText("100件");
  await expect(page.getByRole("article")).toContainText("MOQ");
  await expect(page.getByRole("article")).toContainText("待人工审核");
  await expect(
    page.getByRole("button", { name: /批准|审核|解释|依据|Reject|Override/ }),
  ).toHaveCount(0);
  const width = page.viewportSize()!.width;
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(width);
  if (width >= 1280)
    expect(
      await page
        .locator(".design-stage")
        .evaluate((el) => el.getBoundingClientRect().height),
    ).toBeLessThanOrEqual(800);
  const link = page.getByRole("link", { name: "查看建议" });
  await link.focus();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(recommendationPath);
  await expect(page.locator(".page-heading")).toContainText(
    scenario.display_name,
  );
  await expect(page.locator(".page-heading")).toContainText(
    `物料编码：${scenario.material_code}`,
  );
  await page.getByRole("button", { name: "查看完整依据" }).click();
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "查看 AI 解释" }).click();
  await expect(page.getByRole("dialog")).toContainText("不作为 runtime 证据");
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "进入人工审核" }).click();
  await page.getByRole("button", { name: "按建议批准 100 件" }).click();
  await expect(page.locator(".quantity")).toHaveText("100件");
  await page.getByRole("button", { name: "查看采购申请草稿" }).click();
  await expect(page.getByRole("dialog")).toContainText("人工（Human）");
  await expect(page.getByRole("dialog")).toContainText("DRAFT");
  await expect(page.getByRole("dialog")).toContainText("ERP 写入否 · NO");
  await expect(page.getByRole("dialog")).toContainText(
    "采购订单（PO）未创建 · NO",
  );
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "重新演示" }).click();
  await expect(page.locator(".draft")).toContainText("尚未形成");
  await page
    .getByRole("link", { name: "返回采购决策工作台，重新演示" })
    .click();
  await expect(page).toHaveURL("/");
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "待审核采购建议 · 1" }),
  ).toBeVisible();
  expect(
    await page.evaluate(() => [localStorage.length, sessionStorage.length]),
  ).toEqual([0, 0]);
  expect(businessRequests).toEqual([]);
});

test("deep-link refresh and unknown IDs cannot change material identity", async ({
  page,
}) => {
  await page.goto(recommendationPath);
  await page.reload();
  await expect(page.locator(".page-heading")).toContainText(
    `物料编码：${scenario.material_code}`,
  );
  await expect(page.locator(".design-stage")).toHaveAttribute(
    "data-demo-state",
    "RECOMMENDATION_READY",
  );
  await page.goto("/procurement/UNKNOWN");
  await expect(
    page.getByRole("heading", { name: "未找到采购建议" }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "进入人工审核" })).toHaveCount(
    0,
  );
  await page.getByRole("link", { name: "返回采购决策工作台" }).click();
  await expect(page).toHaveURL("/");
});
