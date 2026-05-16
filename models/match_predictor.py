"""
models/match_predictor.py — Logistic regression match predictor.

Features:
- Elo differential
- Recent form differential (win rate last 20)
- 3-dart average differential
- Checkout % differential
- 180s per leg differential
- H2H record (last 10)
- PDC ranking differential
- Format indicator (sets vs legs)
- Crowd advantage
"""

from __future__ import annotations

import numpy as np
import joblib
from pathlib import Path

try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.calibration import CalibratedClassifierCV
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

MODEL_PATH = Path(__file__).parent / "match_predictor.pkl"

PLAYER_CROWD_CITIES: dict[str, list[str]] = {
    "Luke Littler": ["Manchester", "Liverpool"],
    "Gerwyn Price": ["Cardiff", "Exeter"],
    "Gary Anderson": ["Aberdeen", "Edinburgh"],
    "Peter Wright": ["Edinburgh"],
    "Jonny Clayton": ["Cardiff"],
}


def crowd_advantage(player: str, venue_city: str) -> float:
    home_cities = PLAYER_CROWD_CITIES.get(player, [])
    return 1.0 if venue_city in home_cities else 0.0


class DartsMatchPredictor:
    """
    Logistic regression with calibrated probabilities.
    Falls back to Elo-only if sklearn not available or model not trained.
    """

    def __init__(self):
        if SKLEARN_AVAILABLE:
            self.model = CalibratedClassifierCV(
                LogisticRegression(C=1.0, max_iter=1000),
                method="isotonic",
                cv=5,
            )
            self.scaler = StandardScaler()
        self.trained = False

    def build_features(self, match: dict, stats_cache: dict) -> np.ndarray:
        p1 = match.get("player1", "")
        p2 = match.get("player2", "")
        s1 = stats_cache.get(p1, {})
        s2 = stats_cache.get(p2, {})

        features = [
            s1.get("elo", 1500) - s2.get("elo", 1500),
            s1.get("win_rate_last20", 0.5) - s2.get("win_rate_last20", 0.5),
            s1.get("avg_3dart", 85) - s2.get("avg_3dart", 85),
            s1.get("checkout_pct", 0.4) - s2.get("checkout_pct", 0.4),
            s1.get("avg_180s_per_leg", 0.1) - s2.get("avg_180s_per_leg", 0.1),
            s1.get(f"win_rate_{match.get('tournament_type', '')}", 0.5)
            - s2.get(f"win_rate_{match.get('tournament_type', '')}", 0.5),
            match.get("h2h_p1_wins_last10", 5) / 10,
            s2.get("pdc_ranking", 50) - s1.get("pdc_ranking", 50),
            1 if match.get("format") == "sets" else 0,
            match.get("month", 6),
        ]
        return np.array(features, dtype=float)

    def train(self, match_rows: list[dict], stats_cache: dict) -> None:
        if not SKLEARN_AVAILABLE:
            return
        X, y = [], []
        for m in match_rows:
            feat = self.build_features(m, stats_cache)
            X.append(feat)
            y.append(1 if m.get("winner") == m.get("player1") else 0)

        X_arr = np.array(X)
        y_arr = np.array(y)

        # Need both classes
        if len(np.unique(y_arr)) < 2 or len(X_arr) < 20:
            return

        X_scaled = self.scaler.fit_transform(X_arr)
        self.model.fit(X_scaled, y_arr)
        self.trained = True
        joblib.dump({"model": self.model, "scaler": self.scaler}, MODEL_PATH)

    def load(self) -> bool:
        if MODEL_PATH.exists():
            data = joblib.load(MODEL_PATH)
            self.model = data["model"]
            self.scaler = data["scaler"]
            self.trained = True
            return True
        return False

    def predict_proba(self, match: dict, stats_cache: dict) -> float:
        """Return probability that player1 wins. Falls back to Elo if untrained."""
        if not self.trained or not SKLEARN_AVAILABLE:
            # Elo-only fallback
            s1 = stats_cache.get(match.get("player1", ""), {})
            s2 = stats_cache.get(match.get("player2", ""), {})
            elo_diff = s1.get("elo", 1500) - s2.get("elo", 1500)
            return 1.0 / (1.0 + 10 ** (-elo_diff / 400))

        feat = self.build_features(match, stats_cache)
        feat_scaled = self.scaler.transform(feat.reshape(1, -1))
        return float(self.model.predict_proba(feat_scaled)[0][1])
