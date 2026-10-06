# BullzIQ — Architecture

## Overview
Darts analytics and betting intelligence platform. Tracks players, tournaments, odds snapshots, and model predictions via a Streamlit app backed by SQLite.

## Hosting and odds policy

The React frontend targets Cloudflare and the FastAPI serving layer targets Render. All heavy scraping and modeling stays on GitHub Actions. The website serves cached overnight odds only: no visitor-triggered pulls, startup odds refreshes, or continuous polling worker. Continuous scheduling in `jobs/scheduler.py` is disabled.

The dedicated overnight workflow runs at 07:00 UTC (3 AM Eastern during daylight saving, 2 AM in winter), saves fixtures and odds snapshots, and exports best bets from that cache. Provider access requires `GITHUB_ACTIONS=true` and `BULLZIQ_NIGHTLY_ODDS_REFRESH=true`, with the refresh flag set only on that job's ingestion step. Reloading the website reads the saved prices. Snapshot timestamps remain visible so older prices are identifiable.

The workflow currently publishes SQLite through Git. Publishing those overnight results to the hosted serving database remains deployment work; do not assume GitHub updates automatically synchronize a Render persistent database.

## Data Flow
```
odds-api.io (live darts markets)
        ↓
scrapers/odds_api.py
        ↓
OddsSnapshot table (SQLite: data_files/bullziq.db)
        ↓
db/queries.py query layer
        ↓
Streamlit pages → predictions.py (entry)
        ↓
Real data flag: data_files/db_is_real.flag
```

## Database Schema (`data_files/bullziq.db`)
Managed by SQLAlchemy ORM in `db/schema.py`. Query layer in `db/queries.py`.

| Table | Purpose |
|-------|---------|
| Players | Player profiles, stats, ratings |
| Tournaments | Tournament metadata |
| OddsSnapshot | Live/historical odds per matchup |
| ModelPrediction | ML win probabilities |
| BetLog | Historical bet tracking |

## Seeding Pipeline
- `db/seed_real.py` — seeds from real data sources (primary)
- `db/seed.py` — startup guard, runs seed_real if db_is_real.flag absent

## ML Model
- Win probability from head-to-head form, average stats, recent tournament results
- No external ML library; computed via scoring rules in `db/queries.py`

## API Integrations
| Source | Purpose | Key | Limit |
|--------|---------|-----|-------|
| odds-api.io | Live darts market odds | `ODDS_API_IO_KEY` | 100 req/hr |

Preferred: cache event fetches, avoid per-event loops, filter to near-term fixtures first.

## Key Components
- `predictions.py` — entry, `st.set_page_config`, theme init
- `db/schema.py` — SQLAlchemy ORM models
- `db/queries.py` — all DB query functions (used by pages)
- `scrapers/odds_api.py` — odds-api.io integration
- `components/styles.py` — `themed_dataframe()`, `chart_style()` tokens
- `footer.py` — `add_betting_oracle_footer()`

## Theming
Auto day/night theme by browser local time:
- Day (06:00–20:00): `Light - Sky Glass`
- Night: `Dark - Petrol`
Stored in `st.session_state`. No dropdown unless user requests.

## Storage
- `data_files/bullziq.db` — SQLite (tracked in git)
- `data_files/db_is_real.flag` — presence = real data loaded (tracked)
- `data_files/best_bets_today.json` — Sports Picks Grid feed
