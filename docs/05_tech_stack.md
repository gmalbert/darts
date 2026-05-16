# 05 — Tech Stack & Architecture

## Stack Overview

```
App:        Streamlit (Python) — UI, data display, interactive tools
Database:   SQLite (local dev) → PostgreSQL via SQLAlchemy (production)
ORM:        SQLAlchemy (Core + ORM)
Data:       pandas, numpy
Charts:     Plotly (st.plotly_chart) — interactive, supports zoom/hover
ML:         scikit-learn, scipy — Elo model, match predictor, props model
Scrapers:   requests + BeautifulSoup (existing Python scrapers unchanged)
Scheduler:  APScheduler — odds polling, stats refresh, steam detection
Deploy:     Streamlit Community Cloud (free tier) — connects directly to GitHub
Secrets:    Streamlit secrets.toml / environment variables
```

**Why Streamlit?** The entire data stack is already Python. Streamlit eliminates the frontend/backend split — write one Python file and get an interactive dashboard. No TypeScript, no API layer, no Node. Perfect for analytics-first tools where content is data, not marketing pages.

---

## Repository Structure

```
darts-app/
├── app.py                      # Streamlit entry point (Home page)
├── pages/
│   ├── 1_Tournaments.py        # All DK-covered tournaments
│   ├── 2_Players.py            # Player index + profile browser
│   ├── 3_Matches.py            # Match center
│   ├── 4_Picks.py              # Today's model picks
│   ├── 5_Odds.py               # Live odds tracker + line movement
│   └── 6_Tools.py              # Edge calc, H2H tool, 180s calc
├── components/
│   ├── match_center.py         # Match center layout
│   ├── player_profile.py       # Player stats display
│   ├── picks_feed.py           # Picks feed with edge filter
│   └── odds_chart.py           # Odds movement chart (Plotly)
├── models/
│   ├── elo.py                  # Elo rating system
│   ├── match_predictor.py      # Gradient boosting match predictor
│   └── props_model.py          # 180s / checkout props model
├── scrapers/
│   ├── dartsdatabase.py        # Historical data (dartsdatabase.co.uk)
│   ├── dartsdata_api.py        # Live scores (dartsdata.com)
│   └── odds_api.py             # Odds (the-odds-api.com)
├── db/
│   ├── schema.py               # SQLAlchemy models
│   └── queries.py              # Reusable query helpers
├── jobs/
│   ├── scheduler.py            # APScheduler — odds + stats refresh
│   └── steam_detector.py       # Line movement detection
├── data_files/                 # Seed CSVs, cached data
├── .streamlit/
│   └── config.toml             # Theme, server settings
├── requirements.txt
├── .env.example
└── README.md
```

---

## Database (SQLAlchemy Schema)

```python
# db/schema.py
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

class Player(Base):
    __tablename__ = "players"
    id          = Column(Integer, primary_key=True)
    name        = Column(String, unique=True, nullable=False)
    slug        = Column(String, unique=True, nullable=False)
    nickname    = Column(String)
    nationality = Column(String)
    dob         = Column(DateTime)
    pdc_id      = Column(String)
    dartdb_id   = Column(String)
    created_at  = Column(DateTime, default=datetime.utcnow)

    matches_as_p1 = relationship("Match", foreign_keys="Match.player1_id", back_populates="player1")
    matches_as_p2 = relationship("Match", foreign_keys="Match.player2_id", back_populates="player2")
    elo_history   = relationship("EloHistory", back_populates="player")
    stats_cache   = relationship("PlayerStatsCache", back_populates="player")

class Tournament(Base):
    __tablename__ = "tournaments"
    id          = Column(Integer, primary_key=True)
    name        = Column(String, nullable=False)
    slug        = Column(String, unique=True, nullable=False)
    short_name  = Column(String)
    category    = Column(String)   # 'major' | 'series' | 'premier_league' | 'european_tour'
    dk_covered  = Column(Boolean, default=False)
    format      = Column(String)   # 'sets' | 'legs'
    legs_to_win = Column(Integer)
    sets_to_win = Column(Integer)
    start_month = Column(Integer)
    end_month   = Column(Integer)

class Match(Base):
    __tablename__ = "matches"
    id              = Column(Integer, primary_key=True)
    tournament_id   = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    year            = Column(Integer, nullable=False)
    round           = Column(String)
    player1_id      = Column(Integer, ForeignKey("players.id"), nullable=False)
    player2_id      = Column(Integer, ForeignKey("players.id"), nullable=False)
    score1          = Column(Integer)
    score2          = Column(Integer)
    winner_id       = Column(Integer, ForeignKey("players.id"))
    match_date      = Column(DateTime)
    avg1            = Column(Float)
    avg2            = Column(Float)
    checkout_pct1   = Column(Float)
    checkout_pct2   = Column(Float)
    one_eighties1   = Column(Integer)
    one_eighties2   = Column(Integer)
    created_at      = Column(DateTime, default=datetime.utcnow)

    odds_snapshots = relationship("OddsSnapshot", back_populates="match")
    __table_args__ = (
        Index("ix_match_players", "player1_id", "player2_id"),
        Index("ix_match_tournament_year", "tournament_id", "year"),
    )

class OddsSnapshot(Base):
    __tablename__ = "odds_snapshots"
    id            = Column(Integer, primary_key=True)
    match_id      = Column(Integer, ForeignKey("matches.id"), nullable=False)
    bookmaker     = Column(String)
    market        = Column(String)   # 'h2h' | '180s_over' | '180s_under'
    outcome       = Column(String)
    price         = Column(Integer)  # American odds
    implied_prob  = Column(Float)
    snapshot_time = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("ix_odds_match_time", "match_id", "snapshot_time"),)

class PlayerStatsCache(Base):
    __tablename__ = "player_stats_cache"
    id               = Column(Integer, primary_key=True)
    player_id        = Column(Integer, ForeignKey("players.id"), nullable=False)
    tournament_slug  = Column(String)  # NULL = all tournaments
    year_from        = Column(Integer)
    year_to          = Column(Integer)
    matches_played   = Column(Integer)
    matches_won      = Column(Integer)
    win_rate         = Column(Float)
    avg_3dart        = Column(Float)
    avg_checkout     = Column(Float)
    avg_180s_per_leg = Column(Float)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("player_id", "tournament_slug", "year_from", "year_to"),)

class EloHistory(Base):
    __tablename__ = "elo_history"
    id          = Column(Integer, primary_key=True)
    player_id   = Column(Integer, ForeignKey("players.id"), nullable=False)
    rating      = Column(Float, nullable=False)
    match_id    = Column(Integer, ForeignKey("matches.id"))
    recorded_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("ix_elo_player_time", "player_id", "recorded_at"),)
```

---

## Streamlit App Entry Point

```python
# app.py
import streamlit as st
from db.queries import get_todays_schedule, get_todays_picks

st.set_page_config(
    page_title="Darts Analytics",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🎯 Darts Analytics")
st.caption("Model-driven picks and stats for DraftKings-covered PDC tournaments.")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Today's Schedule")
    schedule = get_todays_schedule()
    if schedule:
        for match in schedule:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 3])
                c1.write(f"**{match['player1']}**")
                c2.write("vs")
                c3.write(f"**{match['player2']}**")
                st.caption(f"{match['tournament']} · {match['round']} · {match['match_time']}")
    else:
        st.info("No matches scheduled today.")

with col2:
    st.subheader("Top Picks Today")
    picks = get_todays_picks(min_edge=0.02)
    for pick in picks[:5]:
        edge_color = "green" if pick["edge_pct"] >= 5 else "orange"
        st.write(f":{edge_color}[**{pick['pick']}**] — {pick['edge_pct']:.1f}% edge")
        st.caption(f"{pick['dk_odds']:+d} · Our prob: {pick['our_prob']*100:.1f}%")
```

---

## Streamlit Theme (`.streamlit/config.toml`)

```toml
[theme]
base                     = "dark"
primaryColor             = "#f0a500"    # amber — darts bullseye gold
backgroundColor          = "#0d1117"   # near-black
secondaryBackgroundColor = "#161b22"   # card/panel surface
textColor                = "#e6edf3"

[server]
headless = true
port = 8501

[browser]
gatherUsageStats = false
```

---

## Database Connection & Caching

```python
# db/queries.py
import os
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

@st.cache_resource
def get_engine():
    db_url = os.getenv("DATABASE_URL", "sqlite:///data_files/darts.db")
    return create_engine(db_url, pool_pre_ping=True)

@st.cache_data(ttl=300)   # cache 5 minutes
def get_todays_picks(min_edge: float = 0.02) -> list[dict]:
    with sessionmaker(get_engine())() as session:
        rows = session.execute(text("""
            SELECT m.id, p1.name AS player1, p2.name AS player2,
                   t.name AS tournament, m.round, os.price AS dk_odds
            FROM matches m
            JOIN players p1 ON p1.id = m.player1_id
            JOIN players p2 ON p2.id = m.player2_id
            JOIN tournaments t ON t.id = m.tournament_id
            LEFT JOIN odds_snapshots os ON os.match_id = m.id
            WHERE m.match_date::date = CURRENT_DATE
            ORDER BY m.match_date
        """)).fetchall()
        return [dict(r._mapping) for r in rows]

@st.cache_data(ttl=3600)  # cache 1 hour
def get_player(slug: str) -> dict | None:
    with sessionmaker(get_engine())() as session:
        row = session.execute(
            text("SELECT * FROM players WHERE slug = :slug"), {"slug": slug}
        ).fetchone()
        return dict(row._mapping) if row else None
```

---

## Scheduler (Background Jobs)

Run as a separate process (Railway worker service or a cron job):

```python
# jobs/scheduler.py
from apscheduler.schedulers.blocking import BlockingScheduler
from scrapers.odds_api import refresh_odds_snapshots
from scrapers.dartsdata_api import refresh_live_scores
from db.queries import rebuild_stats_cache

scheduler = BlockingScheduler()

# Odds refresh every 10 minutes
scheduler.add_job(refresh_odds_snapshots, "interval", minutes=10, id="odds")

# Live scores every 30 seconds (gate behind is_live_event check)
scheduler.add_job(refresh_live_scores, "interval", seconds=30, id="live")

# Nightly stats rebuild at 3 AM UTC
scheduler.add_job(rebuild_stats_cache, "cron", hour=3, id="stats")

if __name__ == "__main__":
    scheduler.start()
```

---

## Deployment

```
Streamlit Community Cloud (free — start here):
  - Connect GitHub repo at share.streamlit.io
  - Set secrets via dashboard (DATABASE_URL, ODDS_API_KEY, etc.)
  - Auto-deploys on push to main
  - URL: https://your-app.streamlit.app
  - Limit: 1 GB RAM, sleeps after inactivity

Railway (paid ~$5/mo — use when you have real traffic):
  - Two services: Streamlit app + scheduler worker
  - Procfile:
      web: streamlit run app.py --server.port=$PORT --server.headless=true
      worker: python -m jobs.scheduler
  - Add Railway PostgreSQL plugin for persistent DB
  - Always-on, no sleep
```