import { test, expect } from "@playwright/test";
test("guided flow, cancellation, ephemeral approval and reset", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(
    page.getByText("Presentation prototype · not runtime evidence"),
  ).toBeAttached();
  await page.getByText("View calculation evidence").click();
  await expect(
    page.getByText("RecommendedPurchaseQty", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Explore the explanation" }).click();
  await expect(
    page.getByText("Prepared presentation wording · no live AI request"),
  ).toBeVisible();
  await page.getByRole("button", { name: "Approve as recommended" }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await expect(page.getByText("DRAFT · EPHEMERAL")).toHaveCount(0);
  await page.getByRole("button", { name: "Approve as recommended" }).click();
  await page.getByRole("button", { name: "Confirm demo approval" }).click();
  await expect(page.getByText("DRAFT · EPHEMERAL")).toBeVisible();
  await expect(page.locator("#draft")).toContainText("100");
  await expect(page.locator("#draft")).toContainText(
    "Human approval ≠ production execution",
  );
  await expect(
    page.getByRole("button", { name: "Approve as recommended" }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: "Reset demo" }).click();
  await expect(page.getByText("DRAFT · EPHEMERAL")).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Explore the explanation" }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});
test("AI unavailable preserves facts and allows evidence based review", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Preview AI unavailable state").check();
  await expect(
    page.getByRole("heading", { name: "AI explanation unavailable" }),
  ).toBeVisible();
  await expect(page.locator(".recommended strong")).toHaveText("100units");
  await page.getByRole("button", { name: "Approve as recommended" }).click();
  await page.getByRole("button", { name: "Confirm demo approval" }).click();
  await expect(page.getByText("DRAFT · EPHEMERAL")).toBeVisible();
  await page.reload();
  await expect(page.getByText("DRAFT · EPHEMERAL")).toHaveCount(0);
});
test("rejection is terminal for the presentation and does not yield approved draft", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Reject recommendation" }).click();
  await expect(page.getByRole("status")).toContainText(
    "Recommendation rejected",
  );
  await expect(page.getByText("DRAFT · EPHEMERAL")).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Approve as recommended" }),
  ).toHaveCount(0);
  await expect(page.locator(".recommended strong")).toHaveText("100units");
});
test("responsive layout and visual review capture", async ({
  page,
}, testInfo) => {
  await page.goto("/");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: testInfo.outputPath("workspace.png"),
    fullPage: true,
  });
  await page.getByRole("button", { name: "Approve as recommended" }).click();
  await page.screenshot({
    path: testInfo.outputPath("confirmation.png"),
    fullPage: true,
  });
  await page.getByRole("button", { name: "Confirm demo approval" }).click();
  await page.screenshot({
    path: testInfo.outputPath("draft.png"),
    fullPage: true,
  });
});

test("keyboard confirmation and laptop viewport", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/");
  await page.getByRole("button", { name: "Approve as recommended" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Tab");
  expect(
    await page.evaluate(
      () => document.activeElement?.closest("dialog") !== null,
    ),
  ).toBeTruthy();
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("button", { name: "Approve as recommended" }),
  ).toBeFocused();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
});
