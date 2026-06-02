# BullzIQ — Model Suggested Enhancements

## Priority 1: Elo Model Improvements

### Surface/Format Weighting
- PDC events use legs-only, sets-based, or mixed formats. A player who excels in long-format sets (World Championship) may underperform in short sprint-format events.
- Add a `format_adjustment` multiplier to Elo updates: weight more heavily for formats where the player has more history.

### Recent Form Decay
- Current Elo does not decay form. Players in multi-week streaks should have a short-term momentum modifier.
- Add a `momentum_score` (exponentially weighted win% over last 10 matches) as a secondary signal.

### Head-to-Head Elo Overlay
- When two players have ≥8 career meetings, blend the global Elo with an H2H Elo sub-rating.

## Priority 2: Statistical Features

### 3-Dart Average Trend
- `avg_3dart` is stored as a static figure. Add rolling 5-match average: `avg_3dart_l5` and `avg_3dart_vs_top20` (against ranked opponents only).

### Checkout Percentage in Pressure
- Track checkout % in finals and semi-finals separately from group stage. High-pressure checkout % is more predictive for major tournaments.

### Double Hit Rate
- Derive `double_hit_rate` from legs data: `legs_won / attempts_on_double`. More granular than overall checkout %.

## Priority 3: Match Prediction Model

### Logistic Regression Baseline
- Add a logistic regression model trained on `[elo_diff, avg_3dart_diff, checkout_pct_diff, format_is_sets]`.
- Use as a calibration check against the Elo-only system.

### Ensemble Output
- Blend Elo win probability with logistic regression probability: `pred = 0.6 * elo_prob + 0.4 * logistic_prob`.

## Priority 4: Calibration

- Run a calibration curve on past predictions stored in `picks` table.
- Apply Platt scaling if systematic over/under-confidence is found in favourite predictions.
