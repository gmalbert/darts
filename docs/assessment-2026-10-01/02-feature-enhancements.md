# Feature enhancements — 16 implementation briefs

These features extend the React/FastAPI app. All server data comes from saved artifacts. Larger calculations, including bracket simulation and explanation generation, run on GitHub Actions. Pure browser calculators may operate on already-loaded inputs without requesting prices.

Each block is an implementation sketch unless marked pure. Proposed fields are not existing API fields. Priorities and effort definitions are in [README](README.md).

## F01 — Overnight briefing with a data-status passport

**Priority: P0 · Effort: M · Target:** HomePage, Shell, /api/v1/meta. **Depends on:** B02, B07, B15.

Replace an empty picks dashboard with a useful morning briefing: what was collected, which fixtures have prices, the last successful overnight run, unsupported markets, and why no recommendations exist. Distinguish an attempted refresh from the timestamp of saved prices. A failed job must not refresh the displayed collection time.

~~~tsx
type Briefing = {
  snapshotAt: string | null;
  lastAttempt: "ok" | "failed" | "unknown";
  fixtures: number;
  priced: number;
  withheld: number;
};
export function MorningBriefing({ data }: { data: Briefing }) {
  return <section aria-label="Overnight data briefing">
    <h1>Your darts research briefing</h1>
    <p>{data.snapshotAt
      ? "Saved prices collected " + new Date(data.snapshotAt).toLocaleString()
      : "No verified price snapshot is available."}</p>
    <p>{data.fixtures} fixtures · {data.priced} priced · {data.withheld} withheld</p>
    {data.lastAttempt === "failed" &&
      <p role="status">The latest overnight update failed. Showing the last valid snapshot.</p>}
  </section>;
}
~~~

**Done when:** a failed refresh preserves yesterday's timestamp, zero fixtures is useful rather than broken-looking, and every price can be traced to a snapshot. This is a direct response to A06/A13, not a request for intraday refreshes.

## F02 — Public forecast audit center

**Priority: P0 · Effort: M · Target:** new /research/model-record page, record API. **Depends on:** B03, B04, M04.

Give every model a public scorecard with sample size, forecast dates, Brier/log loss, calibration, excluded outcomes, and paper-policy results. Publish “No settled forecasts yet” immediately until a ledger exists. Separate reconstructed historical evaluation from prospective records.

~~~python
def public_record(rows, evaluate):
    eligible = [r for r in rows if
                r["origin"] == "prospective"
                and r["frozen_at"] < r["match_start"]
                and r["result"] in ("win", "loss")]
    if not eligible:
        return {"status": "no_settled_forecasts", "n": 0,
                "brier": None, "log_loss": None, "paper_roi": None}
    report = evaluate(eligible)  # M04: verified metric implementation
    return {"status": "measured", "n": len(eligible), **report}
~~~

This integration function assumes datetime objects and a supplied metric function. Persist origin and timestamps in B03.

**Done when:** every chart count reconciles to downloadable ledger rows, unavailable metrics are null, and wins/losses cannot be fabricated by fallback behavior. Inspiration: open data supporting analysis in [FiveThirtyEight's repository](https://github.com/fivethirtyeight/data).

## F03 — Forecast replay: “What did we know then?”

**Priority: P1 · Effort: M · Target:** match detail and a snapshot selector. **Depends on:** B03, B15, M01.

Let users rewind a match to its forecast date, inspect the exact price, model version, available features, and what subsequently changed. This makes corrections understandable and prevents today's player stats from masquerading as yesterday's evidence.

~~~python
def replay_view(match_id, cutoff, forecasts, features):
    candidates = [r for r in forecasts
                  if r["match_id"] == match_id and r["frozen_at"] <= cutoff]
    forecast = max(candidates, key=lambda r: r["frozen_at"], default=None)
    if forecast is None:
        return {"status": "no_forecast_at_selected_time"}
    evidence = [r for r in features
                if r["feature_batch_id"] == forecast["feature_batch_id"]
                and r["available_at"] <= forecast["frozen_at"]]
    return {"status": "ok", "forecast": forecast, "evidence": evidence}
~~~

**Done when:** selecting an old forecast cannot include a later score correction, and every replay is pinned to an immutable batch. “Replay” is inspection of saved evidence, not retrospective prediction marketed as prospective performance.

## F04 — Shareable match passports

**Priority: P1 · Effort: M · Target:** App router, MatchesPage. **Depends on:** B05, B06, B10.

Give each matchup a stable URL containing players, verified format, source coverage, pre-match probabilities, cached prices, historical meetings, and data caveats. Stop making users find a match through transient dropdown state.

~~~tsx
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
type Passport = {
  title: string; format: string | null; snapshotAt: string | null;
  probabilityA: number | null; coverageNotes: string[];
};
type Loader = (key: string, signal: AbortSignal) => Promise<Passport>;
export function MatchPassport({ loadSaved }: { loadSaved: Loader }) {
  const { matchKey } = useParams();
  const [data, setData] = useState<Passport | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    setData(null); setError(null);
    if (!matchKey) { setError("Missing match reference"); return; }
    loadSaved(matchKey, controller.signal).then(
      value => { if (!controller.signal.aborted) setData(value); },
      () => { if (!controller.signal.aborted) setError("Saved research is unavailable"); },
    );
    return () => controller.abort();
  }, [matchKey, loadSaved]);
  return <section>
    <h1>{data?.title ?? "Match research"}</h1>
    {error ? <p role="alert">{error}</p> : !data
      ? <p role="status">Loading saved evidence…</p>
      : <>
        <p>Format: {data.format ?? "Not verified"}</p>
        <p>Saved snapshot: {data.snapshotAt ?? "Unavailable"}</p>
        <p>Player A probability: {data.probabilityA === null ? "Unavailable"
          : new Intl.NumberFormat(undefined, {
            style: "percent", maximumFractionDigits: 1,
          }).format(data.probabilityA)}</p>
        <ul>{data.coverageNotes.map(note => <li key={note}>{note}</li>)}</ul>
      </>}
    <Link to="/matches">Back to fixtures</Link>
  </section>;
}
~~~

Integration sketch: add a Route with path /matches/:matchKey directly inside the existing Routes, using this component as its element. Inject a stable loader that reads the proposed saved-passport endpoint, encodes the canonical key, validates B10's response, and passes through the AbortSignal. It must not initiate provider collection. The identifier requires B05 and must not depend on rebuilt integer IDs.

**Done when:** a bookmarked match survives nightly import and refresh, direct routes work on Cloudflare, and unavailable fields have explicit states.

## F05 — Multi-player comparison workbench

**Priority: P1 · Effort: M · Target:** PlayersPage, batch stats. **Depends on:** B09, B15.

Extend two-player H2H with a shortlist of up to four players, selectable time windows, sample counts, and opponent-adjusted form. Keep observed performance, official ranking, and experimental ratings in separate columns.

~~~python
def comparison_rows(players, measured_stats, window_days):
    result = []
    for player in players[:4]:
        stats = measured_stats.get((player["id"], window_days), {})
        result.append({
            "player": player["name"],
            "window_days": window_days,
            "n_matches": stats.get("n_matches", 0),
            "avg_3dart": stats.get("avg_3dart"),  # None stays missing
            "checkout_fraction": stats.get("checkout_fraction"),
            "elo": player.get("elo"),
        })
    return result
~~~

**Done when:** changing the window changes genuine precomputed observations, and missing stats are never replaced with hard-coded defaults. Inspiration: [Darts Orakel's player-stat and comparison navigation](https://dartsorakel.com/).

## F06 — Tournament path simulator

**Priority: P2 · Effort: L · Target:** TournamentsPage; offline bracket artifact. **Depends on:** B05, B06, M08.

Show the probability of reaching each round, likely opponents, path difficulty, and the impact of a hypothetical upset. Offline simulation can publish a default bracket and a small set of scenario artifacts. The browser selects among saved scenarios; it does not launch heavy work.

~~~python
import random
from collections import Counter

def title_simulation(seed_order, pair_probability, runs=5000, seed=17):
    # Fixed single-elimination bracket; byes/reseeding need explicit rules.
    if runs < 1 or len(seed_order) < 2:
        raise ValueError("Need simulations and a bracket")
    n = len(seed_order)
    if n & (n - 1):
        raise ValueError("Prototype requires a power-of-two field")
    rng, titles = random.Random(seed), Counter()
    for _ in range(runs):
        field = list(seed_order)
        while len(field) > 1:
            field = [a if rng.random() < pair_probability(a, b) else b
                     for a, b in zip(field[::2], field[1::2])]
        titles[field[0]] += 1
    return {p: titles[p] / runs for p in seed_order}
~~~

Pure simulation kernel; validate each supplied probability and extend it for event-specific formats. Run on Actions.

**Done when:** title probabilities sum to one, round advancement is internally consistent, the draw is source-verified, and Monte Carlo error is shown.

## F07 — Format and throw-order laboratory

**Priority: P1 · Effort: M · Target:** ToolsPage. **Depends on:** M08, B06.

Explain why a player can be favored differently in a short leg race and a long set match. Show both “first throw known” and “unknown throw order” scenarios. Label the inputs as leg probabilities, rather than applying a second format boost to a match probability.

~~~python
from math import comb

def iid_race_probability(leg_prob, target):
    # Educational straight race, identical independent leg probabilities.
    if not 0 <= leg_prob <= 1 or target < 1:
        raise ValueError("Invalid leg probability or race target")
    return sum(comb(target + losses - 1, losses) *
               leg_prob ** target * (1 - leg_prob) ** losses
               for losses in range(target))

def format_lab(leg_prob):
    return [{"race_to": target, "p_match": iid_race_probability(leg_prob, target)}
            for target in (3, 6, 10, 16)]
~~~

Pure baseline; M08 supplies alternating throw and nested set rules.

**Done when:** equal players remain 50/50 under symmetric unknown throw order, and labels describe what the calculation actually assumes.

## F08 — Cached book comparison and provenance

**Priority: P1 · Effort: M · Target:** OddsPage, scraper parser, odds query. **Depends on:** B02, B05, M12.

Display every book already returned by the authorized overnight collection, with saved price time and market jurisdiction. Distinguish best saved price from a currently available offer. Never call a Bet365 observation “DraftKings.”

~~~python
def best_saved_price(quotes, selection_id, snapshot_id):
    eligible = [q for q in quotes if
                q["selection_id"] == selection_id
                and q["snapshot_id"] == snapshot_id
                and q["decimal_odds"] > 1
                and q["market_status"] == "open_at_collection"]
    best = max(eligible, key=lambda q: q["decimal_odds"], default=None)
    return None if best is None else {
        "decimal_odds": best["decimal_odds"],
        "book": best["book"],
        "collected_at": best["collected_at"],
        "label": "Best saved price; availability may have changed",
    }
~~~

**Done when:** selection orientation, market rules and collection batch agree across comparisons. Book availability needs provider entitlement; adding extra providers is not part of this proposal. Inspiration: [OddsPortal's darts comparison and odds-format controls](https://www.oddsportal.com/darts/).

## F09 — Overnight market-movement digest

**Priority: P2 · Effort: M · Target:** replace Steam panels. **Depends on:** B14, B15.

Replace claims of 30-minute steam with changes between comparable daily snapshots. Include actual interval endpoints and sample gaps. A daily move cannot establish the timing or cause of intraday steam.

~~~python
def daily_change(previous, current):
    key = ("match_key", "selection_id", "book", "market_key")
    if any(previous[k] != current[k] for k in key):
        raise ValueError("Snapshots are not comparable")
    if current["collected_at"] <= previous["collected_at"]:
        raise ValueError("Need a later snapshot")
    return {
        "from": previous["collected_at"],
        "to": current["collected_at"],
        "change_pp": 100 * (current["implied_prob"] - previous["implied_prob"]),
        "label": "Change between saved overnight prices",
    }
~~~

**Done when:** at least two observations exist for the same market/book/selection, gaps are displayed, and no page or timer collects new odds.

## F10 — Local watchlists and saved research views

**Priority: P1 · Effort: S · Target:** Shell, PlayersPage, MatchesPage. **Depends on:** B05.

Let users pin players and events, then apply local filters to the loaded snapshot. Begin without accounts or cross-device syncing. This creates repeat utility with little backend overhead.

~~~typescript
export function saveWatchlist(ids: string[]) {
  const unique = [...new Set(ids)].slice(0, 100);
  localStorage.setItem("bullziq.watchlist.v1", JSON.stringify(unique));
}
export function readWatchlist(): string[] {
  try {
    const value: unknown = JSON.parse(
      localStorage.getItem("bullziq.watchlist.v1") ?? "[]");
    return Array.isArray(value)
      ? value.filter((v): v is string => typeof v === "string").slice(0, 100)
      : [];
  } catch { return []; }
}
~~~

**Done when:** users can export/delete saved preferences, malformed storage is harmless, and watchlists do not subscribe to polling or notifications. Inspiration: favorite-player organization on [DartConnect](https://www.dartconnect.com/).

## F11 — Calendar export of verified fixture times

**Priority: P2 · Effort: S · Target:** match passport download. **Depends on:** B06, D14.

Provide a one-time .ics download for a selected confirmed fixture. Exclude date-only or provisional times. Include the source and snapshot age in the description.

~~~python
from datetime import datetime, timezone

def calendar_event(match_key, title, start, snapshot_at):
    if start.tzinfo is None:
        raise ValueError("Calendar timestamps must be timezone-aware")
    def esc(value):
        return str(value).replace("\\", "\\\\").replace("\n", "\\n").replace(
            ",", "\\,").replace(";", "\\;").replace("\r", "")
    utc = start.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    generated = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    # Add RFC5545 line folding for long titles/descriptions in integration.
    return "\r\n".join(["BEGIN:VCALENDAR", "VERSION:2.0",
        "PRODID:-//BullzIQ//Fixtures//EN", "BEGIN:VEVENT",
        "UID:" + esc(match_key) + "@bullziq",
        "DTSTAMP:" + generated, "DTSTART:" + utc, "SUMMARY:" + esc(title),
        "DESCRIPTION:Fixture from saved snapshot " + esc(snapshot_at),
        "END:VEVENT", "END:VCALENDAR", ""])
~~~

**Done when:** a fixture imports at the same instant across timezones, ambiguous times are excluded, and long lines are folded. Calendar reminders are controlled by the user's calendar; no notification service is added.

## F12 — Private paper-pick journal

**Priority: P1 · Effort: M · Target:** new research journal tab. **Depends on:** B03, B04.

Let users record a hypothesis, quoted saved price, source forecast, and fixed paper stake. Keep it educational and separate from the official model ledger. Start with local storage and import/export.

~~~typescript
type PaperEntry = {
  id: string; forecastId: string; savedDecimal: number;
  paperStake: number; note: string; recordedAt: string;
};
export function makePaperEntry(forecastId: string, decimal: number, note: string): PaperEntry {
  if (!Number.isFinite(decimal) || decimal <= 1)
    throw new Error("A valid saved decimal price is required");
  return {
    id: crypto.randomUUID(), forecastId, savedDecimal: decimal,
    paperStake: 1, note: note.slice(0, 1000),
    recordedAt: new Date().toISOString(),
  };
}
~~~

**Done when:** entries are labeled paper records, original prices remain immutable, results reconcile to official outcomes, and journal changes cannot alter published model performance.

## F13 — “What would change my conclusion?” sensitivity explorer

**Priority: P2 · Effort: M · Target:** passport and ToolsPage. **Depends on:** M03, M16.

Show how an analysis changes under alternative probabilities and executable-price assumptions. Separate sampling/model uncertainty from user-created scenarios. A robust conclusion should not depend on the third decimal place.

~~~python
def sensitivity(probabilities, decimal_prices):
    cells = []
    for p in probabilities:
        if not 0 <= p <= 1:
            raise ValueError("Probability outside 0–1")
        for price in decimal_prices:
            if price <= 1:
                raise ValueError("Decimal price must exceed one")
            cells.append({"probability": p, "decimal": price,
                          "ev_per_unit": p * price - 1})
    return cells
~~~

Pure arithmetic; run locally in the browser after a TypeScript port.

**Done when:** base assumptions and changed assumptions are visible together, stale saved prices are labeled, and favorable scenarios are not presented as validated forecasts.

## F14 — Player scouting fingerprints

**Priority: P2 · Effort: L · Target:** PlayersPage. **Depends on:** measured visit/attempt data, M10, M11.

Build interpretable style cards: early scoring, finishing, 180 rate, performance on/off throw, and consistency. Use percentiles only against a clearly defined active-player cohort. Show evidence counts beside each dimension.

~~~python
from bisect import bisect_left

def scouting_percentile(value, measured_cohort):
    clean = sorted(x for x in measured_cohort if x is not None)
    if value is None or len(clean) < 20:
        return {"percentile": None, "cohort_n": len(clean)}
    below = bisect_left(clean, value)
    equal = clean.count(value)
    rank = (below + 0.5 * equal) / len(clean)
    return {"percentile": round(100 * rank, 1), "cohort_n": len(clean)}
~~~

Pure percentile calculation; filter finite values and define comparable sample windows upstream.

**Done when:** fingerprints are unavailable for unmeasured stats, their cohort/time window is explicit, and style labels describe data rather than an unverified psychological trait.

## F15 — Forecasting practice challenge

**Priority: P3 · Effort: M · Target:** educational tools. **Depends on:** B03, M04.

Invite users to enter a probability before revealing the saved model estimate. Score probabilities after settlement and explain why a confident wrong answer costs more than a cautious one. Use no wagering or prize mechanisms.

~~~python
def practice_score(probability, outcome):
    if not 0 <= probability <= 1 or outcome not in (0, 1):
        raise ValueError("Invalid probability or binary outcome")
    loss = (probability - outcome) ** 2
    return {"brier": loss, "points": round(100 * (1 - loss), 1)}
~~~

Pure scoring transformation; immutable timestamps are needed to distinguish pre-result submissions from practice after results are known.

**Done when:** the challenge explains the scoring rule, labels retrospective practice, and avoids claiming a short leaderboard establishes skill. Inspiration: expert material on [forecast scoring and calibration](https://www.stat.berkeley.edu/~ryantibs/statlearn-s23/lectures/calibration.pdf).

## F16 — Downloadable event research packs

**Priority: P2 · Effort: M · Target:** tournament hub and Actions publication. **Depends on:** B02, B15.

Publish an event dossier with a narrative briefing, format rules, forecasts, data coverage, CSV tables, and a manifest so users can reproduce the analysis. Static packs can be shared without introducing a new app service.

~~~python
import csv
import io

def research_csv(rows):
    fields = ["match_key", "model_version", "snapshot_at", "p1_probability"]
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        safe = {}
        for field in fields:
            value = row.get(field, "")
            # Neutralize spreadsheet formula injection for textual exports.
            safe[field] = "'" + value if (
                isinstance(value, str) and value.startswith(("=", "+", "-", "@"))
            ) else value
        writer.writerow(safe)
    return out.getvalue()
~~~

Pure export kernel; attach the batch manifest and source attribution in the publication step.

**Done when:** CSV probabilities match the site, all files belong to one snapshot, and redistribution rights are established. Inspiration: event guides on [Darts Orakel](https://dartsorakel.com/) and the research-artifact pattern in [FiveThirtyEight's data repository](https://github.com/fivethirtyeight/data).
