import { chromium } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
const phase = process.argv[2] || "initial";
const out = `design-reviews/apple/${phase}`;
await mkdir(out, { recursive: true });
const browser = await chromium.launch();
const measures = [];
for (const variant of ["C1", "C2", "C3"])
  for (const width of [1440, 1280, 390]) {
    const page = await browser.newPage({
      viewport: { width, height: 800 },
      deviceScaleFactor: 1,
    });
    await page.goto(
      `http://127.0.0.1:4184/apple.html?variant=${variant}&present=1`,
    );
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(300);
    await page
      .locator(".design-stage")
      .screenshot({ path: `${out}/${variant}-${width}.png` });
    measures.push({
      variant,
      width,
      ...(await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        height: document.querySelector(".design-stage").getBoundingClientRect()
          .height,
        minFont: Math.min(
          ...[...document.querySelectorAll(".workspace *")]
            .filter((x) => x.textContent?.trim() && x.children.length === 0)
            .map((x) => parseFloat(getComputedStyle(x).fontSize)),
        ),
      }))),
    });
    if (width === 1440) {
      await page.goto(`http://127.0.0.1:4184/apple.html?variant=${variant}`);
      await page
        .getByRole("button", { name: "控件与状态", exact: true })
        .click();
      await page.waitForTimeout(300);
      await page.screenshot({ path: `${out}/${variant}-controls.png` });
    }
    await page.close();
  }
await writeFile(`${out}/measurements.json`, JSON.stringify(measures, null, 2));
console.log(measures);
await browser.close();
