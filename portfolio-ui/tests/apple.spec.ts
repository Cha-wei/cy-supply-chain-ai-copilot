import { test, expect } from "@playwright/test";
for (const variant of ["C1", "C2", "C3"]) {
  test(`${variant}: facts, boundaries and static previews`, async ({
    page,
  }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto(`/apple.html?variant=${variant}&present=1`);
    await expect(
      page.getByRole("heading", { name: "采购决策", exact: true }),
    ).toBeVisible();
    const rows = page.locator(".evidence-region .facts dd");
    await expect(rows).toHaveText(["30件", "30件", "100件", "70件", "100件"]);
    await expect(page.locator(".calculation-note")).toHaveText(
      "AI 不参与采购数量计算",
    );
    await expect(page.locator(".human-review")).toContainText(
      "最终决策由人工完成",
    );
    await page
      .getByRole("button", { name: "预览人工审核", exact: true })
      .click();
    await expect(page.getByRole("dialog")).toHaveAttribute(
      "data-variant",
      variant,
    );
    await expect(page.getByRole("dialog")).toContainText("不记录批准");
    await page.keyboard.press("Escape");
    await expect(
      page.getByRole("button", { name: "预览人工审核", exact: true }),
    ).toBeFocused();
    await page.getByRole("button", { name: "预览草稿", exact: true }).click();
    await expect(page.getByRole("dialog")).toContainText("批准数量尚未确定");
    await page.keyboard.press("Escape");
    await expect(page.locator(".draft")).toContainText("尚未形成");
    await page.getByRole("button", { name: "查看数据来源说明" }).click();
    await expect(page.locator(".source")).toContainText("页面未执行数据导入");
    expect(errors).toEqual([]);
  });
  test(`${variant}: system controls and responsive frame`, async ({ page }) => {
    await page.goto(`/apple.html?variant=${variant}`);
    await page.getByRole("button", { name: "控件与状态", exact: true }).click();
    await page.getByRole("switch").click();
    await expect(page.getByRole("switch")).toBeChecked();
    await page.getByLabel("输入样本", { exact: true }).fill("视觉样本");
    await expect(
      page.getByRole("button", { name: "不可用样本" }),
    ).toBeDisabled();
    await page.keyboard.press("Escape");
    await page.emulateMedia({ reducedMotion: "reduce" });
    for (const width of [1440, 1280, 390]) {
      await page.setViewportSize({ width, height: 800 });
      await page.goto(`/apple.html?variant=${variant}&present=1`);
      await page.evaluate(() => document.fonts.ready);
      const size = await page.evaluate(() => ({
        width: document.documentElement.scrollWidth,
        height: document.querySelector(".design-stage")!.getBoundingClientRect()
          .height,
        animation: getComputedStyle(document.querySelector(".workspace")!)
          .animationName,
      }));
      expect(size.width).toBeLessThanOrEqual(width);
      if (width >= 1280) expect(size.height).toBeLessThanOrEqual(800);
      expect(size.animation).toBe("none");
      const buttons = await page
        .locator(".system-button")
        .evaluateAll((nodes) =>
          nodes.map((n) => n.getBoundingClientRect().height),
        );
      expect(buttons.every((h) => h >= 44)).toBeTruthy();
    }
  });
}
