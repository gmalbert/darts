"""
db/schema.py — SQLAlchemy 2.0 ORM models for BullzIQ.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

# ── DB path ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data_files" / "bullziq.db"
DB_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# ── Models ─────────────────────────────────────────────────────────────────────

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    nationality = Column(String(3))
    nickname = Column(String)
    pdc_ranking = Column(Integer)
    elo = Column(Float, default=1500.0)
    avg_3dart = Column(Float)
    checkout_pct = Column(Float)
    avg_180s_per_leg = Column(Float)
    win_rate_last20 = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    matches_as_p1 = relationship("Match", foreign_keys="Match.player1_id", back_populates="player1_rel")
    matches_as_p2 = relationship("Match", foreign_keys="Match.player2_id", back_populates="player2_rel")
    elo_history = relationship("EloHistory", back_populates="player")
    stats_cache = relationship("PlayerStatsCache", back_populates="player", uselist=False)


class Tournament(Base):
    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    tournament_type = Column(String)          # world_championship, premier_league, …
    dk_covered = Column(Boolean, default=True)
    prestige_tier = Column(Integer, default=2) # 1=major, 2=ranking, 3=floor
    prize_fund = Column(Integer)               # in GBP
    format_desc = Column(String)               # e.g. "Best of 11 legs"
    typical_month = Column(String)

    matches = relationship("Match", back_populates="tournament")


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"))
    player1_id = Column(Integer, ForeignKey("players.id"))
    player2_id = Column(Integer, ForeignKey("players.id"))
    round_name = Column(String)
    match_date = Column(DateTime)
    legs_to_win = Column(Integer, default=6)
    sets_to_win = Column(Integer)             # NULL for legs-only format
    score1 = Column(Integer)                  # NULL = not yet played
    score2 = Column(Integer)
    winner_id = Column(Integer, ForeignKey("players.id"))
    avg_p1 = Column(Float)
    avg_p2 = Column(Float)
    checkout_pct_p1 = Column(Float)
    checkout_pct_p2 = Column(Float)
    legs_180_p1 = Column(Integer, default=0)
    legs_180_p2 = Column(Integer, default=0)
    is_upcoming = Column(Boolean, default=False)

    tournament = relationship("Tournament", back_populates="matches")
    player1_rel = relationship("Player", foreign_keys=[player1_id], back_populates="matches_as_p1")
    player2_rel = relationship("Player", foreign_keys=[player2_id], back_populates="matches_as_p2")
    winner_rel = relationship("Player", foreign_keys=[winner_id])
    odds_snapshots = relationship("OddsSnapshot", back_populates="match")


class OddsSnapshot(Base):
    __tablename__ = "odds_snapshots"

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    snapshot_time = Column(DateTime, default=datetime.utcnow)
    p1_odds = Column(Integer)   # American moneyline (e.g. -140, +110)
    p2_odds = Column(Integer)
    p1_implied = Column(Float)  # implied probability 0–1
    p2_implied = Column(Float)
    book = Column(String, default="DraftKings")

    match = relationship("Match", back_populates="odds_snapshots")


class EloHistory(Base):
    __tablename__ = "elo_history"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    match_id = Column(Integer, ForeignKey("matches.id"))
    elo_before = Column(Float)
    elo_after = Column(Float)
    recorded_at = Column(DateTime)

    player = relationship("Player", back_populates="elo_history")


class PlayerStatsCache(Base):
    __tablename__ = "player_stats_cache"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), unique=True)
    win_rate_last20 = Column(Float)
    win_rate_premier_league = Column(Float)
    win_rate_world_championship = Column(Float)
    avg_3dart_last10 = Column(Float)
    checkout_pct_last10 = Column(Float)
    avg_180s_last10 = Column(Float)
    form_streak = Column(String)   # e.g. "WWLWW"
    updated_at = Column(DateTime, default=datetime.utcnow)

    player = relationship("Player", back_populates="stats_cache")


class Pick(Base):
    """Model-generated betting picks."""
    __tablename__ = "picks"

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    pick_player_id = Column(Integer, ForeignKey("players.id"))
    model_prob = Column(Float)    # our probability estimate
    dk_odds = Column(Integer)     # American odds at time of pick
    dk_implied = Column(Float)    # DK implied prob
    edge_pct = Column(Float)      # (model_prob - dk_implied) * 100
    confidence = Column(String)   # "high", "medium", "low"
    reasoning = Column(Text)
    pick_time = Column(DateTime, default=datetime.utcnow)
    result = Column(String)       # "win", "loss", NULL if pending
    active = Column(Boolean, default=True)

    match = relationship("Match")
    pick_player = relationship("Player", foreign_keys=[pick_player_id])


class SteamEvent(Base):
    """Flagged line-movement events."""
    __tablename__ = "steam_events"

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    player_steamed = Column(String)
    shift_pct = Column(Float)
    opening_odds = Column(Integer)
    current_odds = Column(Integer)
    opening_implied = Column(Float)
    current_implied = Column(Float)
    detected_at = Column(DateTime, default=datetime.utcnow)

    match = relationship("Match")


def init_db():
    """Create all tables if they don't exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)
