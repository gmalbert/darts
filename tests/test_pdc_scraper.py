"""Tests for the free public PDC results adapter."""

from scrapers.pdc import _classify, _parse_tournament


def test_classify_keeps_major_and_rejects_qualifiers():
    assert _classify("2026 World Matchplay") == "world_matchplay"
    assert _classify("2025 PDC UK Open Amateur Qual 4") is None
    assert _classify("2026 Women's World Matchplay") is None


def test_parse_tournament_maps_completed_fixture():
    tournament = {"id": 123, "name": "2026 World Matchplay", "type": "world_matchplay", "date": "2026-07-21"}

    # Avoid a network call while checking the JSON-to-raw row mapping.
    import scrapers.pdc as pdc

    original = pdc._get_json
    pdc._get_json = lambda path, params=None: {
        "data": {"attributes": {
            "name": "2026 World Matchplay",
            "startDate": "2026-07-21",
            "stages": [{
                "stage": {"name": "Final"},
                "fixtures": [{
                    "status": "Result",
                    "participant1Score": 10,
                    "participant2Score": 8,
                    "participant1": {"firstName": "A", "lastName": "Player"},
                    "participant2": {"firstName": "B", "lastName": "Player"},
                }],
            }],
        }},
    }
    try:
        rows = _parse_tournament(tournament)
    finally:
        pdc._get_json = original

    assert rows[0]["round"] == "Final"
    assert rows[0]["player1"] == "A Player"
    assert rows[0]["winner"] == "A Player"
    assert rows[0]["score1"] == 10
