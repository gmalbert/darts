# Darts Database Assessment

**Date:** 2026-07-21  
**Decision:** Defer implementation

## Summary

Darts Database (`dartsdatabase.co.uk`) is a potentially useful secondary source for historical darts data, but it should not be added to the production ingestion pipeline yet.

The current BullzIQ pipeline already uses the public PDC JSON feed through [`scrapers/pdc.py`](../scrapers/pdc.py). That source is a better fit for the current product, which primarily needs PDC major-event results for ratings, predictions, and historical model inputs.

Darts Database should remain an optional future source for:

- Historical backfills.
- WDF, BDO, regional, and non-major events.
- Player-career and head-to-head expansion.
- Cross-checking PDC data.

## Site capabilities observed

The site currently exposes:

- Player search.
- Event results pages.
- Live scores.
- Rankings and race tables.
- PDC, WDF, BDO, World Seniors, and other event categories.

The site describes itself as covering more than 25,000 players and 8,000 events worldwide. See the [Darts Database homepage](https://dartsdatabase.co.uk/).

An event page such as [PDPA Players Championship 24](https://dartsdatabase.co.uk/display-event.php?eid=25805&tna=PDPA+Players+Championship+24&eda=2026) contains server-rendered result tables with:

- Round names.
- Player names.
- Match scores.
- Three-dart averages when available.
- Player profile links.
- Event metadata such as date, venue, prize fund, and television coverage.

## Cloudflare findings

The homepage loaded normally in the in-app browser. A direct navigation to an event-results page triggered a Cloudflare security-verification page:

> Performing security verification

The normal browser session completed the verification after approximately twelve seconds, after which the event page rendered successfully.

This distinction matters:

- The site is not universally inaccessible.
- Event pages are protected more aggressively than the homepage.
- A browser session may be able to complete the challenge.
- A raw HTTP client or unattended CI runner may receive a challenge, an access denial, or an incomplete response.
- Playwright does not guarantee reliable access from GitHub Actions because Cloudflare may treat automated runners differently.

Direct PowerShell HTTP testing could not be completed in this environment because the local network sandbox denied socket access. Therefore, the exact raw-response status from this workstation was not established.

## Scraping options considered

### Direct HTTP plus HTML parsing

The existing [`scrapers/dartsdatabase.py`](../scrapers/dartsdatabase.py) uses `requests` and BeautifulSoup:

```text
HTTP request → HTML response → BeautifulSoup → normalized match rows → SQLite
```

Advantages:

- Lightweight and inexpensive.
- Easy to run in scheduled jobs.
- Simple to cache, retry, and test.
- Appropriate when event HTML is returned directly.

Risks:

- Cloudflare may challenge or block requests.
- Event IDs are not cleanly sequential by tournament or date.
- Historical discovery can require many requests.
- HTML structure can change without notice.

### Playwright

Playwright can operate a real browser session:

```text
Browser navigation → Cloudflare verification → rendered DOM → extracted results
```

It is useful when:

- JavaScript is required.
- Search or navigation requires interaction.
- Browser cookies or session state are necessary.
- Direct HTTP responses do not contain the result table.

Costs and limitations:

- Slower and heavier than direct HTTP.
- Requires browser binaries and CI setup.
- More vulnerable to timeouts and challenge behavior.
- A successful local browser session does not prove GitHub Actions will work.
- It should not be used to bypass CAPTCHA, access controls, or anti-bot protections.

### Hybrid approach

If Darts Database is revisited, the preferred design is hybrid:

```text
PDC JSON feed
    ↓
Primary production source

Darts Database via direct HTTP
    ↓
Attempted backfill/validation source

Playwright
    ↓
Fallback only for pages that genuinely require browser rendering
```

If implemented later, records should retain source metadata such as:

- `source`.
- `source_event_id`.
- `retrieved_at`.
- Raw-page or response hash where practical.

This allows source conflicts to be reviewed instead of silently overwriting one provider with another.

## Why implementation is deferred

The current application does not require Darts Database to satisfy its primary use case:

- [`db/seed_real.py`](../db/seed_real.py) currently imports the PDC scraper.
- [`scrapers/pdc.py`](../scrapers/pdc.py) uses the public PDC JSON feed.
- The GitHub Actions seed workflow is built around the PDC source.
- The model currently focuses on PDC major-event data and sportsbook odds.

Darts Database could improve coverage, but adding it now would introduce a second data model, Cloudflare reliability concerns, additional deduplication work, and a potentially expensive discovery scan without an immediate product requirement.

## Revisit criteria

Reconsider implementation if one or more of these become important:

- The PDC feed has material historical gaps, especially before the currently observed coverage range.
- BullzIQ needs WDF, BDO, regional, or non-major event data.
- Player profile pages and all-time head-to-head history become core features.
- Independent validation of the PDC feed is required.
- A stable, permitted access method or licensed data arrangement becomes available.

## Recommended future feasibility test

If the source is revisited, begin with a small probe rather than a full scrape:

1. Test one homepage request.
2. Test one current event page.
3. Test one older event page.
4. Test one player-search workflow.
5. Measure challenge frequency, response time, and extraction completeness.
6. Run the probe from the intended CI environment before designing a production scraper.

The immediate decision is to keep Darts Database documented as a possible secondary source and hold off on implementation.
