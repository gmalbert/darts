"""Tests for bounded incremental dartsdatabase discovery."""

from scrapers.dartsdatabase import (
    RECENT_EVENT_LOOKAHEAD,
    RECENT_EVENT_LOOKBACK,
    _recent_discovery_ranges,
)


def test_recent_discovery_window_is_bounded_and_inclusive_of_cursor():
    start, end, step = _recent_discovery_ranges(25_774)[0]

    assert step == 1
    assert start == 25_774 - RECENT_EVENT_LOOKBACK
    assert end == 25_774 + RECENT_EVENT_LOOKAHEAD + 1
    assert end - start == RECENT_EVENT_LOOKBACK + RECENT_EVENT_LOOKAHEAD + 1


def test_recent_discovery_window_never_uses_nonpositive_event_ids():
    start, end, step = _recent_discovery_ranges(100, lookback=500, lookahead=10)[0]

    assert start == 1
    assert end == 111
    assert step == 1
