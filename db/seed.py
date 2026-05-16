"""
db/seed.py — Demo data seed for BullzIQ.

Generates:
- 24 real PDC players with realistic stats
- 9 DK-covered tournaments
- ~600 historical matches (2020–today)
- Elo history from those matches
- Upcoming matches for this week with odds
- Model picks and steam events

Call ensure_seeded() at app startup.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, date
from pathlib import Path

from db.schema import (
    Base, engine, SessionLocal, init_db,
    Player, Tournament, Match, OddsSnapshot,
    EloHistory, PlayerStatsCache, Pick, SteamEvent,
)
from models.elo import DartsElo

RNG = random.Random(42)

# ── Player data ────────────────────────────────────────────────────────────────

PLAYER_DATA = [
    {"name": "Luke Littler",            "nat": "ENG", "nick": "The Nuke",             "elo": 2142, "avg": 101.20, "co": 0.432, "p180": 0.134, "rank": 1},
    {"name": "Luke Humphries",          "nat": "ENG", "nick": "Cool Hand Luke",       "elo": 2095, "avg": 99.10,  "co": 0.412, "p180": 0.125, "rank": 2},
    {"name": "Michael van Gerwen",      "nat": "NED", "nick": "MvG",                  "elo": 2087, "avg": 98.50,  "co": 0.413, "p180": 0.128, "rank": 3},
    {"name": "Michael Smith",           "nat": "ENG", "nick": "Bully Boy",            "elo": 1967, "avg": 97.10,  "co": 0.388, "p180": 0.119, "rank": 5},
    {"name": "Gerwyn Price",            "nat": "WAL", "nick": "The Iceman",           "elo": 1978, "avg": 96.20,  "co": 0.381, "p180": 0.108, "rank": 6},
    {"name": "Peter Wright",            "nat": "SCO", "nick": "Snakebite",            "elo": 1945, "avg": 95.80,  "co": 0.373, "p180": 0.112, "rank": 8},
    {"name": "Rob Cross",               "nat": "ENG", "nick": "Voltage",              "elo": 1901, "avg": 96.50,  "co": 0.385, "p180": 0.110, "rank": 9},
    {"name": "Gary Anderson",           "nat": "SCO", "nick": "The Flying Scotsman",  "elo": 1882, "avg": 96.10,  "co": 0.378, "p180": 0.116, "rank": 10},
    {"name": "Dimitri Van den Bergh",   "nat": "BEL", "nick": "The DreamMaker",       "elo": 1843, "avg": 96.80,  "co": 0.395, "p180": 0.122, "rank": 11},
    {"name": "Jose de Sousa",           "nat": "POR", "nick": "The Special One",      "elo": 1856, "avg": 95.50,  "co": 0.362, "p180": 0.107, "rank": 12},
    {"name": "Damon Heta",              "nat": "AUS", "nick": "The Heat",             "elo": 1804, "avg": 95.00,  "co": 0.369, "p180": 0.108, "rank": 13},
    {"name": "Danny Noppert",           "nat": "NED", "nick": "Freeze",               "elo": 1821, "avg": 95.20,  "co": 0.367, "p180": 0.105, "rank": 14},
    {"name": "Nathan Aspinall",         "nat": "ENG", "nick": "The Asp",              "elo": 1812, "avg": 94.80,  "co": 0.364, "p180": 0.103, "rank": 15},
    {"name": "Stephen Bunting",         "nat": "ENG", "nick": "The Bullet",           "elo": 1789, "avg": 94.50,  "co": 0.358, "p180": 0.101, "rank": 16},
    {"name": "Joe Cullen",              "nat": "ENG", "nick": "The Rockstar",         "elo": 1776, "avg": 94.00,  "co": 0.351, "p180": 0.099, "rank": 17},
    {"name": "Dave Chisnall",           "nat": "ENG", "nick": "Chizzy",               "elo": 1765, "avg": 93.50,  "co": 0.348, "p180": 0.097, "rank": 18},
    {"name": "Jonny Clayton",           "nat": "WAL", "nick": "The Ferret",           "elo": 1742, "avg": 93.20,  "co": 0.352, "p180": 0.098, "rank": 19},
    {"name": "Chris Dobey",             "nat": "ENG", "nick": "Hollywood",            "elo": 1758, "avg": 93.80,  "co": 0.355, "p180": 0.100, "rank": 20},
    {"name": "Andrew Gilding",          "nat": "ENG", "nick": "Triggy",               "elo": 1749, "avg": 93.00,  "co": 0.347, "p180": 0.096, "rank": 21},
    {"name": "Ian White",               "nat": "ENG", "nick": "The Diamond",          "elo": 1703, "avg": 93.00,  "co": 0.346, "p180": 0.095, "rank": 22},
    {"name": "Simon Whitlock",          "nat": "AUS", "nick": "The Wizard",           "elo": 1711, "avg": 92.80,  "co": 0.341, "p180": 0.094, "rank": 23},
    {"name": "Brendan Dolan",           "nat": "IRL", "nick": "The History Maker",    "elo": 1718, "avg": 92.50,  "co": 0.339, "p180": 0.093, "rank": 24},
    {"name": "Ryan Searle",             "nat": "ENG", "nick": "Heavy Metal",          "elo": 1692, "avg": 92.20,  "co": 0.337, "p180": 0.092, "rank": 25},
    {"name": "Callan Rydz",             "nat": "ENG", "nick": "The Riot",             "elo": 1684, "avg": 92.50,  "co": 0.340, "p180": 0.093, "rank": 26},
]

# ── Tournament data ─────────────────────────────────────────────────────────────

TOURNAMENT_DATA = [
    {
        "name": "PDC World Championship",
        "type": "world_championship",
        "tier": 1,
        "prize": 2_500_000,
        "format": "Best of 13 sets (final)",
        "month": "December–January",
    },
    {
        "name": "Premier League Darts",
        "type": "premier_league",
        "tier": 1,
        "prize": 1_000_000,
        "format": "Best of 11 legs",
        "month": "February–May",
    },
    {
        "name": "World Matchplay",
        "type": "world_matchplay",
        "tier": 1,
        "prize": 700_000,
        "format": "Best of 31 legs (final)",
        "month": "July",
    },
    {
        "name": "Grand Slam of Darts",
        "type": "grand_slam",
        "tier": 1,
        "prize": 700_000,
        "format": "Best of 19 legs",
        "month": "November",
    },
    {
        "name": "UK Open",
        "type": "uk_open",
        "tier": 1,
        "prize": 450_000,
        "format": "Best of 11 legs",
        "month": "March",
    },
    {
        "name": "World Grand Prix",
        "type": "world_grand_prix",
        "tier": 1,
        "prize": 600_000,
        "format": "Best of 5 sets (doubles start)",
        "month": "October",
    },
    {
        "name": "Players Championship Finals",
        "type": "players_championship_finals",
        "tier": 2,
        "prize": 500_000,
        "format": "Best of 21 legs (final)",
        "month": "November",
    },
    {
        "name": "European Championship",
        "type": "european_championship",
        "tier": 2,
        "prize": 400_000,
        "format": "Best of 13 legs",
        "month": "October",
    },
    {
        "name": "World Series of Darts Finals",
        "type": "world_series_finals",
        "tier": 2,
        "prize": 500_000,
        "format": "Best of 21 legs (final)",
        "month": "September",
    },
]

# Rounds used in tournament seeding
ROUNDS = ["First Round", "Second Round", "Last 16", "Quarter-Final", "Semi-Final", "Final"]

# Legs to win by tournament type
LEGS_TO_WIN = {
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


# ── Helper functions ────────────────────────────────────────────────────────────

def _prob_to_american(prob: float) -> int:
    prob = max(0.02, min(0.98, prob))
    if prob >= 0.5:
        return -round((prob / (1 - prob)) * 100)
    return round(((1 - prob) / prob) * 100)


def _add_vig(prob: float, vig: float = 0.046) -> float:
    """Apply DraftKings-style vig to implied probability."""
    return min(0.97, prob * (1 + vig))


def _simulate_match(
    p1_elo: float,
    p2_elo: float,
    legs_to_win: int,
) -> tuple[int, int]:
    """Simulate a match result based on Elo win probability."""
    p1_win_prob = 1.0 / (1.0 + 10 ** ((p2_elo - p1_elo) / 400))
    p1_legs, p2_legs = 0, 0
    while p1_legs < legs_to_win and p2_legs < legs_to_win:
        if RNG.random() < p1_win_prob:
            p1_legs += 1
        else:
            p2_legs += 1
    return p1_legs, p2_legs


def _generate_form_streak(win_rate: float) -> str:
    results = []
    for _ in range(5):
        results.append("W" if RNG.random() < win_rate else "L")
    return "".join(results)


# ── Main seed function ──────────────────────────────────────────────────────────

def seed_all() -> None:
    """Populate the database with demo data. Call once when DB is empty."""
    print("BullzIQ: Seeding demo data...")
    session = SessionLocal()

    try:
        # ── 1. Players ──────────────────────────────────────────────────────────
        player_objs: dict[str, Player] = {}
        for p in PLAYER_DATA:
            win_rate = RNG.uniform(0.42, 0.70)
            player = Player(
                name=p["name"],
                nationality=p["nat"],
                nickname=p["nick"],
                pdc_ranking=p["rank"],
                elo=float(p["elo"]),
                avg_3dart=p["avg"],
                checkout_pct=p["co"],
                avg_180s_per_leg=p["p180"],
                win_rate_last20=round(win_rate, 3),
            )
            session.add(player)
            player_objs[p["name"]] = player

        session.flush()  # get IDs

        # ── 2. Tournaments ──────────────────────────────────────────────────────
        tourn_objs: dict[str, Tournament] = {}
        for t in TOURNAMENT_DATA:
            tourn = Tournament(
                name=t["name"],
                tournament_type=t["type"],
                dk_covered=True,
                prestige_tier=t["tier"],
                prize_fund=t["prize"],
                format_desc=t["format"],
                typical_month=t["month"],
            )
            session.add(tourn)
            tourn_objs[t["name"]] = tourn

        session.flush()

        # ── 3. Historical matches (2015–today-7 days) ───────────────────────────
        elo_tracker = DartsElo(k=32)
        # Initialise with 2015 starting Elos (lower than current)
        for p in PLAYER_DATA:
            elo_tracker.ratings[p["name"]] = float(p["elo"]) * 0.75 + DEFAULT_START

        start_date = datetime(2015, 1, 1)
        end_date = datetime.now() - timedelta(days=7)
        players_list = list(player_objs.keys())
        elo_history_rows: list[EloHistory] = []

        match_count = 0
        for tourn_data in TOURNAMENT_DATA:
            tourn_obj = tourn_objs[tourn_data["name"]]
            t_type = tourn_data["type"]
            legs = LEGS_TO_WIN[t_type]

            # Simulate events for each year 2015 onward
            for year in range(2015, datetime.now().year + 1):
                event_start = datetime(year, _typical_month_num(tourn_data["month"]), 1)
                if event_start > end_date:
                    break

                # Generate a small bracket
                pool = RNG.sample(players_list, min(8, len(players_list)))
                RNG.shuffle(pool)
                pairs = [(pool[i], pool[i + 1]) for i in range(0, len(pool) - 1, 2)]

                for i, (p1_name, p2_name) in enumerate(pairs):
                    round_name = ROUNDS[min(i, len(ROUNDS) - 1)]
                    match_day = event_start + timedelta(days=i)
                    if match_day > end_date:
                        continue

                    p1_elo = elo_tracker.get_rating(p1_name)
                    p2_elo = elo_tracker.get_rating(p2_name)
                    s1, s2 = _simulate_match(p1_elo, p2_elo, legs)
                    winner_name = p1_name if s1 > s2 else p2_name
                    loser_name = p2_name if s1 > s2 else p1_name

                    p1 = player_objs[p1_name]
                    p2 = player_objs[p2_name]
                    winner_obj = player_objs[winner_name]

                    # Stats noise
                    avg1 = round(p1.avg_3dart + RNG.gauss(0, 2.5), 2)
                    avg2 = round(p2.avg_3dart + RNG.gauss(0, 2.5), 2)
                    co1 = round(max(0.1, min(0.7, p1.checkout_pct + RNG.gauss(0, 0.04))), 3)
                    co2 = round(max(0.1, min(0.7, p2.checkout_pct + RNG.gauss(0, 0.04))), 3)
                    legs_180_1 = max(0, round(RNG.gauss(p1.avg_180s_per_leg * (s1 + s2) * 3, 1)))
                    legs_180_2 = max(0, round(RNG.gauss(p2.avg_180s_per_leg * (s1 + s2) * 3, 1)))

                    match_obj = Match(
                        tournament_id=tourn_obj.id,
                        player1_id=p1.id,
                        player2_id=p2.id,
                        round_name=round_name,
                        match_date=match_day,
                        legs_to_win=legs,
                        score1=s1,
                        score2=s2,
                        winner_id=winner_obj.id,
                        avg_p1=avg1,
                        avg_p2=avg2,
                        checkout_pct_p1=co1,
                        checkout_pct_p2=co2,
                        legs_180_p1=legs_180_1,
                        legs_180_p2=legs_180_2,
                        is_upcoming=False,
                    )
                    session.add(match_obj)
                    session.flush()

                    # Update Elo
                    elo_before_winner = elo_tracker.get_rating(winner_name)
                    elo_before_loser = elo_tracker.get_rating(loser_name)
                    new_w, new_l = elo_tracker.update(
                        winner_name, loser_name,
                        max(s1, s2), min(s1, s2),
                        legs, t_type,
                    )
                    elo_history_rows.append(EloHistory(
                        player_id=player_objs[winner_name].id,
                        match_id=match_obj.id,
                        elo_before=elo_before_winner,
                        elo_after=new_w,
                        recorded_at=match_day,
                    ))
                    elo_history_rows.append(EloHistory(
                        player_id=player_objs[loser_name].id,
                        match_id=match_obj.id,
                        elo_before=elo_before_loser,
                        elo_after=new_l,
                        recorded_at=match_day,
                    ))
                    match_count += 1

        # bulk add elo history
        for row in elo_history_rows:
            session.add(row)

        session.flush()

        # Update player Elo to current tracker values
        for p_name, p_obj in player_objs.items():
            tracked_elo = elo_tracker.ratings.get(p_name)
            if tracked_elo:
                p_obj.elo = round(tracked_elo, 1)

        # ── 4. Stats cache ──────────────────────────────────────────────────────
        for p_data in PLAYER_DATA:
            p_obj = player_objs[p_data["name"]]
            streak = _generate_form_streak(p_obj.win_rate_last20 or 0.5)
            sc = PlayerStatsCache(
                player_id=p_obj.id,
                win_rate_last20=p_obj.win_rate_last20,
                win_rate_premier_league=round(RNG.uniform(0.35, 0.70), 3),
                win_rate_world_championship=round(RNG.uniform(0.30, 0.75), 3),
                avg_3dart_last10=round(p_data["avg"] + RNG.gauss(0, 1.5), 2),
                checkout_pct_last10=round(max(0.15, p_data["co"] + RNG.gauss(0, 0.03)), 3),
                avg_180s_last10=round(max(0, p_data["p180"] + RNG.gauss(0, 0.01)), 3),
                form_streak=streak,
            )
            session.add(sc)

        session.flush()

        # ── 5. Upcoming matches (today + next 6 days) ───────────────────────────
        today = datetime.now().replace(hour=19, minute=0, second=0, microsecond=0)
        pl_tourn = tourn_objs["Premier League Darts"]
        wm_tourn = tourn_objs["World Matchplay"]

        upcoming_fixtures = [
            # Tonight — Premier League Night 18
            ("Luke Littler",        "Michael van Gerwen", pl_tourn,  "Night 18 — Quarter-Final", today,                      6),
            ("Luke Humphries",      "Michael Smith",       pl_tourn,  "Night 18 — Quarter-Final", today + timedelta(hours=1), 6),
            ("Gerwyn Price",        "Peter Wright",        pl_tourn,  "Night 18 — Quarter-Final", today + timedelta(hours=2), 6),
            ("Rob Cross",           "Gary Anderson",       pl_tourn,  "Night 18 — Quarter-Final", today + timedelta(hours=3), 6),
            # Tomorrow — Premier League semi-finals
            ("Luke Littler",        "Luke Humphries",      pl_tourn,  "Night 18 — Semi-Final",    today + timedelta(days=1),  6),
            ("Michael van Gerwen",  "Michael Smith",       pl_tourn,  "Night 18 — Semi-Final",    today + timedelta(days=1, hours=1), 6),
            # Day after — World Matchplay early rounds
            ("Dimitri Van den Bergh","Nathan Aspinall",    wm_tourn,  "First Round",              today + timedelta(days=2),  7),
            ("Damon Heta",          "Danny Noppert",       wm_tourn,  "First Round",              today + timedelta(days=2, hours=1), 7),
            ("Stephen Bunting",     "Jose de Sousa",       wm_tourn,  "First Round",              today + timedelta(days=3),  7),
            ("Jonny Clayton",       "Chris Dobey",         wm_tourn,  "First Round",              today + timedelta(days=3, hours=1), 7),
        ]

        upcoming_objs: list[Match] = []
        for p1_name, p2_name, tourn_obj, round_name, match_dt, legs in upcoming_fixtures:
            p1 = player_objs[p1_name]
            p2 = player_objs[p2_name]
            m = Match(
                tournament_id=tourn_obj.id,
                player1_id=p1.id,
                player2_id=p2.id,
                round_name=round_name,
                match_date=match_dt,
                legs_to_win=legs,
                is_upcoming=True,
            )
            session.add(m)
            upcoming_objs.append((m, p1, p2, p1_name, p2_name))

        session.flush()

        # ── 6. Odds snapshots for upcoming matches ───────────────────────────────
        picks: list[Pick] = []
        steam_events: list[SteamEvent] = []
        now = datetime.now()

        for match_obj, p1_obj, p2_obj, p1_name, p2_name in upcoming_objs:
            p1_elo = elo_tracker.get_rating(p1_name)
            p2_elo = elo_tracker.get_rating(p2_name)
            fair_p1 = 1.0 / (1.0 + 10 ** ((p2_elo - p1_elo) / 400))

            # Generate 6 snapshots over the last 3 hours
            base_p1_implied = _add_vig(fair_p1)
            base_p2_implied = _add_vig(1 - fair_p1)

            for snap_offset in range(6):
                snap_time = now - timedelta(minutes=(5 - snap_offset) * 30)
                # small random drift
                drift = RNG.gauss(0, 0.008)
                p1_impl = max(0.04, min(0.96, base_p1_implied + drift * snap_offset * 0.3))
                p2_impl = max(0.04, min(0.96, base_p2_implied - drift * snap_offset * 0.3))

                snap = OddsSnapshot(
                    match_id=match_obj.id,
                    snapshot_time=snap_time,
                    p1_odds=_prob_to_american(fair_p1 + RNG.gauss(0, 0.01)),
                    p2_odds=_prob_to_american(1 - fair_p1 + RNG.gauss(0, 0.01)),
                    p1_implied=round(p1_impl, 4),
                    p2_implied=round(p2_impl, 4),
                    book="DraftKings",
                )
                session.add(snap)

            # Current (latest) odds
            current_p1_odds = _prob_to_american(fair_p1)
            current_p2_odds = _prob_to_american(1 - fair_p1)

            # ── Generate pick if meaningful edge exists ──────────────────────────
            dk_implied_p1 = _add_vig(fair_p1)
            edge_p1 = (fair_p1 - dk_implied_p1) * 100

            # Pick the side with positive edge (usually the underdog, since vig is on favourite)
            if fair_p1 < 0.5:  # p1 is underdog — we may have edge
                pick_player = p1_obj
                pick_name = p1_name
                model_prob = fair_p1
                dk_odds = current_p1_odds
                dk_imp = dk_implied_p1
            else:
                pick_player = p2_obj
                pick_name = p2_name
                model_prob = 1 - fair_p1
                dk_odds = current_p2_odds
                dk_imp = _add_vig(1 - fair_p1)

            edge_pct = round((model_prob - dk_imp) * 100 + RNG.gauss(1.5, 1.2), 2)

            if edge_pct > 0.5:
                if edge_pct >= 4:
                    conf = "high"
                elif edge_pct >= 2:
                    conf = "medium"
                else:
                    conf = "low"

                reasoning = (
                    f"Model assigns {round(model_prob * 100, 1)}% win probability. "
                    f"DK implies {round(dk_imp * 100, 1)}%. "
                    f"Elo edge driven by recent form and tournament history."
                )

                pick = Pick(
                    match_id=match_obj.id,
                    pick_player_id=pick_player.id,
                    model_prob=round(model_prob, 4),
                    dk_odds=dk_odds,
                    dk_implied=round(dk_imp, 4),
                    edge_pct=edge_pct,
                    confidence=conf,
                    reasoning=reasoning,
                    pick_time=now - timedelta(minutes=RNG.randint(10, 90)),
                    active=True,
                )
                session.add(pick)

            # ── Steam detection: flag if drift was large ─────────────────────────
            total_drift = abs(drift * 5 * 0.3)
            if total_drift > 0.03:
                direction = p1_name if drift > 0 else p2_name
                steam = SteamEvent(
                    match_id=match_obj.id,
                    player_steamed=direction,
                    shift_pct=round(total_drift * 100, 2),
                    opening_odds=_prob_to_american(fair_p1 + (0 if direction == p1_name else 0)),
                    current_odds=_prob_to_american(fair_p1 + drift * 5 * 0.3),
                    opening_implied=round(base_p1_implied, 4),
                    current_implied=round(p1_impl, 4),
                    detected_at=now - timedelta(minutes=5),
                )
                session.add(steam)

        session.commit()
        print(f"BullzIQ: Seeded {len(PLAYER_DATA)} players, {len(TOURNAMENT_DATA)} tournaments, "
              f"{match_count} historical matches, {len(upcoming_fixtures)} upcoming matches.")

    except Exception as exc:
        session.rollback()
        print(f"BullzIQ seed error: {exc}")
        raise
    finally:
        session.close()


def _typical_month_num(month_str: str) -> int:
    mapping = {
        "January": 1, "February": 2, "March": 3, "April": 4,
        "May": 5, "June": 6, "July": 7, "August": 8,
        "September": 9, "October": 10, "November": 11, "December": 12,
        "December–January": 12,
    }
    first = month_str.split("–")[0].split("–")[0].strip()
    return mapping.get(first, 6)


DEFAULT_START = 250  # offset so initial 2015 Elos are lower, allowing trajectory growth


def ensure_seeded() -> None:
    """Create DB tables and seed demo data if empty.

    If ``data_files/db_is_real.flag`` exists the database was pre-seeded by
    the GitHub Actions workflow with real PDC data — skip the demo seed.
    Safe to call on every Streamlit startup.
    """
    from pathlib import Path
    flag = Path(__file__).resolve().parent.parent / "data_files" / "db_is_real.flag"
    init_db()

    if flag.exists():
        # Real data committed by GH Action — nothing to do
        return

    session = SessionLocal()
    try:
        count = session.query(Player).count()
    finally:
        session.close()

    if count == 0:
        seed_all()
