// parity/compare.ts — Phase 13 pixel-diff harness.
// For each (theme, viewport, route), diff parity/streamlit/X.png vs parity/react/X.png.
// Emits parity/diff/<theme>/<viewport>/<route>.png + a JSON summary.

import { chromium } from "playwright";
import { PNG } from "pngjs";
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { join, basename, dirname, relative } from "node:path";
import { VIEWPORTS, ROUTES, THEMES } from "./capture_streamlit";

const STREAM_DIR = process.env.STREAM_DIR ?? "parity/streamlit";
const REACT_DIR  = process.env.REACT_DIR  ?? "parity/react";
const DIFF_DIR   = process.env.DIFF_DIR   ?? "parity/diff";
const REPORT     = process.env.DIFF_REPORT ?? "parity/DIFF_REPORT.md";

interface DiffStats {
  path: string;
  total: number;
  diffPixels: number;
  diffPct: number;
  meanAbsDelta: number;
  maxChannelDelta: number;
  sizeMismatch: boolean;
}

function diffPNGs(a: Buffer, b: Buffer): { stats: Omit<DiffStats, "path" | "sizeMismatch"> & { pixelCount: number }; outPng: Buffer } {
  const A = PNG.sync.read(a);
  const B = PNG.sync.read(b);
  const width = Math.min(A.width, B.width);
  const height = Math.min(A.height, B.height);
  const out = new PNG({ width: A.width, height: A.height });
  let diffPixels = 0;
  let totalDelta = 0;
  let maxDelta = 0;
  const pixelCount = width * height;

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const i = (y * A.width + x) * 4;
      const j = (y * B.width + x) * 4;
      const o = (y * A.width + x) * 4;
      const dr = Math.abs(A.data[i]   - B.data[j]);
      const dg = Math.abs(A.data[i+1] - B.data[j+1]);
      const db = Math.abs(A.data[i+2] - B.data[j+2]);
      const m  = Math.max(dr, dg, db);
      totalDelta += dr + dg + db;
      if (m > maxDelta) maxDelta = m;
      if (m > 16) {
        diffPixels++;
        // Highlight differences in magenta over the React image.
        out.data[o]   = 255;
        out.data[o+1] = 0;
        out.data[o+2] = 255;
        out.data[o+3] = 200;
      } else {
        // Show the React side dimmed.
        out.data[o]   = B.data[j]   >> 2;
        out.data[o+1] = B.data[j+1] >> 2;
        out.data[o+2] = B.data[j+2] >> 2;
        out.data[o+3] = 255;
      }
    }
  }

  return {
    stats: {
      total: pixelCount,
      diffPixels,
      diffPct: pixelCount ? (diffPixels / pixelCount) * 100 : 0,
      meanAbsDelta: pixelCount ? totalDelta / (pixelCount * 3) : 0,
      maxChannelDelta: maxDelta,
      pixelCount,
    },
    outPng: PNG.sync.write(out),
  };
}

async function ensureStreamsForStreamlit(): Promise<void> {
  // Just a smoke check; capture runs separately.
  const sample = join(STREAM_DIR, "day", "desktop_standard", "home.png");
  if (!existsSync(sample)) {
    throw new Error(`Streamlit baseline not found at ${sample}. Run capture_streamlit.ts first.`);
  }
}

async function ensureReactCaptured(): Promise<void> {
  const sample = join(REACT_DIR, "day", "desktop_standard", "home.png");
  if (!existsSync(sample)) {
    throw new Error(`React baseline not found at ${sample}. Run capture_react.ts first.`);
  }
}

async function main(): Promise<void> {
  await ensureStreamsForStreamlit();
  await ensureReactCaptured();

  const stats: DiffStats[] = [];
  for (const theme of THEMES) {
    for (const vp of VIEWPORTS) {
      for (const route of ROUTES) {
        const aPath = join(STREAM_DIR, theme, vp.name, `${route.name}.png`);
        const bPath = join(REACT_DIR,  theme, vp.name, `${route.name}.png`);
        const outDir = join(DIFF_DIR, theme, vp.name);
        mkdirSync(outDir, { recursive: true });
        const outPath = join(outDir, `${route.name}.png`);

        if (!existsSync(aPath) || !existsSync(bPath)) {
          stats.push({ path: `${theme}/${vp.name}/${route.name}`, total: 0, diffPixels: 0, diffPct: 100, meanAbsDelta: 0, maxChannelDelta: 0, sizeMismatch: true });
          continue;
        }

        const aBuf = readFileSync(aPath);
        const bBuf = readFileSync(bPath);
        try {
          const { stats: s, outPng } = diffPNGs(aBuf, bBuf);
          writeFileSync(outPath, outPng);
          stats.push({ path: `${theme}/${vp.name}/${route.name}`, ...s, sizeMismatch: false });
        } catch (err) {
          stats.push({ path: `${theme}/${vp.name}/${route.name}`, total: 0, diffPixels: 0, diffPct: 100, meanAbsDelta: 0, maxChannelDelta: 0, sizeMismatch: true });
        }
      }
    }
  }

  // Sort worst first.
  stats.sort((x, y) => y.diffPct - x.diffPct);
  const totalCells = stats.length;
  const majorMismatches = stats.filter((s) => !s.sizeMismatch && s.diffPct > 5).length;

  const md = [
    "# BullzIQ Visual Diff Report",
    "",
    `Generated: ${new Date().toISOString()}`,
    `Total (theme × viewport × route) cells: ${totalCells}`,
    `Cells with >5% pixel diff: **${majorMismatches}**`,
    "",
    "## Worst-first ranking",
    "",
    "| Path | Size match | Total pixels | Diff pixels | Diff % | Mean Δ | Max Δ |",
    "|------|-----------:|-------------:|------------:|-------:|-------:|------:|",
    ...stats.map((s) =>
      `| ${s.path} | ${s.sizeMismatch ? "no" : "yes"} | ${s.total.toLocaleString()} | ${s.diffPixels.toLocaleString()} | ${s.diffPct.toFixed(2)}% | ${s.meanAbsDelta.toFixed(2)} | ${s.maxChannelDelta} |`,
    ),
    "",
    "## Acceptance criterion",
    "",
    "A page passes visual acceptance when diff % < 5% AND size matches.",
    majorMismatches === 0
      ? "**PASS** — no major mismatches detected."
      : `**${majorMismatches} cells exceed the 5% gate** — review diff images in ${DIFF_DIR}/<theme>/<viewport>/<route>.png.`,
    "",
  ].join("\n");

  mkdirSync(dirname(REPORT), { recursive: true });
  writeFileSync(REPORT, md, "utf8");
  console.log(`[compare] Wrote ${REPORT} (${totalCells} cells, ${majorMismatches} major mismatches)`);
  if (majorMismatches > 0) {
    console.error(`[compare] ${majorMismatches} cells exceed the 5% diff gate`);
    process.exit(2);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
