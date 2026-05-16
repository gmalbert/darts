"""
scrapers/odds_api.py — The Odds API integration for DraftKings darts lines.

Docs: https://the-odds-api.com/
Free tier: 500 requests/month.

Usage:
    from scrapers.odds_api import fetch_darts_odds, upsert_odds_snapshot

Set ODDS_API_KEY in your .env file.
"""

from __future__ import annotations

import os
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
BASE_URL = "https://api.the-odds-api.com/v4"
SPORT = "darts_pdc"        # The Odds API sport key for PDC darts
MARKETS = "h2h"            # head-to-head moneyline
REGIONS = "us"             # US (DraftKings) odds
ODDS_FORMAT = "american"
BOOK_WHITELIST = {"draftkings"}


def fetch_darts_odds() -> list[dict]:
    """
    Fetch current PDC darts odds from The Odds API.
    Returns a list of match dicts with p1/p2 name and American odds.
    """
    if not ODDS_API_KEY:
        print("ODDS_API_KEY not set. Skipping odds fetch.")
        return []

    url = f"{BASE_URL}/sports/{SPORT}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT,
        "bookmakers": ",".join(BOOK_WHITELIST),
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"Odds API fetch failed: {exc}")
        return []

    # Log remaining quota
    remaining = resp.headers.get("x-requests-remaining", "?")
    used = resp.headers.get("x-requests-used", "?")
    print(f"Odds API: {used} used / {remaining} remaining this month")

    data = resp.json()
    results = []

    for event in data:
        home_team = event.get("home_team", "")
        away_team = event.get("away_team", "")
        commence_time = event.get("commence_time", "")

        dk_bookmaker = next(
            (b for b in event.get("bookmakers", []) if b["key"] in BOOK_WHITELIST),
            None,
        )
        if not dk_bookmaker:
            continue

        h2h_market = next(
            (m for m in dk_bookmaker.get("markets", []) if m["key"] == "h2h"),
            None,
        )
        if not h2h_market:
            continue

        outcomes = {o["name"]: o["price"] for o in h2h_market.get("outcomes", [])}
        p1_odds = outcomes.get(home_team)
        p2_odds = outcomes.get(away_team)

        if p1_odds is None or p2_odds is None:
            continue

        def _implied(odds: float) -> float:
            if odds < 0:
                return (-odds) / (-odds + 100)
            return 100 / (odds + 100)

        results.append({
            "event_id": event.get("id", ""),
            "player1": home_team,
            "player2": away_team,
            "commence_time": commence_time,
            "p1_odds": int(p1_odds),
            "p2_odds": int(p2_odds),
            "p1_implied": round(_implied(p1_odds), 4),
            "p2_implied": round(_implied(p2_odds), 4),
            "book": "DraftKings",
            "fetched_at": datetime.utcnow().isoformat(),
        })

    return results


def upsert_odds_snapshot(match_id: int, p1_odds: int, p2_odds: int) -> None:
    """
    Write a new OddsSnapshot to the database for a given match.
    Called by the APScheduler job every 10 minutes.
    """
    from db.schema import SessionLocal, OddsSnapshot

    def _implied(odds: int) -> float:
        if odds < 0:
            return (-odds) / (-odds + 100)
        return 100 / (odds + 100)

    snapshot = OddsSnapshot(
        match_id=match_id,
        p1_odds=p1_odds,
        p2_odds=p2_odds,
        p1_implied=round(_implied(p1_odds), 4),
        p2_implied=round(_implied(p2_odds), 4),
        book="DraftKings",
        snapshot_time=datetime.utcnow(),
    )
    with SessionLocal() as s:
        s.add(snapshot)
        s.commit()


def refresh_all_odds() -> int:
    """
    Fetch latest odds and upsert snapshots for all upcoming matches.
    Returns number of snapshots written.
    Used by the APScheduler 10-minute job.
    """
    from db.schema import SessionLocal, Match, Player
    from db.queries import get_upcoming_matches

    upcoming = get_upcoming_matches(days=7)
    if upcoming.empty:
        return 0

    api_odds = fetch_darts_odds()
    if not api_odds:
        return 0

    # Match API events to DB matches by player name
    written = 0
    with SessionLocal() as s:
        for row in upcoming.itertuples():
            match_odds = next(
                (
                    o for o in api_odds
                    if (
                        o["player1"].lower() in row.player1.lower()
                        or row.player1.lower() in o["player1"].lower()
                    )
                ),
                None,
            )
            if match_odds:
                upsert_odds_snapshot(
                    row.match_id,
                    match_odds["p1_odds"],
                    match_odds["p2_odds"],
                )
                written += 1

    return written


if __name__ == "__main__":
    print("Testing odds fetch...")
    odds = fetch_darts_odds()
    for o in odds:
        print(f"  {o['player1']} ({o['p1_odds']}) vs {o['player2']} ({o['p2_odds']})")
