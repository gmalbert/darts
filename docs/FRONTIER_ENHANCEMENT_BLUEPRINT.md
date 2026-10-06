# Frontier Enhancement Blueprint

The existing docs already cover data seeding, conventional rating/models, odds, product design, SEO, and compliance. These proposals move from match-level summaries toward throw-state and decision-quality modeling.

## Model additions

### Leg-state win probability

Model each visit using score remaining, darts in hand, thrower, set/leg state, checkout route, and recent scoring distribution. A hierarchical model should partially pool players with sparse televised histories.

```python
def visit_features(score, opp_score, darts_left, on_throw, set_diff):
    return {
        "score": score, "opp_score": opp_score,
        "checkout_available": int(score <= 170 and score not in {169, 168, 166, 165, 163, 162, 159}),
        "darts_left": darts_left, "on_throw": int(on_throw), "set_diff": set_diff,
    }
```

Add a checkout-policy model comparing intended routes with realized outcomes; use it for simulation, not to label player decisions as mistakes without route data. Couple this with fatigue/travel, match format, stage pressure, and opponent-adjusted rolling form.

## Data additions

- Visit/throw sequences with source and correction history.
- Tournament format, board/venue, stage, start time, travel distance, and rest.
- Player handedness/throw speed where reliably available.
- Timestamped odds at open, intermediate snapshots, and close.
- Identity registry for aliases and stable player IDs.

Store `event_time` and `available_time`; late score corrections must not enter historical predictions.

## Product additions

- Interactive leg simulator and checkout-route explorer.
- Live win-probability chart with important visits annotated.
- “Why uncertain” panel for sparse players and format changes.
- Opponent-style matchup card: scoring bursts, doubles, checkout pressure, pace.
- Accessible score display with text labels independent of red/green.

## Evaluation gates

Use tournament-forward validation. Report log loss and calibration at match, set, leg, and visit level; performance by format, stage, player-history depth, and odds band; and CLV after price availability checks. Benchmark against Elo and market-implied probabilities. Do not promote live features unless timestamps prove they were available before each state prediction.
