"""
Export daily best bets for the Sports Picks Grid aggregator.

Queries the BullzIQ SQLite database for upcoming darts matches, estimates
win probability from Elo ratings, compares against the latest DraftKings
odds snapshot, and writes data_files/best_bets_today.json.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# Allow imports from repo root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    from sqlalchemy import desc
    from db.schema import Match, Player, OddsSnapshot, SessionLocal
    DB_AVAILABLE = True
except Exception as e:
    print(f"[darts export] DB import error: {e}")
    DB_AVAILABLE = False

OUT_PATH = ROOT / "data_files" / "best_bets_today.json"
LOOKAHEAD_DAYS = 7
MIN_EDGE = 0.03


def _american_to_prob(odds: int | None) -> float | None:
    if odds is None:
        return None
    if odds > 0:
        return 100.0 / (odds + 100.0)
    else:
        return abs(odds) / (abs(odds) + 100.0)


def _elo_win_prob(elo_a: float, elo_b: float) -> float:
    """Standard Elo expected score for player 1."""
    return 1.0 / (1.0 + 10.0 ** ((elo_b - elo_a) / 400.0))


def _tier(edge: float) -> str:
    if edge >= 0.06:
        return "Elite"
    elif edge >= 0.03:
        return "Strong"
    elif edge >= 0.01:
        return "Good"
    return "Standard"


def get_bets(session) -> list[dict]:
    today = date.today()
    cutoff = today + timedelta(days=LOOKAHEAD_DAYS)
    bets: list[dict] = []

    matches = (
        session.query(Match)
        .filter(Match.is_upcoming == True)
        .filter(Match.match_date >= datetime.combine(today, datetime.min.time()))
        .filter(Match.match_date <= datetime.combine(cutoff, datetime.max.time()))
        .all()
    )

    for match in matches:
        p1: Player | None = session.get(Player, match.player1_id)
        p2: Player | None = session.get(Player, match.player2_id)
        if not p1 or not p2:
            continue

        elo1 = p1.elo or 1500.0
        elo2 = p2.elo or 1500.0
        model_prob_p1 = _elo_win_prob(elo1, elo2)
        model_prob_p2 = 1.0 - model_prob_p1

        # Latest odds snapshot
        snap = (
            session.query(OddsSnapshot)
            .filter(OddsSnapshot.match_id == match.id)
            .order_by(desc(OddsSnapshot.snapshot_time))
            .first()
        )

        if snap:
            implied_p1 = snap.p1_implied or _american_to_prob(snap.p1_odds)
            implied_p2 = snap.p2_implied or _american_to_prob(snap.p2_odds)
        else:
            implied_p1 = implied_p2 = None

        edge_p1 = (model_prob_p1 - implied_p1) if implied_p1 is not None else 0.0
        edge_p2 = (model_prob_p2 - implied_p2) if implied_p2 is not None else 0.0

        # Pick best edge
        if edge_p1 >= edge_p2 and edge_p1 >= MIN_EDGE:
            pick_name = p1.name
            confidence = round(model_prob_p1, 4)
            edge = round(edge_p1, 4)
            odds = snap.p1_odds if snap else None
        elif edge_p2 >= MIN_EDGE:
            pick_name = p2.name
            confidence = round(model_prob_p2, 4)
            edge = round(edge_p2, 4)
            odds = snap.p2_odds if snap else None
        else:
            continue

        match_date_str = match.match_date.strftime("%Y-%m-%d") if match.match_date else today.isoformat()
        game_str = f"{p1.name} vs {p2.name}"

        # Tournament name via relationship (may be None)
        tournament_name = ""
        if match.tournament_id:
            try:
                from db.schema import Tournament
                t = session.get(Tournament, match.tournament_id)
                tournament_name = t.name if t else ""
            except Exception:
                pass

        bets.append({
            "game_date":  match_date_str,
            "game":       game_str,
            "game_time":  match.match_date.strftime("%H:%M") if match.match_date else "",
            "bet_type":   "moneyline",
            "pick":       pick_name,
            "confidence": confidence,
            "edge":       edge,
            "odds":       odds,
            "tier":       _tier(edge),
            "notes":      tournament_name,
        })

    return bets


def main() -> None:
    if not DB_AVAILABLE:
        print("[darts export] DB not available — writing empty output")
        bets: list[dict] = []
    else:
        with SessionLocal() as session:
            bets = get_bets(session)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": {
            "sport":         "Darts",
            "generated_at":  datetime.now(timezone.utc).isoformat(),
            "model_version": "1.0.0",
            "season":        str(datetime.now(timezone.utc).year),
        },
        "bets": bets,
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"[darts export] Wrote {len(bets)} bets → {OUT_PATH}")


if __name__ == "__main__":
    main()
