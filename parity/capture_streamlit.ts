// parity/capture_streamlit.ts — Phase 0 baseline capture for the Streamlit app.
//
// Boots a headless Chromium, walks every primary route at every required viewport
// in both Sky Glass day and Petrol night themes, and writes PNGs into
// parity/streamlit/{day,night}/{viewport}/{route}.png.
//
// Usage:
//   npx tsx parity/capture_streamlit.ts
//
// Env:
//   STREAMLIT_URL (default http://127.0.0.1:8501)
//   PARITY_OUT_DIR (default parity/streamlit)

import { chromium, type Browser, type Page } from "playwright";
import { mkdir } from "node:fs/promises";
import { join } from "node:path";

const STREAMLIT_URL = process.env.STREAMLIT_URL ?? "http://127.0.0.1:8501";
const OUT_DIR = process.env.PARITY_OUT_DIR ?? "parity/streamlit";

export const VIEWPORTS = [
  { name: "desktop_wide",     width: 1440, height: 1000 },
  { name: "desktop_standard", width: 1280, height: 800  },
  { name: "tablet",           width: 768,  height: 1024 },
  { name: "mobile_large",     width: 430,  height: 932  },
  { name: "mobile_standard",  width: 390,  height: 844  },
  { name: "mobile_narrow",    width: 375,  height: 812  },
];

export const ROUTES: Array<{ name: string; path: string }> = [
  { name: "home",        path: "/"                       },
  { name: "players",     path: "/Players"                 },
  { name: "matches",     path: "/Matches"                 },
  { name: "tournaments", path: "/Tournaments"             },
  { name: "odds",        path: "/Odds"                    },
  { name: "tools",       path: "/Tools"                   },
];

export const THEMES = ["day", "night"] as const;
export type Theme = (typeof THEMES)[number];
const selectedRoutes = process.env.PARITY_ROUTE
  ? ROUTES.filter((route) => route.name === process.env.PARITY_ROUTE)
  : ROUTES;

async function snapRoute(browser: Browser, route: { name: string; path: string }, vp: typeof VIEWPORTS[number], theme: Theme): Promise<void> {
  const context = await browser.newContext({
    viewport: { width: vp.width, height: vp.height },
    deviceScaleFactor: 1,
  });
  const page: Page = await context.newPage();

  // Force the biq_mode query param so the embedded iframe-based day/night
  // sync is bypassed on first paint.
  const url = `${STREAMLIT_URL}/?biq_mode=${theme}`;

  // Listen for console errors — surface them but don't crash on render warnings.
  const consoleErrors: string[] = [];
  page.on("pageerror", (err) => consoleErrors.push(err.message));
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });

  await page.goto(url, { waitUntil: "networkidle", timeout: 60_000 });

  // Streamlit's navigation is client-side. Direct deep links render an empty
  // document in this app, so navigate through the actual sidebar just as a
  // user does before taking the baseline screenshot.
  if (route.path !== "/") {
    const label = route.name[0].toUpperCase() + route.name.slice(1);
    const sidebar = page.locator('[data-testid="stSidebar"]');
    await sidebar.getByText(label, { exact: true }).click();
    await page.waitForLoadState("networkidle");
  }

  // Streamlit renders via WebSocket; wait for charts/tables/data to settle.
  await page.waitForTimeout(2500);

  // Give Plotly a moment to finish drawing.
  await page.evaluate(() => new Promise((r) => setTimeout(r, 800)));

  const outDir = join(OUT_DIR, theme, vp.name);
  await mkdir(outDir, { recursive: true });
  const outFile = join(outDir, `${route.name}.png`);
  await page.screenshot({ path: outFile, fullPage: true });

  await context.close();
}

export async function captureStreamlit(): Promise<{ ok: number; errors: string[] }> {
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
            const msg = `[capture_streamlit] ${theme}/${vp.name}/${route.name}: ${(err as Error).message}`;
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

// `tsx` normalizes Windows drive paths differently from `file://` URLs, so
// compare the entrypoint name rather than raw URL strings.
if (process.argv[1]?.replaceAll("\\", "/").endsWith("parity/capture_streamlit.ts")) {
  captureStreamlit()
    .then(({ ok, errors }) => {
      console.log(`[capture_streamlit] ${ok} screenshots OK, ${errors.length} errors`);
      if (errors.length) process.exit(1);
    })
    .catch((err) => {
      console.error(err);
      process.exit(1);
    });
}
