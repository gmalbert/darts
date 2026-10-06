"""backend/calculators/client_math.py — pure-Python mirrors of models/props_model.py + models/elo.py.

These functions are exposed via the FastAPI calc/* endpoints *and* are the
exact formulas the React client ports to TypeScript.  Do not change the
mathematics here without mirroring the change in
`frontend/src/utils/calculators.ts` and adding a parity test.
"""
from __future__ import annotations

import math


# ── Elo ─────────────────────────────────────────────────────────────────────

DEFAULT_RATING = 1500.0


def elo_win_probability(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))


def implied_prob_from_american(odds: int) -> float:
    if odds < 0:
        return (-odds) / (-odds + 100)
    return 100 / (odds + 100)


def to_american_odds(prob: float) -> int:
    prob = max(0.01, min(0.99, prob))
    if prob >= 0.5:
        return -round((prob / (1 - prob)) * 100)
    return round(((1 - prob) / prob) * 100)


def to_decimal_odds(prob: float) -> float:
    prob = max(0.01, min(0.99, prob))
    return round(1 / prob, 2)


# ── Edge & EV ───────────────────────────────────────────────────────────────

def calculate_edge(model_prob: float, dk_american_odds: int) -> dict:
    if dk_american_odds < 0:
        dk_implied = (-dk_american_odds) / (-dk_american_odds + 100)
    else:
        dk_implied = 100 / (dk_american_odds + 100)

    edge_pct = (model_prob - dk_implied) * 100

    if dk_american_odds >= 0:
        payout = dk_american_odds
    else:
        payout = 100 / (-dk_american_odds / 100)

    ev = model_prob * payout - (1 - model_prob) * 100

    if edge_pct >= 5:
        grade = "A"
    elif edge_pct >= 3:
        grade = "B"
    elif edge_pct >= 1.5:
        grade = "C"
    else:
        grade = "D"

    return {
        "model_prob": round(model_prob, 4),
        "dk_implied": round(dk_implied, 4),
        "edge_pct": round(edge_pct, 2),
        "expected_value": round(ev, 2),
        "grade": grade,
    }


# ── 180s Poisson ────────────────────────────────────────────────────────────

def _poisson_cdf(k: int, mu: float) -> float:
    """Cumulative probability of X ≤ k for Poisson(mu)."""
    # Use a simple recurrence for numerical stability (no scipy needed).
    if k < 0:
        return 0.0
    p = math.exp(-mu)
    total = p
    for i in range(1, k + 1):
        p *= mu / i
        total += p
    return min(1.0, total)


def prob_180s_over(expected_180s: float, line: float) -> float:
    return float(1 - _poisson_cdf(math.floor(line), mu=expected_180s))


def prob_180s_under(expected_180s: float, line: float) -> float:
    return 1.0 - prob_180s_over(expected_180s, line)


def expected_180s_in_match(
    avg_180s_per_leg: float,
    legs_to_win: int,
    expected_legs: float | None = None,
) -> float:
    if expected_legs is None:
        expected_legs = legs_to_win * 1.6
    return avg_180s_per_leg * expected_legs


# ── Format variance ─────────────────────────────────────────────────────────

def format_adjusted_probability(
    base_prob: float,
    legs_to_win: int,
    sets_to_win: int | None = None,
) -> float:
    if sets_to_win:
        total_sets = sets_to_win * 2 - 1
        skill_signal = (base_prob - 0.5) * (1 + total_sets / 20)
        return max(0.02, min(0.98, 0.5 + skill_signal))
    skill_signal = (base_prob - 0.5) * (0.6 + legs_to_win / 15)
    return max(0.02, min(0.98, 0.5 + skill_signal))


# ── Parlay ──────────────────────────────────────────────────────────────────

def parlay(legs: list[dict]) -> dict:
    """legs: list of {"prob": float (0-1), "odds": int}"""
    combined_model_prob = 1.0
    combined_implied_prob = 1.0
    combined_decimal = 1.0
    for leg in legs:
        prob = float(leg["prob"])
        odds = int(leg["odds"])
        if odds < 0:
            dk_impl = (-odds) / (-odds + 100)
            decimal = 1 + 100 / (-odds)
        else:
            dk_impl = 100 / (odds + 100)
            decimal = 1 + odds / 100
        combined_model_prob *= prob
        combined_implied_prob *= dk_impl
        combined_decimal *= decimal

    edge_pct = (combined_model_prob - combined_implied_prob) * 100
    ev_100 = combined_model_prob * ((combined_decimal - 1) * 100) - (1 - combined_model_prob) * 100
    return {
        "combined_model_prob": round(combined_model_prob, 4),
        "combined_implied_prob": round(combined_implied_prob, 4),
        "combined_decimal_odds": round(combined_decimal, 4),
        "edge_pct": round(edge_pct, 2),
        "ev_per_100": round(ev_100, 2),
    }


# ── Steam detection (mirror of jobs/scheduler.py logic) ─────────────────────

STEAM_THRESHOLD_PCT = 3.0
WINDOW_MINUTES = 30


def detect_steam(snapshots: list[dict]) -> dict | None:
    """Return a steam event dict if the implied-probability shift over the
    window meets the threshold, else None.

    snapshots: list of {"time": ISO, "p1_implied": float, "p2_implied": float, "p1_odds": int, "p2_odds": int}
    """
    if len(snapshots) < 2:
        return None
    first = snapshots[0]
    latest = snapshots[-1]
    shift = (latest["p1_implied"] - first["p1_implied"]) * 100
    if abs(shift) < STEAM_THRESHOLD_PCT:
        return None
    return {
        "shift_pct": round(shift, 2),
        "opening_odds": first["p1_odds"],
        "current_odds": latest["p1_odds"],
        "opening_implied": first["p1_implied"],
        "current_implied": latest["p1_implied"],
    }
