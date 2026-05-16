# 02 — Predictive Models & Betting Edge

## Model Philosophy

Darts is unusually model-friendly because:
- Head-to-head history is long and well-recorded
- Performance stats (3-dart avg, checkout %) are stable over time
- Venue/crowd effects are measurable (crowd favorites vs traveling players)
- Format variance matters — legs-only vs sets formats change upset probability

Build **three layers**: a baseline rating model, a match-level prediction model, and a props/markets model.

---

## Layer 1 — Elo-Style Player Rating

Start here. Simple, interpretable, good enough to find edge on most markets.

```python
# models/elo.py
from typing import Optional
import math

DEFAULT_K = 32
DEFAULT_RATING = 1500

class DartsElo:
    """
    Standard Elo with adjustments for:
    - Tournament prestige (world champ match matters more than floor event)
    - Format length (best-of-13 legs vs best-of-7 — longer = lower K)
    - Margin of victory (winning 7-0 vs 7-6 updates rating more/less)
    """
    
    TOURNAMENT_K_MULTIPLIERS = {
        "world_championship": 1.5,
        "premier_league": 1.2,
        "world_matchplay": 1.3,
        "grand_slam": 1.3,
        "uk_open": 1.1,
        "players_championship_finals": 1.1,
        "world_grand_prix": 1.2,
        "european_tour": 0.9,
        "players_championship": 0.7,
        "world_series": 1.0,
    }
    
    def __init__(self, k: float = DEFAULT_K):
        self.k = k
        self.ratings: dict[str, float] = {}
    
    def get_rating(self, player: str) -> float:
        return self.ratings.get(player, DEFAULT_RATING)
    
    def expected_score(self, rating_a: float, rating_b: float) -> float:
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    
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
        
        # Margin of victory multiplier
        total_legs = winner_score + loser_score
        max_legs = legs_to_win * 2 - 1
        mov_factor = 1 + (winner_score - loser_score) / max_legs * 0.3
        
        # Tournament weight
        k_mult = self.TOURNAMENT_K_MULTIPLIERS.get(tournament_type, 1.0)
        effective_k = self.k * k_mult * mov_factor
        
        new_ra = ra + effective_k * (1 - ea)
        new_rb = rb + effective_k * (0 - (1 - ea))
        
        self.ratings[winner] = new_ra
        self.ratings[loser] = new_rb
        
        return new_ra, new_rb
    
    def win_probability(self, player_a: str, player_b: str) -> float:
        return self.expected_score(self.get_rating(player_a), self.get_rating(player_b))
    
    def to_american_odds(self, prob: float) -> int:
        """Convert probability to American moneyline odds."""
        if prob >= 0.5:
            return -round((prob / (1 - prob)) * 100)
        else:
            return round(((1 - prob) / prob) * 100)
    
    def build_from_history(self, matches: list[dict]):
        """
        matches: list of dicts with keys:
          winner, loser, winner_score, loser_score, legs_to_win, tournament_type, match_date
        Sort by date before calling.
        """
        sorted_matches = sorted(matches, key=lambda m: m["match_date"])
        for m in sorted_matches:
            self.update(
                m["winner"], m["loser"],
                m["winner_score"], m["loser_score"],
                m["legs_to_win"],
                m.get("tournament_type", "players_championship"),
            )
    
    def get_rankings(self, top_n: int = 50) -> list[tuple[str, float]]:
        sorted_players = sorted(self.ratings.items(), key=lambda x: x[1], reverse=True)
        return sorted_players[:top_n]
```

---

## Layer 2 — Match Prediction Model (Logistic Regression + Features)

Elo alone misses form, venue, and stat-based signals. Add a feature-rich model.

```python
# models/match_predictor.py
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.calibration import CalibratedClassifierCV
import joblib

class DartsMatchPredictor:
    """
    Logistic regression with calibrated probabilities.
    Use calibrated probs (not raw), since we're comparing against bookmaker lines.
    """
    
    def __init__(self):
        self.model = CalibratedClassifierCV(
            LogisticRegression(C=1.0, max_iter=1000),
            method="isotonic",
            cv=5,
        )
        self.scaler = StandardScaler()
        self.feature_names = []
    
    def build_features(self, match: dict, stats_cache: dict) -> np.ndarray:
        """
        Build feature vector for a match.
        stats_cache: {player_name: {avg_3dart, checkout_pct, avg_180s, win_rate_last20, ...}}
        """
        p1 = match["player1"]
        p2 = match["player2"]
        s1 = stats_cache.get(p1, {})
        s2 = stats_cache.get(p2, {})
        
        features = [
            # Elo-derived
            s1.get("elo", 1500) - s2.get("elo", 1500),
            
            # Recent form (last 20 matches)
            s1.get("win_rate_last20", 0.5) - s2.get("win_rate_last20", 0.5),
            
            # Performance stats differential
            s1.get("avg_3dart", 85) - s2.get("avg_3dart", 85),
            s1.get("checkout_pct", 0.4) - s2.get("checkout_pct", 0.4),
            s1.get("avg_180s_per_leg", 0.1) - s2.get("avg_180s_per_leg", 0.1),
            
            # Tournament-specific win rates
            s1.get(f"win_rate_{match['tournament_type']}", 0.5) -
            s2.get(f"win_rate_{match['tournament_type']}", 0.5),
            
            # H2H record (last 10 meetings)
            match.get("h2h_p1_wins_last10", 5) / 10,
            
            # Seeding/ranking
            s2.get("pdc_ranking", 50) - s1.get("pdc_ranking", 50),  # lower rank = better
            
            # Format indicator (sets vs legs)
            1 if match.get("format") == "sets" else 0,
            
            # Month (seasonal form)
            match.get("month", 6),
        ]
        
        return np.array(features, dtype=float)
    
    def train(self, match_rows: list[dict], stats_cache: dict):
        X = []
        y = []
        for m in match_rows:
            feat = self.build_features(m, stats_cache)
            X.append(feat)
            y.append(1 if m["winner"] == m["player1"] else 0)
        
        X = np.array(X)
        y = np.array(y)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
    
    def predict_proba(self, match: dict, stats_cache: dict) -> float:
        """Returns probability that player1 wins."""
        feat = self.build_features(match, stats_cache).reshape(1, -1)
        feat_scaled = self.scaler.transform(feat)
        return self.model.predict_proba(feat_scaled)[0][1]
    
    def save(self, path: str = "models/match_predictor.pkl"):
        joblib.dump({"model": self.model, "scaler": self.scaler}, path)
    
    @classmethod
    def load(cls, path: str = "models/match_predictor.pkl"):
        obj = cls()
        data = joblib.load(path)
        obj.model = data["model"]
        obj.scaler = data["scaler"]
        return obj
```

---

## Layer 3 — Props Model (180s, Checkout %, High Checkout)

DraftKings offers prop-like markets on 180s and checkouts for major events. These are highly modelable.

```python
# models/props_model.py
import numpy as np
from scipy import stats
from scipy.stats import poisson

class PropsModels:
    
    @staticmethod
    def expected_180s(
        player_avg_180s_per_leg: float,
        legs_expected: float,
    ) -> float:
        """
        Expected 180s in a match.
        legs_expected: use (legs_to_win * 2 - 1) * 0.65 as a rough estimate
        since most matches don't go the distance.
        """
        return player_avg_180s_per_leg * legs_expected
    
    @staticmethod
    def prob_over_total_180s(
        p1_rate: float,  # 180s per leg
        p2_rate: float,
        expected_legs: float,
        total_line: float,
    ) -> float:
        """
        Probability that combined 180s exceed the DraftKings total line.
        Combined rate is p1 + p2 per leg, modeled as Poisson.
        """
        combined_rate = (p1_rate + p2_rate) * expected_legs
        # P(X > total_line) = 1 - P(X <= floor(total_line))
        return 1 - poisson.cdf(int(total_line), mu=combined_rate)
    
    @staticmethod
    def expected_checkout_pct(
        player_checkout_history: list[float],  # last N match checkout %s
        window: int = 10,
    ) -> tuple[float, float]:
        """Returns (mean, std) of checkout % over recent window."""
        recent = player_checkout_history[-window:]
        return np.mean(recent), np.std(recent)
    
    @staticmethod
    def high_checkout_prob(
        player_avg: float,  # 3-dart average
        checkout_pct: float,
        target_checkout: int = 100,
        legs_remaining: int = 10,
    ) -> float:
        """
        Rough probability of hitting a checkout >= target in the remaining legs.
        Higher avg + checkout_pct = more shots at high checkouts.
        """
        # Empirically: players averaging 95+ hit 100+ checkouts ~18% of legs they finish
        # Scale roughly linearly with avg above 85
        base_rate = max(0, (player_avg - 80) / 300) * checkout_pct
        prob_at_least_once = 1 - (1 - base_rate) ** legs_remaining
        return min(prob_at_least_once, 0.95)


# Edge calculator — the core of the betting tool
def calculate_edge(
    our_prob: float,
    dk_american_odds: int,
    kelly_fraction: float = 0.25,  # fractional kelly for safety
) -> dict:
    """
    Given our model probability and DraftKings' line,
    calculate the implied probability, edge, and Kelly bet size.
    """
    # DK implied probability (including vig)
    if dk_american_odds > 0:
        dk_prob = 100 / (dk_american_odds + 100)
    else:
        dk_prob = abs(dk_american_odds) / (abs(dk_american_odds) + 100)
    
    edge = our_prob - dk_prob
    
    # Kelly criterion
    if dk_american_odds > 0:
        b = dk_american_odds / 100
    else:
        b = 100 / abs(dk_american_odds)
    
    kelly = (b * our_prob - (1 - our_prob)) / b
    kelly_bet = max(0, kelly * kelly_fraction)  # never negative
    
    return {
        "our_prob": round(our_prob, 4),
        "dk_prob": round(dk_prob, 4),
        "edge": round(edge, 4),
        "edge_pct": round(edge * 100, 2),
        "kelly_full": round(kelly, 4),
        "kelly_quarter": round(kelly_bet, 4),
        "has_edge": edge > 0.02,  # only flag if edge > 2%
        "dk_odds": dk_american_odds,
    }
```

---

## Model Validation & Backtesting

```python
# models/backtester.py
import pandas as pd
import numpy as np

def backtest_model(predictor, matches: list[dict], stats_cache: dict) -> dict:
    """
    Walk-forward backtest — train on history up to each match, predict forward.
    Matches must be sorted by date.
    """
    results = []
    
    for i in range(100, len(matches)):  # need at least 100 matches to train
        train = matches[:i]
        test = matches[i]
        
        predictor.train(train, stats_cache)
        prob = predictor.predict_proba(test, stats_cache)
        actual = 1 if test["winner"] == test["player1"] else 0
        
        results.append({
            "match_date": test["match_date"],
            "predicted_prob": prob,
            "actual": actual,
            "correct": (prob > 0.5) == bool(actual),
        })
    
    df = pd.DataFrame(results)
    
    # Brier score (lower = better calibration)
    brier = np.mean((df["predicted_prob"] - df["actual"]) ** 2)
    
    # Accuracy
    accuracy = df["correct"].mean()
    
    # ROI if betting when edge > threshold
    def roi_at_threshold(threshold_edge: float, dk_odds_col: str = "dk_odds") -> float:
        # Simplified — assumes flat $100 bets
        # In production, join with actual DK odds
        return 0.0  # fill in once you have odds data
    
    return {
        "brier_score": round(brier, 4),
        "accuracy": round(accuracy, 4),
        "n_predictions": len(df),
        "calibration_by_bucket": calibration_curve(df),
    }

def calibration_curve(df: pd.DataFrame) -> list[dict]:
    """Check if predicted 60% really wins 60% of the time."""
    df["bucket"] = pd.cut(df["predicted_prob"], bins=10)
    grouped = df.groupby("bucket")["actual"].agg(["mean", "count"]).reset_index()
    return grouped.to_dict("records")
```

---

## Recommended Model Stack (Priority Order)

| Model | Use For | Complexity | Value |
|-------|---------|-----------|-------|
| Elo (vanilla) | All match picks, quick display | Low | High |
| Elo (tournament-weighted) | Tournament winner futures | Low | High |
| Logistic regression | Match prediction with features | Medium | High |
| Poisson (180s) | Over/under 180s prop | Medium | High |
| Poisson (legs) | Match totals | Medium | Medium |
| Gradient boosting (XGBoost) | Full feature ensemble | High | Medium |
| Markov chain (in-leg) | In-play / live betting | Very High | Low (start) |

Start with Elo + Poisson for 180s. That covers ~80% of DraftKings darts markets.
