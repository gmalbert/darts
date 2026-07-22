"""Tests for safe handling of dartsdatabase access blocks."""

import pytest

from scrapers import dartsdatabase


def test_fetch_event_raises_on_forbidden(monkeypatch):
    class Response:
        status_code = 403

        def raise_for_status(self):
            raise AssertionError("403 should be handled before raise_for_status")

    monkeypatch.setattr(dartsdatabase.requests, "get", lambda *args, **kwargs: Response())

    with pytest.raises(dartsdatabase.SourceAccessError, match="HTTP 403"):
        dartsdatabase._fetch_event(25785, delay=0)


def test_fetch_event_raises_on_rate_limit(monkeypatch):
    class Response:
        status_code = 429

        def raise_for_status(self):
            raise AssertionError("429 should be handled before raise_for_status")

    monkeypatch.setattr(dartsdatabase.requests, "get", lambda *args, **kwargs: Response())

    with pytest.raises(dartsdatabase.SourceAccessError, match="HTTP 429"):
        dartsdatabase._fetch_event(25785, delay=0)
