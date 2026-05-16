"""
models/elo.py — DartsElo rating system.

Supports:
- Tournament prestige K-multipliers
- Margin-of-victory adjustment
- American odds conversion
- Build from historical match records
"""

from __future__ import annotations

DEFAULT_K = 32
DEFAULT_RATING = 1500


class DartsElo:
    TOURNAMENT_K_MULTIPLIERS: dict[str, float] = {
        "world_championship": 1.5,
        "premier_league": 1.2,
        "world_matchplay": 1.3,
        "grand_slam": 1.3,
        "uk_open": 1.1,
        "players_championship_finals": 1.1,
        "world_grand_prix": 1.2,
        "european_championship": 1.1,
        "world_series_finals": 1.0,
        "players_championship": 0.7,
        "european_tour": 0.9,
    }

    def __init__(self, k: float = DEFAULT_K):
        self.k = k
        self.ratings: dict[str, float] = {}

    def get_rating(self, player: str) -> float:
        return self.ratings.get(player, DEFAULT_RATING)

    def expected_score(self, rating_a: float, rating_b: float) -> float:
        return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400))

    def update(
        self,
        winner: str,
        loser: str,
        winner_score: int,
        loser_score: int,
        legs_to_win: int,
        tournament_type: str = "players_championship",
    ) -> tuple[float, float]:
        ra = self.get_rating(winner)
        rb = self.get_rating(loser)
        ea = self.expected_score(ra, rb)

        max_legs = legs_to_win * 2 - 1
        mov_factor = 1.0 + (winner_score - loser_score) / max_legs * 0.3
        k_mult = self.TOURNAMENT_K_MULTIPLIERS.get(tournament_type, 1.0)
        effective_k = self.k * k_mult * mov_factor

        new_ra = ra + effective_k * (1 - ea)
        new_rb = rb + effective_k * (0 - (1 - ea))

        self.ratings[winner] = new_ra
        self.ratings[loser] = new_rb
        return new_ra, new_rb

    def win_probability(self, player_a: str, player_b: str) -> float:
        return self.expected_score(self.get_rating(player_a), self.get_rating(player_b))

    @staticmethod
    def to_american_odds(prob: float) -> int:
        prob = max(0.01, min(0.99, prob))
        if prob >= 0.5:
            return -round((prob / (1 - prob)) * 100)
        return round(((1 - prob) / prob) * 100)

    @staticmethod
    def to_decimal_odds(prob: float) -> float:
        prob = max(0.01, min(0.99, prob))
        return round(1 / prob, 2)

    @staticmethod
    def implied_prob_from_american(odds: int) -> float:
        if odds < 0:
            return (-odds) / (-odds + 100)
        return 100 / (odds + 100)

    def build_from_history(self, matches: list[dict]) -> None:
        """
        matches: list of dicts with keys:
          winner, loser, winner_score, loser_score, legs_to_win,
          tournament_type, match_date
        """
        sorted_matches = sorted(matches, key=lambda m: m["match_date"])
        for m in sorted_matches:
            self.update(
                m["winner"],
                m["loser"],
                m["winner_score"],
                m["loser_score"],
                m.get("legs_to_win", 6),
                m.get("tournament_type", "players_championship"),
            )

    def get_rankings(self, top_n: int = 50) -> list[tuple[str, float]]:
        return sorted(self.ratings.items(), key=lambda x: x[1], reverse=True)[:top_n]

    def calculate_edge(
        self,
        player_a: str,
        player_b: str,
        dk_odds: int,
    ) -> dict:
        """
        Calculate betting edge for player_a given DK American odds.
        Returns dict with edge_pct, model_prob, dk_implied.
        """
        model_prob = self.win_probability(player_a, player_b)
        dk_implied = self.implied_prob_from_american(dk_odds)
        edge_pct = (model_prob - dk_implied) * 100
        return {
            "model_prob": round(model_prob, 4),
            "dk_implied": round(dk_implied, 4),
            "edge_pct": round(edge_pct, 2),
            "fair_odds": self.to_american_odds(model_prob),
        }
