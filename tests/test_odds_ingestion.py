"""
darts/tests/test_odds_ingestion.py — Tests for American-odds implied probability
conversion and the odds ingestion helper logic used by scrapers/odds_api.py.
"""

import pytest


# ── Utility functions mirroring scrapers/odds_api.py helpers ─────────────────

def american_to_implied(odds: int) -> float:
    """Convert American moneyline to implied probability."""
    if odds > 0:
        return 100.0 / (odds + 100)
    return abs(odds) / (abs(odds) + 100)


def remove_vig(p1_raw: float, p2_raw: float) -> tuple[float, float]:
    """Remove bookmaker margin (vig) from two-way market."""
    total = p1_raw + p2_raw
    return p1_raw / total, p2_raw / total


def is_valid_match_odds(p1_odds: int, p2_odds: int) -> bool:
    """Check that a two-sided market has valid non-zero odds."""
    if p1_odds == 0 or p2_odds == 0:
        return False
    p1 = american_to_implied(p1_odds)
    p2 = american_to_implied(p2_odds)
    # Vig market must over-round (>1.0 total implied) for favourites, or be valid
    return 0 < p1 < 1 and 0 < p2 < 1


# ── Implied probability tests ─────────────────────────────────────────────────

class TestAmericanToImplied:

    def test_even_money(self):
        assert abs(american_to_implied(-100) - 0.5) < 0.001

    def test_minus_140(self):
        prob = american_to_implied(-140)
        assert abs(prob - 0.5833) < 0.001

    def test_plus_120(self):
        prob = american_to_implied(120)
        assert abs(prob - 0.4545) < 0.001

    def test_result_in_01(self):
        for odds in [-500, -200, -110, -100, 100, 110, 200, 500]:
            p = american_to_implied(odds)
            assert 0 < p < 1, f"Implied prob {p} out of (0,1) for odds {odds}"


# ── Vig removal tests ─────────────────────────────────────────────────────────

class TestRemoveVig:

    def test_symmetric_market(self):
        # Both players at -110: raw implied = 52.38% each, sums to 104.76%
        raw = american_to_implied(-110)
        p1, p2 = remove_vig(raw, raw)
        assert abs(p1 - 0.5) < 0.001
        assert abs(p2 - 0.5) < 0.001

    def test_no_vig_sum_to_one(self):
        p1_raw = american_to_implied(-140)
        p2_raw = american_to_implied(120)
        p1, p2 = remove_vig(p1_raw, p2_raw)
        assert abs(p1 + p2 - 1.0) < 1e-9

    def test_favourite_higher_after_vig(self):
        p1_raw = american_to_implied(-200)  # heavy favourite
        p2_raw = american_to_implied(170)   # underdog
        p1, p2 = remove_vig(p1_raw, p2_raw)
        assert p1 > p2


# ── Match validity tests ──────────────────────────────────────────────────────

class TestMatchOddsValidation:

    def test_valid_match(self):
        assert is_valid_match_odds(-140, 120) is True

    def test_zero_odds_invalid(self):
        assert is_valid_match_odds(0, -110) is False

    def test_both_zero_invalid(self):
        assert is_valid_match_odds(0, 0) is False

    def test_valid_even_market(self):
        assert is_valid_match_odds(-110, -110) is True

    def test_extreme_favourite_valid(self):
        assert is_valid_match_odds(-800, 600) is True


# ── OddsSnapshot persistence ──────────────────────────────────────────────────

class TestOddsSnapshotPersistence:
    """Test that odds are stored correctly in the database."""

    def test_save_and_retrieve_odds(self, session, upcoming_match):
        from db.schema import OddsSnapshot

        p1_raw = american_to_implied(-140)
        p2_raw = american_to_implied(120)
        p1_nv, p2_nv = remove_vig(p1_raw, p2_raw)

        snap = OddsSnapshot(
            match_id=upcoming_match.id,
            p1_odds=-140,
            p2_odds=120,
            p1_implied=round(p1_nv, 4),
            p2_implied=round(p2_nv, 4),
            book="DraftKings",
        )
        session.add(snap)
        session.flush()

        loaded = session.query(OddsSnapshot).filter_by(id=snap.id).first()
        assert loaded is not None
        assert loaded.p1_odds == -140
        assert abs(loaded.p1_implied + loaded.p2_implied - 1.0) < 0.001

    def test_implied_probs_sum_to_one_after_vig(self, session, upcoming_match):
        from db.schema import OddsSnapshot

        p1_raw = american_to_implied(-110)
        p2_raw = american_to_implied(-110)
        p1_nv, p2_nv = remove_vig(p1_raw, p2_raw)

        snap = OddsSnapshot(
            match_id=upcoming_match.id,
            p1_odds=-110,
            p2_odds=-110,
            p1_implied=p1_nv,
            p2_implied=p2_nv,
        )
        session.add(snap)
        session.flush()
        assert abs(snap.p1_implied + snap.p2_implied - 1.0) < 1e-6
