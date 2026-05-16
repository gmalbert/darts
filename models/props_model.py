"""
models/props_model.py — Poisson / Normal distribution props models.

Covers:
- Over/under 180s count (Poisson)
- Checkout percentage over/under (Normal approximation)
- Calculate edge vs DK odds
"""

from __future__ import annotations

import math

try:
    from scipy.stats import poisson, norm
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


# ── 180s model ─────────────────────────────────────────────────────────────────

def prob_180s_over(
    expected_180s: float,
    line: float,
) -> float:
    """
    Probability of hitting MORE than `line` 180s using Poisson distribution.
    expected_180s: mu for Poisson (avg 180s for this player in a typical match).
    """
    if SCIPY_AVAILABLE:
        # P(X > line) = 1 - P(X <= floor(line))
        return float(1 - poisson.cdf(math.floor(line), mu=expected_180s))
    # Fallback: normal approximation
    std = math.sqrt(expected_180s)
    z = (line + 0.5 - expected_180s) / max(std, 0.01)
    return _normal_cdf_approx(-z)


def prob_180s_under(
    expected_180s: float,
    line: float,
) -> float:
    return 1.0 - prob_180s_over(expected_180s, line)


def expected_180s_in_match(
    avg_180s_per_leg: float,
    legs_to_win: int,
    expected_legs: float | None = None,
) -> float:
    """
    Estimate expected 180s in a full match.
    expected_legs: if None, uses simple heuristic (1.6 × legs_to_win).
    """
    if expected_legs is None:
        expected_legs = legs_to_win * 1.6
    return avg_180s_per_leg * expected_legs


# ── Checkout % model ───────────────────────────────────────────────────────────

def prob_checkout_over(
    player_checkout_pct: float,
    line_pct: float,
    sample_size: int = 20,
) -> float:
    """
    Probability player's checkout % exceeds `line_pct` using normal approx.
    Uses binomial std dev estimate.
    """
    std = math.sqrt(player_checkout_pct * (1 - player_checkout_pct) / sample_size)
    if SCIPY_AVAILABLE:
        return float(1 - norm.cdf(line_pct, loc=player_checkout_pct, scale=max(std, 0.001)))
    z = (line_pct - player_checkout_pct) / max(std, 0.001)
    return _normal_cdf_approx(-z)


# ── Edge calculation ───────────────────────────────────────────────────────────

def calculate_edge(
    model_prob: float,
    dk_american_odds: int,
) -> dict:
    """
    Calculate betting edge.
    Returns: {edge_pct, model_prob, dk_implied, expected_value, grade}.
    """
    if dk_american_odds < 0:
        dk_implied = (-dk_american_odds) / (-dk_american_odds + 100)
    else:
        dk_implied = 100 / (dk_american_odds + 100)

    edge_pct = (model_prob - dk_implied) * 100

    # Expected value per $100 bet
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


# ── Format variance ────────────────────────────────────────────────────────────

FORMAT_VARIANCE_TABLE: dict[tuple, float] = {
    (6, None): 0.33,
    (7, None): 0.30,
    (3, 5): 0.36,
    (3, 7): 0.28,
    (7, 6): 0.25,
}


def format_adjusted_probability(
    base_prob: float,
    legs_to_win: int,
    sets_to_win: int | None = None,
) -> float:
    """Compress/amplify skill gap based on format length."""
    if sets_to_win:
        total_sets = sets_to_win * 2 - 1
        skill_signal = (base_prob - 0.5) * (1 + total_sets / 20)
        return max(0.02, min(0.98, 0.5 + skill_signal))
    else:
        # Pure legs: shorter format = closer to 50%
        skill_signal = (base_prob - 0.5) * (0.6 + legs_to_win / 15)
        return max(0.02, min(0.98, 0.5 + skill_signal))


# ── Utility ────────────────────────────────────────────────────────────────────

def _normal_cdf_approx(z: float) -> float:
    """Abramowitz & Stegun approximation for normal CDF."""
    t = 1 / (1 + 0.2316419 * abs(z))
    d = 0.3989423 * math.exp(-0.5 * z * z)
    p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.7814779 + t * (-1.8212560 + t * 1.3302744))))
    if z >= 0:
        return 1 - p
    return p
