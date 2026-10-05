import { test, expect } from "@playwright/test";
test("C3.1 preserves evidence and explanation-only authority", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/premium.html?present=1");
  await expect(page.locator(".evidence-group dd")).toHaveText([
    "30件",
    "30件",
    "100件",
    "+70件",
  ]);
  await expect(page.locator(".quantity")).toHaveText("100件");
  await page.getByRole("button", { name: "查看完整依据" }).click();
  await expect(page.getByRole("dialog").locator(".facts dd")).toHaveText([
    "30件",
    "30件",
    "100件",
    "70件",
    "100件",
  ]);
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("button", { name: "查看完整依据" }),
  ).toBeFocused();
  await page.getByRole("button", { name: "AI 在这里做什么" }).click();
  await expect(page.locator(".ai-disclosure")).toContainText(
    "不计算或修改采购数量",
  );
  await page.getByRole("button", { name: "预览人工审核", exact: true }).click();
  await expect(page.getByRole("dialog")).toContainText("不记录批准");
  await expect(page.getByRole("dialog")).toHaveAttribute("data-variant", "C31");
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("button", { name: "预览人工审核", exact: true }),
  ).toBeFocused();
  await page.getByRole("button", { name: "预览草稿", exact: true }).click();
  await expect(page.getByRole("dialog")).toContainText("批准数量尚未确定");
  await page.keyboard.press("Escape");
  await expect(page.locator(".draft")).toContainText("尚未形成");
  await expect(page.locator(".workspace-footer")).toContainText("无 ERP 写入");
  expect(errors).toEqual([]);
});
test("C3.1 system typography, frame and reduced motion", async ({ page }) => {
  const fontRequests: string[] = [];
  page.on("request", (r) => {
    if (/\.(woff2?|ttf|otf)(\?|$)/.test(r.url())) fontRequests.push(r.url());
  });
  await page.emulateMedia({ reducedMotion: "reduce" });
  for (const width of [1440, 1280, 390]) {
    await page.setViewportSize({ width, height: 800 });
    await page.goto("/premium.html?present=1");
    await page.evaluate(() => document.fonts.ready);
    const m = await page.evaluate(() => {
      const c = (s: string) => getComputedStyle(document.querySelector(s)!);
      return {
        width: document.documentElement.scrollWidth,
        height: document.querySelector(".design-stage")!.getBoundingClientRect()
          .height,
        font: c(".quantity").fontFamily,
        bodySize: parseFloat(c(".explanation>p").fontSize),
        motion: c(".workspace").animationName,
      };
    });
    expect(m.width).toBeLessThanOrEqual(width);
    if (width >= 1280) expect(m.height).toBeLessThanOrEqual(800);
    expect(m.bodySize).toBeGreaterThanOrEqual(15);
    expect(m.font).toContain("Microsoft YaHei UI");
    expect(m.font).not.toMatch(/Manrope|Noto/);
    expect(m.motion).toBe("none");
    await page.getByRole("button", { name: "AI 在这里做什么" }).click();
    await expect(
      page.locator(".ai-disclosure [data-slot=collapsible-content]"),
    ).toHaveCSS("animation-name", "none");
  }
  expect(fontRequests).toEqual([]);
});
test("C3.1 controls, material selection and modal keyboard", async ({
  page,
}) => {
  await page.goto("/premium.html");
  await page.getByRole("button", { name: "控件与状态", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await page.getByRole("tab", { name: "材质样本" }).click();
  await expect(dialog).toContainText("暖白工作区");
  await page.getByRole("switch").click();
  await expect(page.getByRole("switch")).toBeChecked();
  await page.getByLabel("输入样本", { exact: true }).fill("仅视觉样本");
  await page.getByLabel("备注样本", { exact: true }).fill("不保存");
  await expect(page.getByRole("button", { name: "不可用样本" })).toBeDisabled();
  const bounds = await dialog.boundingBox();
  const viewport = page.viewportSize()!;
  expect(bounds!.x).toBeGreaterThanOrEqual(0);
  expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(viewport.width);
  expect(bounds!.height).toBeLessThanOrEqual(viewport.height);
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("button", { name: "控件与状态", exact: true }),
  ).toBeFocused();
});

test('C3.1 operators and off-switch keep accessible contrast', async ({page})=>{
 await page.goto('/premium.html');
 const luminance=(value:string)=>{const rgb=value.startsWith('#')?value.slice(1).match(/.{2}/g)!.map(v=>parseInt(v,16)):value.match(/[\d.]+/g)!.slice(0,3).map(Number);const c=rgb.map(x=>{x/=255;return x<=.04045?x/12.92:((x+.055)/1.055)**2.4});return c[0]*.2126+c[1]*.7152+c[2]*.0722};
 const ratio=(a:string,b:string)=>{const x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)};
 const operator=await page.locator('.operator').first().evaluate(el=>({color:getComputedStyle(el).color,bg:getComputedStyle(el).getPropertyValue('--surface').trim()}));expect(ratio(operator.color,operator.bg)).toBeGreaterThanOrEqual(4.5);
 await page.getByRole('button',{name:'控件与状态',exact:true}).click();
 const toggle=await page.getByRole('switch').evaluate(el=>({shadow:getComputedStyle(el).boxShadow,border:getComputedStyle(el).getPropertyValue('--field-border').trim(),bg:getComputedStyle(el).getPropertyValue('--surface').trim()}));expect(toggle.shadow).not.toBe('none');expect(ratio(toggle.border,toggle.bg)).toBeGreaterThanOrEqual(3);
});
