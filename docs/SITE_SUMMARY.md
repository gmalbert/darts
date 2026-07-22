> **AI Onboarding Guide** — See also `.github/copilot-instructions.md` for full coding conventions.

# BullzIQ (Darts) — Site Summary

## What This App Does

Streamlit analytics app for professional darts betting (PDC circuit). Tracks player statistics from a real SQLite database, fetches live odds from odds-api.io (not The Odds API), and surfaces value bets with edge calculations. Features auto-detected day/night theming based on browser clock.

## Quick Start

```bash
# 1. Activate virtual environment
.\.venv\Scripts\Activate.ps1        # Windows
source .venv/bin/activate           # macOS/Linux

# 2. Seed the database with real data
python db/seed_real.py

# 3. Run the app
streamlit run predictions.py
```

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit (multi-page) |
| ORM / DB | SQLAlchemy 2.0 + SQLite |
| Odds | odds-api.io (DraftKings + Bet365; NOT The Odds API) |
| Visualization | Plotly |
| Config | python-dotenv (`.env` file) |

## Key Files

| File | Purpose |
|---|---|
| `predictions.py` | Streamlit entry point — page nav, theme detection |
| `db/schema.py` | SQLAlchemy ORM: all data models |
| `db/queries.py` | All data access layer functions — query SQLite here |
| `db/seed_real.py` | Seeds database with real player/match data |
| `db/seed.py` | Startup guard (checks if DB needs seeding) |
| `scrapers/odds_api.py` | odds-api.io client for live darts odds |
| `components/styles.py` | `themed_dataframe()` for all tabular data display |

## Data Flow

1. **Seed**: `db/seed_real.py` → populates SQLite with player stats, historical matches
2. **Live odds**: `scrapers/odds_api.py` → odds-api.io → `OddsSnapshot` writes (only when actual odds available)
3. **UI**: Streamlit reads from SQLite via `db/queries.py` → renders predictions, value bets, player stats

## Environment Variables

| Variable | Purpose | Required |
|---|---|---|
| `ODDS_API_IO_KEY` | odds-api.io — live darts odds (**NOT** `ODDS_API_KEY`) | Required |

**Warning**: The odds provider here is `odds-api.io`, hard limit 100 requests/hour. Do not confuse with `theoddsapi.com` (different service, different key).

## Critical Conventions

- **Real-data-first** — never add or re-enable automatic demo fallback behavior
- **Never** commit `.env`, tokens, or API keys
- **Preserve** existing public function signatures unless explicitly asked to change them
- Use `themed_dataframe(...)` from `components/styles.py` for all tabular data
- Use `chart_style(...)` tokens for chart colors — no hard-coded dark colors
- Use `width='stretch'` or `width='content'` — `use_container_width` is deprecated
- Theme is auto-detected: Day (6:00–20:00) → Light Sky Glass; Night → Dark Petrol
- Do **not** reintroduce a theme dropdown unless asked

## API Rate Limit Strategy

- Hard limit: 100 requests/hour on odds-api.io
- Prefer cached event fetches; avoid duplicate pagination
- Avoid per-event loops unless necessary; filter to near-term fixtures first
- If no lines are available, show user-facing copy: markets are not open yet (do not show empty/error state)

## Common Gotchas

- `OddsSnapshot` writes must be conditional on actual odds availability — do not write empty snapshots
- Guard all numeric formatting against `None`/NaN — use `pd.to_numeric(..., errors="coerce")`
- `round` field in player data is nullable — always provide explicit fallbacks
- `data_files/bullziq.db` and `data_files/db_is_real.flag` are tracked in Git as configured
