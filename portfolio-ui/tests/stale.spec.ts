import { test, expect, type Page } from "@playwright/test";
import {
  initialState,
  reducer,
  bindingComponents,
  preparedBinding,
  nextDemoBinding,
  isStale,
  draftAvailable,
  explanationAvailable,
  demoStep,
  type State,
  type Event,
} from "../src/state";
import { recommendationPath } from "../src/fixture";

function decide(
  state: State,
  kind: "pending" | "approve" | "override" | "reject",
) {
  if (kind === "pending") return state;
  const opened = reducer(state, {
    type: "OPEN",
    dialog: kind === "approve" ? "review" : kind,
  });
  const reviewId = opened.review.id;
  return reducer(
    opened,
    kind === "approve"
      ? { type: "APPROVE", reviewId }
      : kind === "override"
        ? { type: "OVERRIDE", reviewId, quantity: "120", reason: "上一轮原因" }
        : { type: "REJECT", reviewId, reason: "上一轮拒绝原因" },
  );
}

test("each of four components irreversibly stales pending/approved/overridden/rejected reviews", () => {
  expect(bindingComponents).toEqual([
    "analysis_run_id",
    "snapshot_package_identity",
    "accepted_content_view_digest",
    "analysis_date",
  ]);
  for (const kind of ["pending", "approve", "override", "reject"] as const)
    for (const component of bindingComponents) {
      const original = decide(initialState, kind);
      const oldDecision = original.review.decision;
      const stale = reducer(original, {
        type: "SIMULATE_RUN",
        binding: { ...preparedBinding, [component]: "SIMULATED-CHANGED" },
      });
      expect(demoStep(stale)).toBe("STALE");
      expect(stale.review.id).toBe(original.review.id);
      expect(stale.review.binding).toBe(original.review.binding);
      expect(stale.review.decision).toBe(oldDecision);
      expect(stale.review.stale).toBe(true);
      expect(draftAvailable(stale)).toBe(false);
      expect(explanationAvailable(stale)).toBe(false);
      const reverted = reducer(stale, {
        type: "SIMULATE_RUN",
        binding: preparedBinding,
      });
      expect(reverted.review).toBe(stale.review);
      expect(isStale(reverted)).toBe(true);
      expect(draftAvailable(reverted)).toBe(false);
      for (const current of [stale, reverted]) {
        for (const dialog of [
          "review",
          "override",
          "reject",
          "draft",
          "explanation",
        ] as const)
          expect(reducer(current, { type: "OPEN", dialog })).toBe(current);
        const events: Event[] = [
          { type: "APPROVE", reviewId: current.review.id },
          {
            type: "OVERRIDE",
            reviewId: current.review.id,
            quantity: "120",
            reason: "不能批准",
          },
          { type: "REJECT", reviewId: current.review.id, reason: "不能拒绝" },
        ];
        for (const event of events)
          expect(reducer(current, event)).toBe(current);
      }
    }
});

test("re-review makes a distinct empty instance; old decisions/drafts/events never carry over", () => {
  for (const kind of ["pending", "approve", "override", "reject"] as const) {
    let state = decide(initialState, kind);
    if (draftAvailable(state))
      state = reducer(state, { type: "OPEN", dialog: "draft" });
    const stale = reducer(state, {
      type: "SIMULATE_RUN",
      binding: nextDemoBinding(state),
    });
    const oldReview = stale.review;
    const next = reducer(stale, { type: "REREVIEW" });
    expect(next.review).not.toBe(oldReview);
    expect(next.review.id).not.toBe(oldReview.id);
    expect(next.review.binding).toEqual(stale.currentBinding);
    expect(next.previousReview).toBe(oldReview);
    expect(oldReview.stale).toBe(true);
    expect(next.review.decision).toBeNull();
    expect(next.review.draftViewed).toBe(false);
    expect(draftAvailable(next)).toBe(false);
    expect(demoStep(next)).toBe("RECOMMENDATION_READY");
    expect(explanationAvailable(next)).toBe(false);
    expect(reducer(next, { type: "OPEN", dialog: "explanation" })).toBe(next);
    expect(reducer(next, { type: "REREVIEW" })).toBe(next);
    for (const dialog of ["review", "override", "reject"] as const) {
      const opened = reducer(next, { type: "OPEN", dialog });
      const oldEvent: Event =
        dialog === "review"
          ? { type: "APPROVE", reviewId: oldReview.id }
          : dialog === "override"
            ? {
                type: "OVERRIDE",
                reviewId: oldReview.id,
                quantity: "120",
                reason: "旧回调",
              }
            : { type: "REJECT", reviewId: oldReview.id, reason: "旧回调" };
      expect(reducer(opened, oldEvent)).toBe(opened);
    }
    const approved = decide(next, "approve");
    expect(approved.review.decision).toMatchObject({
      kind: "approve",
      approvedQuantity: "100",
      override: false,
    });
    expect(draftAvailable(approved)).toBe(true);
    expect(approved.previousReview).toBe(oldReview);
    expect(oldReview.stale).toBe(true);
  }
});

test("matching binding does not stale; retired explanation never revives, even on original binding", () => {
  const matching = reducer(initialState, {
    type: "SIMULATE_RUN",
    binding: { ...preparedBinding },
  });
  expect(isStale(matching)).toBe(false);
  expect(explanationAvailable(matching)).toBe(true);
  let state = reducer(initialState, { type: "OPEN", dialog: "explanation" });
  state = reducer(state, {
    type: "SIMULATE_RUN",
    binding: nextDemoBinding(state),
  });
  expect(state.dialog).toBeNull();
  const old = state.review;
  state = reducer(state, { type: "SIMULATE_RUN", binding: preparedBinding });
  state = reducer(state, { type: "REREVIEW" });
  expect(explanationAvailable(state)).toBe(false);
  expect(old.stale).toBe(true);
  state = reducer(state, { type: "RESET" });
  expect(state).toBe(initialState);
  expect(old.stale).toBe(true);
  expect(explanationAvailable(state)).toBe(true);
});

async function simulate(page: Page) {
  await page.getByRole("button", { name: "查看展示边界" }).click();
  await expect(page.getByRole("dialog")).toContainText("演示控制");
  await expect(page.getByRole("dialog")).toContainText(
    "不表示浏览器检测到了真实数据更新",
  );
  await page.getByRole("button", { name: "模拟输入数据更新" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.locator(".design-stage")).toHaveAttribute(
    "data-demo-state",
    "STALE",
  );
  await expect(
    page.getByRole("button", { name: "重新审核", exact: true }),
  ).toBeFocused();
}
async function checkStale(page: Page) {
  await expect(page.locator(".page-heading .status")).toHaveText(
    "审核已失效 · 演示",
  );
  for (const name of [
    "按建议批准",
    "修改采购数量",
    "拒绝建议",
    "查看采购申请草稿",
    "查看 AI 解释",
  ])
    await expect(page.getByRole("button", { name, exact: true })).toHaveCount(
      0,
    );
  await expect(page.getByRole("status")).toContainText("已模拟输入数据更新");
  await expect(
    page.getByRole("heading", { name: "AI 解释不可用" }),
  ).toBeVisible();
  await expect(page.locator(".explanation")).not.toContainText("目前需要补足");
  await expect(page.locator(".quantity")).toHaveText("100件");
  await expect(
    page.locator(".evidence-group dl > div").filter({ hasText: "MOQ 调整" }),
  ).toHaveText("MOQ 调整+70件");
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(page.viewportSize()!.width);
}

test("pending → stale → new review; deterministic approval works without explanation", async ({
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
  await expect(
    page.getByRole("button", { name: "模拟输入数据更新" }),
  ).toHaveCount(0);
  await page.getByRole("link", { name: /查看建议：/ }).click();
  const oldId = await page.locator("main").getAttribute("data-review-id");
  await expect(
    page.getByRole("button", { name: "模拟输入数据更新" }),
  ).toHaveCount(0);
  await simulate(page);
  await checkStale(page);
  await page.getByRole("button", { name: "重新审核", exact: true }).click();
  await expect(page.locator("main")).not.toHaveAttribute(
    "data-review-id",
    oldId!,
  );
  await expect(page.locator("main")).toHaveAttribute(
    "data-review-stale",
    "false",
  );
  await expect(
    page.getByRole("button", { name: "按建议批准", exact: true }),
  ).toBeFocused();
  await expect(page.locator(".decision-summary")).toHaveCount(0);
  await expect(page.locator(".draft")).toContainText("尚未形成 · 等待人工决定");
  await expect(page.locator(".freshness-note")).toContainText("未重新计算");
  await expect(
    page.getByRole("heading", { name: "AI 解释不可用" }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "查看 AI 解释" })).toHaveCount(
    0,
  );
  await page.getByRole("button", { name: "按建议批准", exact: true }).click();
  await page.getByRole("button", { name: "按建议批准 100 件" }).click();
  await page.getByRole("button", { name: "查看采购申请草稿" }).click();
  await expect(page.getByRole("dialog")).toContainText("人工批准数量100件");
  await expect(page.getByRole("dialog")).toContainText("生产执行否 · NO");
  expect(
    await page.evaluate(() => [localStorage.length, sessionStorage.length]),
  ).toEqual([0, 0]);
  expect(requests).toEqual([]);
  expect(errors).toEqual([]);
});

for (const kind of ["approve", "override", "reject"] as const)
  test(`${kind} → stale retains only reference → empty new review`, async ({
    page,
  }) => {
    await page.goto(recommendationPath);
    await page
      .getByRole("button", {
        name:
          kind === "approve"
            ? "按建议批准"
            : kind === "override"
              ? "修改采购数量"
              : "拒绝建议",
        exact: true,
      })
      .click();
    if (kind === "override") await page.getByLabel("批准数量").fill("120");
    if (kind !== "approve")
      await page.getByRole("textbox", { name: /原因/ }).fill("上一轮人工原因");
    await page
      .getByRole("button", {
        name:
          kind === "approve"
            ? "按建议批准 100 件"
            : kind === "override"
              ? "确认修改并批准"
              : "确认拒绝",
      })
      .click();
    if (kind !== "reject") {
      await page.getByRole("button", { name: "查看采购申请草稿" }).click();
      await expect(page.getByRole("dialog")).toContainText(
        `人工批准数量${kind === "override" ? "120" : "100"}件`,
      );
      await page.keyboard.press("Escape");
    }
    await simulate(page);
    await checkStale(page);
    await expect(
      page.getByRole("heading", { name: "上一轮人工决定" }),
    ).toBeVisible();
    await expect(page.locator(".stale-decision-note")).toContainText(
      "已失效，仅供参考",
    );
    if (kind !== "reject") {
      await expect(page.locator(".stale-summary")).toContainText(
        `人工批准${kind === "override" ? "120" : "100"}件`,
      );
      await expect(page.locator(".draft")).toContainText(
        "STALE / NON-ACTIONABLE · 需重新审核",
      );
    } else
      await expect(page.locator(".stale-summary")).not.toContainText(
        "人工批准",
      );
    await page.getByRole("button", { name: "重新审核", exact: true }).click();
    await expect(page.locator(".design-stage")).toHaveAttribute(
      "data-demo-state",
      "RECOMMENDATION_READY",
    );
    await expect(page.locator(".decision-summary")).toHaveCount(0);
    await expect(page.locator(".draft")).toContainText(
      "尚未形成 · 等待人工决定",
    );
    await page
      .getByRole("button", { name: "修改采购数量", exact: true })
      .click();
    await expect(page.getByLabel("批准数量")).toHaveValue("");
    await expect(page.getByLabel("调整原因")).toHaveValue("");
    await page.getByLabel("批准数量").fill("130");
    await page.getByLabel("调整原因").fill("新的人工原因");
    await page.getByRole("button", { name: "确认修改并批准" }).click();
    await page.getByRole("button", { name: "查看采购申请草稿" }).click();
    await expect(page.getByRole("dialog")).toContainText("人工批准数量130件");
    await expect(page.getByRole("dialog")).toContainText("来源建议数量100件");
  });

test("keyboard demo controls, repeated cycles, reduced motion and reset/refresh", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto(recommendationPath);
  const info = page.getByRole("button", { name: "查看展示边界" });
  await info.focus();
  await page.keyboard.press("Enter");
  await page.keyboard.press("Escape");
  await expect(info).toBeFocused();
  await expect(page.locator(".design-stage")).toHaveAttribute(
    "data-demo-state",
    "RECOMMENDATION_READY",
  );
  for (let cycle = 0; cycle < 2; cycle++) {
    await info.click();
    const button = page.getByRole("button", { name: "模拟输入数据更新" });
    await button.focus();
    await page.keyboard.press("Enter");
    await expect(
      page.getByRole("button", { name: "重新审核", exact: true }),
    ).toBeFocused();
    await expect(page.locator(".workspace")).toHaveCSS(
      "animation-name",
      "none",
    );
    await info.click();
    await expect(button).toBeDisabled();
    await page.keyboard.press("Escape");
    await expect(info).toBeFocused();
    const review = page.getByRole("button", { name: "重新审核", exact: true });
    await review.focus();
    await page.keyboard.press("Enter");
    await expect(
      page.getByRole("button", { name: "按建议批准", exact: true }),
    ).toBeFocused();
    await expect(page.locator("main")).toHaveAttribute(
      "data-review-id",
      String(cycle + 2),
    );
  }
  for (const action of ["reset", "refresh"]) {
    await simulate(page);
    if (action === "reset") {
      await info.click();
      await page.getByRole("button", { name: "重新演示", exact: true }).click();
    } else await page.reload();
    await expect(page.locator("main")).toHaveAttribute("data-review-id", "1");
    await expect(page.locator(".design-stage")).toHaveAttribute(
      "data-demo-state",
      "RECOMMENDATION_READY",
    );
    await expect(
      page.getByRole("button", { name: "查看 AI 解释" }),
    ).toBeVisible();
    await expect(page.locator(".draft")).toContainText("尚未形成");
    expect(
      await page.evaluate(() => [localStorage.length, sessionStorage.length]),
    ).toEqual([0, 0]);
  }
});
