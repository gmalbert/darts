# BullzIQ — Architecture

## Overview
Darts analytics and betting intelligence platform. Tracks players, tournaments, odds snapshots, and model predictions via a Streamlit app backed by SQLite.

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
