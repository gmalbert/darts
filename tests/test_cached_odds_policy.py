"""Verify that web/local processes cannot pull provider odds."""

from unittest.mock import Mock

import pytest

from jobs import scheduler
from scrapers import odds_api


@pytest.mark.parametrize("github,permission", [(None, None), (None, "true"), ("true", None)])
def test_provider_pulls_blocked_outside_overnight_job(monkeypatch, github, permission):
    for key, value in (("GITHUB_ACTIONS", github), ("BULLZIQ_NIGHTLY_ODDS_REFRESH", permission)):
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)
    request = Mock()
    monkeypatch.setattr(odds_api.requests, "get", request)
    with pytest.raises(RuntimeError, match="overnight GitHub Actions"):
        odds_api._get("events", {})
    request.assert_not_called()


def test_overnight_job_can_request_provider_odds(monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("BULLZIQ_NIGHTLY_ODDS_REFRESH", "true")
    monkeypatch.setattr(odds_api, "_request_times", [])
    response = object()
    request = Mock(return_value=response)
    monkeypatch.setattr(odds_api.requests, "get", request)
    assert odds_api._get("events", {}) is response
    request.assert_called_once()


def test_continuous_scheduler_is_disabled():
    with pytest.raises(SystemExit, match="Continuous scheduling is disabled"):
        scheduler.run_scheduler()
    with pytest.raises(RuntimeError, match="Continuous odds refresh is disabled"):
        scheduler.job_refresh_odds()
