# Darts (BullzIQ) — 12-Month Feature Roadmap

> Generated: 2026-07-31 | Horizon: August 2026 – July 2027

---

## Executive Summary

BullzIQ evolves from a single-tournament darts prediction app into a comprehensive
darts analytics platform covering PDC, BDO/WDF, and major televised events with
deep player profiling, leg simulation, and live match intelligence.

---

## Q1 (Aug–Oct 2026) — Data Foundation

### Feature 1 — DartConnect / ProDarts Stats Integration

Ingest match-level statistics: checkout percentage, 180s per leg, average
score per 3 darts, darts taken at double. Build per-player rolling averages.

```python
# scrapers/dartsstats.py
import requests, pandas as pd
from pathlib import Path

DATA_DIR = Path("data_files")
PRODARTSDB_BASE = "https://api.dartsdatabase.co.uk/v1"

def fetch_player_stats(player_name: str) -> dict:
    """Fetch player career stats from darts database API."""
    resp = requests.get(
        f"{PRODARTSDB_BASE}/players/search",
        params={"name": player_name, "limit": 1},
        timeout=15,
    )
    data = resp.json()
    if not data.get("players"):
        return {}
    p = data["players"][0]
    return {
        "avg_180_per_leg": p.get("180s_per_leg", 0),
        "checkout_pct": p.get("checkout_pct", 0),
        "three_dart_avg": p.get("three_dart_average", 0),
        "first_9_avg": p.get("first_nine_average", 0),
        "double_rate": p.get("doubles_per_leg", 0),
    }

def build_rolling_player_features(match_stats: pd.DataFrame, player: str,
                                    n: int = 10) -> dict:
    """Compute rolling averages over last N matches."""
    recent = (
        match_stats[match_stats["player"] == player]
        .sort_values("match_date", ascending=False)
        .head(n)
    )
    if recent.empty:
        return {}
    return {
        "avg_3dart_l10": recent["three_dart_avg"].mean(),
        "checkout_pct_l10": recent["checkout_pct"].mean(),
        "avg_180s_l10": recent["count_180"].mean(),
        "avg_darts_per_leg_l10": recent["darts_per_leg"].mean(),
    }
```

### Feature 2 — Leg Simulation Engine (Monte Carlo)

Simulate individual legs using per-player scoring distributions and
checkout charts. Output win probability per set and match.

```python
# analytics/leg_simulator.py
import numpy as np
from scipy.stats import norm

def simulate_leg(
    player_a_avg: float, player_b_avg: float,
    player_a_checkout_pct: float, player_b_checkout_pct: float,
    starting_score: int = 501,
    n_sim: int = 10_000,
) -> dict:
    """Simulate a single 501 leg N times. Return win probabilities."""
    a_wins = 0
    for _ in range(n_sim):
        score_a, score_b = starting_score, starting_score
        turn = 0  # 0 = A, 1 = B
        while True:
            if turn == 0:
                visit = max(0, min(180, int(np.random.normal(player_a_avg, 20))))
                score_a -= visit
                if score_a <= 0:
                    if score_a == 0 and np.random.random() < player_a_checkout_pct:
                        a_wins += 1
                        break
                    score_a += visit  # bust
                turn = 1
            else:
                visit = max(0, min(180, int(np.random.normal(player_b_avg, 20))))
                score_b -= visit
                if score_b <= 0:
                    if score_b == 0 and np.random.random() < player_b_checkout_pct:
                        break
                    score_b += visit
                turn = 0
    return {"p_a_wins": a_wins / n_sim, "p_b_wins": 1 - a_wins / n_sim}
```

### Feature 3 — Tournament Format Aware Predictions

Adjust predictions based on match format: first to 3 sets vs first to 7
legs vs first to 10 legs. Shorter formats increase upset probability.

```python
# analytics/format_adjustment.py
import numpy as np
from scipy.stats import binom

def match_win_prob_from_leg_prob(
    p_leg_win: float, legs_to_win: int, total_legs: int
) -> float:
    """P(player wins match) given P(player wins each leg) and format."""
    # Sum over all winning paths
    p_match = sum(
        binom.pmf(k, n, p_leg_win)
        for n in range(legs_to_win, total_legs + 1)
        for k in [legs_to_win]
        if n - legs_to_win < legs_to_win
    )
    # Simpler: use negative binomial
    from scipy.stats import nbinom
    return float(nbinom.sf(total_legs - legs_to_win - 1, legs_to_win, p_leg_win))
```

### Feature 4 — Player vs Player Head-to-Head Intelligence

Build comprehensive H2H records by tournament level, format, and crowd
factor (crowd often cheers for particular players in PDC events).

```python
# db/queries.py (add H2H)
def get_h2h_record(player_a: str, player_b: str, session) -> dict:
    from db.schema import Fight as Match
    matches = session.query(Match).filter(
        ((Match.player_a == player_a) & (Match.player_b == player_b)) |
        ((Match.player_a == player_b) & (Match.player_b == player_a))
    ).all()
    a_wins = sum(1 for m in matches if m.winner == player_a)
    b_wins = len(matches) - a_wins
    return {"total": len(matches), "a_wins": a_wins, "b_wins": b_wins,
            "a_win_pct": a_wins / max(len(matches), 1)}
```

### Feature 5 — Checkout Table & Finishing Route Optimizer

Display optimal finishing routes for any remaining score (e.g., 121 =
T20, T11, D5). Useful for analysis and as a viewer aid.

```python
# utils/checkout_routes.py
CHECKOUT_TABLE = {
    170: ["T20", "T20", "Bull"],
    167: ["T20", "T19", "Bull"],
    164: ["T20", "T18", "Bull"],
    160: ["T20", "T20", "D20"],
    158: ["T20", "T20", "D19"],
    121: ["T20", "T11", "D5"],
    120: ["T20", "S20", "D20"],
    119: ["T19", "T12", "D13"],
    2: ["D1"],
    1: None,  # Cannot checkout on 1
}

def get_checkout_route(score: int) -> list[str] | None:
    return CHECKOUT_TABLE.get(score)

def best_checkout_probability(
    score: int, player_stats: dict
) -> float:
    """Estimate P(checkout on this visit) given player checkout ability."""
    route = get_checkout_route(score)
    if not route:
        return 0.0
    # Simplified: scale by player's overall checkout percentage
    difficulty = len(route) / 3  # 1 dart easier than 3
    return player_stats.get("checkout_pct", 0.3) / difficulty
```

---

## Q2 (Nov 2026 – Jan 2027) — Model Enhancements

### Feature 6 — Pressure Scoring Metric

Track player 3-dart averages in crucial legs (deciding legs, match legs,
final set legs). Players with high pressure averages are more reliable picks.

```python
# analytics/pressure_scoring.py
import pandas as pd

def compute_pressure_average(match_data: pd.DataFrame, player: str) -> dict:
    """Average score in high-pressure situations vs regular."""
    player_data = match_data[match_data["player"] == player]
    pressure_legs = player_data[player_data["is_deciding_leg"] == True]
    normal_legs = player_data[player_data["is_deciding_leg"] == False]
    return {
        "normal_avg": normal_legs["three_dart_avg"].mean(),
        "pressure_avg": pressure_legs["three_dart_avg"].mean() if len(pressure_legs) > 0 else None,
        "pressure_factor": (pressure_legs["three_dart_avg"].mean() /
                             normal_legs["three_dart_avg"].mean())
                            if len(pressure_legs) > 5 else 1.0,
    }
```

### Feature 7 — Tournament Seeding & Path Analysis

For each player in a draw, compute their projected path to the final
and identify the most dangerous potential opponents in each round.

### Feature 8 — Elo Rating System for Darts

Build a PDC-specific Elo system accounting for match format (best-of-5,
best-of-7, etc.) and tournament prestige (World Championship > ranking events).

```python
# analytics/darts_elo.py
import pandas as pd

K_BY_TOURNAMENT = {"World Championship": 40, "Premier League": 30,
                    "Masters": 25, "Other": 20}
INITIAL_ELO = 1500

def build_darts_elo(matches: pd.DataFrame) -> pd.DataFrame:
    elo = {}
    records = []
    for _, m in matches.sort_values("match_date").iterrows():
        pa, pb = m["player_a"], m["player_b"]
        ea = elo.get(pa, INITIAL_ELO)
        eb = elo.get(pb, INITIAL_ELO)
        exp_a = 1 / (1 + 10 ** ((eb - ea) / 400))
        k = K_BY_TOURNAMENT.get(m.get("tournament_tier", "Other"), 20)
        actual_a = 1.0 if m["winner"] == pa else 0.0
        elo[pa] = ea + k * (actual_a - exp_a)
        elo[pb] = eb + k * ((1 - actual_a) - (1 - exp_a))
        records.append({"match_id": m.get("match_id"), "player_a": pa, "player_b": pb,
                          "elo_a": elo[pa], "elo_b": elo[pb]})
    return pd.DataFrame(records)
```

### Feature 9 — Scoring Consistency (Standard Deviation)

Players with low variance in scoring are more predictable and better for
handicap betting. Players with high variance are upset-prone.

```python
# analytics/consistency.py
import pandas as pd, numpy as np

def compute_scoring_consistency(player: str, match_stats: pd.DataFrame) -> dict:
    recent = match_stats[match_stats["player"] == player]["three_dart_avg"]
    if len(recent) < 5:
        return {"consistency_score": 50.0}
    cv = recent.std() / recent.mean() if recent.mean() > 0 else 0
    return {
        "avg": recent.mean(), "std": recent.std(),
        "cv": cv,  # Lower = more consistent
        "consistency_score": max(0, 100 - cv * 200),
    }
```

### Feature 10 — Handicap Leg Model

Predict covers for handicap markets (e.g., Player A -3.5 legs).
More granular than match-winner; often better EV.

---

## Q3 (Feb–Apr 2027) — Visual Analytics

### Feature 11 — Player Scoring Distribution Chart

Violin plot of each player's 3-dart score distribution. High skew toward
140+ indicates elite scorer; flat distribution = inconsistent.

### Feature 12 — Tournament History Heat Map

For each player × tournament combination, show historical performance
(color = average finish). Identifies tournament specialists.

### Feature 13 — Live Match Tracker

Real-time leg-by-leg update during PDC events. Display current averages,
180s, and win probability update after each visit.

```python
# pages/live_match.py
import streamlit as st, time

def render_live_match(match_id: int) -> None:
    st.title("🎯 Live Match Tracker")
    placeholder = st.empty()
    while True:
        from db.queries import get_live_match_data
        data = get_live_match_data(match_id)
        with placeholder.container():
            col1, col2 = st.columns(2)
            col1.metric(data["player_a"], f"Avg: {data['avg_a']:.1f}")
            col2.metric(data["player_b"], f"Avg: {data['avg_b']:.1f}")
            st.metric("Sets", f"{data['sets_a']} - {data['sets_b']}")
        time.sleep(30)
        st.rerun()
```

### Feature 14 — Checkout Percentage by Score Range

For each player, display checkout success rates for common scores:
170, 121-140, 100-120, 61-99, 40-60, 2-40.

### Feature 15 — Season Stats Leaderboard

Rankings of all active PDC players by: average, 180s per leg, checkout %,
prize money, and win rate.

---

## Q4 (May–Jul 2027) — Automation & Platform

### Feature 16 — World Championship Simulator

Monte Carlo simulate the full PDC World Championship draw (96 players).
Output winner probabilities, each player's probability of reaching each round.

```python
# analytics/worlds_simulator.py
import numpy as np, pandas as pd
from collections import defaultdict

def simulate_worlds(player_elos: dict, n_sim: int = 10_000) -> pd.DataFrame:
    players = list(player_elos.keys())
    wins_per_round = defaultdict(lambda: defaultdict(int))
    rounds = ["Last 64", "Last 32", "Last 16", "QF", "SF", "Final", "Winner"]

    for _ in range(n_sim):
        remaining = players[:]
        np.random.shuffle(remaining)
        for round_name in rounds:
            next_round = []
            for i in range(0, len(remaining), 2):
                p1, p2 = remaining[i], remaining[i+1]
                p1_elo = player_elos.get(p1, INITIAL_ELO)
                p2_elo = player_elos.get(p2, INITIAL_ELO)
                p1_wp = 1 / (1 + 10 ** ((p2_elo - p1_elo) / 400))
                winner = p1 if np.random.random() < p1_wp else p2
                next_round.append(winner)
                wins_per_round[winner][round_name] += 1
            remaining = next_round

    return pd.DataFrame([
        {"player": p, **{r: wins_per_round[p][r]/n_sim for r in rounds}}
        for p in players
    ]).sort_values("Winner", ascending=False)
```

### Feature 17 — Automated Odds Snapshot Archive

Save The Odds API snapshots every 4 hours during active tournaments.
Build historical odds database for line movement and CLV analysis.

### Feature 18 — AI Match Preview

GPT-4o-mini generates a 100-word match preview covering H2H, recent
form, checkout rates, and model recommendation.

### Feature 19 — Weekend Tournament Card Generator

Auto-generate a formatted PDF card of all PDC weekend matches with
model picks, odds, and key stats.

### Feature 20 — Discord Alert System

Post high-confidence picks to Discord before PDC event start time.
Include match time, venue, model probability, and recommended stake.

### Feature 21 — Player Development Tracking

Track players' 3-dart average progression over their career. Identify
rising stars and declining veterans.

```python
# analytics/player_development.py
import pandas as pd, numpy as np

def compute_career_trajectory(player: str, stats_history: pd.DataFrame) -> dict:
    player_data = stats_history[stats_history["player"] == player].sort_values("year")
    if len(player_data) < 3:
        return {"trajectory": "insufficient_data"}
    x = np.arange(len(player_data))
    y = player_data["three_dart_avg"].values
    slope = np.polyfit(x, y, 1)[0]
    return {
        "current_avg": y[-1],
        "peak_avg": y.max(),
        "peak_year": player_data.iloc[y.argmax()]["year"],
        "annual_trend": round(slope, 2),
        "trajectory": "improving" if slope > 0.5 else ("declining" if slope < -0.5 else "stable"),
    }
```

### Feature 22 — Betting ROI Calendar

Visual calendar showing model performance day-by-day. Green/red cells
show daily P&L. Monthly and weekly aggregation views.

---

## Timeline Summary

| Quarter | Focus | Key Deliverables |
|---------|-------|-----------------|
| Q1 Aug–Oct 2026 | Data foundation | DartConnect stats, leg simulator, format adjustment, H2H, checkout table |
| Q2 Nov 2026–Jan 2027 | Model enhancements | Pressure scoring, path analysis, Elo system, consistency metric, handicap model |
| Q3 Feb–Apr 2027 | Visual analytics | Scoring distribution, tournament history heatmap, live tracker, checkout pcts, leaderboard |
| Q4 May–Jul 2027 | Automation | Worlds simulator, odds archive, AI preview, PDF card, Discord alerts, dev tracking, ROI calendar |
