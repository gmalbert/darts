# Historical Data Seeding Guide

## Overview

BullzIQ uses a **two-tier data strategy**:

1. **Real PDC Data** (dartsdatabase.co.uk) — Full historical match results from 2015–present
2. **Demo Data** (fallback) — Sample matches for testing if real scraping fails

Users **always load a pre-seeded database** so they don't wait for cold-start scrapes. The seeding process runs:
- **Nightly** via GitHub Actions (automated)
- **On-demand** via manual trigger
- **Manually** on your machine for local testing

---

## Quick Start

### Automated (Nightly via GitHub Actions) ✅ ALREADY RUNNING

No action needed — the workflow `.github/workflows/seed_db.yml` is deployed and runs automatically:

- **Daily at 03:00 UTC** — full rebuild from 2015
- **On push to `db/seed_real.py`, `scrapers/dartsdatabase.py`** — auto-trigger
- **On manual workflow dispatch** — run anytime from Actions UI

The seeded database is automatically committed with `[skip ci]` to avoid infinite loops.

---

## Manual Seeding (Local Machine)

Run this to pull fresh historical data and build `data_files/bullziq.db`:

```bash
# Clean any existing data
rm -Force data_files/bullziq.db data_files/db_is_real.flag

# Full seed from 2015 (takes 30–40 minutes)
python -m db.seed_real --start-year 2015
```

### What This Does

1. **Wipes existing tables** — clean slate
2. **Scans dartsdatabase.co.uk** — discovers PDC major events (World Championship, Premier League, etc.)
  - Probes ~2500 event IDs
   - Filters for tournaments from `start_year` onward
   - Extracts match results, player averages, scores
  - Prints heartbeat progress during scans (range start/end + periodic probe counts)
3. **Builds ORM entities** — creates Player, Tournament, Match, EloHistory records
4. **Computes Elo ratings** — updates player ratings based on historical matches
5. **Fetches live odds** — DraftKings odds from The Odds API (uses `ODDS_API_KEY` from `.env`)
6. **Writes flag file** — `data_files/db_is_real.flag` signals "real data loaded"

### Command-Line Options

```bash
# Full rebuild (default)
python -m db.seed_real --start-year 2015

# Refresh only current year (keeps old data, updates recent matches)
python -m db.seed_real --refresh-only

# Custom year range
python -m db.seed_real --start-year 2010
```

### Sample Output

```
=== BullzIQ Real Data Seeder  (start_year=2015, refresh_only=False) ===

Dropping and recreating ORM tables...
Scraping dartsdatabase.co.uk from 2015...
Scanning dartsdatabase.co.uk for PDC major events from 2015...
  Found: [25774] Premier League Week 15  (2026-05-14)
  Found: [24900] PDPA Players Championship 17  (2022-06-15)
  ...
Loaded 3012 raw matches from dartsdatabase.co.uk
Created 674 player records.
Imported 2919 historical matches.
Wrote 5838 EloHistory records.

Flag written: data_files/db_is_real.flag

=== Seed complete ===
```

### Observed Coverage (first run, May 2026)

| Tournament | Years Found | Matches |
|-----------|-------------|--------|
| PDC World Championship | 2018–2025 | 1118 |
| Premier League Darts | 2021–2026 | 406 |
| UK Open | 2018, 2025–2026 | 602 |
| World Matchplay | 2020–2025 | 187 |
| Grand Slam of Darts | 2019–2025 | 119 |
| World Grand Prix | 2021–2025 | 124 |
| World Series Finals | 2021–2024 | 108 |
| Players Championship Finals | 2023–2025 | 189 |

**Date range:** 2018-02-10 → 2026-05-14  
**Players:** 674  
**Note:** Coverage starts at 2018 because PDC event IDs from 2015–2017 are in a lower ID range. The discovery scan was updated to probe from eid=10000 to capture these. Re-running from scratch will extend coverage back to ~2015.

---

## GitHub Actions Workflow

The file `.github/workflows/seed_db.yml` controls automated seeding.

### Trigger Points

| Trigger | Schedule | Behavior |
|---------|----------|----------|
| **Schedule** | 03:00 UTC daily | Full rebuild from 2015 |
| **Push** | On changes to seed/scraper files | Full rebuild |
| **Manual (workflow_dispatch)** | Anytime via Actions UI | Full rebuild |

### Push Trigger Files

Changes to these files trigger an automatic seed:
- `db/seed_real.py`
- `scrapers/dartsdatabase.py`
- `scrapers/odds_api.py`
- `.github/workflows/seed_db.yml`

### Manual Trigger

1. Go to **GitHub** → your repo → **Actions** tab
2. Select **Seed Database** workflow
3. Click **Run workflow** → choose `main` branch → **Run workflow**
4. Watch the logs in real-time
5. Check the database commit in the latest commit message

### What Gets Committed

After each successful seed, the workflow commits:
- `data_files/bullziq.db` — pre-seeded SQLite database
- `data_files/db_is_real.flag` — flag indicating real data is loaded

**Note:** Commits use `[skip ci]` to prevent triggering CI pipelines, avoiding infinite loops.

---

## How It Works: Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ seed_real.py (entry point)                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Drop old tables (unless --refresh-only)                    │
│     ↓                                                            │
│  2. Call scrapers.dartsdatabase.seed_database()                │
│     ├─→ _discover_events(start_year) scans event IDs          │
│     ├─→ _fetch_event(eid) for each discovered event           │
│     ├─→ _parse_event_page(html, eid) extracts matches         │
│     └─→ Write raw_matches table (plain SQLite, not ORM)        │
│     ↓                                                            │
│  3. Read raw_matches → build ORM entities                      │
│     ├─→ Create Tournament records (only PDC majors)            │
│     ├─→ Create Player records (deduplicated)                  │
│     └─→ Create Match records with win/loss                    │
│     ↓                                                            │
│  4. Compute historical Elo ratings                              │
│     ├─→ Process matches chronologically                       │
│     ├─→ Update player ratings after each match                │
│     └─→ Write EloHistory records (audit trail)                │
│     ↓                                                            │
│  5. Fetch live odds (The Odds API)                             │
│     ├─→ Query upcoming matches                                │
│     ├─→ Get DraftKings lines                                  │
│     └─→ Cache in OddsSnapshot table                           │
│     ↓                                                            │
│  6. Write db_is_real.flag                                       │
│     └─→ Signals to ensure_seeded(): skip demo, use real data  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Issue: "dartsdatabase.co.uk may have blocked the scrape"

**Cause:** dartsdatabase.co.uk returned no match data (could be rate limiting, site down, or network issue).

**Fix:**
1. Check the site is up: `https://www.dartsdatabase.co.uk/display-event.php?eid=25774`
2. Wait a few minutes and retry (polite delay is 1 second between requests)
3. Check network/firewall isn't blocking dartsdatabase.co.uk

**Fallback:** If scraping fails, `seed_real.py` automatically falls back to demo data so the app still runs.

---

### Issue: "No raw matches found" or very few matches

**Cause:**
- Event ID ranges are inaccurate (dartsdatabase IDs aren't strictly chronological)
- All discovered events fall outside `start_year` range
- PDC major keyword filtering is too strict

**Fix:**
1. Reduce `start_year` to capture more events:
   ```bash
   python -m db.seed_real --start-year 2010
   ```
2. Check discovery output for found events — look for year spread
3. If events are being found but not imported, check the keyword list in `scrapers/dartsdatabase.py` (`PDC_MAJOR_KEYWORDS`)

---

### Issue: GH Action fails with "ODDS_API_KEY not found"

**Cause:** The secret wasn't added to GitHub.

**Fix:**
1. Go to your GitHub repo
2. **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `ODDS_API_KEY`
5. Value: (copy from your local `.env`)
6. Re-run the workflow

---

### Issue: Database file won't commit ("permission denied")

**Cause:** `.gitignore` isn't forcing track of `bullziq.db`.

**Fix:** Verify `.gitignore` has the force-track exceptions:
```
# In .gitignore:
!data_files/bullziq.db
!data_files/db_is_real.flag
```

Then:
```bash
git add -f data_files/bullziq.db data_files/db_is_real.flag
git commit -m "chore(db): force-track seeded database"
git push
```

---

## Architecture

### Tables Created

| Table | Purpose | Source |
|-------|---------|--------|
| `raw_matches` | Temporary hold for scraped data | dartsdatabase.co.uk |
| `players` | Player records with Elo, stats | ORM |
| `tournaments` | Tournament metadata | ORM + demo data |
| `matches` | Match records with scores, winner | ORM (from raw_matches) |
| `elo_history` | Audit trail of Elo changes per match | ORM (computed) |
| `odds_snapshots` | Live odds cache (DraftKings) | The Odds API |

### Key Files

| File | Purpose |
|------|---------|
| `db/seed_real.py` | Main seeding orchestrator |
| `scrapers/dartsdatabase.py` | HTML scraper + event discovery |
| `db/seed.py` | Demo seeder (fallback) |
| `db/schema.py` | ORM schema definitions |
| `models/elo.py` | Elo rating engine |
| `.github/workflows/seed_db.yml` | GitHub Actions automation |

---

## Performance Notes

- **Full seed (2015–2026):** 45–60 minutes
  - ~2500 event ID probes (1s delay each) after expanding lower discovery range
  - ~3000–4500 match imports expected (more with 2015–2017 coverage)
  - Elo computation is fast (<1 min)
- **Partial refresh (current year only):** 5–10 minutes
- **Live odds fetch:** <1 minute

---

## Data Retention

- **Raw data** (`raw_matches`) is **dropped on each full seed** — temporary staging table
- **ORM data** (players, matches, elo_history) is **versioned** — old records kept for audit
- **Flag file** (`db_is_real.flag`) indicates when real data was last loaded
- **Demo data** is never automatically deleted — manually clear if needed

---

## Questions?

Check the source files:
- Scraper logic: [scrapers/dartsdatabase.py](../scrapers/dartsdatabase.py)
- Pipeline: [db/seed_real.py](../db/seed_real.py)
- Workflow: [.github/workflows/seed_db.yml](../.github/workflows/seed_db.yml)
