import { chromium } from "playwright";
import { writeFileSync, mkdirSync } from "node:fs";
import { dirname } from "node:path";

const STREAMLIT_PORT = 8501;
const REACT_PORT = 5173;

const ROUTES = ["home", "Players", "Matches", "Tournaments", "Odds", "Tools"];
const REACT_ROUTES = ["home", "players", "matches", "tournaments", "odds", "tools"];

interface MetricResult {
  route: string;
  app: string;
  domContentLoaded: number;
  load: number;
  lcp: number;
  requests: number;
  transferred: number;
  jsHeap: number;
}

async function checkServer(port: number): Promise<boolean> {
  try {
    const res = await fetch(`http://127.0.0.1:${port}/`, { signal: AbortSignal.timeout(3000) });
    return res.ok;
  } catch {
    return false;
  }
}

async function measureRoute(
  page: import("playwright").Page,
  url: string,
  appName: string,
  routeName: string
): Promise<MetricResult> {
  await page.goto(url, { waitUntil: "load", timeout: 30000 });

  const timing = await page.evaluate(() => {
    const t = performance.timing;
    return {
      domContentLoaded: t.domContentLoadedEventEnd - t.navigationStart,
      load: t.loadEventEnd - t.navigationStart,
    };
  });

  await page.waitForTimeout(3000);

  const resourceData = await page.evaluate(() => {
    const entries = performance.getEntriesByType("resource");
    const transferred = entries.reduce((s: number, r: any) => s + (r.transferSize || 0), 0);
    const requests = entries.length;
    const jsHeap = (performance as any).memory?.usedJSHeapSize ?? 0;
    return { transferred, requests, jsHeap };
  });

  const lcp = await page.evaluate(() => {
    return new Promise<number>((resolve) => {
      try {
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          resolve(entries[entries.length - 1]?.startTime ?? 0);
        }).observe({ type: "largest-contentful-paint", buffered: true });
      } catch {
        // observer not supported or no entries
      }
      setTimeout(() => resolve(0), 5000);
    });
  });

  return {
    route: routeName,
    app: appName,
    domContentLoaded: timing.domContentLoaded,
    load: timing.load,
    lcp: Math.round(lcp * 100) / 100,
    requests: resourceData.requests,
    transferred: resourceData.transferred,
    jsHeap: resourceData.jsHeap,
  };
}

function formatKB(bytes: number): string {
  return (bytes / 1024).toFixed(1);
}

function formatMB(bytes: number): string {
  return (bytes / (1024 * 1024)).toFixed(2);
}

function writeReport(results: MetricResult[], outDir: string) {
  mkdirSync(outDir, { recursive: true });

  const header =
    "| Route | App | DOMContentLoaded (ms) | Load (ms) | LCP (ms) | Requests | Transferred (KB) | JS Heap (MB) |\n" +
    "|-------|-----|----------------------:|----------:|---------:|---------:|-----------------:|-------------:|";

  const rows = results.map(
    (r) =>
      `| ${r.route} | ${r.app} | ${r.domContentLoaded} | ${r.load} | ${r.lcp} | ${r.requests} | ${formatKB(r.transferred)} | ${formatMB(r.jsHeap)} |`
  );

  const md = `# Performance Metrics Report\n\n${header}\n${rows.join("\n")}\n`;
  writeFileSync(`${outDir}/METRICS_REPORT.md`, md, "utf-8");

  const csvHeader = "Route,App,DOMContentLoaded (ms),Load (ms),LCP (ms),Requests,Transferred (KB),JS Heap (MB)";
  const csvRows = results.map(
    (r) =>
      `${r.route},${r.app},${r.domContentLoaded},${r.load},${r.lcp},${r.requests},${formatKB(r.transferred)},${formatMB(r.jsHeap)}`
  );

  writeFileSync(`${outDir}/metrics.csv`, `${csvHeader}\n${csvRows.join("\n")}\n`, "utf-8");
}

function printSummary(results: MetricResult[]) {
  const streamlit = results.filter((r) => r.app === "Streamlit");
  const react = results.filter((r) => r.app === "React");

  const avgLoad = (arr: MetricResult[]) =>
    arr.length ? arr.reduce((s, r) => s + r.load, 0) / arr.length : 0;
  const totalTransferred = (arr: MetricResult[]) => arr.reduce((s, r) => s + r.transferred, 0);

  const stAvgLoad = avgLoad(streamlit);
  const reAvgLoad = avgLoad(react);
  const stTotalKB = formatKB(totalTransferred(streamlit));
  const reTotalKB = formatKB(totalTransferred(react));

  console.log("\n=== Summary ===");
  console.log(
    `Average load time — Streamlit: ${Math.round(stAvgLoad)}ms | React: ${Math.round(reAvgLoad)}ms`
  );
  console.log(`Total transferred — Streamlit: ${stTotalKB} KB | React: ${reTotalKB} KB`);

  if (streamlit.length && react.length) {
    const faster = stAvgLoad < reAvgLoad ? "Streamlit" : "React";
    const diff = Math.abs(Math.round(stAvgLoad - reAvgLoad));
    console.log(`${faster} is faster on average by ${diff}ms`);
  }
}

(async () => {
  try {
    const [stOk, reOk] = await Promise.all([
      checkServer(STREAMLIT_PORT),
      checkServer(REACT_PORT),
    ]);

    if (!stOk) console.warn(`WARNING: Streamlit server not reachable on port ${STREAMLIT_PORT}`);
    if (!reOk) console.warn(`WARNING: React server not reachable on port ${REACT_PORT}`);
    if (!stOk && !reOk) {
      console.error("No servers running. Exiting.");
      process.exit(0);
    }

    const browser = await chromium.launch({ headless: true });
    const results: MetricResult[] = [];

    for (let i = 0; i < ROUTES.length; i++) {
      const streamlitRoute = ROUTES[i];
      const reactRoute = REACT_ROUTES[i];

      if (stOk) {
        const page = await browser.newPage();
        const stUrl = `http://127.0.0.1:${STREAMLIT_PORT}/${streamlitRoute}?biq_mode=day`;
        try {
          console.log(`Measuring Streamlit: ${streamlitRoute}...`);
          results.push(await measureRoute(page, stUrl, "Streamlit", streamlitRoute));
        } catch (e) {
          console.warn(`Skipping Streamlit ${streamlitRoute}: ${e}`);
        }
        await page.close();
      }

      if (reOk) {
        const page = await browser.newPage();
        const reUrl = `http://127.0.0.1:${REACT_PORT}/${reactRoute}?biq_mode=day`;
        try {
          console.log(`Measuring React: ${reactRoute}...`);
          results.push(await measureRoute(page, reUrl, "React", reactRoute));
        } catch (e) {
          console.warn(`Skipping React ${reactRoute}: ${e}`);
        }
        await page.close();
      }
    }

    await browser.close();

    if (results.length) {
      writeReport(results, dirname("parity/METRICS_REPORT.md"));
      printSummary(results);
      console.log("\nFiles written: parity/METRICS_REPORT.md, parity/metrics.csv");
    } else {
      console.warn("No measurements collected.");
    }
  } catch (e) {
    console.error(`Fatal error: ${e}`);
  }

  process.exit(0);
})();
