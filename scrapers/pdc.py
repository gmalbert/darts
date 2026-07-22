"""Free PDC results scraper backed by the public tournament JSON feed.

The PDC website loads tournament hubs from the same public endpoint used by
the site itself.  This avoids the Cloudflare-protected DartsDatabase pages and
keeps the request count small: one calendar request per year plus one request
per relevant tournament.
"""

from __future__ import annotations

import sqlite3
import time
from datetime import date
from typing import Iterable

import requests

BASE_URL = "https://tournaments.darts.web.gc.pdcservices.co.uk/v2"
HEADERS = {
    "Accept": "application/json",
    "User-Agent": "BullzIQResearch/1.0 (+https://github.com/gmalbert/darts)",
}
REQUEST_DELAY = 0.35

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

TOURNAMENT_IDS = {value: value for value in KEYWORD_TO_TYPE.values()}


def _get_json(path: str, *, params: dict[str, object] | None = None) -> dict:
    response = requests.get(
        f"{BASE_URL}/{path.lstrip('/')}",
        params=params,
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()
    time.sleep(REQUEST_DELAY)
    return response.json()


def _classify(name: str) -> str | None:
    lowered = name.lower()
    if any(excluded in lowered for excluded in ("women", "qual", "qualifier", "qualifying")):
        return None
    for keyword, tournament_type in KEYWORD_TO_TYPE.items():
        if keyword in lowered:
            return tournament_type
    return None


def _calendar_year(year: int) -> list[dict]:
    payload = _get_json("calendar", params={
        "page.size": 250,
        "filter": f"seasonID:eq:{year}",
    })
    return payload.get("data", [])


def _discover_tournaments(start_year: int, end_year: int) -> Iterable[dict]:
    seen: set[str] = set()
    for year in range(start_year, end_year + 1):
        entries = _calendar_year(year)
        print(f"  PDC calendar {year}: {len(entries)} tournaments")
        for entry in entries:
            attrs = entry.get("attributes") or {}
            name = str(attrs.get("name") or "").strip()
            tournament_type = _classify(name)
            tournament_id = str(entry.get("id") or "")
            if not tournament_type or not tournament_id or tournament_id in seen:
                continue
            seen.add(tournament_id)
            yield {
                "id": int(tournament_id),
                "name": name,
                "type": tournament_type,
                "date": str(attrs.get("startDate") or ""),
            }


def _participant_name(participant: dict | None) -> str:
    if not participant:
        return ""
    first = str(participant.get("firstName") or "").strip()
    last = str(participant.get("lastName") or "").strip()
    return " ".join(part for part in (first, last) if part)


def _parse_tournament(tournament: dict) -> list[dict]:
    payload = _get_json(str(tournament["id"]))
    attrs = (payload.get("data") or {}).get("attributes") or {}
    event_date = str(attrs.get("startDate") or tournament.get("date") or "")[:10]
    if not event_date:
        return []
    try:
        event_year = date.fromisoformat(event_date).year
    except ValueError:
        return []

    matches: list[dict] = []
    for stage in attrs.get("stages") or []:
        round_name = str((stage.get("stage") or {}).get("name") or "Unknown")
        for fixture in stage.get("fixtures") or []:
            p1 = _participant_name(fixture.get("participant1"))
            p2 = _participant_name(fixture.get("participant2"))
            if not p1 or not p2:
                continue
            s1 = fixture.get("participant1Score")
            s2 = fixture.get("participant2Score")
            if s1 is None or s2 is None or fixture.get("status") != "Result":
                continue
            s1, s2 = int(s1), int(s2)
            matches.append({
                "event_id": int(tournament["id"]),
                "tournament_type": tournament["type"],
                "tournament_name": str(attrs.get("name") or tournament["name"]),
                "match_date": event_date,
                "year": event_year,
                "round": round_name,
                "player1": p1,
                "score1": s1,
                "score2": s2,
                "player2": p2,
                "winner": p1 if s1 > s2 else p2 if s2 > s1 else "",
                "avg_p1": None,
                "avg_p2": None,
            })
    return matches


def seed_database(
    db_path: str = "data_files/bullziq.db",
    start_year: int = 2015,
    end_year: int | None = None,
    recent_only: bool = False,
) -> None:
    """Fetch public PDC major results into the existing raw_matches table."""
    current_year = date.today().year
    first_year = current_year if recent_only else start_year
    last_year = current_year if end_year is None else end_year
    if recent_only:
        last_year = current_year

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            tournament_id TEXT,
            year INTEGER,
            round TEXT,
            player1 TEXT,
            score1 INTEGER,
            score2 INTEGER,
            player2 TEXT,
            winner TEXT,
            match_date TEXT,
            avg_p1 REAL,
            avg_p2 REAL,
            source TEXT DEFAULT 'pdc',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(event_id, player1, player2, round)
        )
    """)
    conn.commit()

    total = 0
    tournaments = list(_discover_tournaments(first_year, last_year))
    print(f"PDC public feed: {len(tournaments)} relevant tournaments ({first_year}-{last_year})")
    for tournament in tournaments:
        matches = _parse_tournament(tournament)
        print(f"  {tournament['name']}: {len(matches)} completed matches")
        for match in matches:
            cur.execute("""
                INSERT INTO raw_matches
                (event_id, tournament_id, year, round, player1, score1, score2,
                 player2, winner, match_date, avg_p1, avg_p2, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pdc')
                ON CONFLICT(event_id, player1, player2, round) DO UPDATE SET
                    tournament_id = excluded.tournament_id,
                    year = excluded.year,
                    score1 = excluded.score1,
                    score2 = excluded.score2,
                    winner = excluded.winner,
                    match_date = excluded.match_date,
                    avg_p1 = excluded.avg_p1,
                    avg_p2 = excluded.avg_p2,
                    source = 'pdc'
            """, (
                match["event_id"], match["tournament_type"], match["year"],
                match["round"], match["player1"], match["score1"], match["score2"],
                match["player2"], match["winner"], match["match_date"],
                match["avg_p1"], match["avg_p2"],
            ))
            total += 1
        conn.commit()
    conn.close()
    print(f"PDC seed complete: {total} raw match rows written to {db_path}")
