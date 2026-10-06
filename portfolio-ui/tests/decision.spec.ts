import { test, expect } from "@playwright/test";
import { reducer, initialState, demoStep } from "../src/state";
import { decisionAdjustment, validateOverride } from "../src/decision-input";
import { recommendationPath, scenario } from "../src/fixture";

const invalid = [
  "",
  " ",
  "0",
  "0.000",
  "-5",
  "-0.5",
  "99.999",
  "99.99999999999999999999999999",
  "1e3",
  "1E3",
  "1,000",
  "1_000",
  " 150",
  "150 ",
  "150\n",
  ".5",
  "150.",
  "NaN",
  "Infinity",
  "-Infinity",
  "1.2.3",
  "１２５",
  "1/3",
];

test("exact override grammar, precision and guards match existing semantics", () => {
  const opened = reducer(initialState, { type: "OPEN", dialog: "override" });
  for (const quantity of invalid) {
    expect(validateOverride(quantity, "原因").quantity, quantity).toBeTruthy();
    expect(
      reducer(opened, { type: "OVERRIDE", quantity, reason: "原因" }),
    ).toBe(opened);
  }
  for (const quantity of [null, undefined, 120, 120.5, [], {}])
    expect(validateOverride(quantity, "原因").quantity).toBeTruthy();
  for (const reason of ["", "  ", "\n\t"]) {
    expect(reducer(opened, { type: "OVERRIDE", quantity: "120", reason })).toBe(
      opened,
    );
    expect(
      reducer(reducer(initialState, { type: "OPEN", dialog: "reject" }), {
        type: "REJECT",
        reason,
      }).decision,
    ).toBeNull();
  }
  for (const quantity of [
    "100",
    "120",
    "100.000000000000000000001",
    "110.125",
    "999999999999999999.0001",
    "+125",
    "0125.00",
    "125.00",
  ]) {
    const result = reducer(opened, {
      type: "OVERRIDE",
      quantity,
      reason: " 人工原文\n保留 ",
    });
    expect(result.decision).toEqual({
      actor: "Human",
      kind: "approve",
      approvedQuantity: quantity,
      sourceRecommendation: "100",
      override: true,
      reason: " 人工原文\n保留 ",
    });
    expect(demoStep(result)).toBe("OVERRIDDEN");
    expect(reducer(result, { type: "OPEN", dialog: "draft" }).draftViewed).toBe(
      true,
    );
    for (const dialog of ["review", "override", "reject"] as const)
      expect(reducer(result, { type: "OPEN", dialog })).toBe(result);
    expect(
      reducer(result, { type: "OVERRIDE", quantity: "150", reason: "重复" }),
    ).toBe(result);
    expect(reducer(result, { type: "REJECT", reason: "重复" })).toBe(result);
  }
  expect(decisionAdjustment("120")).toBe("+20");
  expect(decisionAdjustment("100.000000000000000000001")).toBe(
    "+0.000000000000000000001",
  );
  expect(decisionAdjustment("999999999999999999.0001")).toBe(
    "+999999999999999899.0001",
  );
  expect(decisionAdjustment("0100.00")).toBe("0.00");
  expect(scenario.recommended).toBe("100");
  expect(
    reducer(initialState, {
      type: "OVERRIDE",
      quantity: "120",
      reason: "原因",
    }),
  ).toBe(initialState);
  expect(reducer(initialState, { type: "REJECT", reason: "原因" })).toBe(
    initialState,
  );
});

test("reject has no approved quantity, blocks Draft and repeated decisions", () => {
  const rejected = reducer(
    reducer(initialState, { type: "OPEN", dialog: "reject" }),
    { type: "REJECT", reason: "不批准" },
  );
  expect(rejected.decision).toEqual({
    kind: "reject",
    actor: "Human",
    sourceRecommendation: "100",
    reason: "不批准",
  });
  expect(rejected.decision).not.toHaveProperty("approvedQuantity");
  expect(demoStep(rejected)).toBe("REJECTED");
  expect(reducer(rejected, { type: "OPEN", dialog: "draft" })).toBe(rejected);
  for (const dialog of ["review", "override", "reject"] as const)
    expect(reducer(rejected, { type: "OPEN", dialog })).toBe(rejected);
  expect(reducer(rejected, { type: "APPROVE" })).toBe(rejected);
  expect(
    reducer(rejected, { type: "OVERRIDE", quantity: "120", reason: "再批准" }),
  ).toBe(rejected);
  expect(reducer(rejected, { type: "REJECT", reason: "重复" })).toBe(rejected);
  expect(reducer(rejected, { type: "RESET" })).toBe(initialState);
});

test("100 → explicit override 120 → Draft 120, source remains 100", async ({
  page,
}) => {
  const requests: string[] = [],
    errors: string[] = [];
  page.on("request", (r) => {
    if (["fetch", "xhr"].includes(r.resourceType()) || r.method() !== "GET")
      requests.push(r.url());
  });
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await page.getByRole("link", { name: /查看建议：/ }).click();
  await page.getByRole("button", { name: "修改采购数量", exact: true }).click();
  await page.getByLabel("批准数量").fill("120");
  await page.getByLabel("调整原因").fill("本次演示选择采购 120 件。");
  await page.getByRole("button", { name: "确认修改并批准" }).click();
  await expect(page.locator(".design-stage")).toHaveAttribute(
    "data-demo-state",
    "OVERRIDDEN",
  );
  await expect(page.getByRole("status")).toHaveText(
    "人工已修改并批准 120 件，原建议保持不变。",
  );
  await expect(page.locator(".quantity")).toHaveText("100件");
  const summary = page.locator(".decision-summary");
  await expect(summary).toContainText("系统建议100件");
  await expect(summary).toContainText("人工批准120件");
  await expect(summary).toContainText("调整+20件");
  await expect(summary).toContainText("修改数量");
  await expect(summary).toContainText("本次演示选择采购 120 件。");
  const draft = page.getByRole("button", { name: "查看采购申请草稿" });
  await expect(draft).toBeFocused();
  await draft.click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toContainText("人工批准数量120件");
  await expect(dialog).toContainText("来源建议数量100件");
  await expect(dialog).toContainText("DRAFT");
  await expect(dialog).toContainText("ERP 写入否 · NO");
  await expect(dialog).toContainText("采购订单（PO）未创建 · NO");
  await expect(dialog).toContainText("生产执行否 · NO");
  await page.keyboard.press("Escape");
  await expect(draft).toBeFocused();
  expect(
    await page.evaluate(() => [localStorage.length, sessionStorage.length]),
  ).toEqual([0, 0]);
  expect(requests).toEqual([]);
  expect(errors).toEqual([]);
});

test("invalid override fails closed, errors linked to fields, correction can retry", async ({
  page,
}) => {
  await page.goto(recommendationPath);
  await page.getByRole("button", { name: "修改采购数量", exact: true }).click();
  const qty = page.getByLabel("批准数量");
  await page.getByLabel("调整原因").fill("调整原因");
  for (const value of [
    "",
    "0",
    "-1",
    "99.999",
    "1e3",
    "1,000",
    "150.",
    "NaN",
  ]) {
    await qty.fill(value);
    await page.getByRole("button", { name: "确认修改并批准" }).click();
    await expect(qty).toHaveAttribute("aria-invalid", "true");
    await expect(qty).toHaveAttribute("aria-describedby", /quantity-error/);
    await expect(qty).toBeFocused();
    await expect(page.getByRole("alert")).toBeVisible();
    await expect(page.locator(".design-stage")).toHaveAttribute(
      "data-demo-state",
      "REVIEW_OPEN",
    );
    await expect(page.locator(".decision-summary")).toHaveCount(0);
    await expect(page.locator(".draft")).toContainText("尚未形成");
    await expect(page.locator(".quantity")).toHaveText("100件");
  }
  await qty.fill("120");
  await page.getByLabel("调整原因").fill("  ");
  await page.getByRole("button", { name: "确认修改并批准" }).click();
  await expect(page.getByLabel("调整原因")).toHaveAttribute(
    "aria-describedby",
    "reason-error",
  );
  await expect(page.getByLabel("调整原因")).toBeFocused();
  await expect(page.locator(".decision-summary")).toHaveCount(0);
  await page.getByLabel("调整原因").fill("更正后的原因");
  await page.getByRole("button", { name: "确认修改并批准" }).click();
  await expect(page.locator(".design-stage")).toHaveAttribute(
    "data-demo-state",
    "OVERRIDDEN",
  );
});

test("reject requires reason, announces rejection and never offers approved Draft", async ({
  page,
}) => {
  const requests: string[] = [];
  page.on("request", (r) => {
    if (["fetch", "xhr"].includes(r.resourceType()) || r.method() !== "GET")
      requests.push(r.url());
  });
  await page.goto(recommendationPath);
  await page.getByRole("button", { name: "拒绝建议", exact: true }).click();
  await page.getByRole("button", { name: "确认拒绝" }).click();
  await expect(page.getByLabel("拒绝原因")).toBeFocused();
  await expect(page.getByLabel("拒绝原因")).toHaveAttribute(
    "aria-invalid",
    "true",
  );
  await expect(page.locator(".decision-summary")).toHaveCount(0);
  await page.getByLabel("拒绝原因").fill("本次不批准此建议。");
  await page.getByRole("button", { name: "确认拒绝" }).click();
  await expect(page.locator(".design-stage")).toHaveAttribute(
    "data-demo-state",
    "REJECTED",
  );
  await expect(page.getByRole("status")).toHaveText(
    "人工已拒绝建议，不形成已批准草稿。",
  );
  await expect(page.locator(".decision-summary")).toContainText(
    "系统建议100件",
  );
  await expect(page.locator(".decision-summary")).not.toContainText("人工批准");
  await expect(page.locator(".decision-summary")).toContainText(
    "本次不批准此建议。",
  );
  await expect(
    page.getByRole("button", { name: "查看采购申请草稿" }),
  ).toHaveCount(0);
  await expect(page.locator(".draft")).toContainText("未形成 · 建议已拒绝");
  await expect(page.locator(".quantity")).toHaveText("100件");
  await expect(page.getByRole("button", { name: "重新演示" })).toBeFocused();
  expect(
    await page.evaluate(() => [localStorage.length, sessionStorage.length]),
  ).toEqual([0, 0]);
  expect(requests).toEqual([]);
});

test("all decisions accessible by keyboard; cancellation and field Enter never decide", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto(recommendationPath);
  for (const name of ["按建议批准", "修改采购数量", "拒绝建议"]) {
    const trigger = page.getByRole("button", { name, exact: true });
    await trigger.focus();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("dialog")).toBeVisible();
    if (name === "修改采购数量") {
      await page.getByLabel("批准数量").fill("120");
      await page.getByLabel("调整原因").fill("只是输入");
      await page.getByLabel("批准数量").focus();
      await page.keyboard.press("Enter");
      await expect(page.getByRole("dialog")).toBeVisible();
      await expect(page.locator(".decision-summary")).toHaveCount(0);
    }
    await page.keyboard.press("Tab");
    expect(
      await page.evaluate(
        () => !!document.activeElement?.closest('[role="dialog"]'),
      ),
    ).toBe(true);
    await page.keyboard.press("Escape");
    await expect(trigger).toBeFocused();
    await expect(page.locator(".decision-summary")).toHaveCount(0);
    if (name !== "按建议批准") {
      await trigger.click();
      const dialog = page.getByRole("dialog");
      const box = await dialog.boundingBox();
      expect(box!.x).toBeGreaterThanOrEqual(0);
      expect(box!.x + box!.width).toBeLessThanOrEqual(
        page.viewportSize()!.width,
      );
      await expect(dialog).toHaveCSS("animation-name", "none");
      await page.getByRole("button", { name: "取消", exact: true }).click();
      await expect(trigger).toBeFocused();
    }
  }
});

test("override/reject refresh and reset clear decisions, fields and drafts", async ({
  page,
}) => {
  await page.goto(recommendationPath);
  for (const kind of ["override", "reject"])
    for (const action of ["refresh", "reset"]) {
      await page
        .getByRole("button", {
          name: kind === "override" ? "修改采购数量" : "拒绝建议",
          exact: true,
        })
        .click();
      if (kind === "override") await page.getByLabel("批准数量").fill("120");
      await page.getByRole("textbox", { name: /原因/ }).fill("用于重置验证");
      await page
        .getByRole("button", {
          name: kind === "override" ? "确认修改并批准" : "确认拒绝",
        })
        .click();
      if (action === "refresh") await page.reload();
      else await page.getByRole("button", { name: "重新演示" }).click();
      await expect(page.locator(".design-stage")).toHaveAttribute(
        "data-demo-state",
        "RECOMMENDATION_READY",
      );
      await expect(page.locator(".decision-summary")).toHaveCount(0);
      await expect(page.locator(".draft")).toContainText("尚未形成");
      expect(
        await page.evaluate(() => [localStorage.length, sessionStorage.length]),
      ).toEqual([0, 0]);
      await page
        .getByRole("button", { name: "修改采购数量", exact: true })
        .click();
      await expect(page.getByLabel("批准数量")).toHaveValue("");
      await expect(page.getByLabel("调整原因")).toHaveValue("");
      await page.keyboard.press("Escape");
    }
});

test("large exact value and long reason stay readable without overflow", async ({
  page,
}) => {
  await page.goto(recommendationPath);
  await page.getByRole("button", { name: "修改采购数量", exact: true }).click();
  const quantity = "1".repeat(60) + ".0001";
  await page.getByLabel("批准数量").fill(quantity);
  await page.getByLabel("调整原因").fill("人工原因".repeat(50));
  await page.getByRole("button", { name: "确认修改并批准" }).click();
  await expect(page.locator(".decision-summary")).toContainText(quantity);
  expect(
    await page
      .getByRole("status")
      .evaluate((el) => el.scrollWidth <= el.clientWidth),
  ).toBe(true);
  expect(
    await page
      .locator(".human-review")
      .evaluate((el) => el.scrollWidth <= el.clientWidth),
  ).toBe(true);
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(page.viewportSize()!.width);
  await page.getByRole("button", { name: "查看采购申请草稿" }).click();
  await expect(page.getByRole("dialog")).toContainText(quantity);
  expect(
    await page
      .getByRole("dialog")
      .evaluate((el) => el.scrollWidth <= el.clientWidth),
  ).toBe(true);
});
