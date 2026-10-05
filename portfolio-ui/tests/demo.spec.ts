import { test, expect } from "@playwright/test";
import { initialState, reducer, demoStep } from "../src/state";
import { scenario, recommendationPath } from "../src/fixture";

test("presentation guards cannot invent or repeat Human approval", () => {
  expect(reducer(initialState, { type: "APPROVE" })).toBe(initialState);
  expect(reducer(initialState, { type: "OPEN", dialog: "draft" })).toBe(
    initialState,
  );
  const review = reducer(initialState, { type: "OPEN", dialog: "review" });
  const cancel = reducer(review, { type: "CLOSE" });
  expect(cancel.decision).toBeNull();
  const approved = reducer(review, { type: "APPROVE" });
  expect(approved.decision).toEqual({
    kind: "approve",
    actor: "Human",
    approvedQuantity: "100",
    sourceRecommendation: "100",
    override: false,
  });
  expect(reducer(approved, { type: "APPROVE" })).toBe(approved);
  expect(reducer(approved, { type: "OPEN", dialog: "review" })).toBe(approved);
  expect(scenario.recommended).toBe("100");
  expect(demoStep(reducer(approved, { type: "OPEN", dialog: "draft" }))).toBe(
    "DRAFT_READY",
  );
  expect(reducer(approved, { type: "RESET" })).toBe(initialState);
});

test("Recommendation → Evidence → Explanation → Human approval → Draft", async ({
  page,
}) => {
  const errors: string[] = [],
    requests: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("request", (r) => {
    if (["fetch", "xhr"].includes(r.resourceType()) || r.method() !== "GET")
      requests.push(r.url());
  });
  await page.goto(recommendationPath);
  const stage = page.locator(".design-stage");
  await expect(stage).toHaveAttribute(
    "data-demo-state",
    "RECOMMENDATION_READY",
  );
  await expect(page.locator(".quantity")).toHaveText("100件");
  await expect(
    page.getByRole("button", { name: "查看采购申请草稿" }),
  ).toHaveCount(0);
  await expect(page.locator(".draft")).toContainText("尚未形成");
  await page.getByRole("button", { name: "查看完整依据" }).click();
  await expect(stage).toHaveAttribute("data-demo-state", "EVIDENCE_VIEWED");
  for (const [key, value] of scenario.facts) {
    await expect(
      page.getByRole("dialog").locator(".facts>div").filter({ hasText: key }),
    ).toContainText(value);
  }
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("button", { name: "查看完整依据" }),
  ).toBeFocused();
  await page.getByRole("button", { name: "查看 AI 解释" }).click();
  await expect(stage).toHaveAttribute("data-demo-state", "EXPLANATION_VIEWED");
  await expect(page.getByRole("dialog")).toContainText("未发起实时 AI 请求");
  await expect(page.getByRole("dialog")).toContainText("不作为 runtime 证据");
  await expect(page.getByRole("dialog")).toContainText("不计算或修改采购数量");
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "进入人工审核" }).click();
  await expect(stage).toHaveAttribute("data-demo-state", "REVIEW_OPEN");
  await expect(page.getByRole("dialog")).toContainText("目前尚无人工决定");
  await page.getByRole("button", { name: "按建议批准 100 件" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(stage).toHaveAttribute("data-demo-state", "APPROVED");
  await expect(page.getByRole("status")).toHaveText(
    "人工已按建议批准 100 件，原建议保持不变。",
  );
  await expect(page.locator(".quantity")).toHaveText("100件");
  const draft = page.getByRole("button", { name: "查看采购申请草稿" });
  await expect(draft).toBeFocused();
  await draft.click();
  await expect(stage).toHaveAttribute("data-demo-state", "DRAFT_READY");
  const dialog = page.getByRole("dialog");
  await expect(dialog).toContainText("DRAFT");
  await expect(dialog).toContainText("人工（Human）");
  await expect(
    dialog.locator(".facts>div").filter({ hasText: "人工批准数量" }),
  ).toContainText("100件");
  await expect(
    dialog.locator(".facts>div").filter({ hasText: "来源建议数量" }),
  ).toContainText("100件");
  await expect(dialog).toContainText("ERP 写入否 · NO");
  await expect(dialog).toContainText("采购订单（PO）未创建 · NO");
  await expect(dialog).toContainText("人工批准 ≠ 生产执行");
  await expect(dialog).toContainText("不提交、不持久保存");
  await page.keyboard.press("Escape");
  await expect(draft).toBeFocused();
  expect(
    await page.evaluate(() => [localStorage.length, sessionStorage.length]),
  ).toEqual([0, 0]);
  expect(requests).toEqual([]);
  expect(errors).toEqual([]);
});

test("cancel/Escape and keyboard focus never approve implicitly", async ({
  page,
}) => {
  await page.goto(recommendationPath);
  const review = page.getByRole("button", { name: "进入人工审核" });
  await review.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Tab");
  expect(
    await page.evaluate(
      () => !!document.activeElement?.closest('[role="dialog"]'),
    ),
  ).toBe(true);
  await page.keyboard.press("Escape");
  await expect(review).toBeFocused();
  await expect(page.locator(".design-stage")).toHaveAttribute(
    "data-demo-state",
    "RECOMMENDATION_READY",
  );
  await review.click();
  await page.getByRole("button", { name: "返回查看" }).click();
  await expect(review).toBeFocused();
  await expect(page.locator(".draft")).toContainText("尚未形成");
  await review.click();
  const confirm = page.getByRole("button", { name: "按建议批准 100 件" });
  await confirm.focus();
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("button", { name: "查看采购申请草稿" }),
  ).toBeFocused();
});

test("refresh and explicit reset clear ephemeral approval", async ({
  page,
}) => {
  await page.goto(recommendationPath);
  for (const action of ["reset", "refresh"]) {
    await page.getByRole("button", { name: "进入人工审核" }).click();
    await page.getByRole("button", { name: "按建议批准 100 件" }).click();
    if (action === "reset")
      await page.getByRole("button", { name: "重新演示" }).click();
    else await page.reload();
    await expect(page.locator(".design-stage")).toHaveAttribute(
      "data-demo-state",
      "RECOMMENDATION_READY",
    );
    await expect(
      page.getByRole("button", { name: "查看采购申请草稿" }),
    ).toHaveCount(0);
    await expect(page.locator(".draft")).toContainText("尚未形成");
    await expect(page.locator(".quantity")).toHaveText("100件");
  }
});

test("frozen font, responsive frame, reduced motion and dialog boundaries", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto(recommendationPath);
  await page.evaluate(() => document.fonts.ready);
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
  await expect(page.locator(".workspace")).toHaveCSS("animation-name", "none");
  const c = await page.context().newCDPSession(page);
  await c.send("DOM.enable");
  await c.send("CSS.enable");
  const d = await c.send("DOM.getDocument");
  for (const selector of ["h1", ".quantity", ".explanation>p"]) {
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
        (f) => f.familyName.includes("Noto Sans SC") && f.isCustomFont,
      ),
    ).toBe(true);
  }
  await c.detach();
  for (const name of ["查看完整依据", "查看 AI 解释", "进入人工审核"]) {
    await page.getByRole("button", { name, exact: true }).click();
    const box = await page.getByRole("dialog").boundingBox();
    expect(box!.x).toBeGreaterThanOrEqual(0);
    expect(box!.x + box!.width).toBeLessThanOrEqual(width);
    await page.keyboard.press("Escape");
  }
  await page.getByRole("button", { name: "进入人工审核" }).click();
  await page.getByRole("button", { name: "按建议批准 100 件" }).click();
  await expect(page.locator(".draft-ready")).toHaveCSS(
    "animation-name",
    "none",
  );
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(width);
});

test("frozen primary and summary contrast remain legible", async ({ page }) => {
  await page.goto(recommendationPath);
  const luminance = (value: string) => {
    const c = value
      .match(/[\d.]+/g)!
      .slice(0, 3)
      .map(Number)
      .map((x) => {
        x /= 255;
        return x <= 0.04045 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4;
      });
    return c[0] * 0.2126 + c[1] * 0.7152 + c[2] * 0.0722;
  };
  const ratio = (a: string, b: string) => {
    const x = luminance(a),
      y = luminance(b);
    return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
  };
  const primary = page.getByRole("button", { name: "进入人工审核" });
  for (const hover of [false, true]) {
    if (hover) await primary.hover();
    await expect
      .poll(async () => {
        const c = await primary.evaluate((el) => ({
          fg: getComputedStyle(el).color,
          bg: getComputedStyle(el).backgroundColor,
        }));
        return ratio(c.fg, c.bg);
      })
      .toBeGreaterThanOrEqual(4.5);
  }
  const operator = await page
    .locator(".operator")
    .first()
    .evaluate((el) => ({
      fg: getComputedStyle(el).color,
      bg: getComputedStyle(el.closest(".recommendation-surface")!)
        .backgroundColor,
    }));
  expect(ratio(operator.fg, operator.bg)).toBeGreaterThanOrEqual(4.5);
});

test("font failure still allows explicit approval and draft", async ({
  page,
}) => {
  await page.route(/\.woff2?(\?|$)/, (route) => route.abort());
  await page.goto(recommendationPath);
  await page.evaluate(() => document.fonts.ready);
  await page.getByRole("button", { name: "进入人工审核" }).click();
  await page.getByRole("button", { name: "按建议批准 100 件" }).click();
  await page.getByRole("button", { name: "查看采购申请草稿" }).click();
  await expect(page.getByRole("dialog")).toContainText("DRAFT");
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(page.viewportSize()!.width);
});
