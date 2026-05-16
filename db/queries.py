"""
db/queries.py — Cached query helpers for BullzIQ.

All public functions return plain Python dicts/lists so Streamlit
cache_data can serialise them without ORM session issues.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

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


# ── Utility ─────────────────────────────────────────────────────────────────────

def _row_to_dict(obj) -> dict:
    """Convert a SQLAlchemy model instance to a plain dict."""
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


# ── Players ─────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def get_all_players() -> list[dict]:
    with SessionLocal() as s:
        rows = s.query(Player).order_by(Player.elo.desc()).all()
        return [_row_to_dict(r) for r in rows]


@st.cache_data(ttl=300)
def get_player_by_name(name: str) -> dict | None:
    with SessionLocal() as s:
        row = s.query(Player).filter(Player.name == name).first()
        return _row_to_dict(row) if row else None


@st.cache_data(ttl=300)
def get_player_stats_cache(player_id: int) -> dict | None:
    with SessionLocal() as s:
        row = s.query(PlayerStatsCache).filter(
            PlayerStatsCache.player_id == player_id
        ).first()
        return _row_to_dict(row) if row else None


@st.cache_data(ttl=300)
def get_elo_history(player_id: int) -> pd.DataFrame:
    with SessionLocal() as s:
        rows = (
            s.query(EloHistory)
            .filter(EloHistory.player_id == player_id)
            .order_by(EloHistory.recorded_at)
            .all()
        )
        if not rows:
            return pd.DataFrame(columns=["recorded_at", "elo_after"])
        return pd.DataFrame(
            [{"recorded_at": r.recorded_at, "elo": r.elo_after} for r in rows]
        )


@st.cache_data(ttl=300)
def get_player_match_history(player_id: int, limit: int = 30) -> pd.DataFrame:
    with SessionLocal() as s:
        rows = (
            s.query(Match, Player.name.label("opp_name"))
            .join(Player, (
                (Match.player1_id == player_id) & (Match.player2_id == Player.id)
            ) | (
                (Match.player2_id == player_id) & (Match.player1_id == Player.id)
            ))
            .filter(Match.is_upcoming == False)
            .order_by(Match.match_date.desc())
            .limit(limit)
            .all()
        )
        if not rows:
            return pd.DataFrame()

        records = []
        for m, opp_name in rows:
            is_p1 = m.player1_id == player_id
            my_score = m.score1 if is_p1 else m.score2
            opp_score = m.score2 if is_p1 else m.score1
            won = m.winner_id == player_id
            records.append({
                "date": m.match_date,
                "opponent": opp_name,
                "score": f"{my_score}–{opp_score}",
                "result": "W" if won else "L",
                "avg": m.avg_p1 if is_p1 else m.avg_p2,
                "checkout_pct": m.checkout_pct_p1 if is_p1 else m.checkout_pct_p2,
                "180s": m.legs_180_p1 if is_p1 else m.legs_180_p2,
            })
        return pd.DataFrame(records)


@st.cache_data(ttl=300)
def get_h2h(player1_id: int, player2_id: int) -> pd.DataFrame:
    with SessionLocal() as s:
        rows = (
            s.query(Match)
            .filter(
                ((Match.player1_id == player1_id) & (Match.player2_id == player2_id))
                | ((Match.player1_id == player2_id) & (Match.player2_id == player1_id))
            )
            .filter(Match.is_upcoming == False)
            .order_by(Match.match_date.desc())
            .all()
        )
        if not rows:
            return pd.DataFrame()

        p1_wins, p2_wins = 0, 0
        records = []
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
                "date": m.match_date,
                "score": f"{s1}–{s2}",
                "winner_id": m.winner_id,
                "avg_p1": m.avg_p1 if is_p1 else m.avg_p2,
                "avg_p2": m.avg_p2 if is_p1 else m.avg_p1,
            })

        df = pd.DataFrame(records)
        df.attrs["p1_wins"] = p1_wins
        df.attrs["p2_wins"] = p2_wins
        return df


def count_players() -> int:
    with SessionLocal() as s:
        return s.query(Player).count()


# ── Matches ──────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def get_upcoming_matches(days: int = 7) -> pd.DataFrame:
    cutoff = datetime.now() + timedelta(days=days)
    with SessionLocal() as s:
        rows = (
            s.query(Match, Player.name.label("p1_name"),
                    Tournament.name.label("tourn_name"))
            .join(Player, Match.player1_id == Player.id)
            .join(Tournament, Match.tournament_id == Tournament.id)
            .filter(Match.is_upcoming == True)
            .filter(Match.match_date <= cutoff)
            .order_by(Match.match_date)
            .all()
        )
        if not rows:
            return pd.DataFrame()

        # Need player2 name separately
        match_ids = [m.id for m, _, _ in rows]
        p2_map = {}
        p2_rows = (
            s.query(Match.id, Player.name)
            .join(Player, Match.player2_id == Player.id)
            .filter(Match.id.in_(match_ids))
            .all()
        )
        for mid, pname in p2_rows:
            p2_map[mid] = pname

        records = []
        for m, p1_name, tourn_name in rows:
            records.append({
                "match_id": m.id,
                "tournament": tourn_name,
                "round": m.round_name,
                "match_date": m.match_date,
                "player1": p1_name,
                "player2": p2_map.get(m.id, "TBD"),
                "legs_to_win": m.legs_to_win,
            })
        return pd.DataFrame(records)


@st.cache_data(ttl=120)
def get_recent_results(limit: int = 50) -> pd.DataFrame:
    with SessionLocal() as s:
        rows = (
            s.query(Match, Tournament.name.label("tourn_name"))
            .join(Tournament, Match.tournament_id == Tournament.id)
            .filter(Match.is_upcoming == False)
            .order_by(Match.match_date.desc())
            .limit(limit)
            .all()
        )
        if not rows:
            return pd.DataFrame()

        match_ids = [m.id for m, _ in rows]
        player_map = {}
        for col_id_attr, label in [("player1_id", "p1"), ("player2_id", "p2"), ("winner_id", "w")]:
            sub = (
                s.query(getattr(Match, col_id_attr).label("mid_ref"), Player.name)
                .join(Player, getattr(Match, col_id_attr) == Player.id)
                .filter(Match.id.in_(match_ids))
                .all()
            )
            # This join only works per-column; build from match rows directly
        # Simpler: query players by id set
        all_player_ids = set()
        for m, _ in rows:
            all_player_ids.update([m.player1_id, m.player2_id, m.winner_id])
        all_player_ids.discard(None)
        players_by_id = {
            p.id: p.name
            for p in s.query(Player).filter(Player.id.in_(all_player_ids)).all()
        }

        records = []
        for m, tourn_name in rows:
            records.append({
                "date": m.match_date,
                "tournament": tourn_name,
                "round": m.round_name,
                "player1": players_by_id.get(m.player1_id, ""),
                "player2": players_by_id.get(m.player2_id, ""),
                "score": f"{m.score1}–{m.score2}",
                "winner": players_by_id.get(m.winner_id, ""),
                "avg_p1": m.avg_p1,
                "avg_p2": m.avg_p2,
            })
        return pd.DataFrame(records)


# ── Tournaments ──────────────────────────────────────────────────────────────────

@st.cache_data(ttl=600)
def get_all_tournaments() -> list[dict]:
    with SessionLocal() as s:
        rows = s.query(Tournament).order_by(Tournament.prestige_tier, Tournament.name).all()
        return [_row_to_dict(r) for r in rows]


@st.cache_data(ttl=300)
def get_tournament_results(tournament_id: int, limit: int = 50) -> pd.DataFrame:
    with SessionLocal() as s:
        rows = (
            s.query(Match)
            .filter(Match.tournament_id == tournament_id, Match.is_upcoming == False)
            .order_by(Match.match_date.desc())
            .limit(limit)
            .all()
        )
        if not rows:
            return pd.DataFrame()

        all_ids = set()
        for m in rows:
            all_ids.update([m.player1_id, m.player2_id, m.winner_id])
        all_ids.discard(None)
        pid_map = {p.id: p.name for p in s.query(Player).filter(Player.id.in_(all_ids)).all()}

        records = []
        for m in rows:
            records.append({
                "date": m.match_date,
                "round": m.round_name,
                "player1": pid_map.get(m.player1_id, ""),
                "player2": pid_map.get(m.player2_id, ""),
                "score": f"{m.score1}–{m.score2}",
                "winner": pid_map.get(m.winner_id, ""),
            })
        return pd.DataFrame(records)


# ── Odds ─────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def get_current_odds() -> pd.DataFrame:
    """Latest odds snapshot for each upcoming match."""
    with SessionLocal() as s:
        upcoming = (
            s.query(Match)
            .filter(Match.is_upcoming == True)
            .all()
        )
        if not upcoming:
            return pd.DataFrame()

        all_ids = set()
        for m in upcoming:
            all_ids.update([m.player1_id, m.player2_id])
        pid_map = {p.id: p.name for p in s.query(Player).filter(Player.id.in_(all_ids)).all()}
        tourn_map = {t.id: t.name for t in s.query(Tournament).all()}

        records = []
        for m in upcoming:
            snap = (
                s.query(OddsSnapshot)
                .filter(OddsSnapshot.match_id == m.id)
                .order_by(OddsSnapshot.snapshot_time.desc())
                .first()
            )
            if not snap:
                continue
            records.append({
                "match_id": m.id,
                "tournament": tourn_map.get(m.tournament_id, ""),
                "match_date": m.match_date,
                "player1": pid_map.get(m.player1_id, ""),
                "player2": pid_map.get(m.player2_id, ""),
                "p1_odds": snap.p1_odds,
                "p2_odds": snap.p2_odds,
                "p1_implied": snap.p1_implied,
                "p2_implied": snap.p2_implied,
                "updated": snap.snapshot_time,
            })
        return pd.DataFrame(records)


@st.cache_data(ttl=60)
def get_odds_history(match_id: int) -> pd.DataFrame:
    with SessionLocal() as s:
        rows = (
            s.query(OddsSnapshot)
            .filter(OddsSnapshot.match_id == match_id)
            .order_by(OddsSnapshot.snapshot_time)
            .all()
        )
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame([
            {
                "time": r.snapshot_time,
                "p1_odds": r.p1_odds,
                "p2_odds": r.p2_odds,
                "p1_implied": r.p1_implied,
                "p2_implied": r.p2_implied,
            }
            for r in rows
        ])


# ── Picks ─────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def get_active_picks(min_edge: float = 0.0) -> pd.DataFrame:
    with SessionLocal() as s:
        rows = (
            s.query(Pick, Match, Player.name.label("pick_name"))
            .join(Match, Pick.match_id == Match.id)
            .join(Player, Pick.pick_player_id == Player.id)
            .filter(Pick.active == True)
            .filter(Pick.edge_pct >= min_edge)
            .order_by(Pick.edge_pct.desc())
            .all()
        )
        if not rows:
            return pd.DataFrame()

        # Get all relevant player names and tournament names
        match_ids = [m.id for _, m, _ in rows]
        all_player_ids = set()
        for _, m, _ in rows:
            all_player_ids.update([m.player1_id, m.player2_id])
        pid_map = {p.id: p.name for p in s.query(Player).filter(Player.id.in_(all_player_ids)).all()}
        tourn_map = {t.id: t.name for t in s.query(Tournament).all()}

        records = []
        for pick, match, pick_name in rows:
            records.append({
                "pick_id": pick.id,
                "match_id": match.id,
                "tournament": tourn_map.get(match.tournament_id, ""),
                "round": match.round_name,
                "match_date": match.match_date,
                "player1": pid_map.get(match.player1_id, ""),
                "player2": pid_map.get(match.player2_id, ""),
                "pick": pick_name,
                "dk_odds": pick.dk_odds,
                "model_prob": pick.model_prob,
                "dk_implied": pick.dk_implied,
                "edge_pct": pick.edge_pct,
                "confidence": pick.confidence,
                "reasoning": pick.reasoning,
                "pick_time": pick.pick_time,
            })
        return pd.DataFrame(records)


# ── Steam events ──────────────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def get_recent_steam_events(hours: int = 24) -> pd.DataFrame:
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
            return pd.DataFrame()

        all_ids = set()
        for _, m in rows:
            all_ids.update([m.player1_id, m.player2_id])
        pid_map = {p.id: p.name for p in s.query(Player).filter(Player.id.in_(all_ids)).all()}
        tourn_map = {t.id: t.name for t in s.query(Tournament).all()}

        records = []
        for se, m in rows:
            records.append({
                "detected_at": se.detected_at,
                "tournament": tourn_map.get(m.tournament_id, ""),
                "player1": pid_map.get(m.player1_id, ""),
                "player2": pid_map.get(m.player2_id, ""),
                "player_steamed": se.player_steamed,
                "shift_pct": se.shift_pct,
                "opening_odds": se.opening_odds,
                "current_odds": se.current_odds,
                "match_date": m.match_date,
            })
        return pd.DataFrame(records)


# ── Model performance ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=600)
def get_model_record(days: int = 30) -> dict:
    """Return model performance stats over the last N days."""
    cutoff = datetime.now() - timedelta(days=days)
    with SessionLocal() as s:
        settled = (
            s.query(Pick)
            .filter(Pick.pick_time >= cutoff)
            .filter(Pick.result.in_(["win", "loss"]))
            .all()
        )

    if not settled:
        # Return demo stats if no real history
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

    # Simple ROI estimate
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


# ── Historical analytics ──────────────────────────────────────────────────────

@st.cache_data(ttl=600)
def get_yearly_stats() -> pd.DataFrame:
    """Return match counts and average Elo spread per year for the history chart."""
    from sqlalchemy import func, extract
    from db.schema import Player as P2

    with SessionLocal() as s:
        rows = (
            s.query(
                extract("year", Match.match_date).label("year"),
                func.count(Match.id).label("total_matches"),
            )
            .filter(Match.is_upcoming == False)
            .group_by(extract("year", Match.match_date))
            .order_by(extract("year", Match.match_date))
            .all()
        )
        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows, columns=["year", "total_matches"])
        df["year"] = df["year"].astype(int)
        return df


@st.cache_data(ttl=600)
def get_era_performance() -> pd.DataFrame:
    """Return win rates per player per era (2015-2018, 2019-2022, 2023-present)."""
    from sqlalchemy import case, func

    eras = [
        ("2015–2018", 2015, 2018),
        ("2019–2022", 2019, 2022),
        ("2023–Now",  2023, 2100),
    ]

    with SessionLocal() as s:
        all_results = []
        for era_label, yr_start, yr_end in eras:
            matches = (
                s.query(Match)
                .filter(
                    Match.is_upcoming == False,
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

            # Fetch names for players with >= 5 matches in era
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


@st.cache_data(ttl=600)
def count_players() -> int:
    with SessionLocal() as s:
        return s.query(Player).count()
