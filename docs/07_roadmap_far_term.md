# 07 — Far-Term Roadmap (Months 4–24)

## Month 4–6: Live & Monetization

### Live Scoring During Events

When there's a live PDC event (Premier League runs 16 weeks, Worlds runs 4 weeks), live pages are the highest-traffic pages. Build this before your first major event.

```python
# apps/api/jobs/live_event_detector.py
from datetime import date, timedelta
from db import get_tournaments_in_range

async def is_live_event_today() -> bool:
    """
    Check if any DK-covered tournament has matches today.
    Used to gate expensive live polling.
    """
    today = date.today()
    active = await get_tournaments_in_range(today, today)
    return len(active) > 0

async def get_todays_schedule() -> list[dict]:
    """Return today's scheduled matches from DB + live status from dartsdata."""
    scheduled = await get_scheduled_matches(date.today())
    live = get_live_matches()  # from dartsdata.com API

    # Merge: mark scheduled matches as live if they appear in live feed
    live_ids = {m['id'] for m in live}
    for match in scheduled:
        match['is_live'] = match.get('external_id') in live_ids
        if match['is_live']:
            live_match = next(m for m in live if m['id'] == match['external_id'])
            match['live_score1'] = live_match.get('score1')
            match['live_score2'] = live_match.get('score2')
    return scheduled
```

### Monetization Stack

```
Revenue streams (priority order):

1. DraftKings affiliate (CPA/RevShare)
   - Apply: draftkings.com/affiliates (or via Impact.com)
   - CPA: ~$200-400 per qualified depositor
   - RevShare: 20-35% of player losses (ongoing)
   - Better to start CPA, switch to RevShare once you have volume

2. Display ads (Mediavine/Raptive threshold: 50k sessions/mo)
   - Use Google AdSense until you hit that threshold
   - Sports analytics sites typically earn $8-15 RPM

3. Other sportsbook affiliates
   - FanDuel (also covers darts)
   - BetMGM
   - Caesars
   - Never show competing DK and FanDuel banners on same page — pick one as primary

4. Premium tier ($9.99/mo) — Month 12+
   - Earlier picks (12 hours before public)
   - Kelly sizing recommendations
   - Email alerts for high-edge picks
   - API access
```

```tsx
// Affiliate link management — centralized so you can A/B test
// apps/web/src/lib/affiliates.ts

const AFFILIATES = {
  draftkings: {
    base: 'https://sportsbook.draftkings.com',
    tag: process.env.NEXT_PUBLIC_DK_AFFILIATE_ID,
    buildUrl: (path: string, tag: string) =>
      `https://sportsbook.draftkings.com${path}?wpcid=${tag}`,
  },
  fanduel: {
    base: 'https://sportsbook.fanduel.com',
    tag: process.env.NEXT_PUBLIC_FD_AFFILIATE_ID,
    buildUrl: (path: string, tag: string) =>
      `https://sportsbook.fanduel.com${path}?pid=${tag}`,
  },
}

export function buildAffiliateUrl(
  book: 'draftkings' | 'fanduel',
  path: string = '/sports/darts',
): string {
  const aff = AFFILIATES[book]
  return aff.buildUrl(path, aff.tag ?? '')
}

// Track clicks to attribute conversions
export async function trackAffiliateClick(book: string, page: string, matchId?: string) {
  await fetch('/api/track', {
    method: 'POST',
    body: JSON.stringify({ event: 'affiliate_click', book, page, matchId }),
  })
}
```

---

## Month 6–9: Improved Models & Props

### XGBoost Ensemble

Once you have enough fresh data (1+ year of your own odds snapshots), upgrade the match predictor.

```python
# models/xgboost_predictor.py
import xgboost as xgb
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.calibration import CalibratedClassifierCV
import optuna

class XGBDartsPredictor:
    def __init__(self):
        self.model = None
        self.scaler = None

    def tune_hyperparams(self, X_train, y_train, n_trials: int = 50):
        """Use Optuna to find best XGBoost params via time-series CV."""
        def objective(trial):
            params = {
                'max_depth': trial.suggest_int('max_depth', 3, 8),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'n_estimators': trial.suggest_int('n_estimators', 50, 500),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
            }
            model = xgb.XGBClassifier(**params, eval_metric='logloss', use_label_encoder=False)
            tscv = TimeSeriesSplit(n_splits=5)
            scores = []
            for train_idx, val_idx in tscv.split(X_train):
                model.fit(X_train[train_idx], y_train[train_idx])
                prob = model.predict_proba(X_train[val_idx])[:, 1]
                brier = np.mean((prob - y_train[val_idx]) ** 2)
                scores.append(brier)
            return np.mean(scores)

        study = optuna.create_study(direction='minimize')
        study.optimize(objective, n_trials=n_trials)
        return study.best_params

    def train(self, X, y, tune: bool = True):
        from sklearn.preprocessing import StandardScaler
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        best_params = self.tune_hyperparams(X_scaled, y) if tune else {}
        base = xgb.XGBClassifier(**best_params, eval_metric='logloss', use_label_encoder=False)
        self.model = CalibratedClassifierCV(base, method='isotonic', cv=5)
        self.model.fit(X_scaled, y)

    def feature_importance(self) -> dict:
        """Which features drive the model most."""
        base = self.model.estimator
        return dict(zip(FEATURE_NAMES, base.feature_importances_))
```

### Checkout % Prop Model

```python
# models/checkout_prop.py
import numpy as np
from scipy.stats import norm

def checkout_over_under_edge(
    player_checkout_history: list[float],  # match-by-match checkout %
    dk_line: float,                         # DraftKings over/under line e.g. 42.5
    dk_over_odds: int,
    dk_under_odds: int,
) -> dict:
    """
    Model player's checkout % as normally distributed around recent mean.
    Compare to DK line for edge.
    """
    recent = player_checkout_history[-15:]  # last 15 matches
    mu = np.mean(recent)
    sigma = np.std(recent)

    if sigma < 0.01:
        sigma = 0.05  # floor to avoid degenerate distributions

    # Probability player beats the line
    prob_over = 1 - norm.cdf(dk_line / 100, loc=mu, scale=sigma)
    prob_under = 1 - prob_over

    edge_over = calculate_edge(prob_over, dk_over_odds)
    edge_under = calculate_edge(prob_under, dk_under_odds)

    return {
        'model_mean_checkout': round(mu * 100, 1),
        'model_std': round(sigma * 100, 1),
        'line': dk_line,
        'prob_over': round(prob_over, 4),
        'prob_under': round(prob_under, 4),
        'edge_over': edge_over,
        'edge_under': edge_under,
        'best_bet': 'over' if edge_over['edge'] > edge_under['edge'] else 'under',
    }
```

---

## Month 9–12: User Accounts & Alerts

### Email Alerts for High-Edge Picks

```python
# jobs/alert_sender.py
import resend  # Resend.com — generous free tier, great deliverability
import os

resend.api_key = os.getenv("RESEND_API_KEY")

def send_pick_alert(subscribers: list[str], pick: dict):
    """Send a pick alert email when edge > 5%."""
    html = f"""
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
      <h2 style="color: #f0a500;">🎯 High-Edge Pick Alert</h2>
      <p><strong>{pick['player']}</strong> to beat {pick['opponent']}</p>
      <table style="width:100%; border-collapse:collapse;">
        <tr>
          <td style="color:#888; padding:4px 0;">Tournament</td>
          <td style="text-align:right;">{pick['tournament']}</td>
        </tr>
        <tr>
          <td style="color:#888; padding:4px 0;">DraftKings odds</td>
          <td style="text-align:right; font-family:monospace;">{pick['dk_odds']:+d}</td>
        </tr>
        <tr>
          <td style="color:#888; padding:4px 0;">Model probability</td>
          <td style="text-align:right;">{pick['our_prob']*100:.1f}%</td>
        </tr>
        <tr>
          <td style="color:#888; padding:4px 0;"><strong>Edge</strong></td>
          <td style="text-align:right; color:#3fb950; font-weight:bold;">+{pick['edge_pct']:.1f}%</td>
        </tr>
      </table>
      <a href="{pick['match_url']}" style="display:block; margin-top:16px; background:#f0a500;
         color:#000; text-align:center; padding:10px; border-radius:6px; text-decoration:none;
         font-weight:bold;">View Full Analysis</a>
      <p style="color:#888; font-size:11px; margin-top:24px;">
        This is a model output, not financial advice. Bet responsibly.
        <a href="{{unsubscribe_url}}">Unsubscribe</a>
      </p>
    </div>
    """

    resend.Emails.send({
        "from": "picks@yourdomain.com",
        "to": subscribers,
        "subject": f"🎯 {pick['player']} +{pick['edge_pct']:.1f}% edge — {pick['tournament']}",
        "html": html,
    })
```

### Bet Tracker (User Accounts)

```prisma
// Add to schema.prisma
model User {
  id        String   @id @default(cuid())
  email     String   @unique
  createdAt DateTime @default(now())
  tier      String   @default("free")  // 'free' | 'pro'
  bets      Bet[]
  alerts    AlertSubscription[]
}

model Bet {
  id         String   @id @default(cuid())
  userId     String
  user       User     @relation(fields: [userId], references: [id])
  matchId    Int
  pickedSide String   // player name
  odds       Int
  stake      Decimal  @db.Decimal(10, 2)
  result     String?  // 'win' | 'loss' | 'push' | null (pending)
  profit     Decimal? @db.Decimal(10, 2)
  createdAt  DateTime @default(now())
}

model AlertSubscription {
  id        String  @id @default(cuid())
  userId    String
  user      User    @relation(fields: [userId], references: [id])
  minEdge   Decimal @default(0.05)  // only alert if edge > X
  active    Boolean @default(true)
}
```

---

## Month 12–18: Scale & Public API

### Public API (rate-limited, free tier)

Expose a limited API so other developers can build on your data. This drives backlinks, press, and community.

```python
# apps/api/routers/public_api.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi_limiter.depends import RateLimiter

router = APIRouter(prefix="/public/v1", tags=["Public API"])

# Free tier: 100 requests/hour
@router.get("/players/{slug}", dependencies=[Depends(RateLimiter(times=100, hours=1))])
async def get_player(slug: str):
    player = await fetch_player(slug)
    if not player:
        raise HTTPException(404, "Player not found")
    return {
        "name": player.name,
        "nationality": player.nationality,
        "elo": player.current_elo,
        "avg_3dart_career": player.career_avg,
        "avg_3dart_last20": player.avg_last20,
        "checkout_pct": player.checkout_pct,
        "_source": "yourdomain.com",
    }

@router.get("/matches/upcoming", dependencies=[Depends(RateLimiter(times=60, hours=1))])
async def upcoming_matches(tournament: str | None = None):
    matches = await fetch_upcoming(tournament_filter=tournament)
    return [
        {
            "id": m.id,
            "tournament": m.tournament.name,
            "round": m.round,
            "player1": m.player1.name,
            "player2": m.player2.name,
            "match_date": m.match_date.isoformat() if m.match_date else None,
        }
        for m in matches[:50]
    ]
```

---

## Month 18–24: Advanced Features

| Feature | Notes |
|---------|-------|
| **In-play model** | Markov chain per-leg model. Requires real-time leg scores — expensive data feed or aggressive dartsdata.com polling. High ceiling. |
| **Bracket simulator** | Monte Carlo sim for World Championship — show expected probability of each player reaching each round. High SEO value, shareable. |
| **Fantasy darts integration** | DraftKings offers DFS for darts during Worlds. Project points using 3-dart avg + 180s rate. Completely different monetization angle. |
| **Podcast / video** | Tournament preview content drives email list growth and brand recognition. |
| **Discord community** | Discord server for model discussion. Moderate engagement carefully. |
| **Mobile app** | React Native with Expo. Primarily useful for push notifications during live events. |

### Bracket Simulator (Monte Carlo)

```python
# models/bracket_simulator.py
import random
from typing import List
from models.elo import DartsElo

def simulate_tournament(
    entrants: List[str],  # ordered by seeding
    elo: DartsElo,
    n_simulations: int = 10000,
) -> dict[str, dict[str, float]]:
    """
    Returns probability of each player reaching each round.
    entrants: list of player names, seeded 1 through N.
    """
    results = {p: {'r1': 0, 'qf': 0, 'sf': 0, 'f': 0, 'w': 0} for p in entrants}

    for _ in range(n_simulations):
        remaining = list(entrants)
        round_name = 'r1'

        while len(remaining) > 1:
            next_round = []
            random.shuffle(remaining)  # simplified — real draw is structured

            for i in range(0, len(remaining), 2):
                p1 = remaining[i]
                p2 = remaining[i + 1] if i + 1 < len(remaining) else None
                if p2 is None:
                    next_round.append(p1)
                    continue

                prob_p1 = elo.win_probability(p1, p2)
                winner = p1 if random.random() < prob_p1 else p2
                next_round.append(winner)

                if round_name == 'r1':
                    results[p1]['r1'] += 1
                    results[p2]['r1'] += 1
                elif round_name == 'qf':
                    results[winner]['qf'] += 1
                # etc.

            remaining = next_round
            round_name = {'r1': 'qf', 'qf': 'sf', 'sf': 'f', 'f': 'w'}.get(round_name, 'w')

        results[remaining[0]]['w'] += 1

    # Normalize to probabilities
    for player in results:
        for rd in results[player]:
            results[player][rd] /= n_simulations

    return results
```
