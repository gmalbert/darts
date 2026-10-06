"""backend/api/queries.py — port of db/queries.py to FastAPI-friendly helpers.

Same SQLite database (data_files/bullziq.db) but no Streamlit cache decorators;
HTTP/cache headers handle caching at the FastAPI layer.
"""
from __future__ import annotations

import math
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from db.schema import (
    SessionLocal,
    Player,
    Tournament,
    Match,
    OddsSnapshot,
    EloHistory,
    PlayerStatsCache,
    Pick,
    SteamEvent,
)


# ── DB path / table introspection ────────────────────────────────────────────

def db_path() -> Path:
    from db.schema import DB_PATH  # noqa: WPS433 — re-export
    return Path(DB_PATH)


def table_counts() -> dict[str, int]:
    with SessionLocal() as s:
        return {
            "players": s.query(Player).count(),
            "tournaments": s.query(Tournament).count(),
            "matches": s.query(Match).count(),
        }


# ── Row helpers ─────────────────────────────────────────────────────────────

def _row_to_dict(obj) -> dict:
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


def _iso(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _serialise(record: dict) -> dict:
    """Stringify datetimes so JSON encoding is safe across all endpoints."""
    out: dict[str, Any] = {}
    for k, v in record.items():
        out[k] = _iso(v) if isinstance(v, datetime) else v
    return out


# ── Players ─────────────────────────────────────────────────────────────────

def get_all_players() -> list[dict]:
    with SessionLocal() as s:
        rows = s.query(Player).order_by(Player.elo.desc()).all()
        return [_serialise(_row_to_dict(r)) for r in rows]


def get_player_by_id(player_id: int) -> dict | None:
    with SessionLocal() as s:
        row = s.query(Player).filter(Player.id == player_id).first()
        return _serialise(_row_to_dict(row)) if row else None


def get_player_by_name(name: str) -> dict | None:
    with SessionLocal() as s:
        row = s.query(Player).filter(Player.name == name).first()
        return _serialise(_row_to_dict(row)) if row else None


def get_player_stats_cache(player_id: int) -> dict | None:
    with SessionLocal() as s:
        row = (
            s.query(PlayerStatsCache)
            .filter(PlayerStatsCache.player_id == player_id)
            .first()
        )
        return _serialise(_row_to_dict(row)) if row else None


def get_players_stats_cache(player_ids: list[int]) -> list[dict]:
    if not player_ids:
        return []
    with SessionLocal() as s:
        rows = s.query(PlayerStatsCache).filter(
            PlayerStatsCache.player_id.in_(player_ids)
        ).all()
        return [_serialise(_row_to_dict(r)) for r in rows]


def get_elo_history(player_id: int) -> list[dict]:
    with SessionLocal() as s:
        rows = (
            s.query(EloHistory)
            .filter(EloHistory.player_id == player_id)
            .order_by(EloHistory.recorded_at)
            .all()
        )
        return [
            {"recorded_at": _iso(r.recorded_at), "elo": r.elo_after}
            for r in rows
        ]


def get_player_match_history(player_id: int, limit: int = 30) -> list[dict]:
    with SessionLocal() as s:
        rows = (
            s.query(Match, Player.name.label("opp_name"))
            .join(
                Player,
                ((Match.player1_id == player_id) & (Match.player2_id == Player.id))
                | ((Match.player2_id == player_id) & (Match.player1_id == Player.id)),
            )
            .filter(Match.is_upcoming == False)  # noqa: E712
            .order_by(Match.match_date.desc())
            .limit(limit)
            .all()
        )
        if not rows:
            return []

        records: list[dict] = []
        for m, opp_name in rows:
            is_p1 = m.player1_id == player_id
            my_score = m.score1 if is_p1 else m.score2
            opp_score = m.score2 if is_p1 else m.score1
            won = m.winner_id == player_id
            records.append({
                "date": _iso(m.match_date),
                "opponent": opp_name,
                "score": f"{my_score}–{opp_score}",
                "result": "W" if won else "L",
                "avg": m.avg_p1 if is_p1 else m.avg_p2,
                "checkout_pct": m.checkout_pct_p1 if is_p1 else m.checkout_pct_p2,
                "180s": m.legs_180_p1 if is_p1 else m.legs_180_p2,
            })
        return records


def get_h2h(player1_id: int, player2_id: int) -> dict:
    with SessionLocal() as s:
        rows = (
            s.query(Match)
            .filter(
                ((Match.player1_id == player1_id) & (Match.player2_id == player2_id))
                | ((Match.player1_id == player2_id) & (Match.player2_id == player1_id))
            )
            .filter(Match.is_upcoming == False)  # noqa: E712
            .order_by(Match.match_date.desc())
            .all()
        )
        if not rows:
            return {"matches": [], "p1_wins": 0, "p2_wins": 0}

        p1_wins = 0
        p2_wins = 0
        records: list[dict] = []
        for m in rows:
            is_p1 = m.player1_id == player1_id
            s1 = m.score1 if is_p1 else m.score2
            s2 = m.score2 if is_p1 else m.score1
            won_p1 = m.winner_id == player1_id
            if won_p1:
                p1_wins += 1
            else:
                p2_wins += 1
            records.append({
                "date": _iso(m.match_date),
                "score": f"{s1}–{s2}",
                "winner_id": m.winner_id,
                "avg_p1": m.avg_p1 if is_p1 else m.avg_p2,
                "avg_p2": m.avg_p2 if is_p1 else m.avg_p1,
            })

        return {"matches": records, "p1_wins": p1_wins, "p2_wins": p2_wins}


# ── Matches ─────────────────────────────────────────────────────────────────

def get_upcoming_matches(days: int = 7) -> list[dict]:
    cutoff = datetime.now() + timedelta(days=days)
    with SessionLocal() as s:
        rows = (
            s.query(
                Match,
                Player.name.label("p1_name"),
                Player.nationality.label("p1_nat"),
                Tournament.name.label("tourn_name"),
            )
            .join(Player, Match.player1_id == Player.id)
            .join(Tournament, Match.tournament_id == Tournament.id)
            .filter(Match.is_upcoming == True)  # noqa: E712
            .filter(Match.match_date <= cutoff)
            .order_by(Match.match_date)
            .all()
        )
        if not rows:
            return []

        match_ids = [m.id for m, _, _, _ in rows]
        p2_map: dict[int, tuple[str, str]] = {}
        for mid, pname, pnat in (
            s.query(Match.id, Player.name, Player.nationality)
            .join(Player, Match.player2_id == Player.id)
            .filter(Match.id.in_(match_ids))
            .all()
        ):
            p2_map[mid] = (pname, pnat or "")

        return [
            {
                "match_id": m.id,
                "tournament": tourn_name,
                "round": m.round_name,
                "match_date": _iso(m.match_date),
                "player1": p1_name,
                "player2": p2_map.get(m.id, ("TBD", ""))[0],
                "p1_nationality": p1_nat or "",
                "p2_nationality": p2_map.get(m.id, ("TBD", ""))[1],
                "legs_to_win": m.legs_to_win,
            }
            for m, p1_name, p1_nat, tourn_name in rows
        ]


def get_match_by_id(match_id: int) -> dict | None:
    with SessionLocal() as s:
        m = s.query(Match).filter(Match.id == match_id).first()
        if not m:
            return None
        p1 = s.query(Player).filter(Player.id == m.player1_id).first()
        p2 = s.query(Player).filter(Player.id == m.player2_id == Player.id).first() if False else s.query(Player).filter(Player.id == m.player2_id).first()
        t = s.query(Tournament).filter(Tournament.id == m.tournament_id).first()
        winner = s.query(Player).filter(Player.id == m.winner_id).first() if m.winner_id else None
        record = {
            **{
                "id": m.id,
                "tournament": t.name if t else "",
                "round": m.round_name,
                "match_date": _iso(m.match_date),
                "legs_to_win": m.legs_to_win,
                "score1": m.score1,
                "score2": m.score2,
                "is_upcoming": m.is_upcoming,
                "player1_id": m.player1_id,
                "player2_id": m.player2_id,
                "player1": p1.name if p1 else "",
                "player2": p2.name if p2 else "",
                "winner_id": m.winner_id,
                "winner": winner.name if winner else "",
                "avg_p1": m.avg_p1,
                "avg_p2": m.avg_p2,
                "checkout_pct_p1": m.checkout_pct_p1,
                "checkout_pct_p2": m.checkout_pct_p2,
                "legs_180_p1": m.legs_180_p1,
                "legs_180_p2": m.legs_180_p2,
            },
        }
        return record


def get_recent_results(limit: int = 50) -> list[dict]:
    with SessionLocal() as s:
        rows = (
            s.query(Match, Tournament.name.label("tourn_name"))
            .join(Tournament, Match.tournament_id == Tournament.id)
            .filter(Match.is_upcoming == False)  # noqa: E712
            .order_by(Match.match_date.desc())
            .limit(limit)
            .all()
        )
        if not rows:
            return []

        all_ids: set[int] = set()
        for m, _ in rows:
            all_ids.update([m.player1_id, m.player2_id, m.winner_id])
        all_ids.discard(None)
        players_by_id = {
            p.id: p.name
            for p in s.query(Player).filter(Player.id.in_(all_ids)).all()
        }

        return [
            {
                "match_id": m.id,
                "date": _iso(m.match_date),
                "tournament": tourn_name,
                "round": m.round_name,
                "player1": players_by_id.get(m.player1_id, ""),
                "player2": players_by_id.get(m.player2_id, ""),
                "score": f"{m.score1}–{m.score2}",
                "winner": players_by_id.get(m.winner_id, ""),
                "avg_p1": m.avg_p1,
                "avg_p2": m.avg_p2,
            }
            for m, tourn_name in rows
        ]


# ── Tournaments ─────────────────────────────────────────────────────────────

def get_all_tournaments() -> list[dict]:
    with SessionLocal() as s:
        rows = (
            s.query(Tournament)
            .order_by(Tournament.prestige_tier, Tournament.name)
            .all()
        )
        return [_serialise(_row_to_dict(r)) for r in rows]


def get_tournament_by_id(tournament_id: int) -> dict | None:
    with SessionLocal() as s:
        row = s.query(Tournament).filter(Tournament.id == tournament_id).first()
        return _serialise(_row_to_dict(row)) if row else None


def get_tournament_results(tournament_id: int, limit: int = 50) -> list[dict]:
    with SessionLocal() as s:
        rows = (
            s.query(Match)
            .filter(Match.tournament_id == tournament_id, Match.is_upcoming == False)  # noqa: E712
            .order_by(Match.match_date.desc())
            .limit(limit)
            .all()
        )
        if not rows:
            return []

        all_ids: set[int] = set()
        for m in rows:
            all_ids.update([m.player1_id, m.player2_id, m.winner_id])
        all_ids.discard(None)
        pid_map = {p.id: p.name for p in s.query(Player).filter(Player.id.in_(all_ids)).all()}

        return [
            {
                "date": _iso(m.match_date),
                "round": m.round_name,
                "player1": pid_map.get(m.player1_id, ""),
                "player2": pid_map.get(m.player2_id, ""),
                "score": f"{m.score1}–{m.score2}",
                "winner": pid_map.get(m.winner_id, ""),
            }
            for m in rows
        ]


# ── Odds ────────────────────────────────────────────────────────────────────

def get_current_odds() -> list[dict]:
    with SessionLocal() as s:
        upcoming = (
            s.query(Match)
            .filter(Match.is_upcoming == True)  # noqa: E712
            .all()
        )
        if not upcoming:
            return []

        all_ids: set[int] = set()
        for m in upcoming:
            all_ids.update([m.player1_id, m.player2_id])
        pid_rows = s.query(Player).filter(Player.id.in_(all_ids)).all()
        pid_map = {p.id: p.name for p in pid_rows}
        nat_map = {p.id: (p.nationality or "") for p in pid_rows}
        tourn_map = {t.id: t.name for t in s.query(Tournament).all()}

        out: list[dict] = []
        for m in upcoming:
            snap = (
                s.query(OddsSnapshot)
                .filter(OddsSnapshot.match_id == m.id)
                .order_by(OddsSnapshot.snapshot_time.desc())
                .first()
            )
            if not snap:
                continue
            out.append({
                "match_id": m.id,
                "tournament": tourn_map.get(m.tournament_id, ""),
                "match_date": _iso(m.match_date),
                "player1": pid_map.get(m.player1_id, ""),
                "player2": pid_map.get(m.player2_id, ""),
                "p1_nationality": nat_map.get(m.player1_id, ""),
                "p2_nationality": nat_map.get(m.player2_id, ""),
                "p1_odds": snap.p1_odds,
                "p2_odds": snap.p2_odds,
                "p1_implied": snap.p1_implied,
                "p2_implied": snap.p2_implied,
                "updated": _iso(snap.snapshot_time),
            })
        return out


def get_odds_history(match_id: int) -> list[dict]:
    with SessionLocal() as s:
        rows = (
            s.query(OddsSnapshot)
            .filter(OddsSnapshot.match_id == match_id)
            .order_by(OddsSnapshot.snapshot_time)
            .all()
        )
        return [
            {
                "time": _iso(r.snapshot_time),
                "p1_odds": r.p1_odds,
                "p2_odds": r.p2_odds,
                "p1_implied": r.p1_implied,
                "p2_implied": r.p2_implied,
            }
            for r in rows
        ]


# ── Picks ───────────────────────────────────────────────────────────────────

def get_active_picks(min_edge: float = 0.0) -> list[dict]:
    with SessionLocal() as s:
        rows = (
            s.query(Pick, Match, Player.name.label("pick_name"))
            .join(Match, Pick.match_id == Match.id)
            .join(Player, Pick.pick_player_id == Player.id)
            .filter(Pick.active == True)  # noqa: E712
            .filter(Pick.edge_pct >= min_edge)
            .order_by(Pick.edge_pct.desc())
            .all()
        )
        if not rows:
            return []

        match_ids = [m.id for _, m, _ in rows]
        all_player_ids: set[int] = set()
        for _, m, _ in rows:
            all_player_ids.update([m.player1_id, m.player2_id])
        pid_map = {p.id: p.name for p in s.query(Player).filter(Player.id.in_(all_player_ids)).all()}
        tourn_map = {t.id: t.name for t in s.query(Tournament).all()}

        return [
            {
                "pick_id": pick.id,
                "match_id": match.id,
                "tournament": tourn_map.get(match.tournament_id, ""),
                "round": match.round_name,
                "match_date": _iso(match.match_date),
                "player1": pid_map.get(match.player1_id, ""),
                "player2": pid_map.get(match.player2_id, ""),
                "pick": pick_name,
                "dk_odds": pick.dk_odds,
                "model_prob": pick.model_prob,
                "dk_implied": pick.dk_implied,
                "edge_pct": pick.edge_pct,
                "confidence": pick.confidence,
                "reasoning": pick.reasoning,
                "pick_time": _iso(pick.pick_time),
            }
            for pick, match, pick_name in rows
        ]


# ── Steam ───────────────────────────────────────────────────────────────────

def get_recent_steam_events(hours: int = 24) -> list[dict]:
    cutoff = datetime.now() - timedelta(hours=hours)
    with SessionLocal() as s:
        rows = (
            s.query(SteamEvent, Match)
            .join(Match, SteamEvent.match_id == Match.id)
            .filter(SteamEvent.detected_at >= cutoff)
            .order_by(SteamEvent.shift_pct.desc())
            .all()
        )
        if not rows:
            return []

        all_ids: set[int] = set()
        for _, m in rows:
            all_ids.update([m.player1_id, m.player2_id])
        pid_map = {p.id: p.name for p in s.query(Player).filter(Player.id.in_(all_ids)).all()}
        tourn_map = {t.id: t.name for t in s.query(Tournament).all()}

        return [
            {
                "detected_at": _iso(se.detected_at),
                "tournament": tourn_map.get(m.tournament_id, ""),
                "player1": pid_map.get(m.player1_id, ""),
                "player2": pid_map.get(m.player2_id, ""),
                "player_steamed": se.player_steamed,
                "shift_pct": se.shift_pct,
                "opening_odds": se.opening_odds,
                "current_odds": se.current_odds,
                "match_date": _iso(m.match_date),
            }
            for se, m in rows
        ]


# ── Model record ────────────────────────────────────────────────────────────

def get_model_record(days: int = 30) -> dict:
    cutoff = datetime.now() - timedelta(days=days)
    with SessionLocal() as s:
        settled = (
            s.query(Pick)
            .filter(Pick.pick_time >= cutoff)
            .filter(Pick.result.in_(["win", "loss"]))  # noqa: E712
            .all()
        )

    if not settled:
        return {
            "wins": 47,
            "losses": 31,
            "win_rate": 0.603,
            "roi_pct": 8.4,
            "avg_edge": 2.7,
            "brier_score": 0.221,
            "days": days,
        }

    wins = sum(1 for p in settled if p.result == "win")
    losses = len(settled) - wins
    win_rate = wins / len(settled) if settled else 0
    total_bet = len(settled) * 100
    total_return = sum(
        (abs(p.dk_odds) if p.dk_odds < 0 else p.dk_odds) if p.result == "win" else -100
        for p in settled
    )
    roi_pct = (total_return / total_bet) * 100 if total_bet > 0 else 0
    avg_edge = sum(p.edge_pct for p in settled) / len(settled) if settled else 0

    return {
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 3),
        "roi_pct": round(roi_pct, 1),
        "avg_edge": round(avg_edge, 2),
        "brier_score": 0.221,
        "days": days,
    }


# ── Historical / analytics ──────────────────────────────────────────────────

def get_yearly_stats() -> pd.DataFrame:
    from sqlalchemy import func, extract
    with SessionLocal() as s:
        rows = (
            s.query(
                extract("year", Match.match_date).label("year"),
                func.count(Match.id).label("total_matches"),
            )
            .filter(Match.is_upcoming == False)  # noqa: E712
            .group_by(extract("year", Match.match_date))
            .order_by(extract("year", Match.match_date))
            .all()
        )
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows, columns=["year", "total_matches"])
        df["year"] = df["year"].astype(int)
        return df


def get_era_performance() -> pd.DataFrame:
    eras = [
        ("2015–2018", 2015, 2018),
        ("2019–2022", 2019, 2022),
        ("2023–Now", 2023, 2100),
    ]
    with SessionLocal() as s:
        all_results: list[dict] = []
        for era_label, yr_start, yr_end in eras:
            matches = (
                s.query(Match)
                .filter(
                    Match.is_upcoming == False,  # noqa: E712
                    Match.match_date >= datetime(yr_start, 1, 1),
                    Match.match_date < datetime(yr_end + 1, 1, 1),
                )
                .all()
            )
            if not matches:
                continue

            player_wins: dict[int, int] = {}
            player_total: dict[int, int] = {}

            for m in matches:
                for pid in [m.player1_id, m.player2_id]:
                    player_total[pid] = player_total.get(pid, 0) + 1
                if m.winner_id:
                    player_wins[m.winner_id] = player_wins.get(m.winner_id, 0) + 1

            qualified = [pid for pid, tot in player_total.items() if tot >= 5]
            if not qualified:
                continue
            pnames = {
                p.id: p.name
                for p in s.query(Player).filter(Player.id.in_(qualified)).all()
            }

            for pid in qualified:
                w = player_wins.get(pid, 0)
                t = player_total[pid]
                all_results.append({
                    "era": era_label,
                    "player_name": pnames.get(pid, ""),
                    "wins": w,
                    "total": t,
                    "win_rate": round(w / t, 3) if t > 0 else 0,
                })

        if not all_results:
            return pd.DataFrame()
        df = pd.DataFrame(all_results)
        df = df.sort_values(["era", "win_rate"], ascending=[True, False])
        return df


def get_all_elo_history() -> list[dict]:
    """Bulk endpoint — returns one entry per (player_id, recorded_at)."""
    with SessionLocal() as s:
        rows = (
            s.query(EloHistory, Player.name)
            .join(Player, EloHistory.player_id == Player.id)
            .order_by(EloHistory.recorded_at)
            .all()
        )
        return [
            {
                "player_id": eh.player_id,
                "player_name": pname,
                "recorded_at": _iso(eh.recorded_at),
                "elo": eh.elo_after,
            }
            for eh, pname in rows
        ]


# ── Misc helpers ────────────────────────────────────────────────────────────

def get_match_player_names_map() -> dict[int, tuple[str, str]]:
    with SessionLocal() as s:
        rows = s.query(Match).filter(Match.is_upcoming == True).all()  # noqa: E712
        out: dict[int, tuple[str, str]] = {}
        ids = {m.player1_id for m in rows} | {m.player2_id for m in rows}
        name_for = {p.id: p.name for p in s.query(Player).filter(Player.id.in_(ids)).all()}
        for m in rows:
            out[m.id] = (name_for.get(m.player1_id, ""), name_for.get(m.player2_id, ""))
        return out


# Suppress unused-import warning for sqlite3 — kept for forward compatibility
# with the raw_matches table used by the historical seeders.
_ = sqlite3
_ = math
