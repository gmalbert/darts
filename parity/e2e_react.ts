import { chromium } from "playwright";

const routes = ["/", "/players", "/matches", "/tournaments", "/odds", "/tools"];
const BASE = "http://127.0.0.1:5173";

interface RouteResult {
  route: string;
  consoleErrors: string[];
  failedRequests: string[];
  hasContent: boolean;
}

async function testRoute(page: any, route: string): Promise<RouteResult> {
  const consoleErrors: string[] = [];
  const failedRequests: string[] = [];
  let hasContent = false;

  const onConsole = (msg: any) => {
    if (msg.type() === "error") {
      consoleErrors.push(msg.text());
    }
  };

  const onPageError = (err: Error) => {
    consoleErrors.push(err.message);
  };

  const onRequestFailed = (req: any) => {
    failedRequests.push(req.url());
  };

  page.on("console", onConsole);
  page.on("pageerror", onPageError);
  page.on("requestfailed", onRequestFailed);

  try {
    await page.goto(`${BASE}${route}`, { timeout: 30000, waitUntil: "networkidle" });

    const bodyText = await page.evaluate(() => document.body?.innerText?.trim() ?? "");
    hasContent = bodyText.length > 0;

    const tabs = await page.$$(".tab, .tabs");
    if (tabs.length > 0) {
      for (const tab of tabs) {
        try {
          await tab.click();
          await page.waitForTimeout(500);
        } catch {
        }
      }
    }
  } catch (err: any) {
    consoleErrors.push(`Navigation error: ${err.message}`);
  } finally {
    page.removeListener("console", onConsole);
    page.removeListener("pageerror", onPageError);
    page.removeListener("requestfailed", onRequestFailed);
  }

  return { route, consoleErrors, failedRequests, hasContent };
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const results: RouteResult[] = [];

  for (const route of routes) {
    const page = await browser.newPage();
    const result = await testRoute(page, route);
    results.push(result);
    await page.close();
  }

  await browser.close();

  const totalConsoleErrors = results.reduce((sum, r) => sum + r.consoleErrors.length, 0);
  const totalFailedRequests = results.reduce((sum, r) => sum + r.failedRequests.length, 0);
  const allHaveContent = results.every((r) => r.hasContent);
  const passed = totalConsoleErrors === 0 && totalFailedRequests === 0 && allHaveContent;

  console.log(`\nRoutes tested: ${results.length}`);
  console.log(`Console errors: ${totalConsoleErrors}`);
  console.log(`Failed network requests: ${totalFailedRequests}`);
  console.log(`All pages have content: ${allHaveContent}`);

  for (const r of results) {
    for (const err of r.consoleErrors) {
      console.log(`  [${r.route}] console error: ${err}`);
    }
    for (const url of r.failedRequests) {
      console.log(`  [${r.route}] failed request: ${url}`);
    }
  }

  console.log(`\nOverall: ${passed ? "PASS" : "FAIL"}`);
  process.exit(passed ? 0 : 1);
}

main();
