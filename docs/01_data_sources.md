# 01 — Data Sources

## Source Hierarchy

| Source | Cost | Coverage | Quality | Use For |
|--------|------|----------|---------|---------|
| dartsdatabase.co.uk | Free | PDC 1994–present | High | Historical seeding, all-time records |
| DartsDB.com | Free | PDC 1992–present, Elo ratings | High | Model training baseline |
| dartsdata.com (unofficial API) | Free | PDC live + recent | Medium | Live scores, recent results |
| Sportradar Darts v2 | Paid (~$150/mo trial) | Full PDC + WDF | Very High | Production live data |
| iDarts API (idarts.nl) | Paid (contact) | PDC + WDF + BDO | Very High | Deep stats, used by TV commentators |
| DraftKings sportsbook page | Free (scrape) | Odds only | N/A | Odds tracking |
| The-odds-api.com | Free tier (500 req/mo) | Odds aggregation | High | Multi-book odds comparison |

---

## 1. dartsdatabase.co.uk — Free Historical Scraper

The most important free source. Covers every PDC event back to the mid-1990s.

```python
# scrapers/dartsdatabase.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import sqlite3

BASE_URL = "https://www.dartsdatabase.co.uk"

TOURNAMENT_IDS = {
    "world_championship": "1",
    "premier_league": "2",
    "world_matchplay": "5",
    "grand_slam": "19",
    "uk_open": "10",
    "world_grand_prix": "7",
    "players_championship_finals": "48",
    "world_series_finals": "116",
}

def get_tournament_results(tournament_id: str, year: int) -> list[dict]:
    """Scrape all match results for a given tournament and year."""
    url = f"{BASE_URL}/TournamentResults.aspx?TournamentID={tournament_id}&Year={year}"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; DartsResearch/1.0)"}
    
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    
    results = []
    table = soup.find("table", {"class": "resultstable"})
    if not table:
        return results
    
    for row in table.find_all("tr")[1:]:  # skip header
        cols = [td.get_text(strip=True) for td in row.find_all("td")]
        if len(cols) >= 6:
            results.append({
                "tournament_id": tournament_id,
                "year": year,
                "round": cols[0],
                "player1": cols[1],
                "score1": cols[2],
                "score2": cols[3],
                "player2": cols[4],
                "date": cols[5] if len(cols) > 5 else None,
            })
    
    time.sleep(1.5)  # be polite — 1 req per 1.5s
    return results


def get_player_stats(player_name: str) -> dict:
    """Fetch career stats for a player."""
    url = f"{BASE_URL}/PlayerDetails.aspx"
    params = {"PlayerName": player_name}
    headers = {"User-Agent": "Mozilla/5.0"}
    
    resp = requests.get(url, params=params, headers=headers, timeout=10)
    soup = BeautifulSoup(resp.text, "html.parser")
    
    stats = {}
    stat_table = soup.find("table", {"id": "statsTable"})
    if stat_table:
        for row in stat_table.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) == 2:
                stats[cols[0].get_text(strip=True)] = cols[1].get_text(strip=True)
    
    time.sleep(1.0)
    return stats


def seed_database(db_path: str = "darts.db", start_year: int = 2000):
    """Full historical seed. Run once. Takes ~30 min with polite delays."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id TEXT,
            tournament_name TEXT,
            year INTEGER,
            round TEXT,
            player1 TEXT,
            player2 TEXT,
            score1 INTEGER,
            score2 INTEGER,
            winner TEXT,
            date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    
    current_year = 2025
    for name, tid in TOURNAMENT_IDS.items():
        for year in range(start_year, current_year + 1):
            print(f"Fetching {name} {year}...")
            results = get_tournament_results(tid, year)
            for r in results:
                try:
                    s1 = int(r["score1"]) if r["score1"].isdigit() else None
                    s2 = int(r["score2"]) if r["score2"].isdigit() else None
                    winner = r["player1"] if (s1 and s2 and s1 > s2) else r["player2"]
                    cur.execute("""
                        INSERT INTO matches 
                        (tournament_id, tournament_name, year, round, player1, player2, 
                         score1, score2, winner, date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (tid, name, year, r["round"], r["player1"], r["player2"],
                          s1, s2, winner, r["date"]))
                except Exception as e:
                    print(f"  Error on row: {e}")
            conn.commit()
    
    conn.close()
    print("Seed complete.")
```

---

## 2. dartsdata.com — Unofficial Live API

This API is called by the dartsdata.com website. Undocumented but stable.

```python
# scrapers/dartsdata_api.py
import requests
from datetime import date, timedelta

DARTSDATA_BASE = "https://www.dartsdata.com/api"

def get_matches_on_date(target_date: date) -> list[dict]:
    """
    Fetch all match data for a given date.
    Returns leg-by-leg data including 3-dart averages when available.
    """
    url = f"{DARTSDATA_BASE}/matches"
    params = {"date": target_date.strftime("%Y-%m-%d")}
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.dartsdata.com/",
        "Accept": "application/json",
    }
    
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    if resp.status_code == 200:
        return resp.json()
    return []


def get_live_matches() -> list[dict]:
    """Poll for live match state. Call every 30s during events."""
    url = f"{DARTSDATA_BASE}/live"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.dartsdata.com/"}
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code == 200:
        return resp.json()
    return []


def get_player_tournament_stats(player_id: str, tournament_id: str) -> dict:
    url = f"{DARTSDATA_BASE}/player/{player_id}/tournament/{tournament_id}"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.dartsdata.com/"}
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code == 200:
        return resp.json()
    return {}


# Scheduled polling — run via cron or APScheduler
def start_live_poller(callback, interval_seconds: int = 30):
    """
    Example usage in a FastAPI lifespan or background thread.
    callback(matches) is called each poll with the latest match list.
    """
    import time
    while True:
        try:
            matches = get_live_matches()
            if matches:
                callback(matches)
        except Exception as e:
            print(f"Live poll error: {e}")
        time.sleep(interval_seconds)
```

---

## 3. The Odds API — Odds Aggregation (Free Tier Available)

```python
# scrapers/odds_api.py
import requests
import os

ODDS_API_KEY = os.getenv("ODDS_API_KEY")  # free tier: 500 req/mo
BASE = "https://api.the-odds-api.com/v4"

DARTS_SPORT_KEY = "darts_pdc_world_championship"  # check /sports endpoint for all keys

def get_available_darts_sports() -> list[dict]:
    url = f"{BASE}/sports"
    r = requests.get(url, params={"apiKey": ODDS_API_KEY})
    all_sports = r.json()
    return [s for s in all_sports if "darts" in s.get("key", "").lower()]


def get_odds(sport_key: str, markets: list[str] = ["h2h"]) -> list[dict]:
    """
    markets options: h2h (moneyline), spreads, totals
    Returns odds from all available bookmakers.
    """
    url = f"{BASE}/sports/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us,uk,eu",
        "markets": ",".join(markets),
        "oddsFormat": "american",
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def extract_draftkings_line(game: dict) -> dict | None:
    """Pull just DraftKings lines from an odds response."""
    for bookie in game.get("bookmakers", []):
        if bookie["key"] == "draftkings":
            return {
                "event": f"{game['home_team']} vs {game['away_team']}",
                "commence_time": game["commence_time"],
                "markets": bookie["markets"],
            }
    return None


def store_odds_snapshot(db_conn, sport_key: str):
    """Snapshot current odds to DB for line movement tracking."""
    import json
    from datetime import datetime
    
    games = get_odds(sport_key)
    cur = db_conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS odds_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sport_key TEXT,
            event_id TEXT,
            home_team TEXT,
            away_team TEXT,
            bookmaker TEXT,
            market TEXT,
            outcome TEXT,
            price INTEGER,
            snapshot_time TIMESTAMP
        )
    """)
    
    now = datetime.utcnow()
    for game in games:
        for bookie in game.get("bookmakers", []):
            for market in bookie.get("markets", []):
                for outcome in market.get("outcomes", []):
                    cur.execute("""
                        INSERT INTO odds_snapshots 
                        (sport_key, event_id, home_team, away_team, bookmaker, 
                         market, outcome, price, snapshot_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (sport_key, game["id"], game["home_team"], game["away_team"],
                          bookie["key"], market["key"], outcome["name"],
                          outcome["price"], now))
    db_conn.commit()
```

---

## 4. Database Schema (PostgreSQL / SQLite)

```sql
-- players
CREATE TABLE players (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    nickname    TEXT,
    nationality TEXT,
    dob         DATE,
    pdc_id      TEXT,
    dartsdb_id  TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- tournaments  
CREATE TABLE tournaments (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    short_name  TEXT,
    category    TEXT,  -- 'major', 'series', 'premier_league', 'european_tour'
    dk_covered  BOOLEAN DEFAULT FALSE,
    format      TEXT,  -- 'sets', 'legs'
    legs_to_win INTEGER,
    sets_to_win INTEGER,
    start_month INTEGER,
    end_month   INTEGER
);

-- matches
CREATE TABLE matches (
    id              SERIAL PRIMARY KEY,
    tournament_id   INTEGER REFERENCES tournaments(id),
    year            INTEGER,
    round           TEXT,
    player1_id      INTEGER REFERENCES players(id),
    player2_id      INTEGER REFERENCES players(id),
    score1          INTEGER,  -- legs or sets won
    score2          INTEGER,
    winner_id       INTEGER REFERENCES players(id),
    match_date      DATE,
    venue           TEXT,
    -- performance stats (populated when available)
    avg1            NUMERIC(5,2),  -- 3-dart average player1
    avg2            NUMERIC(5,2),
    checkout_pct1   NUMERIC(5,2),
    checkout_pct2   NUMERIC(5,2),
    legs_180s1      INTEGER,
    legs_180s2      INTEGER,
    high_checkout1  INTEGER,
    high_checkout2  INTEGER,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_matches_player1 ON matches(player1_id);
CREATE INDEX idx_matches_player2 ON matches(player2_id);
CREATE INDEX idx_matches_tournament ON matches(tournament_id, year);

-- odds snapshots (for line movement)
CREATE TABLE odds_snapshots (
    id              SERIAL PRIMARY KEY,
    match_id        INTEGER REFERENCES matches(id),
    bookmaker       TEXT,
    market          TEXT,  -- 'h2h', 'totals_180s', 'checkout_over_under'
    outcome         TEXT,
    price           INTEGER,  -- american odds
    implied_prob    NUMERIC(5,4),
    snapshot_time   TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_odds_match ON odds_snapshots(match_id, snapshot_time);

-- derived player stats (materialized/cached)
CREATE TABLE player_stats_cache (
    player_id       INTEGER REFERENCES players(id),
    tournament_id   INTEGER REFERENCES tournaments(id),
    year_from       INTEGER,
    year_to         INTEGER,
    matches_played  INTEGER,
    matches_won     INTEGER,
    win_rate        NUMERIC(5,4),
    avg_3dart       NUMERIC(5,2),
    avg_checkout    NUMERIC(5,2),
    avg_180s_per_leg NUMERIC(5,3),
    h2h_record      JSONB,  -- {"opponent_id": {"w": 5, "l": 3}, ...}
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (player_id, tournament_id, year_from, year_to)
);
```

---

## 5. Scheduled Data Jobs

```python
# jobs/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from scrapers.dartsdata_api import get_matches_on_date, get_live_matches
from scrapers.odds_api import store_odds_snapshot
from datetime import date
import asyncio

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job("cron", hour=3, minute=0)  # 3am daily
async def daily_results_pull():
    """Pull yesterday's completed match results."""
    yesterday = date.today() - timedelta(days=1)
    matches = get_matches_on_date(yesterday)
    await upsert_matches(matches)
    print(f"[daily] Pulled {len(matches)} matches for {yesterday}")

@scheduler.scheduled_job("interval", seconds=30)  # every 30s during live events
async def live_score_poll():
    """Only burns rate limit if there's a live event — check first."""
    if not await is_live_event_today():
        return
    matches = get_live_matches()
    await broadcast_live_updates(matches)  # push to websocket clients

@scheduler.scheduled_job("interval", minutes=15)  # every 15 min
async def odds_snapshot():
    """Snapshot odds from all DK-covered darts events."""
    for sport_key in DK_DARTS_SPORT_KEYS:
        store_odds_snapshot(get_db_conn(), sport_key)

scheduler.start()
```

---

## 6. Data Quality Notes

- **3-dart averages** are not always available from free sources — dartsdata.com has them for most PDC TV events but not every Players Championship.
- **Bull's-eye checkout routes** are not tracked in free sources. If you want "checkout route" data (e.g., T20, T19, Bull), you'll need iDarts or Sportradar.
- **Premier League** data is the most complete — it's heavily covered by TV and therefore all stat sites.
- **World Series legs** (Tokyo, Melbourne, etc.) have patchier historical coverage pre-2015.
- Always deduplicate player names — "Michael van Gerwen" vs "MVG" vs "van Gerwen, Michael" all appear in different sources.

```python
# utils/name_normalizer.py
import re

KNOWN_ALIASES = {
    "mvg": "Michael van Gerwen",
    "van gerwen": "Michael van Gerwen",
    "the power": "Phil Taylor",
    "taylor": "Phil Taylor",
    "the iceman": "Gerwyn Price",
    "the machine": "James Wade",
    "superchin": "Glen Durrant",
    "the wizard": "Simon Whitlock",
    "chuck": "Chuck Aiston",
}

def normalize_player_name(raw: str) -> str:
    clean = raw.strip().lower()
    clean = re.sub(r"[^a-z ]", "", clean)
    for alias, canonical in KNOWN_ALIASES.items():
        if alias in clean:
            return canonical
    # Title-case as fallback
    return raw.strip().title()
```
