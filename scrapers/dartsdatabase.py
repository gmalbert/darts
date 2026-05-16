"""
scrapers/dartsdatabase.py — Real data scraper for dartsdatabase.co.uk

The site migrated from .aspx to .php.  Event results now live at:
    https://www.dartsdatabase.co.uk/display-event.php?eid=<ID>

Discover strategy
-----------------
Event IDs are NOT sequential by date — they span PDC, WDF, BDO, ADO etc. in
the same ID space.  The approach here is:
  1. Build an in-memory catalog by scanning a wide ID range (recent events are
     ~24 000–26 000; 2015 PDC events tend to fall in ~18 000–23 000).
  2. Keep only events whose title matches a PDC major keyword list.
  3. Parse each matched event for its full bracket/round results.

Polite scraping: 1.0–1.5 s delay between requests, User-Agent declared.

Usage::
    from scrapers.dartsdatabase import seed_database
    seed_database(db_path="data_files/bullziq.db", start_year=2015)
"""

from __future__ import annotations

import re
import time
import sqlite3
from datetime import datetime
from typing import Generator

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.dartsdatabase.co.uk"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; BullzIQResearch/1.0; "
        "+https://bullziq.com/about)"
    )
}

# ── PDC major event keywords (case-insensitive) ───────────────────────────────
PDC_MAJOR_KEYWORDS = [
    "world championship",
    "premier league",
    "world matchplay",
    "grand slam",
    "uk open",
    "world grand prix",
    "players championship final",
    "world series of darts final",
    "european championship",
]

# Keyword → tournament_type (matches TOURNAMENT_DATA keys in seed.py)
KEYWORD_TO_TYPE: dict[str, str] = {
    "world championship": "world_championship",
    "premier league": "premier_league",
    "world matchplay": "world_matchplay",
    "grand slam": "grand_slam",
    "uk open": "uk_open",
    "world grand prix": "world_grand_prix",
    "players championship final": "players_championship_finals",
    "world series of darts final": "world_series_finals",
    "european championship": "european_championship",
}

# Estimated discovery ranges by era (calibrated from probing the site)
# eid=23500 → 2013, eid=24300 → 2020, eid=24900 → 2022, eid=25774 → May 2026
# PDC majors (few per year, higher ID density in recent years)
DISCOVERY_RANGES: list[tuple[int, int, int]] = [
    # (start, end, step) — wider step = fewer requests, may miss events
    # Calibration points (from live probing):
    #   eid=23500 → ADO event, Jan 2013
    #   eid=24300 → Colorado Open, Nov 2020
    #   eid=24900 → PDPA PC 17, Jun 2022
    #   eid=25774 → Premier League Week 15, May 2026
    # PDC events from 2015–2017 appear to be in the 10000–18000 range.
    (10_000, 14_000, 15),   # ~2010–2014 era
    (14_000, 18_000, 10),   # ~2014–2017 era
    (18_000, 20_000, 10),   # ~2013–2016 era (PDC events mixed with others)
    (20_000, 22_500, 8),    # ~2016–2019 era
    (22_500, 24_000, 5),    # ~2019–2021 era
    (24_000, 24_800, 3),    # ~2021–2022 era
    (24_800, 25_200, 2),    # ~2022–2023 era
    (25_200, 25_900, 1),    # ~2024–2026 era (dense, scan every ID)
]


# ── Parsing helpers ───────────────────────────────────────────────────────────

def _parse_event_page(html: str, eid: int) -> dict | None:
    """
    Parse a display-event.php page.  Returns a dict with:
        name, date, tournament_type, matches: list[dict]
    or None if the page has no usable match data.
    """
    soup = BeautifulSoup(html, "html.parser")

    # ── Extract event name and date from the page ──────────────────────────
    # The event name lives in: <div class="chip"><strong>Name DD/MM/YYYY</strong></div>
    chip_div = soup.find("div", class_="chip")
    if chip_div:
        strong_el = chip_div.find("strong")
        raw_header = strong_el.get_text(" ", strip=True) if strong_el else chip_div.get_text(" ", strip=True)
    else:
        # Fallback: try any heading tag
        header_el = soup.find("h2") or soup.find("h3") or soup.find("h4")
        raw_header = header_el.get_text(" ", strip=True) if header_el else ""

    # Date is usually DD/MM/YYYY at the end
    date_match = re.search(r"(\d{2}/\d{2}/\d{4})", raw_header)
    event_date: datetime | None = None
    if date_match:
        try:
            event_date = datetime.strptime(date_match.group(1), "%d/%m/%Y")
        except ValueError:
            pass

    event_name = re.sub(r"\d{2}/\d{2}/\d{4}", "", raw_header).strip()
    # Also check the page title tag
    if not event_name:
        title_el = soup.find("title")
        event_name = title_el.get_text(strip=True) if title_el else f"Event {eid}"

    # ── Classify as a PDC major (or skip) ─────────────────────────────────
    name_lower = event_name.lower()
    t_type: str | None = None
    for kw, tt in KEYWORD_TO_TYPE.items():
        if kw in name_lower:
            t_type = tt
            break

    if not t_type:
        return None  # Not a PDC major we care about

    if event_date is None:
        return None  # Can’t date the event

    # ── Parse the results table ───────────────────────────────────────────
    # Table class on the new PHP site is "w3-table w3-striped w3-white"
    matches: list[dict] = []
    current_round = "Unknown"

    results_table = soup.find("table", class_="w3-table") or soup.find("table")
    if not results_table:
        return None

    for row in results_table.find_all("tr"):
        cells = [td.get_text(strip=True) for td in row.find_all("td")]
        if not cells:
            continue

        if len(cells) == 1:
            # Round header row: "Quarter Final", "Semi Final", etc.
            round_text = cells[0].strip()
            if round_text and not re.search(r"\d", round_text[:3]):
                current_round = round_text
            continue

        if len(cells) >= 3:
            # Match row: "Player A (avg)" | "s1 V s2" | "Player B (avg)"
            p1_raw = cells[0]
            score_raw = cells[1]
            p2_raw = cells[2]

            # Strip averages from player names: "Luke Littler (100.20)" → "Luke Littler"
            p1_name = re.sub(r"\s*\(\d+\.\d+\)", "", p1_raw).strip()
            p2_name = re.sub(r"\s*\(\d+\.\d+\)", "", p2_raw).strip()

            # Extract averages
            avg_m1 = re.search(r"\((\d+\.\d+)\)", p1_raw)
            avg_m2 = re.search(r"\((\d+\.\d+)\)", p2_raw)
            avg_p1 = float(avg_m1.group(1)) if avg_m1 else None
            avg_p2 = float(avg_m2.group(1)) if avg_m2 else None

            # Parse score: "6 V 3"
            score_match = re.match(r"(\d+)\s*[Vv]\s*(\d+)", score_raw.strip())
            if not score_match:
                continue

            s1 = int(score_match.group(1))
            s2 = int(score_match.group(2))

            if not p1_name or not p2_name:
                continue

            winner = p1_name if s1 > s2 else p2_name if s2 > s1 else ""

            matches.append({
                "event_id": eid,
                "tournament_type": t_type,
                "tournament_name": event_name,
                "match_date": event_date.strftime("%Y-%m-%d"),
                "year": event_date.year,
                "round": current_round,
                "player1": p1_name,
                "score1": s1,
                "score2": s2,
                "player2": p2_name,
                "winner": winner,
                "avg_p1": avg_p1,
                "avg_p2": avg_p2,
            })

    if not matches:
        return None

    return {"name": event_name, "date": event_date, "tournament_type": t_type, "matches": matches}


def _fetch_event(eid: int, delay: float = 1.0) -> dict | None:
    """Fetch and parse one event page. Returns None if no PDC major data."""
    url = f"{BASE_URL}/display-event.php"
    try:
        resp = requests.get(url, params={"eid": eid}, headers=HEADERS, timeout=15)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"  Request failed for eid={eid}: {exc}")
        return None
    finally:
        time.sleep(delay)

    return _parse_event_page(resp.text, eid)


def _discover_events(start_year: int = 2015, end_year: int | None = None) -> Generator[dict, None, None]:
    """
    Scan ID ranges to discover PDC major events between start_year and end_year (inclusive).
    Yields parsed event dicts.
    """
    seen_eids: set[int] = set()

    for range_start, range_end, step in DISCOVERY_RANGES:
        for eid in range(range_start, range_end, step):
            if eid in seen_eids:
                continue
            seen_eids.add(eid)

            event = _fetch_event(eid, delay=1.0)
            if event is None:
                continue

            event_year = event["date"].year
            if event_year < start_year:
                continue
            if end_year is not None and event_year > end_year:
                continue

            print(f"  Found: [{eid}] {event['name']}  ({event['date'].date()})")
            yield event


# ── Public API ────────────────────────────────────────────────────────────────

def get_tournament_results(tournament_id: str, year: int) -> list[dict]:
    """
    Legacy compatibility shim — kept so old callers don’t break.
    With the new PHP URL structure this stub always returns [];
    use seed_database() instead.
    """
    return []


# Kept for backwards compatibility with old scrapers/dartsdatabase.py
TOURNAMENT_IDS: dict[str, str] = {
    "world_championship":        "world_championship",
    "premier_league":            "premier_league",
    "world_matchplay":           "world_matchplay",
    "grand_slam":                "grand_slam",
    "uk_open":                   "uk_open",
    "world_grand_prix":          "world_grand_prix",
    "players_championship_finals": "players_championship_finals",
    "world_series_finals":       "world_series_finals",
}


def seed_database(db_path: str = "data_files/bullziq.db", start_year: int = 2015, end_year: int | None = None) -> None:
    """
    Discover PDC major events from dartsdatabase.co.uk and write raw match
    rows to the ``raw_matches`` SQLite table.

    Designed for scheduled/manual use.  Polite delays between requests.
    Scans ~2 500 event IDs using adaptive step sizes (see DISCOVERY_RANGES).
    Pass end_year to limit the scrape to a specific year range.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw_matches (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id        INTEGER,
            tournament_id   TEXT,
            year            INTEGER,
            round           TEXT,
            player1         TEXT,
            score1          INTEGER,
            score2          INTEGER,
            player2         TEXT,
            winner          TEXT,
            match_date      TEXT,
            avg_p1          REAL,
            avg_p2          REAL,
            source          TEXT DEFAULT 'dartsdatabase',
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(event_id, player1, player2, round)
        )
    """)
    conn.commit()

    total = 0
    year_range = f"{start_year}–{end_year}" if end_year else f"{start_year}+"
    print(f"Scanning dartsdatabase.co.uk for PDC major events ({year_range})...")

    for event in _discover_events(start_year=start_year, end_year=end_year):
        for m in event["matches"]:
            cur.execute(
                """
                INSERT OR IGNORE INTO raw_matches
                (event_id, tournament_id, year, round, player1, score1,
                 score2, player2, winner, match_date, avg_p1, avg_p2)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    m["event_id"], m["tournament_type"], m["year"],
                    m["round"], m["player1"], m["score1"],
                    m["score2"], m["player2"], m["winner"],
                    m["match_date"], m.get("avg_p1"), m.get("avg_p2"),
                ),
            )
            total += 1
        conn.commit()

    conn.close()
    print(f"Seed complete: {total} raw match rows written to {db_path}")


if __name__ == "__main__":
    print("Starting dartsdatabase.co.uk historical seed (new PHP format)...")
    seed_database(start_year=2015)
