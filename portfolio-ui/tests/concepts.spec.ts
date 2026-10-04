import { test, expect } from "@playwright/test";
for (const concept of ["A", "B", "C"]) {
  test(`concept ${concept}: same facts, readable Chinese and bounded previews`, async ({
    page,
  }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto(`/concepts.html?concept=${concept}`);
    await page.evaluate(() => document.fonts.ready);
    const board = page.locator(".artboard");
    await expect(board).toContainText("SIMULATED");
    await expect(board).toContainText("采购申请草稿");
    await expect(board).toContainText("AI");
    await expect(board).toContainText("人工");
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    const smallText = await board
      .locator("*")
      .evaluateAll((els) =>
        els
          .filter(
            (e) =>
              e.children.length === 0 &&
              e.textContent?.trim() &&
              getComputedStyle(e).display !== "none" &&
              parseFloat(getComputedStyle(e).fontSize) < 12,
          )
          .map((e) => e.textContent),
      );
    expect(smallText).toEqual([]);
    await page.getByRole("button", { name: "查看计算依据" }).click();
    const modal = page.getByRole("dialog");
    await expect(modal).toBeVisible();
    for (const [key, value] of [
      ["ShortageQty", "30"],
      ["BasePurchaseNeed", "30"],
      ["ApplicableMOQ", "100"],
      ["MOQAdjustmentQty", "70"],
      ["RecommendedPurchaseQty", "100"],
    ]) {
      await expect(
        modal.locator("dl>div").filter({ hasText: key }),
      ).toContainText(value);
    }
    await page.keyboard.press("Escape");
    await expect(modal).toHaveCount(0);
    await page.getByRole("button", { name: "查看 AI 解释" }).click();
    await expect(modal).toContainText("没有调用 AI 服务");
    await page.keyboard.press("Escape");
    await page.getByRole("button", { name: "预览人工审核" }).click();
    await expect(modal).toContainText("不记录批准");
    await page.keyboard.press("Escape");
    await expect(board).toContainText("待人工决定");
    expect(errors).toEqual([]);
  });
}
test("concept selector supports arrow keys and deep links", async ({
  page,
}) => {
  await page.goto("/concepts.html?concept=A");
  await page.getByRole("tab", { name: "A 决策画布" }).focus();
  await page.keyboard.press("ArrowRight");
  await expect(page.getByRole("tab", { name: "B 空间供应链" })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  await expect(page).toHaveURL(/concept=B/);
  await page.reload();
  await expect(page.locator(".concept-b")).toBeVisible();
});

test("presentation frames preserve desktop readability and audited control sizes", async ({
  page,
}) => {
  for (const width of [1280, 1440]) {
    await page.setViewportSize({ width, height: 800 });
    for (const concept of ["A", "B", "C"]) {
      await page.goto(`/concepts.html?concept=${concept}`);
      await page.evaluate(() => document.fonts.ready);
      const rect = await page.locator(".artboard").boundingBox();
      expect(rect!.height).toBeLessThanOrEqual(800);
      const heights = await page
        .locator(".artboard button")
        .evaluateAll((els) =>
          els.map((e) => parseFloat(getComputedStyle(e).height)),
        );
      expect(heights.every((h) => h >= 44)).toBeTruthy();
    }
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/concepts.html?concept=B");
  await expect(page.locator(".result-plane")).toHaveCSS("rotate", "0deg");
  await page.goto("/concepts.html?concept=C");
  await expect(page.locator(".c-result>strong")).toHaveCSS(
    "white-space",
    "nowrap",
  );
});
