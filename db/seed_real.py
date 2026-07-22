"""
db/seed_real.py — Real PDC data seeder for BullzIQ.

Pipeline
--------
1. Wipe existing DB tables (clean slate)
2. Scrape the public PDC results feed → raw_matches SQLite table
3. Import raw_matches into ORM (Player, Tournament, Match, EloHistory)
4. Compute Elo ratings chronologically over all historical matches
5. Fetch live DraftKings odds via odds-api.io (if ODDS_API_IO_KEY is set)
6. Write data_files/db_is_real.flag so ensure_seeded() skips demo data

Usage
-----
    # Full rebuild from 2015 (run in CI or once manually):
    python -m db.seed_real

    # Partial refresh — only re-scrape the current year, keep old DB:
    python -m db.seed_real --refresh-only
"""

from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# ── Paths ──────────────────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = _ROOT / "data_files" / "bullziq.db"
FLAG_PATH = _ROOT / "data_files" / "db_is_real.flag"
LOCK_PATH = _ROOT / "data_files" / "db_seed_in_progress.flag"

# ── Project imports (deferred so init_db runs at the right moment) ─────────────
from db.schema import Base, engine, SessionLocal, init_db
from db.schema import Player, Tournament, Match, EloHistory, OddsSnapshot
from models.elo import DartsElo
from scrapers.pdc import seed_database as _scrape_raw, TOURNAMENT_IDS

# Reuse player metadata + tournament metadata from the existing demo seed
from db.seed import PLAYER_DATA, TOURNAMENT_DATA

# ── Lookup tables ──────────────────────────────────────────────────────────────
# PDC feed tournament ID  →  tournament_type key
_TOURN_ID_TO_TYPE: dict[str, str] = {v: k for k, v in TOURNAMENT_IDS.items()}

# tournament_type key  →  TOURNAMENT_DATA entry
_TOURN_TYPE_META: dict[str, dict] = {t["type"]: t for t in TOURNAMENT_DATA}

_LEGS_TO_WIN: dict[str, int] = {
    "world_championship": 7,
    "premier_league": 6,
    "world_matchplay": 10,
    "grand_slam": 8,
    "uk_open": 6,
    "world_grand_prix": 3,
    "players_championship_finals": 8,
    "european_championship": 7,
    "world_series_finals": 7,
}

# Known player metadata indexed by name
_KNOWN_PLAYERS: dict[str, dict] = {p["name"]: p for p in PLAYER_DATA}


# ── Date parsing ───────────────────────────────────────────────────────────────

def _parse_date(raw: str | None, fallback_year: int) -> datetime:
    """Robustly parse a raw date string from the PDC results feed."""
    if not raw or str(raw).strip() in ("None", "", "nan"):
        return datetime(fallback_year, 7, 1)
    s = str(raw).strip()
    for fmt in (
        "%d %b %Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y",
        "%B %d, %Y", "%d %B %Y", "%d.%m.%Y",
    ):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    # Last resort — use the year embedded in the string
    for part in s.split():
        if len(part) == 4 and part.isdigit():
            return datetime(int(part), 7, 1)
    return datetime(fallback_year, 7, 1)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _utc_now_naive() -> datetime:
    # ORM DateTime columns here are stored as naive UTC datetimes.
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ── Main pipeline ──────────────────────────────────────────────────────────────

def run(
    start_year: int = 2015,
    end_year: int | None = None,
    refresh_only: bool = False,
    refresh_odds: bool = False,
) -> None:
    year_range = f"{start_year}–{end_year}" if end_year else f"{start_year}+"
    print(f"\n=== BullzIQ Real Data Seeder  (years={year_range}, refresh_only={refresh_only}) ===\n")

    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOCK_PATH.write_text(f"started={_utc_now_iso()}\n")

    try:
        # ── 1. Clean existing tables ───────────────────────────────────────────
        if refresh_only:
            print("Rebuilding ORM tables from existing raw data + refreshed scrape...")
        else:
            print("Dropping and recreating ORM tables...")

        if not refresh_only:
            Base.metadata.drop_all(engine)
            # Full rebuild starts from a blank raw staging table.
            _conn = sqlite3.connect(str(DB_PATH))
            _conn.execute("DROP TABLE IF EXISTS raw_matches")
            _conn.commit()
            _conn.close()

            init_db()  # (re)create all ORM tables

        # ── 2. Scrape the free public PDC feed ─────────────────────────────────
        scrape_from = datetime.now().year if refresh_only else start_year
        scrape_to = datetime.now().year if refresh_only else end_year
        print(f"Scraping the public PDC results feed from {scrape_from}...")
        _scrape_raw(
            db_path=str(DB_PATH),
            start_year=scrape_from,
            end_year=scrape_to,
            recent_only=refresh_only,
        )

        # Preserve the last good ORM database if an incremental source refresh
        # fails. Rebuild only after the raw scrape has completed successfully.
        if refresh_only:
            Base.metadata.drop_all(engine)
            init_db()

        # ── 3. Load raw matches ───────────────────────────────────────────────
        conn = sqlite3.connect(str(DB_PATH))
        try:
            raw_df = pd.read_sql(
                "SELECT * FROM raw_matches ORDER BY year, COALESCE(match_date, '1970-01-01')",
                conn,
            )
        except Exception as exc:
            print(f"Could not read raw_matches: {exc}")
            return
        finally:
            conn.close()

        if raw_df.empty:
            raise RuntimeError(
                "No raw matches found from the public PDC feed. "
                "Real seeding aborted; demo fallback is disabled."
            )

        print(f"Loaded {len(raw_df)} raw matches from the public PDC feed")

        # ── 4. Build ORM entities ─────────────────────────────────────────────
        with SessionLocal() as s:

            # --- Tournaments (only those covered by the PDC major filter) ---
            tourn_db: dict[str, int] = {}  # tournament_type → DB id
            for t_type, tid in TOURNAMENT_IDS.items():
                meta = _TOURN_TYPE_META.get(t_type)
                if not meta:
                    continue
                t = Tournament(
                    name=meta["name"],
                    tournament_type=t_type,
                    prestige_tier=meta.get("tier", 2),
                    prize_fund=meta.get("prize", 0),
                    format_desc=meta.get("format", ""),
                    typical_month=meta.get("month", ""),
                    dk_covered=True,
                )
                s.add(t)
                s.flush()
                tourn_db[t_type] = t.id

            s.flush()

            # --- Players: gather all unique names in raw data ---
            all_names: set[str] = set()
            for col in ("player1", "player2"):
                all_names |= set(raw_df[col].dropna().str.strip().tolist())
            all_names.discard("")

            player_id_map: dict[str, int] = {}
            for pname in sorted(all_names):
                meta = _KNOWN_PLAYERS.get(pname, {})
                p = Player(
                    name=pname,
                    nationality=meta.get("nat"),
                    nickname=meta.get("nick"),
                    pdc_ranking=meta.get("rank"),
                    elo=float(meta.get("elo", 1500)),
                    avg_3dart=meta.get("avg"),
                    checkout_pct=meta.get("co"),
                    avg_180s_per_leg=meta.get("p180"),
                )
                s.add(p)
                s.flush()
                player_id_map[pname] = p.id

            s.commit()
            print(f"Created {len(player_id_map)} player records.")

            # --- Initialise Elo tracker with 2015 starting points ---
            elo = DartsElo(k=32)
            for pname in player_id_map:
                meta = _KNOWN_PLAYERS.get(pname, {})
                elo.ratings[pname] = float(meta.get("elo", 1500)) * 0.75 + 250

            # --- Import matches + build Elo history in chronological order ---
            match_count = 0
            elo_batch: list[EloHistory] = []

            for _, row in raw_df.iterrows():
                t_type = _TOURN_ID_TO_TYPE.get(str(row["tournament_id"]))
                if not t_type or t_type not in tourn_db:
                    continue

                p1_name = str(row["player1"]).strip() if pd.notna(row["player1"]) else ""
                p2_name = str(row["player2"]).strip() if pd.notna(row["player2"]) else ""
                winner_name = str(row["winner"]).strip() if pd.notna(row.get("winner")) else ""

                if not p1_name or not p2_name:
                    continue
                if p1_name not in player_id_map or p2_name not in player_id_map:
                    continue

                year = int(row["year"]) if pd.notna(row.get("year")) else datetime.now().year
                match_dt = _parse_date(row.get("match_date"), year)

                s1 = int(row["score1"]) if pd.notna(row.get("score1")) else 0
                s2 = int(row["score2"]) if pd.notna(row.get("score2")) else 0

                winner_id = player_id_map.get(winner_name) if winner_name else None

                # Elo update
                legs = _LEGS_TO_WIN.get(t_type, 6)
                elo_before_p1 = elo.get_rating(p1_name)
                elo_before_p2 = elo.get_rating(p2_name)

                if winner_id == player_id_map.get(p1_name) and s1 > s2:
                    new_elo_w, new_elo_l = elo.update(
                        winner=p1_name, loser=p2_name,
                        winner_score=s1, loser_score=s2,
                        legs_to_win=legs, tournament_type=t_type,
                    )
                    elo_after_p1, elo_after_p2 = new_elo_w, new_elo_l
                elif winner_id == player_id_map.get(p2_name) and s2 > s1:
                    new_elo_w, new_elo_l = elo.update(
                        winner=p2_name, loser=p1_name,
                        winner_score=s2, loser_score=s1,
                        legs_to_win=legs, tournament_type=t_type,
                    )
                    elo_after_p1, elo_after_p2 = new_elo_l, new_elo_w
                else:
                    elo_after_p1 = elo.get_rating(p1_name)
                    elo_after_p2 = elo.get_rating(p2_name)

                m = Match(
                    tournament_id=tourn_db[t_type],
                    player1_id=player_id_map[p1_name],
                    player2_id=player_id_map[p2_name],
                    winner_id=winner_id,
                    score1=s1,
                    score2=s2,
                    round_name=str(row.get("round", "Unknown") or "Unknown"),
                    match_date=match_dt,
                    is_upcoming=False,
                )
                s.add(m)
                s.flush()

                elo_batch.append(EloHistory(
                    player_id=player_id_map[p1_name],
                    match_id=m.id,
                    elo_before=elo_before_p1,
                    elo_after=elo_after_p1,
                    recorded_at=match_dt,
                ))
                elo_batch.append(EloHistory(
                    player_id=player_id_map[p2_name],
                    match_id=m.id,
                    elo_before=elo_before_p2,
                    elo_after=elo_after_p2,
                    recorded_at=match_dt,
                ))

                match_count += 1
                if match_count % 200 == 0:
                    s.commit()
                    print(f"  {match_count} matches processed...")

            for eh in elo_batch:
                s.add(eh)

            # Update each player's current Elo to the final computed value
            for pname, pid in player_id_map.items():
                final_elo = elo.ratings.get(pname)
                if final_elo is not None:
                    p_obj = s.get(Player, pid)
                    if p_obj:
                        p_obj.elo = round(final_elo, 1)

            s.commit()
            print(f"Imported {match_count} historical matches.")
            print(f"Wrote {len(elo_batch)} EloHistory records.")

        # ── 5. Live odds via odds-api.io (opt-in) ─────────────────────────────
        # Odds have their own scheduled refresh path. Avoid spending shared API
        # quota during every historical/PDC data seed unless explicitly asked.
        if refresh_odds:
            _refresh_odds()
        else:
            print("Skipping odds refresh (use --refresh-odds to opt in).")

        # ── 6. Write real-data flag ───────────────────────────────────────────
        FLAG_PATH.parent.mkdir(parents=True, exist_ok=True)
        FLAG_PATH.write_text(f"seeded={_utc_now_iso()}\nrows={match_count}\n")
        print(f"Flag written: {FLAG_PATH}")
        print("\n=== Seed complete ===")
    finally:
        LOCK_PATH.unlink(missing_ok=True)


# ── Odds refresh (also callable standalone) ───────────────────────────────────

# Maps odds-api.io league name substrings → tournament_type keys in DB
_LEAGUE_TO_TYPE: dict[str, str] = {
    "premier league":             "premier_league",
    "world championship":         "world_championship",
    "world matchplay":            "world_matchplay",
    "grand slam":                 "grand_slam",
    "uk open":                    "uk_open",
    "world grand prix":           "world_grand_prix",
    "players championship finals": "players_championship_finals",
    "world series":               "world_series_finals",
    "european championship":      "european_championship",
}


def _league_to_tournament_id(
    league_name: str, tourn_by_type: dict[str, int], default_id: int | None
) -> int | None:
    lg = league_name.lower()
    for keyword, t_type in _LEAGUE_TO_TYPE.items():
        if keyword in lg:
            return tourn_by_type.get(t_type, default_id)
    return None  # don't create stubs for non-major leagues


def _refresh_odds() -> None:
    from scrapers.odds_api import fetch_darts_events, fetch_darts_odds

    print("Fetching upcoming darts events (odds-api.io)...")
    # Warm the shared event cache with one set of pagination calls.
    # fetch_darts_events() and fetch_darts_odds() both call _fetch_all_darts_events()
    # internally; after this call the cache is warm, so the second call is free.
    events = fetch_darts_events()
    print(f"  {len(events)} events with resolved player names.")

    print("Fetching live darts odds (odds-api.io, next 7 days)...")
    # Pass raw_events=None — the 30-min cache in odds_api.py means no re-pagination.
    # days_ahead=7: request odds for events in the seeding window (1 call each).
    odds = fetch_darts_odds(days_ahead=7)
    odds_by_event: dict[str, dict] = {o["event_id"]: o for o in odds}

    if not events:
        print("  No darts events available.")
        return

    with SessionLocal() as s:
        players = {p.name.lower(): p for p in s.query(Player).all()}
        tourn_by_type: dict[str, int] = {
            t.tournament_type: t.id for t in s.query(Tournament).all()
        }
        default_tourn_id = next(iter(tourn_by_type.values()), None)

        stubs_created = 0
        odds_written = 0

        for ev in events:
            p1 = _fuzzy_player(ev["player1"], players)
            p2 = _fuzzy_player(ev["player2"], players)
            if not p1 or not p2:
                continue

            tourn_id = _league_to_tournament_id(
                ev.get("league_name", ""), tourn_by_type, None
            )
            if not tourn_id:
                continue  # skip non-PDC-major events

            commence_dt = (
                datetime.fromisoformat(ev["commence_time"].rstrip("Z"))
                if ev.get("commence_time")
                else _utc_now_naive()
            )

            # Find or create the upcoming match stub
            m = (
                s.query(Match)
                .filter_by(player1_id=p1.id, player2_id=p2.id, is_upcoming=True)
                .filter(Match.match_date >= _utc_now_naive())
                .first()
            )
            if not m:
                m = Match(
                    tournament_id=tourn_id,
                    player1_id=p1.id,
                    player2_id=p2.id,
                    match_date=commence_dt,
                    is_upcoming=True,
                )
                s.add(m)
                s.flush()
                stubs_created += 1

            # Attach odds snapshot if available for this event
            ev_odds = odds_by_event.get(ev["event_id"])
            if ev_odds:
                snap = OddsSnapshot(
                    match_id=m.id,
                    p1_odds=ev_odds["p1_odds"],
                    p2_odds=ev_odds["p2_odds"],
                    p1_implied=ev_odds["p1_implied"],
                    p2_implied=ev_odds["p2_implied"],
                    book=ev_odds.get("book", "DraftKings"),
                    snapshot_time=_utc_now_naive(),
                )
                s.add(snap)
                odds_written += 1

        s.commit()
        print(f"  Created {stubs_created} upcoming match stubs, "
              f"{odds_written} odds snapshots.")


def _fuzzy_player(name: str, players: dict[str, Player]) -> Player | None:
    """Case-insensitive substring match against known player names."""
    name_l = name.lower()
    if "," in name_l:
        parts = [p.strip() for p in name_l.split(",", 1)]
        if len(parts) == 2 and parts[0] and parts[1]:
            name_l = f"{parts[1]} {parts[0]}"
    # Exact match first
    if name_l in players:
        return players[name_l]
    # Partial match
    for key, obj in players.items():
        if name_l in key or key in name_l:
            return obj
    return None


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed BullzIQ DB with real PDC data.")
    parser.add_argument(
        "--start-year", type=int, default=2015,
        help="Earliest year to scrape (default: 2015)",
    )
    parser.add_argument(
        "--end-year", type=int, default=None,
        help="Latest year to scrape, inclusive (default: no limit).",
    )
    parser.add_argument(
        "--refresh-only", action="store_true",
        help="Only scrape the current year (fast daily refresh).",
    )
    parser.add_argument(
        "--refresh-odds", action="store_true",
        help="Also fetch live odds; normally handled by the dedicated odds job.",
    )
    args = parser.parse_args()
    run(
        start_year=args.start_year,
        end_year=args.end_year,
        refresh_only=args.refresh_only,
        refresh_odds=args.refresh_odds,
    )
