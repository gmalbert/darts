<p align="center">
	<img src="data_files/logo.png" alt="BullzIQ logo" width="220" />
</p>

# BullzIQ (PDC Darts Analytics)

BullzIQ is a Streamlit app for PDC darts analytics with:
- Elo-based player ratings
- Match and props modeling
- Upcoming fixture tracking
- DraftKings odds ingestion and movement views

The project is now **real-data-first** (no automatic demo fallback).

---

## Current Data/Platform Status

- Historical match data: scraped from dartsdatabase.co.uk
- Live odds provider: odds-api.io (`/v3`, sport=`darts`)
- Bookmakers on current plan: DraftKings + BetMGM BR
- Odds API rate limit: 100 requests/hour
- App theme: auto day/night based on browser local time
	- Day: Sky Glass
	- Night: Petrol

### Why you may see "Lines not open yet"

This is expected when upcoming fixtures are in the DB but sportsbooks have not posted moneylines yet.
Fixtures can appear before odds snapshots exist.

---

## Features

### Predictions (Home)
- Daily picks ranked by model edge
- Upcoming schedule
- Steam move panel
- Historical performance charts

### Players
- Elo rankings and history charts
- Player profile stats
- Recent matches
- Head-to-head comparison

### Matches
- Upcoming fixtures (with odds when available)
- Recent results
- Match-level odds movement + H2H details

### Odds
- Current lines
- Implied probability movement
- Steam move feed

### Tools
- Edge calculator
- 180s calculator
- Format variance explorer
- Parlay edge helper

---

## Odds Ingestion Notes

- Upcoming match stubs are created independently from odds availability.
- Odds snapshots are only written when ML markets exist.
- The scheduler refreshes odds periodically (see [jobs/scheduler.py](jobs/scheduler.py)).

If fixtures are visible but odds are missing, the most common reason is simply that lines are not open yet.

---

## Documentation

- Seeding guide: [docs/11_data_seeding.md](docs/11_data_seeding.md)
- Data sources: [docs/01_data_sources.md](docs/01_data_sources.md)
- Models: [docs/02_models.md](docs/02_models.md)
- Legal/compliance: [docs/09_legal_and_compliance.md](docs/09_legal_and_compliance.md)

---

## Disclaimer

Model output is informational and not financial advice.
