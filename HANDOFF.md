# BullzIQ Migration — Handoff Status

> **TL;DR:** Backend (FastAPI) and React frontend are **DONE and running**.
> All endpoints are live, returning real data. React frontend serves on port 5173
> and passes the Playwright e2e check with **0 console errors and 0 failed network
> requests** across all 6 routes. Streamlit baseline screenshots captured.
> Metrics comparison complete — React is **3.5× faster** on page load and transfers
> **55% less data** than Streamlit.
>
> **NOT DONE: the 5% pixel-diff gate.** All 72 theme × viewport × route cells still
> exceed 5% (best ~10%, worst ~56%). See §3.1. Feature/data parity is in place;
> the gap is CSS-level geometry, not missing functionality.

---

## 0. Repo / environment

- **Repo root:** `C:\Users\Greg\web_apps\darts`
- **Python:** 3.13.15 (FastAPI 0.141.1, uvicorn 0.52.3, pydantic 2.13.5, sqlalchemy 2.0.54)
- **Node:** v24.19.0, npm 12.0.2
- **Playwright:** 1.63.0 (npm package)
- **SQLite DB:** `data_files/bullziq.db` — seeded with real data (813 players, 9 tournaments, 6548 matches)
- **DB schema:** `db/schema.py` (SQLAlchemy 2.0) — unchanged from Streamlit

## 1. Currently running processes

| Service | Port | URL | Notes |
|---|---|---|---|
| Streamlit (original) | **8501** | http://127.0.0.1:8501 | Baseline for comparison |
| FastAPI (new backend) | **8001** | http://127.0.0.1:8001 | All /api/v1/* endpoints live |
| Vite dev server (React) | **5173** | http://127.0.0.1:5173 | React frontend |

## 2. What is DONE (all items complete)

### 2.1 FastAPI backend — COMPLETE
- **File:** `backend/app.py` (405 lines)
- **File:** `backend/api/queries.py` (652 lines)
- **File:** `backend/calculators/client_math.py` (179 lines)
- All endpoints under `/api/v1`: health, meta, players, matches, tournaments, odds, picks, steam, model/record, model/elo-history, analytics/yearly, analytics/era, calc/edge, calc/elo-prob, calc/format-adjust, calc/180s, calc/parlay, legal/footer
- CORS configured for `localhost:5173` and `127.0.0.1:5173`
- Fixed parlay endpoint Pydantic model → dict conversion bug

### 2.2 React frontend — COMPLETE
- **Location:** `frontend/` — Vite + React + TypeScript
- **TypeScript:** Zero compilation errors, `npm run build` succeeds
- **Pages built (all 6):**
  - `pages/HomePage.tsx` — 5 tabs (Picks, Schedule, Steam, Model Info, Historical)
  - `pages/PlayersPage.tsx` — 3 tabs (Rankings, Player Profile, Head-to-Head)
  - `pages/MatchesPage.tsx` — 3 tabs (Upcoming, Recent Results, Match Detail)
  - `pages/TournamentsPage.tsx` — 2 tabs (All Tournaments, Tournament Detail)
  - `pages/OddsPage.tsx` — 3 tabs (Current Lines, Line Movement, Steam Moves)
  - `pages/ToolsPage.tsx` — 4 tabs (Edge, 180s, Format Variance, Parlay)
- **Components:** Shell (sidebar nav), Tabs, BettingOracleFooter, ModelDisclaimer
- **Theme:** Auto day/night from `?biq_mode` query param (matches Streamlit). Light = Sky Glass (#f6fbff), Dark = Petrol (#071418)
- **API client:** `api/client.ts` — typed fetch wrapper for all FastAPI endpoints
- **Calculators:** `utils/calculators.ts` — verbatim port of `client_math.py` (Elo, edge, Poisson, format-adjust, parlay)
- **Formatters:** `utils/formatters.ts` — nationality flags, American odds, dates
- **CSS:** `index.css` — complete CSS variable system mirroring Streamlit's `--biq-*` tokens

### 2.3 Streamlit baseline capture — COMPLETE
- **Script:** `parity/capture_streamlit.ts`
- **Output:** `parity/streamlit/` — 72 PNGs (6 routes × 6 viewports × 2 themes)
- All screenshots captured successfully

### 2.4 React capture — COMPLETE
- **Script:** `parity/capture_react.ts`
- **Output:** `parity/react/` — 72 PNGs (6 routes × 6 viewports × 2 themes)
- All screenshots captured successfully, 0 errors

### 2.5 Pixel-diff comparison — HARNESS COMPLETE, 5% GATE NOT MET
- **Script:** `parity/compare.ts`
- **Output:** `parity/DIFF_REPORT.md` + `parity/diff/` images
- **Current result: 72 / 72 cells exceed the 5% gate.** Best ~10% (night/desktop), worst ~55.7% (`day/mobile_narrow/matches`). All sizes match (no layout collapse).
- The diff is dominated by CSS-level geometry — Streamlit's internal `st.columns()` padding/gutters, font rasterisation, and its mobile column-stacking thresholds — not by missing content or features.
- This is the one open parity gap. Details and remediation options in §3.1.

### 2.6 Visual reference doc — COMPLETE
- **File:** `docs/STREAMLIT_VISUAL_REFERENCE.md` — 450+ line comprehensive spec of all 6 pages
- Covers: global shell, theme tokens, all page layouts, card/table/chart structures, filters, empty states, column ratios, badge styles, legal copy, responsive behavior

### 2.7 E2E test — PASSING
- **Script:** `parity/e2e_react.ts` — Playwright click-through of all 6 routes
- **Current result:** 6 routes, **0 console errors, 0 failed network requests, all pages have content**
- Bugs found and fixed to get here:
  - `calc/parlay` passed Pydantic models to `client_math.parlay()` → HTTP 500 (fixed: converts to dicts)
  - `PlayersPage` prefetched `/players/{id}/stats` for all 813 players → 813 HTTP requests, all 404 because the stats cache is empty (fixed: replaced with a single `/players/stats-batch` call)
  - `/players/{id}/stats` has no rows in this DB — stats cache is unpopulated; profile stats legitimately show "No stats available"
  - `get_recent_results()` omitted `match_id`, so React list keys were `undefined` → key warning; also the UI read `m.match_date`/`m.score1`/`m.score2`, which that endpoint never returns (it returns `date` and a combined `score` string)
  - Implied probabilities were rendered without ×100 (`0.4%` instead of `40.0%`) on `/odds`, including bar widths and the shift-in-pp column
  - Emoji written as `\uXXXX` escapes inside **JSX text** rendered literally (e.g. a literal `\uD83E\uDD20 BullzIQ Odds Tracker` heading)
  - `natFlag()` was being passed player *names* instead of nationality codes, so every player showed the 🌍 fallback. `/matches` and `/odds` now return `p1_nationality`/`p2_nationality`
  - `calculators.parity.test.ts` asserted camelCase keys while both Python and TypeScript use snake_case → test failed on a correct implementation. All expected values were re-verified against `client_math.py`. `npm run test:calc` now passes

### 2.8 Performance metrics — COMPLETE
- **Script:** `parity/metrics.ts`
- **Output:** `parity/METRICS_REPORT.md` + `parity/metrics.csv`

#### Results summary:
| Metric | Streamlit | React/FastAPI | Improvement |
|---|---|---|---|
| Avg page load | 313ms | 88ms | **3.5× faster** |
| Total transferred | 46,415 KB | 20,789 KB | **55% less** |
| HTTP requests (avg) | 167 | 64 | **62% fewer** |
| JS Heap (avg) | 36.7 MB | 11.3 MB | **69% less** |
| LCP (avg) | 1,065ms | 141ms | **7.5× faster** |

## 3. Known issues / future work

### 3.1 Pixel-diff parity (5% gate)
Desktop viewports are 9–16% diff. Achieving <5% would require:
- Matching Streamlit's exact font rendering (platform-dependent, irreducible)
- Matching Streamlit's `st.columns()` internal padding/margins exactly
- Adjusting sidebar width, metric card spacing, tab underline thickness
- Mobile viewports are further off (27–57%) due to Streamlit's responsive column stacking

### 3.2 Players page stats cache is empty (data, not code)
`/players/{id}/stats` reads the `PlayerStatsCache` table, which has **no rows** in `data_files/bullziq.db`. Individual requests return a legitimate `404 No stats cache for player N`, so the Player Profile tab shows "No stats available". The Rankings tab no longer depends on it (it uses `win_rate_last20` from `/players`, and stats now come from one `/players/stats-batch` call). Populating the cache belongs in the overnight GitHub Actions job per `AGENTS.md`, not in a visitor-triggered path.

### 3.3 Charts
React pages use CSS/SVG bar charts instead of Plotly. For full parity, `react-plotly.js` should be wired up for:
- Elo trajectory line charts
- Poisson distribution bars
- Edge distribution histograms
- Year-by-year match volume
- Era performance grouped bars
- Odds implied probability charts

### 3.4 Streamlit stability
Streamlit dies periodically (likely due to WebSocket disconnection or memory). Consider running it with `--server.maxMessageSize` or a process supervisor.

### 3.5 Stale parity artifacts
`parity/` contains ~100 debug log files and probe PNGs from earlier iterations, plus `parity/smoke_react.ts`, which targets port **5174** and asserts CSS classes from a superseded design (`.two select`, `.range-label`, `.selected`, `.js-plotly-plot`). It does not match the current UI. Use `parity/e2e_react.ts` as the authoritative check; consider deleting the stale logs and `smoke_react.ts`.

## 4. Quick start

```bash
# 1. Start all services
cd C:\Users\Greg\web_apps\darts
Start-Process python -ArgumentList "-m uvicorn backend.app:app --host 127.0.0.1 --port 8001" -WindowStyle Hidden
Start-Process python -ArgumentList "-m streamlit run predictions.py --server.port 8501 --server.address 127.0.0.1 --server.headless true" -WindowStyle Hidden
cd frontend && npx vite --host 127.0.0.1 --port 5173

# 2. Verify
curl http://127.0.0.1:8001/api/v1/health    # FastAPI
curl -o NUL -s -w "%{http_code}" http://127.0.0.1:8501  # Streamlit
curl -o NUL -s -w "%{http_code}" http://127.0.0.1:5173  # React

# 3. Run parity checks
cd C:\Users\Greg\web_apps\darts
npx tsx parity/e2e_react.ts        # E2E test
npx tsx parity/capture_react.ts    # React screenshots
npx tsx parity/capture_streamlit.ts # Streamlit screenshots
npx tsx parity/compare.ts          # Pixel diff
npx tsx parity/metrics.ts          # Performance metrics
```

## 5. File structure summary

```
backend/
  app.py                    # FastAPI app — all routes, CORS, lifespan
  api/queries.py            # DB query layer (port of db/queries.py)
  calculators/client_math.py # Pure-Python math mirrors

frontend/                   # React + TS + Vite
  src/
    main.tsx                # Entry point
    App.tsx                 # Router (react-router-dom)
    index.css               # CSS variables + layout styles
    theme/tokens.ts         # Day (Sky Glass) + Night (Petrol) tokens
    theme/ThemeProvider.tsx  # Auto day/night via ?biq_mode
    api/client.ts           # Typed fetch wrapper
    hooks/useApi.tsx         # Data fetching hook
    utils/calculators.ts    # Elo, edge, Poisson, format, parlay
    utils/formatters.ts     # Flags, odds, dates
    components/layout/Shell.tsx # Sidebar + main layout
    components/controls/Tabs.tsx # Tab switching
    components/legal/Footer.tsx  # Betting Oracle footer + RG
    pages/HomePage.tsx      # 5 tabs
    pages/PlayersPage.tsx   # 3 tabs
    pages/MatchesPage.tsx   # 3 tabs
    pages/TournamentsPage.tsx # 2 tabs
    pages/OddsPage.tsx      # 3 tabs
    pages/ToolsPage.tsx     # 4 tabs

parity/
  capture_streamlit.ts      # Streamlit baseline capture
  capture_react.ts          # React capture
  compare.ts                # Pixel-diff harness
  e2e_react.ts              # E2E error check
  metrics.ts                # Performance comparison
  DIFF_REPORT.md            # Visual diff results
  METRICS_REPORT.md         # Performance metrics
  metrics.csv               # Raw metrics data
  streamlit/                # 72 Streamlit PNGs
  react/                    # 72 React PNGs
  diff/                     # Diff images

docs/
  STREAMLIT_VISUAL_REFERENCE.md # 450+ line UI spec
```

---

**Last update:** 2026-10-05. Backend + React frontend complete and verified: `npx tsx parity/e2e_react.ts` → PASS (6 routes, 0 console errors, 0 failed requests); `npm run test:calc` → pass; `npx tsc -b --noEmit` → clean; `npx vite build` → clean; `python -m py_compile` → clean. Open item: the 5% pixel-diff gate (§2.5, §3.1) and Plotly chart parity (§3.3). React on 5173, FastAPI on 8001, Streamlit on 8501.
