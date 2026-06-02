# BullzIQ (Darts) — Next 5 Features to Implement

> **Based on:** Codebase gap analysis as of July 2025

---

## Feature 1: Player Form Decay Weighting

**Why:** The current rating system treats a win from 2 years ago the same as a win from last week. In darts, form is highly volatile — a player can go from world-class to inconsistent within months. Exponential time-decay on historical match weights would materially improve prediction accuracy.

**How:**
1. In `db/queries.py`, when computing player ratings, retrieve match dates alongside results
2. Apply weight = `exp(-λ × days_ago)` where `λ = 0.002` (approximately halves weight every year)
3. Pass weighted match results to the Elo/rating update function in the existing schema
4. Add a "Form Decay" toggle in the UI sidebar to compare decayed vs non-decayed ratings

**Complexity:** Medium

---

## Feature 2: Head-to-Head Breakdown Page

**Why:** Darts fans are deeply interested in H2H records between players. The current app shows summary statistics but no dedicated H2H matchup page with a historical timeline chart.

**How:**
1. Add a `pages/head_to_head.py` Streamlit page
2. Accept two player selections via `st.selectbox`
3. Display: total H2H record (wins/losses), last 10 meetings with result, sets/legs per meeting, venue breakdown (major tournament vs qualifier)
4. Add a Plotly timeline scatter chart: date on X-axis, winner on Y-axis (binary)
5. Wire into the sidebar navigation in `predictions.py`

**Complexity:** Low

---

## Feature 3: Tournament Bracket Visualization

**Why:** The PDC World Championship and Premier League are the app's core focus. An interactive bracket visualization showing predicted match winners for each round would be the flagship UI feature.

**How:**
1. Load upcoming tournament fixtures from `scrapers/odds_api.py` (fixtures already fetched)
2. Use a Plotly custom scatter/tree layout to render the bracket (no native Plotly bracket component — use custom shapes)
3. For each unfilled slot, show the model's predicted winner with win probability
4. Update the bracket dynamically after each match result is logged in `db/schema.py`

**Complexity:** Medium

---

## Feature 4: Odds Comparison with Edge Detection

**Why:** The app uses odds-api.io as the sole odds source. Adding a best-price comparison across available bookmakers in the odds-api.io response, alongside the model's implied probability, would let users see value edge at a glance.

**How:**
1. `scrapers/odds_api.py` already fetches multiple bookmakers per event — parse all books, not just the first
2. For each outcome, compute: `model_prob`, `best_book_odds` (maximum available odds), `implied_prob` = 1/best_odds, `edge` = model_prob − implied_prob
3. Display a sortable table on the upcoming events page: Player A | Player B | Model % | Best Odds | Book | Edge
4. Highlight rows where edge > 3% (Strong tier) in green

**Complexity:** Medium

---

## Feature 5: Model Prediction Outcome Logging

**Why:** The app currently generates predictions but does not automatically record whether they were correct. A rolling 30-day accuracy log would prove model quality and enable calibration improvement.

**How:**
1. After each match completes, call `db/queries.py` to mark the recorded prediction as resolved with actual result
2. Add `predicted_winner`, `predicted_prob`, `actual_winner`, `correct` columns to the existing predictions table in `db/schema.py`
3. Add a `pages/model_performance.py` page showing: rolling 30-day accuracy, predicted probability decile calibration chart, ROI at flat stake per tier
4. Run the result reconciliation in a GitHub Actions scheduled workflow or trigger via the Streamlit sidebar refresh button

**Complexity:** Low
