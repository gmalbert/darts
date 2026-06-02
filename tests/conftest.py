"""
darts/tests/conftest.py — shared fixtures for BullzIQ darts tests.
Uses an in-memory SQLite database so tests never touch the real data file.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.schema import Base, Player, Tournament, Match, OddsSnapshot, EloHistory


@pytest.fixture(scope="session")
def engine():
    """In-memory SQLite engine."""
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def session(engine):
    """Transactional session that rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    sess = Session()
    yield sess
    sess.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def player_a(session) -> Player:
    p = Player(name="Michael van Gerwen", nationality="NED", pdc_ranking=1, elo=2100.0)
    session.add(p)
    session.flush()
    return p


@pytest.fixture
def player_b(session) -> Player:
    p = Player(name="Peter Wright", nationality="SCO", pdc_ranking=2, elo=1950.0)
    session.add(p)
    session.flush()
    return p


@pytest.fixture
def tournament(session) -> Tournament:
    t = Tournament(name="PDC World Darts Championship", tournament_type="world_championship", prestige_tier=1)
    session.add(t)
    session.flush()
    return t


@pytest.fixture
def upcoming_match(session, player_a, player_b, tournament) -> Match:
    m = Match(
        tournament_id=tournament.id,
        player1_id=player_a.id,
        player2_id=player_b.id,
        match_date=datetime(2025, 12, 27, 19, 30),
        legs_to_win=6,
        is_upcoming=True,
    )
    session.add(m)
    session.flush()
    return m
