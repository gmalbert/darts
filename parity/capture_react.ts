// parity/capture_react.ts — Phase 13 React capture.
// Mirrors capture_streamlit.ts exactly so the diff is meaningful.

import { chromium, type Browser, type Page } from "playwright";
import { mkdir } from "node:fs/promises";
import { join } from "node:path";
import { VIEWPORTS, ROUTES, THEMES, type Theme } from "./capture_streamlit";

const REACT_URL = process.env.REACT_URL ?? "http://127.0.0.1:5173";
const OUT_DIR = process.env.PARITY_OUT_DIR ?? "parity/react";
const selectedRoutes = process.env.PARITY_ROUTE
  ? ROUTES.filter((route) => route.name === process.env.PARITY_ROUTE)
  : ROUTES;

async function snapRoute(browser: Browser, route: { name: string; path: string }, vp: typeof VIEWPORTS[number], theme: Theme): Promise<void> {
  const context = await browser.newContext({
    viewport: { width: vp.width, height: vp.height },
    deviceScaleFactor: 1,
  });
  const page: Page = await context.newPage();

  // The React app reads `biq_mode` from localStorage (browser-local time by default).
  // We seed it before any page script runs to lock the theme.
  await context.addInitScript((t: Theme) => {
    try {
      const hour = t === "day" ? 12 : 22;
      const fakeNow = new Date();
      fakeNow.setHours(hour, 0, 0, 0);
      const RealDate = Date;
      // eslint-disable-next-line no-global-assign
      Date = class extends RealDate {
        constructor(...args: ConstructorParameters<typeof Date>) {
          // @ts-expect-error Date constructor overloaded
          super(...(args.length ? args : [fakeNow]));
        }
        static now() {
          return fakeNow.getTime();
        }
      } as unknown as DateConstructor;
    } catch {
      /* ignore */
    }
  }, theme);

  const consoleErrors: string[] = [];
  page.on("pageerror", (err) => consoleErrors.push(err.message));
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });

  await page.goto(`${REACT_URL}${route.path}?biq_mode=${theme}`, { waitUntil: "networkidle", timeout: 60_000 });
  await page.waitForTimeout(1500);
  await page.evaluate(() => new Promise((r) => setTimeout(r, 600)));
  // Plotly performs a resize on the next animation frame. Let it settle before
  // resetting the nested app scroll immediately ahead of the capture.
  await page.waitForTimeout(500);
  // The React replica scrolls within <main>, like Streamlit's app viewport.
  // Always capture its top-of-page state rather than a browser-restored offset.
  await page.locator("main").evaluate((element) => { element.scrollTop = 0; });

  const outDir = join(OUT_DIR, theme, vp.name);
  await mkdir(outDir, { recursive: true });
  const outFile = join(outDir, `${route.name}.png`);
  // `main` is intentionally its own scroll container. Page full-page capture
  // and locator screenshotting can both scroll it while preparing the image.
  // A fixed viewport clip preserves the Streamlit baseline's top-of-app view.
  await page.screenshot({ path: outFile, clip: { x: 0, y: 0, width: vp.width, height: vp.height } });

  await context.close();
}

export async function captureReact(): Promise<{ ok: number; errors: string[] }> {
  const browser = await chromium.launch({ headless: true });
  const errors: string[] = [];
  let ok = 0;
  try {
    for (const theme of THEMES) {
      for (const vp of VIEWPORTS) {
      for (const route of selectedRoutes) {
          try {
            await snapRoute(browser, route, vp, theme);
            ok++;
            console.log(`  ✓ ${theme}/${vp.name}/${route.name}`);
          } catch (err) {
            const msg = `[capture_react] ${theme}/${vp.name}/${route.name}: ${(err as Error).message}`;
            console.error(msg);
            errors.push(msg);
          }
        }
      }
    }
  } finally {
    await browser.close();
  }
  return { ok, errors };
}

if (process.argv[1]?.replaceAll("\\", "/").endsWith("parity/capture_react.ts")) {
  captureReact()
    .then(({ ok, errors }) => {
      console.log(`[capture_react] ${ok} screenshots OK, ${errors.length} errors`);
      if (errors.length) process.exit(1);
    })
    .catch((err) => {
      console.error(err);
      process.exit(1);
    });
}
