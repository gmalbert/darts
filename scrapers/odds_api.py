"""
scrapers/odds_api.py — odds-api.io integration for DraftKings/Bet365 darts lines.

Docs: https://docs.odds-api.io/
Base URL: https://api.odds-api.io/v3
Sport slug: darts
Free tier: 100 req/hour, bookmakers selected in the account (DraftKings + Bet365).

Usage:
    from scrapers.odds_api import fetch_darts_odds, upsert_odds_snapshot

Set ODDS_API_IO_KEY in your .env file.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

ODDS_API_IO_KEY = os.getenv("ODDS_API_IO_KEY", "")
BASE_URL = "https://api.odds-api.io/v3"
SPORT = "darts"

# Bookmakers selected for this account.
# The ML market returns decimal odds; we convert to American integers.
BOOKMAKERS = ["DraftKings", "Bet365"]
ODDS_BATCH_SIZE = 10  # odds-api.io /odds/multi limit
REQUEST_BUDGET_PER_HOUR = int(os.getenv("ODDS_API_IO_REQUEST_BUDGET", "20"))
# Bet365 is the selected book with current darts coverage; keep this override
# configurable if the account’s selected books change again.
EVENT_BOOKMAKER_FILTER = os.getenv("ODDS_API_IO_EVENT_BOOKMAKER", BOOKMAKERS[1])
_request_times: list[float] = []

# Placeholder names used by odds-api.io before draw brackets are set.
_PLACEHOLDER_PREFIXES = (
    "winner of", "last 64", "last 32", "last 16",
    "quarter-final", "semi-final", "sf player", "qf player",
    "winner sf", "winner qf", "tbd", "player ",
)

# How long to reuse the paginated events list before re-fetching (seconds).
EVENT_CACHE_TTL_SEC = 1800  # 30 minutes

# Module-level event cache.
_events_cache: list[dict] = []
_events_cache_ts: float = 0.0


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _is_real_player(name: str) -> bool:
    """Return False for bracket-placeholder names that aren't real players yet."""
    n = name.strip().lower()
    return not any(n.startswith(p) for p in _PLACEHOLDER_PREFIXES)


def _decimal_to_american(decimal_odds: float) -> int:
    """Convert decimal odds (e.g. 1.91) to American moneyline integer."""
    if decimal_odds >= 2.0:
        return round((decimal_odds - 1) * 100)
    return round(-100.0 / (decimal_odds - 1))


def _decimal_to_implied(decimal_odds: float) -> float:
    """Decimal odds → implied probability [0, 1]."""
    if decimal_odds <= 0:
        return 0.0
    return round(1.0 / decimal_odds, 4)


def _get(path: str, params: dict) -> requests.Response | None:
    """GET helper; returns None on network error."""
    now = time.monotonic()
    _request_times[:] = [t for t in _request_times if now - t < 3600]
    if len(_request_times) >= REQUEST_BUDGET_PER_HOUR:
        print(
            f"odds-api.io request budget reached ({REQUEST_BUDGET_PER_HOUR}/hour); "
            f"skipping /{path}."
        )
        return None

    params = {"apiKey": ODDS_API_IO_KEY, **params}
    try:
        _request_times.append(now)
        resp = requests.get(f"{BASE_URL}/{path}", params=params, timeout=15)
        return resp
    except requests.RequestException as exc:
        print(f"odds-api.io request failed ({path}): {exc}")
        return None


def _fetch_all_darts_events() -> list[dict]:
    """
    Paginate /events for all pending/live darts events.
    Results are cached for EVENT_CACHE_TTL_SEC (30 min) to conserve the
    100 req/hr budget — callers receive the cached list at zero API cost.
    """
    global _events_cache, _events_cache_ts
    now = time.monotonic()
    if _events_cache and (now - _events_cache_ts) < EVENT_CACHE_TTL_SEC:
        return _events_cache

    events: list[dict] = []
    skip = 0
    limit = 50
    while True:
        event_params = {
            "sport": SPORT,
            "status": "pending,live",
            "limit": limit,
            "skip": skip,
        }
        # Ask the API to return only events that have odds at the target book.
        # This avoids fetching every darts event when DraftKings has no market.
        if EVENT_BOOKMAKER_FILTER:
            event_params["bookmaker"] = EVENT_BOOKMAKER_FILTER
        resp = _get("events", event_params)
        if resp is None:
            print("odds-api.io events request failed before receiving a response.")
            break
        if resp.status_code != 200:
            print(
                f"odds-api.io events request returned HTTP {resp.status_code}: "
                f"{resp.text[:240]}"
            )
            break
        page = resp.json()
        if not isinstance(page, list) or not page:
            break
        events.extend(page)
        if len(page) < limit:
            break
        skip += limit

    if events:
        _events_cache = events
        _events_cache_ts = now
    return events


def fetch_darts_events() -> list[dict]:
    """
    Return all pending/live darts events from odds-api.io with resolved player names.
    Each dict has: event_id, player1, player2, commence_time, league_name.
    Does NOT fetch odds (costs 1 req/event); use fetch_darts_odds() for that.
    """
    if not ODDS_API_IO_KEY:
        return []
    events = _fetch_all_darts_events()
    return [
        {
            "event_id": str(e["id"]),
            "player1": e.get("home", ""),
            "player2": e.get("away", ""),
            "commence_time": e.get("date", ""),
            "league_name": e.get("league", {}).get("name", ""),
        }
        for e in events
        if _is_real_player(e.get("home", "")) and _is_real_player(e.get("away", ""))
    ]


def fetch_darts_odds(
    events: list[dict] | None = None,
    days_ahead: int = 3,
) -> list[dict]:
    """
    Fetch current darts odds from odds-api.io.
    Returns a list of match dicts with p1/p2 names and American moneyline odds.
    Only events that have at least one bookmaker ML market are included.

    Args:
        events: Pre-fetched event list from _fetch_all_darts_events() or
                fetch_darts_events().  Pass this to avoid a redundant pagination
                call when the caller already has the list.  If None, fetches fresh.
        days_ahead: Only request odds for events starting within this many days.
                    Keeps per-run request count low (1 call per qualifying event).
                    Default 3 days for seeding; use 1 for the 10-min scheduler job.
    """
    if not ODDS_API_IO_KEY:
        print("ODDS_API_IO_KEY not set. Skipping odds fetch.")
        return []

    if events is None:
        events = _fetch_all_darts_events()
    if not events:
        print("odds-api.io: no darts events found.")
        return []

    cutoff = datetime.now(timezone.utc) + timedelta(days=days_ahead)

    # Filter to resolved-name events within the time window
    candidate_events = []
    for e in events:
        if not (_is_real_player(e.get("home", "")) and _is_real_player(e.get("away", ""))):
            continue
        try:
            start = datetime.fromisoformat(e["date"].replace("Z", "+00:00"))
        except (KeyError, ValueError):
            continue
        if start <= cutoff:
            candidate_events.append(e)

    print(f"odds-api.io: {len(events)} darts events total, "
          f"{len(candidate_events)} within {days_ahead}d with resolved names.")

    results: list[dict] = []
    requests_used = 0
    status_counts: dict[str, int] = {}
    empty_bookmakers = 0
    missing_ml = 0

    # Batch requests reduce a 50-event refresh from 50 calls to at most 5,
    # which matters on free/rate-limited accounts.
    for offset in range(0, len(candidate_events), ODDS_BATCH_SIZE):
        batch = candidate_events[offset:offset + ODDS_BATCH_SIZE]
        event_ids = ",".join(str(event["id"]) for event in batch)
        resp = _get("odds/multi", {
            "eventIds": event_ids,
            "bookmakers": ",".join(BOOKMAKERS),
        })
        requests_used += 1
        if resp is None:
            status_counts["network_error"] = status_counts.get("network_error", 0) + 1
            continue
        if resp.status_code != 200:
            key = str(resp.status_code)
            status_counts[key] = status_counts.get(key, 0) + 1
            continue

        payload = resp.json()
        response_events = payload if isinstance(payload, list) else [payload]
        for data in response_events:
            bookmakers_data = data.get("bookmakers", {})
            if not bookmakers_data:
                empty_bookmakers += 1
                continue

            # Try each preferred bookmaker in order.
            ml_home: float | None = None
            ml_away: float | None = None
            book_used: str = ""
            for bk_name in BOOKMAKERS:
                markets = bookmakers_data.get(bk_name)
                if not markets:
                    continue
                ml_market = next((m for m in markets if m.get("name") == "ML"), None)
                if not ml_market or not ml_market.get("odds"):
                    continue
                o = ml_market["odds"][0]
                try:
                    ml_home = float(o["home"])
                    ml_away = float(o["away"])
                    book_used = bk_name
                    break
                except (KeyError, TypeError, ValueError):
                    continue

            if ml_home is None or ml_away is None:
                missing_ml += 1
                continue

            results.append({
                "event_id": str(data.get("id", "")),
                "player1": data.get("home", ""),
                "player2": data.get("away", ""),
                "commence_time": data.get("date", ""),
                "p1_odds": _decimal_to_american(ml_home),
                "p2_odds": _decimal_to_american(ml_away),
                "p1_implied": _decimal_to_implied(ml_home),
                "p2_implied": _decimal_to_implied(ml_away),
                "book": book_used,
                "fetched_at": _utc_now_iso(),
            })

    diagnostics = ", ".join(f"HTTP {k}: {v}" for k, v in status_counts.items())
    print(f"odds-api.io: {requests_used} odds requests used, "
          f"{len(results)} events with ML odds returned "
          f"(empty bookmakers={empty_bookmakers}, missing ML={missing_ml}"
          f"{', ' + diagnostics if diagnostics else ''}).")
    return results


def upsert_odds_snapshot(
    match_id: int, p1_odds: int, p2_odds: int, book: str = "DraftKings"
) -> None:
    """
    Write a new OddsSnapshot to the database for a given match.
    Called by the APScheduler job every 30 minutes.
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
        book=book,
        snapshot_time=_utc_now_naive(),
    )
    with SessionLocal() as s:
        s.add(snapshot)
        s.commit()


def refresh_all_odds() -> int:
    """
    Fetch latest odds and upsert snapshots for all upcoming matches.
    Returns number of snapshots written.
    Used by the APScheduler 10-minute job.

    Rate budget: fetches events once (cached) + batched odds for events in the
    next 24 hours. Typical cost is 1-2 event calls plus 1-6 batch calls per
    refresh, protected by a 20-request/hour process budget.
    """
    from db.queries import get_upcoming_matches

    upcoming = get_upcoming_matches(days=7)
    if upcoming.empty:
        return 0

    # Fetch events once; pass to fetch_darts_odds to avoid re-pagination.
    # days_ahead=1: only pay for odds on matches starting in the next 24 hours.
    events = _fetch_all_darts_events()
    api_odds = fetch_darts_odds(events=events, days_ahead=1)
    if not api_odds:
        return 0

    # Match API events to DB matches by fuzzy player name
    written = 0
    for row in upcoming.itertuples():
        p1_lower = row.player1.lower()
        p2_lower = row.player2.lower()
        match_odds = next(
            (
                o for o in api_odds
                if (
                    _name_match(o["player1"], p1_lower)
                    or _name_match(o["player1"], p2_lower)
                )
            ),
            None,
        )
        if match_odds:
            upsert_odds_snapshot(
                row.match_id,
                match_odds["p1_odds"],
                match_odds["p2_odds"],
                match_odds.get("book", "DraftKings"),
            )
            written += 1

    return written


def _name_match(api_name: str, db_name_lower: str) -> bool:
    """
    Fuzzy match between odds-api.io name (e.g. "Clayton, Jonny") and
    DB name (e.g. "jonny clayton").  Handles "Surname, First" and
    "First Surname" formats.
    """
    api_lower = api_name.lower()

    # Direct substring match
    if api_lower in db_name_lower or db_name_lower in api_lower:
        return True

    # Handle "Surname, First" → "first surname"
    if "," in api_lower:
        parts = [p.strip() for p in api_lower.split(",", 1)]
        reordered = f"{parts[1]} {parts[0]}"
        if reordered in db_name_lower or db_name_lower in reordered:
            return True

    # Last name only match (fallback)
    last = api_lower.split(",")[0].strip()
    if last and last in db_name_lower:
        return True

    return False


if __name__ == "__main__":
    print("Testing odds-api.io darts fetch...")
    odds = fetch_darts_odds()
    if odds:
        for o in odds:
            print(f"  {o['player1']} ({o['p1_odds']:+d}) vs "
                  f"{o['player2']} ({o['p2_odds']:+d})  [{o['book']}]")
    else:
        print("  No odds returned (markets may not be open yet).")
