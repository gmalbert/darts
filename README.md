# Darts Analytics

A Streamlit-powered betting analytics app for PDC darts tournaments covered by DraftKings. Model-driven picks, player stats, live odds tracking, and interactive tools — all in Python.

> **Disclaimer:** Model outputs are for informational purposes only. Not betting advice. 21+ only where legal. Gambling problem? Call 1-800-522-4700.

---

## Features

### Match Center
Every DK-covered match gets a dedicated analysis page with:
- Model win probability vs. DraftKings implied odds (edge %)
- Head-to-head stat comparison (3-dart avg, checkout %, 180s per leg)
- H2H history table
- Odds movement chart with steam move detection
- Embedded 180s over/under calculator

### Player Profiles
- Elo rating history chart (Plotly)
- Career stats and recent-form metrics
- Tournament breakdown table
- Last 20 match results

### Today's Picks Feed
- All model picks ranked by edge %
- Adjustable minimum-edge filter slider
- Market filter (H2H, 180s Over, 180s Under)
- Reasoning bullets for each pick

### Odds Tracker
- Live DraftKings odds snapshots (refreshed every 10 minutes)
- Line movement chart per match
- Steam move alerts (≥3 percentage point shift in 30 minutes)

### Interactive Tools
- **Edge Calculator** — enter odds and your probability estimate, get edge % and quarter-Kelly sizing
- **180s Calculator** — Poisson-based over/under expected value tool
- **H2H Tool** — compare any two players head-to-head

### Tournament Hubs
Coverage for all 9 DraftKings-booked PDC events:
- PDC World Championship
- Premier League Darts
- World Matchplay
- Grand Slam of Darts
- World Series of Darts
- European Tour
- UK Open
- World Grand Prix
- Players Championship Finals

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| App | Streamlit |
| Database | SQLite (dev) → PostgreSQL (prod) |
| ORM | SQLAlchemy |
| Data | pandas, numpy |
| Charts | Plotly |
| ML | scikit-learn, scipy |
| Scrapers | requests, BeautifulSoup |
| Scheduler | APScheduler |
| Deploy | Streamlit Community Cloud / Railway |

---

## Project Structure

```
darts-app/
├── app.py                      # Home page (schedule + top picks)
├── pages/
│   ├── 1_Tournaments.py
│   ├── 2_Players.py
│   ├── 3_Matches.py
│   ├── 4_Picks.py
│   ├── 5_Odds.py
│   └── 6_Tools.py
├── components/
│   ├── match_center.py
│   ├── player_profile.py
│   ├── picks_feed.py
│   ├── odds_chart.py
│   └── disclaimers.py
├── models/
│   ├── elo.py
│   ├── match_predictor.py
│   └── props_model.py
├── scrapers/
│   ├── dartsdatabase.py
│   ├── dartsdata_api.py
│   └── odds_api.py
├── db/
│   ├── schema.py
│   └── queries.py
├── jobs/
│   ├── scheduler.py
│   └── steam_detector.py
├── scripts/
│   └── train_predictor.py
├── data_files/
├── .streamlit/
│   └── config.toml
├── requirements.txt
└── .env.example
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Git

### Installation

```bash
git clone <your-repo>
cd darts-app

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env           # add your API keys
```

### Seed Historical Data

```bash
python -m scrapers.dartsdatabase seed --start-year 2000
```

This pulls ~15,000 PDC match results from dartsdatabase.co.uk (free, no API key needed).

### Run Locally

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501).

### Train the Match Predictor

```bash
python scripts/train_predictor.py
```

Trains on historical data and saves the model to `models/match_predictor.pkl`. Target Brier score < 0.22.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```
DATABASE_URL=sqlite:///data_files/darts.db   # PostgreSQL URL for production
ODDS_API_KEY=                                 # from the-odds-api.com (free: 500 req/mo)
DK_AFFILIATE_ID=                              # from DraftKings affiliate program
RESEND_API_KEY=                              # for pick alert emails (optional)
```

For Streamlit Community Cloud, add these as secrets in the dashboard (not `.env`).

---

## Deployment

### Streamlit Community Cloud (free, recommended to start)

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo, set main file to `app.py`
4. Add secrets via the dashboard
5. Deploy — auto-redeploys on every push to `main`

### Railway (when you need always-on + scheduler)

```
Procfile:
  web:    streamlit run app.py --server.port=$PORT --server.headless=true
  worker: python -m jobs.scheduler
```

Add a Railway PostgreSQL plugin and set `DATABASE_URL` from the plugin's connection string.

---

## Data Sources

| Source | Cost | Used For |
|--------|------|---------|
| [dartsdatabase.co.uk](https://www.dartsdatabase.co.uk) | Free | Historical results (1994–present) |
| [dartsdata.com](https://www.dartsdata.com) | Free (unofficial) | Live scores |
| [the-odds-api.com](https://the-odds-api.com) | Free tier (500 req/mo) | DraftKings odds |

---

## Models

### Elo Rating (`models/elo.py`)
Standard Elo with adjustments for tournament prestige, format length, and margin of victory. K-factor multiplied 1.5× for World Championship matches.

### Match Predictor (`models/match_predictor.py`)
Logistic regression (upgrades to XGBoost in V2) trained on head-to-head Elo difference, recent form metrics, and format-adjusted win rates. Backtest target: Brier score < 0.22, accuracy > 60%.

### Props Model (`models/props_model.py`)
Poisson distribution for 180s totals; normal distribution for checkout % markets.

---

## Roadmap

See [docs/06_roadmap_near_term.md](docs/06_roadmap_near_term.md) (Days 1–90) and [docs/07_roadmap_far_term.md](docs/07_roadmap_far_term.md) (Months 4–24).

**MVP (first 90 days):**
- [x] Historical data seed
- [ ] Player profiles with Elo chart
- [ ] Match center with model probability
- [ ] Today's picks feed
- [ ] 180s calculator
- [ ] Odds tracker
- [ ] Deploy to Streamlit Community Cloud

---

## Legal

- Model outputs are informational only. Not betting advice.
- Must be 21+ and in a legal jurisdiction to wager.
- This site participates in the DraftKings affiliate program.
- Gambling problem? Call **1-800-522-4700** or visit [ncpgambling.org](https://www.ncpgambling.org).

See [docs/09_legal_and_compliance.md](docs/09_legal_and_compliance.md) for full compliance checklist.
