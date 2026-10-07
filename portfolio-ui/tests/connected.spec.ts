import { test, expect, type Page, type APIRequestContext } from "@playwright/test";
const origin = "http://127.0.0.1:4193";
const detail = "/procurement/SIM-M2";
const snapshot = async (request: APIRequestContext) => (await request.get("/demo/state")).json();
async function intent(request: APIRequestContext, op: string, args: object = {}) {
  const v = await snapshot(request);
  return request.post("/demo/intent", { headers: { Origin: origin }, data: { op, intent: crypto.randomUUID(), session: v.session, ...(op === "initialize" ? {} : { run: v.run, review: v.review.id }), ...args } });
}
async function approve(page: Page) {
  const rereview = page.getByRole("button", { name: "重新审核", exact: true });
  if (await rereview.isVisible()) await rereview.click();
  await page.getByRole("button", { name: "按建议批准", exact: true }).click();
  await page.getByRole("button", { name: "按建议批准 100 件", exact: true }).click();
  await expect(page.getByRole("button", { name: "查看采购申请草稿" })).toBeVisible();
}
async function newRun(page: Page) {
  await page.getByRole("button", { name: "查看展示边界" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "模拟新分析运行", exact: true }).first().click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
}
test.beforeEach(async ({ request }, info) => {
  const v = await snapshot(request);
  expect((await intent(request, v.initialized ? "new_analysis" : "initialize")).ok()).toBeTruthy();
  if (!info.title.startsWith("AI unavailable")) expect((await intent(request, "open_review")).ok()).toBeTruthy();
});

test("workspace to detail uses runtime identity and derived facts", async ({ page, request }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "采购决策工作台" })).toBeVisible();
  await expect(page.getByText("物料编码：SIM-M2")).toBeVisible();
  const run = (await snapshot(request)).run;
  await page.getByRole("link", { name: /查看建议/ }).click();
  await expect(page).toHaveURL(new RegExp(detail));
  await expect(page.locator(".equation")).toContainText("30");
  await expect(page.locator(".equation")).toContainText("70");
  await expect(page.locator(".quantity")).toContainText("100");
  expect((await snapshot(request)).run).toBe(run);
});

test("evidence stays read-only and contains five Python facts", async ({ page, request }) => {
  await page.goto(detail);
  const run = (await snapshot(request)).run;
  await page.getByRole("button", { name: /查看完整依据/ }).click();
  for (const field of ["ShortageQty", "BasePurchaseNeed", "ApplicableMOQ", "MOQAdjustmentQty", "RecommendedPurchaseQty"]) await expect(page.getByRole("dialog")).toContainText(field);
  await page.keyboard.press("Escape");
  expect((await snapshot(request)).run).toBe(run);
});

test("AI unavailable is truthful and does not block approve and Draft", async ({ page, request }) => {
  await page.goto(detail);
  await page.getByRole("button", { name: "请求 AI 解释" }).click();
  await expect.poll(async () => (await snapshot(request)).explanationOutcome).not.toBe("NOT_REQUESTED");
  await expect(page.getByRole("heading", { name: "AI 解释不可用" })).toBeVisible();
  await approve(page);
  await page.getByRole("button", { name: "查看采购申请草稿" }).click();
  await expect(page.getByRole("dialog")).toContainText("100");
  await expect(page.getByRole("dialog")).toContainText("DRAFT");
});

test("approve state survives refresh and a second tab", async ({ page, context, request }) => {
  await page.goto(detail); await approve(page);
  const a = await snapshot(request);
  expect(a.review.decision.reason).toBeNull();
  await expect(page.locator(".decision-reason")).toHaveCount(0);
  await page.reload();
  await expect(page.getByRole("button", { name: "查看采购申请草稿" })).toBeVisible();
  const other = await context.newPage(); await other.goto(detail);
  await expect(other.getByRole("button", { name: "查看采购申请草稿" })).toBeVisible();
  const b = await snapshot(request); expect(b.run).toBe(a.run); expect(b.review.id).toBe(a.review.id);
  await other.close();
});

test("override 120 changes only Human decision and Draft", async ({ page, request }) => {
  await page.goto(detail);
  await page.getByRole("button", { name: "修改采购数量", exact: true }).click();
  await page.getByLabel("批准数量").fill("120"); await page.getByLabel("调整原因").fill("模拟备料安排");
  const responsePromise = page.waitForResponse(r => r.url().endsWith('/demo/intent') && r.request().postDataJSON()?.op === 'override');
  await page.getByRole("button", { name: "确认修改并批准" }).click();
  const wire = await (await responsePromise).text();
  expect(wire).not.toContain('explicit_human_quantity_override');
  expect(wire).not.toContain('override_reason');
  expect(JSON.parse(wire).review.decision.reason).toBe('模拟备料安排');
  await expect(page.locator('.decision-reason dd')).toHaveText('模拟备料安排');
  await expect(page.locator(".decision-summary")).toContainText("120");
  await expect(page.locator(".decision-summary")).toContainText("修改数量");
  await expect(page.locator(".decision-summary")).not.toContainText("+20");
  const v = await snapshot(request); expect(v.facts.recommended).toBe("100"); expect(v.draft.quantity.numerator).toBe("120");
  await page.getByRole("button", { name: "查看采购申请草稿" }).click();
  await expect(page.getByRole("dialog")).toContainText("120");
  await page.reload();
  await expect(page.locator('.decision-reason dd')).toHaveText('模拟备料安排');
  expect((await snapshot(request)).review.decision.reason).toBe('模拟备料安排');
  await newRun(page);
  await expect(page.getByRole('heading',{name:'当前审核已失效'})).toBeVisible();
  await expect(page.locator('.decision-reason dd')).toHaveText('模拟备料安排');
  const stale = await snapshot(request);
  expect(stale.review.decision.reason).toBe('模拟备料安排');
  expect(JSON.stringify(stale)).not.toContain('explicit_human_quantity_override');
  expect(JSON.stringify(stale)).not.toContain('override_reason');
});

for (const value of ["", "99.999", "0", "-1", " 120", "120 ", "1e3", "1,000", "NaN", "120."]) {
  test(`Python rejects invalid quantity ${JSON.stringify(value)} without decision`, async ({ page, request }) => {
    await page.goto(detail); await page.getByRole("button", { name: "修改采购数量", exact: true }).click();
    await page.getByLabel("批准数量").fill(value); await page.getByLabel("调整原因").fill("reason");
    await page.getByRole("button", { name: "确认修改并批准" }).click();
    await expect(page.locator("#quantity-error")).toBeVisible();
    expect((await snapshot(request)).review.decision).toBeNull();
    await page.getByLabel("批准数量").fill("100"); await page.getByRole("button", { name: "确认修改并批准" }).click();
    await expect(page.getByRole("button", { name: "查看采购申请草稿" })).toBeVisible();
  });
}

test("exact long quantity crosses browser unchanged", async ({ page, request }) => {
  const value = "+000120.000000000000000000000000000000000000001";
  let transmitted = "";
  page.on("request", r => { if (r.method() === "POST" && r.postDataJSON()?.op === "override") transmitted = r.postDataJSON().quantity; });
  await page.goto(detail); await page.getByRole("button", { name: "修改采购数量", exact: true }).click();
  await page.getByLabel("批准数量").fill(value); await page.getByLabel("调整原因").fill("exact");
  await page.getByRole("button", { name: "确认修改并批准" }).click();
  await expect(page.getByRole("button", { name: "查看采购申请草稿" })).toBeVisible();
  expect(transmitted).toBe(value);
  const q = (await snapshot(request)).draft.quantity;
  expect(typeof q.numerator).toBe("string"); expect(typeof q.denominator).toBe("string"); expect(q.denominator.length).toBeGreaterThan(30);
});

test("reject reason required and no approved Draft", async ({ page, request }) => {
  await page.goto(detail); await page.getByRole("button", { name: "拒绝建议", exact: true }).click();
  await page.getByRole("button", { name: "确认拒绝" }).click();
  await expect(page.locator("#reason-error")).toBeVisible();
  await page.getByLabel("拒绝原因").fill("本轮不采购"); await page.getByRole("button", { name: "确认拒绝" }).click();
  await expect(page.locator(".decision-summary")).toContainText("本轮不采购");
  expect((await snapshot(request)).review.decision.reason).toBe('本轮不采购');
  await page.reload();
  await expect(page.locator('.decision-reason dd')).toHaveText('本轮不采购');
  expect((await snapshot(request)).canDraft).toBe(false);
  await expect(page.getByRole("button", { name: "查看采购申请草稿" })).toHaveCount(0);
});

for (const decision of ["pending", "approve", "override", "reject"] as const) {
  test(`${decision} → real new analysis → permanent stale → fresh review`, async ({ page, request }) => {
    await intent(request, "open_review");
    if (decision === "approve") await intent(request, "approve");
    if (decision === "override") await intent(request, "override", { quantity: "120", reason: "reason" });
    if (decision === "reject") await intent(request, "reject", { reason: "reason" });
    const old = await snapshot(request);
    await page.goto(detail); await newRun(page);
    await expect(page.getByRole("heading", { name: "当前审核已失效" })).toBeVisible();
    const fresh = await snapshot(request);
    expect(fresh.run).not.toBe(old.run); expect(fresh.binding.accepted_content_view_digest).toBe(old.binding.accepted_content_view_digest);
    expect(fresh.canDraft).toBe(false);
    await page.getByRole("button", { name: "重新审核", exact: true }).click();
    await expect(page.getByRole("button", { name: "按建议批准", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "按建议批准", exact: true })).toBeFocused();
    const review = await snapshot(request); expect(review.review.id).not.toBe(old.review.id); expect(review.review.decision).toBeNull();
    await approve(page);
  });
}

test("stale transport reference and duplicate intent cannot decide twice", async ({ request }) => {
  await intent(request,"open_review"); const v = await snapshot(request);
  const body = { op:"approve",intent:crypto.randomUUID(),session:v.session,run:v.run,review:v.review.id };
  const send = (data: object) => request.post('/demo/intent',{headers:{Origin:origin},data});
  expect((await send(body)).ok()).toBeTruthy(); expect((await send(body)).ok()).toBeTruthy();
  expect((await send({...body,op:'reject',reason:'no'})).status()).toBe(409);
  await intent(request,'new_analysis'); await intent(request,'open_review');
  expect((await send({...body,intent:crypto.randomUUID()})).status()).toBe(409);
  expect((await snapshot(request)).review.decision).toBeNull();
});

test("immutable Review refuses later explanation", async ({ request }) => {
  await intent(request,'open_review'); expect((await intent(request,'explain')).status()).toBe(409);
});

test("keyboard Escape focus and frozen font", async ({ page }) => {
  await page.goto(detail);
  const trigger = page.getByRole('button',{name:/查看完整依据/}); await trigger.focus(); await page.keyboard.press('Enter');
  await expect(page.getByRole('dialog')).toBeVisible(); await page.keyboard.press('Escape'); await expect(trigger).toBeFocused();
  await expect(page.getByRole('heading', { name: '采购决策', exact: true })).toHaveCSS('font-family',/Noto Sans SC/);
});

test("reduced motion and no overflow with dialog", async ({ page }, info) => {
  await page.emulateMedia({reducedMotion:'reduce'}); await page.goto(detail);
  await page.getByRole('button',{name:'修改采购数量',exact:true}).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({path:info.outputPath('connected-dialog.png'),fullPage:true});
});

test("workspace and detail responsive screenshots", async ({ page }, info) => {
  for(const url of ['/',detail]) {
    await page.goto(url); await expect(page.getByText('物料编码：SIM-M2')).toBeVisible();
    await page.evaluate(()=>document.fonts.ready);
    expect(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({path:info.outputPath(url==='/'?'workspace.png':'detail.png'),fullPage:true});
  }
});

test("no hosted requests or browser persistence", async ({ page }) => {
  const foreign:string[]=[]; page.on('request',r=>{if(!r.url().startsWith(origin))foreign.push(r.url());});
  await page.goto(detail); await approve(page);
  expect(foreign).toEqual([]);
  expect(await page.evaluate(()=>[localStorage.length,sessionStorage.length])).toEqual([0,0]);
  await expect(page.locator('footer')).toContainText('无 ERP');
});

test("runtime failure never falls back to fixture", async ({ page }) => {
  await page.route('**/demo/state',route=>route.abort()); await page.goto('/');
  await expect(page.getByRole('button',{name:'重新连接'})).toBeVisible();
  await expect(page.locator('.task-row')).toHaveCount(0);
});

test("opening Review and Draft does not create runs", async ({ page, request }) => {
  await page.goto(detail); const run=(await snapshot(request)).run;
  await approve(page); await page.getByRole('button',{name:'查看采购申请草稿'}).click();
  expect((await snapshot(request)).run).toBe(run);
});

test("workspace count follows Python terminal state", async ({ page }) => {
  await page.goto(detail); await approve(page); await page.goto('/');
  await expect(page.locator('.overview-strip')).toContainText('0');
  await expect(page.locator('.task-row')).toContainText('已完成人工决定');
});

test("uncertain approval response reads state without replay", async ({ page, request }) => {
  let approvals=0;
  await page.route('**/demo/intent',async route=>{
    if(route.request().postDataJSON().op==='approve') {
      approvals++;
      await route.fetch(); // Python commits; client loses only the response
      await route.abort();
    } else await route.continue();
  });
  await page.goto(detail); await approve(page);
  expect(approvals).toBe(1);
  expect((await snapshot(request)).canDraft).toBe(true);
  await expect(page.getByRole('alert')).toBeVisible();
});

test("cross-tab new run closes old approval dialog", async ({ page, request }) => {
  await page.goto(detail); await page.getByRole('button',{name:'按建议批准',exact:true}).click();
  await intent(request,'new_analysis');
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.getByRole('heading',{name:'当前审核已失效'})).toBeVisible();
  expect((await snapshot(request)).review.decision).toBeNull();
});

test("session loss does not restore browser decision", async ({ page }) => {
  await page.goto(detail); await approve(page);
  await page.route('**/demo/state',route=>route.fulfill({json:{initialized:false,session:'different-server-session'}}));
  await expect(page.getByRole('button',{name:'重新连接'})).toBeVisible();
  await expect(page.locator('.decision-summary')).toHaveCount(0);
  await expect(page.getByRole('button',{name:'查看采购申请草稿'})).toHaveCount(0);
});

test("frozen primary and summary contrast remain legible", async ({ page }) => {
  await page.goto(detail);
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
  const primary = page.getByRole("button", { name: "按建议批准", exact: true });
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
  await page.goto(detail);
  await page.evaluate(() => document.fonts.ready);
  await page.getByRole("button", { name: "按建议批准", exact: true }).click();
  await page.getByRole("button", { name: "按建议批准 100 件" }).click();
  await page.getByRole("button", { name: "查看采购申请草稿" }).click();
  await expect(page.getByRole("dialog")).toContainText("DRAFT");
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(page.viewportSize()!.width);
});


test("actual rendered Chinese fonts remain bundled Noto", async ({page, context}) => {
  const cdp = await context.newCDPSession(page);
  await cdp.send('DOM.enable'); await cdp.send('CSS.enable');
  for (const [url, selectors] of [["/", ['h1','.task-identity h3']], [detail, ['h1','.quantity']]] as const) {
    await page.goto(url); await expect(page.locator('h1')).toBeVisible(); await page.evaluate(()=>document.fonts.ready);
    const {root}=await cdp.send('DOM.getDocument');
    for(const selector of selectors) {
      const {nodeId}=await cdp.send('DOM.querySelector',{nodeId:root.nodeId,selector});
      const {fonts}=await cdp.send('CSS.getPlatformFontsForNode',{nodeId});
      expect(fonts.length).toBeGreaterThan(0);
      expect(fonts.every(f=>f.isCustomFont && /Noto Sans SC/.test(f.familyName))).toBe(true);
    }
  }
});

for (const name of ['按建议批准','修改采购数量','拒绝建议']) {
  test(`keyboard cancel and focus trap: ${name}`, async ({page,request})=>{
    await page.emulateMedia({reducedMotion:'reduce'}); await page.goto(detail);
    const trigger=page.getByRole('button',{name,exact:true});
    await trigger.focus(); await page.keyboard.press('Enter');
    const dialog=page.getByRole('dialog'); await expect(dialog).toBeVisible();
    if(name==='修改采购数量') { await page.getByLabel('批准数量').fill('120'); await page.keyboard.press('Enter'); }
    for(let i=0;i<9;i++) { await page.keyboard.press('Tab'); expect(await dialog.evaluate(el=>el.contains(document.activeElement))).toBe(true); }
    expect((await snapshot(request)).review.decision).toBeNull();
    await page.keyboard.press('Escape'); await expect(trigger).toBeFocused();
    await trigger.click(); await dialog.getByRole('button',{name:name==='按建议批准'?'返回查看':'取消',exact:true}).click();
    await expect(trigger).toBeFocused(); expect((await snapshot(request)).review.decision).toBeNull();
  });
}

test("long exact decision and reason stay within surfaces",async({page,request})=>{
  await page.goto(detail); await page.getByRole('button',{name:'修改采购数量',exact:true}).click();
  await page.getByLabel('批准数量').fill('1'.repeat(60)+'.0001');
  await page.getByLabel('调整原因').fill('人工原因'.repeat(50));
  await page.getByRole('button',{name:'确认修改并批准'}).click();
  await expect(page.getByRole('button',{name:'查看采购申请草稿'})).toBeVisible();
  const v=await snapshot(request);
  await page.reload(); await expect(page.locator('.decision-summary')).toContainText(v.draft.quantityText);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.getByRole('button',{name:'查看采购申请草稿'}).click();
  await expect(page.getByRole('dialog')).toContainText(v.draft.quantityText);
  expect(await page.getByRole('dialog').evaluate(el=>el.scrollWidth<=el.clientWidth)).toBe(true);
});

test("unknown route cannot select a different material",async({request})=>{
  const before=await snapshot(request);
  expect((await request.get('/procurement/M2')).status()).toBe(404);
  expect((await snapshot(request)).run).toBe(before.run);
});

test("one stable module across workspace and detail, compact task row", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator('h1')).toBeVisible(); await page.evaluate(() => document.fonts.ready);
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
  await expect(page).toHaveURL(detail);
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
  await expect(page).toHaveURL(detail);
  await page
    .getByRole("link", { name: "返回采购决策工作台" })
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
  await expect(page.locator('h1')).toBeVisible(); await page.evaluate(() => document.fonts.ready);
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
