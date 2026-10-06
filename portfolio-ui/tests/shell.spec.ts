import { test, expect } from "@playwright/test";
import { recommendationPath } from "../src/fixture";

test("one stable module across workspace and detail, compact task row", async ({
  page,
}) => {
  await page.goto("/");
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() =>
    Promise.all(
      document.getAnimations().map((animation) => animation.finished),
    ),
  );
  const rail = page.getByRole("complementary", { name: "应用导航栏" });
  const modules = page.getByRole("navigation", { name: "应用模块" });
  await expect(rail).toBeVisible();
  await expect(modules.getByRole("link")).toHaveCount(1);
  await expect(
    modules.getByRole("link", { name: "采购决策", exact: true }),
  ).toBeVisible();
  await expect(modules).not.toContainText(
    /库存管理|供应商管理|采购订单|分析中心|设置|用户中心|审批中心/,
  );
  const railBefore = await rail.boundingBox();
  const desktop = page.viewportSize()!.width >= 1280;
  if (desktop) expect(railBefore!.width).toBe(96);
  else expect(railBefore!.height).toBeLessThanOrEqual(80);
  const row = page.getByRole("link", { name: /查看建议：/ });
  if (desktop) {
    const box = await row.boundingBox();
    expect(box!.height).toBeGreaterThanOrEqual(100);
    expect(box!.height).toBeLessThanOrEqual(130);
  }
  await expect(row).toContainText("MOQ 调整+70");
  await expect(row).not.toContainText("满足最低起订量");
  // Clicking the material name (not the arrow) activates the whole row.
  await row.getByRole("heading", { name: "装配连接件" }).click();
  await expect(page).toHaveURL(recommendationPath);
  await expect(rail).toBeVisible();
  await expect(modules.getByRole("link")).toHaveCount(1);
  await page.evaluate(() =>
    Promise.all(
      document.getAnimations().map((animation) => animation.finished),
    ),
  );
  const railAfter = await rail.boundingBox();
  expect(railAfter!.x).toBe(railBefore!.x);
  expect(railAfter!.y).toBe(railBefore!.y);
  expect(railAfter!.width).toBe(railBefore!.width);
  await expect(page.locator(".page-heading")).toContainText("M2");
  await expect(page.locator(".context-bar")).toContainText("返回工作台");
  await modules.getByRole("link", { name: "采购决策", exact: true }).click();
  await expect(page).toHaveURL("/");
});

test("task row focus, keyboard, hover and reduced motion", async ({ page }) => {
  await page.goto("/");
  const row = page.getByRole("link", { name: /查看建议：/ });
  await row.focus();
  await expect(row).toBeFocused();
  await expect(row).toHaveCSS("outline-style", "solid");
  await row.hover();
  await expect(row.locator(".task-affordance svg")).toHaveCSS(
    "transform",
    "matrix(1, 0, 0, 1, 3, 0)",
  );
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(recommendationPath);
  await page
    .getByRole("link", { name: "返回采购决策工作台，重新演示" })
    .click();
  await page.emulateMedia({ reducedMotion: "reduce" });
  await row.hover();
  await expect(row).toHaveCSS("transition-duration", "0s");
  await expect(row.locator(".task-affordance svg")).toHaveCSS(
    "transition-duration",
    "0s",
  );
});

test("workspace retains frozen font and intermediate width stays usable", async ({
  page,
}) => {
  await page.goto("/");
  await page.evaluate(() => document.fonts.ready);
  const c = await page.context().newCDPSession(page);
  await c.send("DOM.enable");
  await c.send("CSS.enable");
  const d = await c.send("DOM.getDocument");
  for (const selector of ["h1", ".task-identity h3", ".overview-strip dd"]) {
    const n = await c.send("DOM.querySelector", {
      nodeId: d.root.nodeId,
      selector,
    });
    const { fonts } = await c.send("CSS.getPlatformFontsForNode", {
      nodeId: n.nodeId,
    });
    expect(fonts.length).toBeGreaterThan(0);
    expect(
      fonts.every(
        (f) => f.isCustomFont && f.familyName.includes("Noto Sans SC"),
      ),
    ).toBe(true);
  }
  await c.detach();
  await page.setViewportSize({ width: 900, height: 800 });
  await expect(page.locator(".task-row .status")).toBeVisible();
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(900);
});
