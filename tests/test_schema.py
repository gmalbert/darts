"""
darts/tests/test_schema.py — ORM schema tests for BullzIQ darts app.
"""

import pytest
from db.schema import Player, Tournament, Match, OddsSnapshot, EloHistory


class TestPlayerModel:

    def test_create_player(self, session, player_a):
        assert player_a.id is not None
        assert player_a.name == "Michael van Gerwen"

    def test_default_elo(self, session):
        p = Player(name="Unknown Dart Player")
        session.add(p)
        session.flush()
        assert p.elo == 1500.0

    def test_unique_name_constraint(self, session, player_a):
        dup = Player(name="Michael van Gerwen")
        session.add(dup)
        with pytest.raises(Exception):
            session.flush()

    def test_query_by_name(self, session, player_a):
        result = session.query(Player).filter_by(name="Michael van Gerwen").first()
        assert result is not None
        assert result.pdc_ranking == 1


class TestTournamentModel:

    def test_create_tournament(self, session, tournament):
        assert tournament.id is not None
        assert tournament.tournament_type == "world_championship"

    def test_prestige_tier(self, session, tournament):
        assert tournament.prestige_tier == 1

    def test_default_dk_covered(self, session):
        t = Tournament(name="Random Floor Event", tournament_type="floor")
        session.add(t)
        session.flush()
        assert t.dk_covered is True

    def test_unique_name(self, session, tournament):
        dup = Tournament(name="PDC World Darts Championship")
        session.add(dup)
        with pytest.raises(Exception):
            session.flush()


class TestMatchModel:

    def test_create_match(self, session, upcoming_match):
        assert upcoming_match.id is not None
        assert upcoming_match.is_upcoming is True

    def test_match_links_players(self, session, upcoming_match, player_a, player_b):
        assert upcoming_match.player1_id == player_a.id
        assert upcoming_match.player2_id == player_b.id

    def test_score_null_when_upcoming(self, session, upcoming_match):
        assert upcoming_match.score1 is None
        assert upcoming_match.score2 is None

    def test_query_upcoming(self, session, upcoming_match):
        upcoming = session.query(Match).filter_by(is_upcoming=True).all()
        assert len(upcoming) >= 1


class TestOddsSnapshotModel:

    def test_create_odds_snapshot(self, session, upcoming_match, player_a, player_b):
        snap = OddsSnapshot(
            match_id=upcoming_match.id,
            p1_odds=-140,
            p2_odds=120,
            p1_implied=0.5833,
            p2_implied=0.4545,
            book="DraftKings",
        )
        session.add(snap)
        session.flush()
        assert snap.id is not None

    def test_default_book(self, session, upcoming_match):
        snap = OddsSnapshot(match_id=upcoming_match.id, p1_odds=-110, p2_odds=-110)
        session.add(snap)
        session.flush()
        assert snap.book == "DraftKings"

    def test_odds_stored_as_integers(self, session, upcoming_match):
        snap = OddsSnapshot(match_id=upcoming_match.id, p1_odds=-200, p2_odds=170)
        session.add(snap)
        session.flush()
        loaded = session.query(OddsSnapshot).filter_by(id=snap.id).first()
        assert isinstance(loaded.p1_odds, int)
