# Historical Data Seeding Guide

## Overview

BullzIQ uses a **real-data-first strategy**:

1. **Real PDC Data** (official public PDC results feed) — Full historical match results from 2015–present
2. **No automatic demo fallback** — seeding aborts if real scrape data is unavailable

Users **always load a pre-seeded database** so they don't wait for cold-start scrapes. The seeding process runs:
- **Nightly** via GitHub Actions (automated incremental refresh)
- **On-demand** via manual trigger
- **Manually** on your machine for local testing

---

## Quick Start

### Automated (Nightly via GitHub Actions) ✅ ALREADY RUNNING

No action needed — the workflow `.github/workflows/seed_db.yml` is deployed and runs automatically:

- **Daily at 03:00 UTC** — incremental refresh of recent event IDs, rebuilding the ORM from accumulated raw data
- **On push to `db/seed_real.py`, `scrapers/pdc.py`** — auto-trigger
- **On manual workflow dispatch** — run anytime from Actions UI

The seeded database is automatically committed with `[skip ci]` to avoid infinite loops.

---

## Manual Seeding (Local Machine)

Run this to pull fresh historical data and build `data_files/bullziq.db`:

```bash
# Clean any existing data
rm -Force data_files/bullziq.db data_files/db_is_real.flag

# Full seed from 2015 (typically about 5–6 minutes)
python -m db.seed_real --start-year 2015
```

### What This Does

1. **Rebuilds ORM tables** — incremental refreshes retain the raw staging table; full rebuilds reset it
2. **Reads the public PDC calendar and tournament feed** — discovers PDC major events (World Championship, Premier League, etc.)
  - Incremental refreshes read the current season only
  - Full rebuilds read one calendar page per year, then one JSON document per relevant tournament
  - Extracts completed match results, players, scores, round names, and dates
3. **Builds ORM entities** — creates Player, Tournament, Match, EloHistory records
4. **Computes Elo ratings** — updates player ratings based on historical matches
5. **Optionally fetches live odds** — odds are normally handled by the dedicated odds job, not every data seed
6. **Writes flag file** — `data_files/db_is_real.flag` signals "real data loaded"

### Command-Line Options

```bash
# Full rebuild (manual/reconciliation)
python -m db.seed_real --start-year 2015

# Incremental refresh (keeps historical raw data and scans a bounded recent ID window)
python -m db.seed_real --refresh-only

# Optional: include odds in this run (uses shared API quota)
python -m db.seed_real --refresh-only --refresh-odds

# Custom year range
python -m db.seed_real --start-year 2010
```

### Sample Output

```
=== BullzIQ Real Data Seeder  (start_year=2015, refresh_only=False) ===

Dropping and recreating ORM tables...
Scraping the public PDC results feed from 2015...
  PDC calendar 2015: 107 tournaments
  PDC calendar 2026: 221 tournaments
  ...
Loaded 6541 raw matches from the public PDC feed
Created 813 player records.
Imported 6541 historical matches.
Wrote 13082 EloHistory records.

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
**Note:** The official feed includes event hubs back to 2015. Future/current-season hubs may be discovered before their fixtures are completed; those contribute zero completed matches until the next refresh.

---

## GitHub Actions Workflow

The file `.github/workflows/seed_db.yml` controls automated seeding.

### Trigger Points

| Trigger | Schedule | Behavior |
|---------|----------|----------|
| **Schedule** | 03:00 UTC daily | Incremental recent-event refresh |
| **Push** | On changes to seed/scraper files | Full rebuild |
| **Manual (workflow_dispatch)** | Anytime via Actions UI | Incremental by default; optional full rebuild |

### Push Trigger Files

Changes to these files trigger an automatic seed:
- `db/seed_real.py`
- `scrapers/dartsdatabase.py`
- `scrapers/odds_api.py`
- `.github/workflows/seed_db.yml`

### Manual Trigger

1. Go to **GitHub** → your repo → **Actions** tab
2. Select **Seed Database** workflow
3. Click **Run workflow** → choose `main` branch → leave **Re-scan all historical event IDs** off for an incremental refresh, or enable it for a full reconciliation → **Run workflow**
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
│     ├─→ incremental mode scans IDs around the raw-data cursor  │
│     ├─→ full mode scans all configured event ID ranges         │
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
│  5. Fetch live odds (odds-api.io)                              │
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

### Issue: "PDC public feed request failed"

**Cause:** The official feed was temporarily unavailable or returned a
rate-limit/server error.

**Fix:**
1. Check a public hub: `https://www.pdc.tv/tournament-hub/10639`
2. Wait a few minutes and retry (the scraper spaces requests by 0.35 seconds)
3. Confirm the runner can reach `pdcservices.co.uk`

**Behavior:** If scraping fails, `seed_real.py` aborts with an error. It does not auto-seed demo data.

---

### Issue: "No raw matches found" or very few matches

**Cause:**
- The PDC calendar filter or public feed schema changed
- All discovered events fall outside `start_year` range
- PDC major keyword filtering is too strict

**Fix:**
1. Reduce `start_year` to capture more events:
   ```bash
   python -m db.seed_real --start-year 2010
   ```
2. Check discovery output for found events — look for year spread
3. If events are being found but not imported, check the keyword list in `scrapers/pdc.py` (`KEYWORD_TO_TYPE`)

---

### Issue: GH Action fails with "ODDS_API_IO_KEY not set"

**Cause:** The secret wasn't added to GitHub.

**Fix:**
1. Go to your GitHub repo
2. **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `ODDS_API_IO_KEY`
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
| `raw_matches` | Temporary hold for scraped data | Official PDC public feed |
| `players` | Player records with Elo, stats | ORM |
| `tournaments` | Tournament metadata | ORM |
| `matches` | Match records with scores, winner | ORM (from raw_matches) |
| `elo_history` | Audit trail of Elo changes per match | ORM (computed) |
| `odds_snapshots` | Live odds cache (DraftKings) | odds-api.io |

### Key Files

| File | Purpose |
|------|---------|
| `db/seed_real.py` | Main seeding orchestrator |
| `scrapers/pdc.py` | Public PDC calendar/feed scraper |
| `db/seed.py` | Startup DB checks (no auto demo fallback) |
| `db/schema.py` | ORM schema definitions |
| `models/elo.py` | Elo rating engine |
| `.github/workflows/seed_db.yml` | GitHub Actions automation |

---

## Performance Notes

- **Full seed (2015–2026):** about 5–6 minutes
  - One calendar request per year plus one request per relevant tournament
  - ~6500 completed major-event matches in the current run
  - Elo computation is fast (<1 min)
- **Partial refresh (current year only):** about 1 minute
- **Live odds fetch:** <1 minute

---

## Data Retention

- **Raw data** (`raw_matches`) is **dropped on each full seed** — temporary staging table
- **ORM data** (players, matches, elo_history) is **versioned** — old records kept for audit
- **Flag file** (`db_is_real.flag`) indicates when real data was last loaded
- **Demo data** is not automatically seeded by app startup or real seeding

---

## Questions?

Check the source files:
- Scraper logic: [scrapers/pdc.py](../scrapers/pdc.py)
- Pipeline: [db/seed_real.py](../db/seed_real.py)
- Workflow: [.github/workflows/seed_db.yml](../.github/workflows/seed_db.yml)
