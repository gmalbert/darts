# 06 — Near-Term Roadmap (Days 1–90)

## Philosophy

Resist building everything. The goal of the first 90 days is one thing: **be the best page on the internet for any DK-covered darts match**. That means one excellent match center beats ten mediocre pages.

---

## Week 1–2: Foundation

### Tasks
- [ ] Create virtual environment and install dependencies
- [ ] Set up SQLite DB with SQLAlchemy schema (`db/schema.py`)
- [ ] Run historical seed from dartsdatabase.co.uk (2000–present)
- [ ] Verify data: spot-check 10 known match results
- [ ] Stand up `app.py` with working Streamlit home page
- [ ] Deploy to Streamlit Community Cloud (connect GitHub repo)

```bash
# Bootstrap commands
git clone <your-repo>
cd darts-app
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Seed historical data
python -m scrapers.dartsdatabase seed --start-year 2000

# Verify
python - <<'EOF'
import sqlite3
conn = sqlite3.connect('data_files/darts.db')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM matches')
print('Total matches:', cur.fetchone()[0])
cur.execute('SELECT year, COUNT(*) FROM matches GROUP BY year ORDER BY year DESC LIMIT 5')
print('Recent years:', cur.fetchall())
EOF

# Run locally
streamlit run app.py
```

### `requirements.txt` (starting point)
```
streamlit>=1.35
sqlalchemy>=2.0
pandas>=2.2
plotly>=5.22
numpy>=1.26
scikit-learn>=1.5
scipy>=1.13
requests>=2.32
beautifulsoup4>=4.12
apscheduler>=3.10
python-dotenv>=1.0
joblib>=1.4
```

### Deliverable
A local SQLite DB with ~15,000 historical PDC matches and a running Streamlit app.

---

## Week 3–4: Player Profiles

Build `pages/2_Players.py` first — lowest-risk with the highest data-to-page ratio.

### Tasks
- [ ] Build Elo model, train on full history, store results in `elo_history` table
- [ ] Build `PlayerStatsCache` refresh function (runs nightly via APScheduler)
- [ ] Build player index: searchable `st.dataframe` of all active PDC players
- [ ] Build player profile: stat cards, Elo line chart (Plotly), recent matches table
- [ ] Deploy to Streamlit Community Cloud

```python
# pages/2_Players.py
import streamlit as st
import pandas as pd
from db.queries import get_all_players, get_player, get_player_stats, get_elo_history

st.set_page_config(page_title="Players | Darts Analytics", layout="wide")
st.title("Player Profiles")

players = get_all_players()
df_idx  = pd.DataFrame(players)[["name", "nationality", "elo", "dk_win_rate"]]
df_idx  = df_idx.sort_values("elo", ascending=False).reset_index(drop=True)

selected = st.selectbox("Search players", df_idx["name"].tolist())

if selected:
    from components.player_profile import render_player_profile
    render_player_profile(selected)
```

### Deliverable
Working player profiles for all active PDC players.

---

## Week 5–6: Match Center + Pre-Match Analysis

### Tasks
- [ ] Build `pages/3_Matches.py` — the core page
- [ ] Add stat comparison columns (avg, checkout %, 180s)
- [ ] Add H2H history dataframe (last 10 meetings)
- [ ] Add latest DK odds display
- [ ] Set up The Odds API polling (every 10 min) for upcoming DK darts events
- [ ] Train logistic regression match predictor on historical data
- [ ] Backtest model — log Brier score and accuracy
- [ ] Display model probability on match center page

```python
# scripts/train_predictor.py
from models.match_predictor import DartsMatchPredictor
from models.backtester import backtest_model
from db.queries import get_all_matches_with_stats, build_stats_cache

matches     = get_all_matches_with_stats()
stats_cache = build_stats_cache(matches)

predictor = DartsMatchPredictor()
results   = backtest_model(predictor, matches, stats_cache)

print(f"Brier Score: {results['brier_score']:.4f}")   # target < 0.22
print(f"Accuracy:    {results['accuracy']:.1%}")      # target > 60%
print(f"N:           {results['n_predictions']}")

predictor.train(matches, stats_cache)
predictor.save("models/match_predictor.pkl")
```

### Deliverable
Match center pages for all upcoming DK-covered darts events with model probability.

---

## Week 7–8: Picks Feed + Interactive Tools

### Tasks
- [ ] Build `pages/4_Picks.py` — today's model picks with edge % filter slider
- [ ] Build edge calculator tool in `pages/6_Tools.py`
- [ ] Build 180s over/under Poisson calculator in `pages/6_Tools.py`
- [ ] Add responsible gambling disclaimer to all picks pages (see `09_legal_and_compliance.md`)
- [ ] Wire up DraftKings affiliate link

```python
# Tournament metadata (static — lives in db/seed_data.py or a JSON file)
DK_TOURNAMENTS = [
    {
        "slug": "pdc-world-championship",
        "name": "PDC World Championship",
        "category": "major",
        "format": "sets",
        "sets_to_win": 7,
        "month": "December-January",
        "venue": "Alexandra Palace, London",
        "betting_notes": [
            "Early round upsets more common in sets format",
            "Quarter/semi-final match markets offer best risk-adjusted edge",
            "Seeded draw — identify bracket quadrants with early high-seed clashes",
        ],
    },
    {
        "slug": "premier-league-darts",
        "name": "Premier League Darts",
        "category": "premier_league",
        "format": "legs",
        "legs_to_win": 6,
        "month": "February-May",
        "venue": "Multiple UK/European cities",
        "betting_notes": [
            "Traveling players show measurable performance dips on European legs",
            "Night Winner market (best of 11) has more variance — good for model edge",
            "First 4 weeks form strongly predicts Play-Off qualification",
        ],
    },
    # ... remaining 7 DK-covered tournaments
]
```

### Deliverable
Picks feed and two interactive tools.

---

## Week 9–10: Tournament Hubs

### Tasks
- [ ] Build `pages/1_Tournaments.py` — tournament index and hub
- [ ] Populate all 9 DK-covered tournaments with schedule, past winners, form guide
- [ ] Add tournament explainer text (format, history, betting notes)
- [ ] Add outright winner odds table (from The Odds API)

### Deliverable
9 tournament pages with schedules and context.

---

## Week 11–12: Polish & Analytics

### Tasks
- [ ] Add `st.set_page_config` metadata (page title, icon) consistently across all pages
- [ ] Review all `st.cache_data` TTLs — ensure picks refresh every 5 min, player data every hour
- [ ] Add error handling for missing DB rows (`st.warning` instead of crash)
- [ ] Add logging for scraper failures (Python `logging` module → file)
- [ ] Test on Streamlit Community Cloud: verify secrets, DB connection, scheduler
- [ ] Write first 5 analysis posts (can be Streamlit pages or a linked blog)

---

## 90-Day Success Metrics

| Metric | Target |
|--------|--------|
| App pages shipped | 6+ |
| Players profiled | 200+ |
| Model Brier score | < 0.22 |
| Model accuracy | > 60% |
| DraftKings affiliate clicks | 100+/month |
| App uptime | > 99% |
| Odds refresh latency | < 15 min |