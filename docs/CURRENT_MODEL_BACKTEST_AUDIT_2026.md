# Current-model backtest audit (2026)

## Verdict

The database contains 6,548 completed matches and Elo history, but the `picks` table has zero rows. Only four odds snapshots exist. Therefore there is no frozen prediction/outcome join for last year and no measurable accuracy, Brier score, log loss, CLV, win rate, or ROI. Live UI claims and `best_bets_today.json` cannot substitute for a pre-match ledger.

## Changes justified by the evidence gap

1. Run rolling-origin Elo as the mandatory baseline; update ratings only after each match.
2. Add format, event tier, leg/set length, throw order, recency, opponent-adjusted averages, checkout rate, and stage pressure only when available before the match. Shrink sparse players toward tour means.
3. Train a calibrated Bradley-Terry/logistic challenger and compare it with Elo by season/event. Persist model version and inputs.
4. Capture multiple-book opening, selection, and closing prices; de-vig two-way markets and settle every pick automatically.

## Betting strategy decision

- **Match winner:** paper-only until a chronological holdout exists.
- **Handicap/sets/legs/totals/180s/checkouts:** separate targets need format-aware distributions; no current evidence.
- **Correct score/props/parlays:** disabled; dependence within a match makes naive combinations unsafe.
- **Staking:** no Kelly; use flat paper stakes after logging begins.

## Release gate

500+ frozen match forecasts spanning event tiers, better log loss/Brier than Elo and de-vigged market, positive CLV, and an audited 300+ bet policy with uncertainty and drawdown.
