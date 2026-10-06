# Design enhancements — 16 implementation briefs

Retain Sky Glass/Petrol and automatic local-time theming. Improve information hierarchy, data honesty, and interaction before changing the brand. Proposed components target React; the legacy Streamlit app should share terminology and formatting while it remains supported.

Code blocks are scoped implementation examples. Integrate shared classes/components, replace conflicting inline styles, and test both themes. New props and data fields require the linked backend briefs.

## D01 — Mobile navigation that preserves all six destinations

**Priority: P0 · Effort: S · Target:** Shell, index.css. **Depends on:** none.

The sidebar disappears below 992px. Add an always-available mobile header with a native disclosure menu. Start with a disclosure instead of a modal drawer, avoiding focus-trap complexity.

~~~tsx
import { NavLink } from "react-router-dom";
const destinations = [
  ["/", "Home"], ["/players", "Players"], ["/matches", "Matches"],
  ["/tournaments", "Tournaments"], ["/odds", "Odds"], ["/tools", "Tools"],
];
export function MobileNavigation() {
  return <header className="mobile-header">
    <NavLink to="/">BullzIQ</NavLink>
    <details><summary>Menu</summary>
      <nav aria-label="Mobile navigation">
        {destinations.map(([path, label]) =>
          <NavLink key={path} to={path} end={path === "/"}>{label}</NavLink>)}
      </nav>
    </details>
  </header>;
}
~~~

~~~css
.mobile-header { display: none; }
@media (max-width: 992px) {
  .mobile-header { display: flex; justify-content: space-between; padding: 1rem; }
  .mobile-header nav { display: grid; gap: .5rem; }
  .mobile-header nav a, .mobile-header summary { padding: .65rem; }
}
~~~

**Done when:** every route is reachable at 390px with keyboard and touch, there is no horizontal page overflow, and the active destination is understandable.

## D02 — One owner for tab visibility, with accessible keyboard behavior

**Priority: P0 · Effort: M · Target:** shared Tabs and three affected page wrappers. **Depends on:** none.

Remove the two independent visibility systems that cause blank panels. Supply content to one tab component; do not nest another panel whose active key is permanently the first tab.

~~~tsx
import { useId, useRef, useState, type ReactNode } from "react";
type Panel = { key: string; label: string; content: ReactNode };
export function ResearchTabs({ panels }: { panels: Panel[] }) {
  const id = useId();
  const [index, setIndex] = useState(0);
  const buttons = useRef<Array<HTMLButtonElement | null>>([]);
  if (!panels.length) return null;
  function activate(i: number) {
    setIndex(i);
    buttons.current[i]?.focus();
  }
  return <>
    <div role="tablist" aria-label="Research sections" className="tabs">
      {panels.map((panel, i) =>
        <button key={panel.key} ref={el => { buttons.current[i] = el; }}
          role="tab" id={id + "-tab-" + i} aria-selected={i === index}
          aria-controls={id + "-panel-" + i} tabIndex={i === index ? 0 : -1}
          onClick={() => activate(i)}
          onKeyDown={event => {
            const next = event.key === "ArrowRight" ? (i + 1) % panels.length
              : event.key === "ArrowLeft" ? (i + panels.length - 1) % panels.length
              : event.key === "Home" ? 0
              : event.key === "End" ? panels.length - 1 : null;
            if (next !== null) { event.preventDefault(); activate(next); }
          }}>{panel.label}</button>)}
    </div>
    {panels.map((panel, i) =>
      <section key={panel.key} role="tabpanel" tabIndex={0}
        id={id + "-panel-" + i} aria-labelledby={id + "-tab-" + i}
        hidden={i !== index}>{panel.content}</section>)}
  </>;
}
~~~

For the three affected pages, pass existing rankings/profile/H2H/detail content directly as content rather than the old hidden TabPanel. Keep panel order stable and consider unmounting expensive panels only after preserving their user state.

**Done when:** profile, H2H, tournament detail and movement contain visible content; arrows/Home/End work; selected tabs and panels have matching relationships. Behavior follows [WAI-ARIA's tabs pattern](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/).

## D03 — A single probability and percentage-point language

**Priority: P0 · Effort: S · Target:** formatters, OddsPage, PlayersPage, HomePage. **Depends on:** B10.

Use fractions internally; percentages only in display. Edge differences should be “percentage points” or “pp,” while expected return is a percentage of stake. Raw implied probabilities can sum above 100% because of margin; only normalize a decorative two-way bar, and label it accordingly.

~~~typescript
export function probabilityText(value: number | null): string {
  return value !== null && Number.isFinite(value) && value >= 0 && value <= 1
    ? new Intl.NumberFormat(undefined, {
        style: "percent", maximumFractionDigits: 1 }).format(value)
    : "Unavailable";
}
export function signedPoints(points: number): string {
  return (points > 0 ? "+" : "") + points.toFixed(1) + " pp";
}
export function normalizedBar(a: number, b: number) {
  if (![a, b].every(x => Number.isFinite(x) && x >= 0) || a + b === 0)
    return null;
  return { aWidth: 100 * a / (a + b), bWidth: 100 * b / (a + b) };
}
~~~

**Done when:** 0.4 displays as 40%, checkout fractions use the same formatter, raw implied sums are visible separately, and -8.4% ROI cannot become “+-8.4%.”

## D04 — Honest loading, missing-data, failure, and stale states

**Priority: P0 · Effort: M · Target:** all data-driven panels. **Depends on:** F01, B10.

An empty array should not stand in for every state. Use specific messages and keep valid cached content when one ancillary endpoint fails. A missing performance record must be absent, not zero or a demo record.

~~~tsx
type PanelState = "loading" | "failed" | "empty" | "stale" | "ready";
export function DataStatus({ state, timestamp }: {
  state: PanelState; timestamp?: string;
}) {
  const messages = {
    loading: "Loading saved data…",
    failed: "Saved data could not be loaded. Try opening this page again.",
    empty: "No verified observations are available for this view.",
    stale: "Showing an older saved snapshot. Prices may have changed.",
    ready: "Saved data available.",
  };
  return <div className="data-status" role="status">
    <p>{messages[state]}</p>
    {timestamp && <time dateTime={timestamp}>{new Date(timestamp).toLocaleString()}</time>}
  </div>;
}
~~~

**Done when:** API failures, valid no-pick runs, missing markets and old snapshots get distinct copy; no automatic retry loop or provider refresh is introduced.

## D05 — A research-first home hierarchy

**Priority: P1 · Effort: S · Target:** HomePage. **Depends on:** F01, F02.

Replace the logo-plus-performance wall with a concise purpose statement, snapshot context, and the next useful action. Keep the logo smaller; give match research and verified records room above the fold.

~~~tsx
import { Link } from "react-router-dom";
export function ResearchHero({ snapshotAt }: { snapshotAt: string | null }) {
  return <header className="research-hero">
    <p className="eyebrow">BullzIQ · PDC darts research</p>
    <h1>Understand the matchup before trusting the number.</h1>
    <p>Explore player form, format, saved prices, and the evidence behind each forecast.</p>
    <p>{snapshotAt ? "Snapshot: " + new Date(snapshotAt).toLocaleString()
      : "A verified overnight snapshot is not yet available."}</p>
    <Link className="btn-primary" to="/matches">Explore matchups</Link>
    <Link to="/research/model-record">Inspect the model record</Link>
  </header>;
}
~~~

Add the research record route from F02 before rendering that link.

**Done when:** a newcomer can identify the site's purpose and price freshness without opening a tab, and unsupported ROI no longer dominates the page.

## D06 — Contrast-aware semantic theme tokens

**Priority: P1 · Effort: M · Target:** theme tokens, CSS, charts. **Depends on:** none.

The palette is distinctive; use it consistently. Add accent-foreground, warning-text, chart-grid, typography and spacing tokens. The night cyan accent needs a dark foreground for filled buttons rather than white. Use text labels as well as colors for positive/negative meaning.

~~~css
:root {
  --biq-accent: #0369a1;
  --biq-accent-foreground: #ffffff;
  --biq-warning-text: #854d0e;
  --biq-space-1: .25rem;
  --biq-space-2: .5rem;
  --biq-space-4: 1rem;
  --biq-radius: .75rem;
}
[data-mode="night"] {
  --biq-accent: #00b4d8;
  --biq-accent-foreground: #062228;
  --biq-warning-text: #fcd34d;
}
.btn-primary, .sidebar-nav a.active {
  color: var(--biq-accent-foreground);
}
.badge-edge-med { color: var(--biq-warning-text); border-color: currentColor; }
~~~

Set data-mode in the existing theme effect and migrate inline colors; retain automatic time selection and no theme dropdown.

**Done when:** measured text contrast meets the chosen WCAG AA criteria in both themes, charts use tokens, and warning text remains readable. Source: [WCAG 2.2](https://www.w3.org/TR/WCAG22/).

## D07 — Scan-friendly responsive research tables

**Priority: P1 · Effort: M · Target:** rankings, results, odds tables. **Depends on:** B09, B10.

Use sortable columns, bounded pages, numeric alignment, visible sample sizes, and horizontal scrolling within a named region. Do not render all 813 players by default. A native paged table is a simpler starting point than virtualization.

~~~tsx
type RankRow = { id: number; name: string; elo: number };
export function RankingsTable({ rows }: { rows: RankRow[] }) {
  return <div className="table-wrap" role="region"
    aria-label="Player ratings table" tabIndex={0}>
    <table>
      <caption>Research ratings · saved overnight dataset</caption>
      <thead><tr><th scope="col">Player</th><th scope="col">Elo</th></tr></thead>
      <tbody>{rows.map(row =>
        <tr key={row.id}><th scope="row">{row.name}</th>
          <td className="numeric">{Math.round(row.elo)}</td></tr>)}</tbody>
    </table>
  </div>;
}
~~~

~~~css
.numeric { text-align: right; font-variant-numeric: tabular-nums; }
.table-wrap { max-width: 100%; overflow: auto; }
.table-wrap caption { padding: .75rem; text-align: left; }
~~~

**Done when:** long tables remain navigable by keyboard and mobile, first-load rows are bounded, and sorting is reflected by aria-sort on column controls.

## D08 — Searchable player selection and connected labels

**Priority: P1 · Effort: M · Target:** PlayersPage, ToolsPage. **Depends on:** B05.

Replace unwieldy 813-option dropdowns with name filtering and a real labeled selection. A search plus native select is a reliable baseline; use a complete accessible combobox library only if richer autocomplete is needed.

~~~tsx
import { useState } from "react";
export function PlayerPicker({ players, onSelect }: {
  players: Array<{ id: number; name: string }>;
  onSelect: (id: number) => void;
}) {
  const [query, setQuery] = useState("");
  const [value, setValue] = useState("");
  const options = players.filter(p => p.name.toLocaleLowerCase()
    .includes(query.toLocaleLowerCase())).slice(0, 50);
  return <fieldset>
    <legend>Select a player</legend>
    <label>Search name <input type="search" value={query}
      onChange={event => { setQuery(event.target.value); setValue(""); }} /></label>
    <label>Matching players <select value={value} onChange={event => {
      setValue(event.target.value);
      if (event.target.value) onSelect(Number(event.target.value));
    }}><option value="">Choose a player</option>
      {options.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
    </select></label>
    <p role="status">{options.length} matches shown; narrow your search for more.</p>
  </fieldset>;
}
~~~

**Done when:** label clicks focus the corresponding control, the two H2H selectors have unique names, and aliases resolve through canonical identity. [Radix primitives](https://github.com/radix-ui/primitives) are an alternative for more involved components.

## D09 — Probability cards with sample size and qualified uncertainty

**Priority: P1 · Effort: M · Target:** match passport, pick cards. **Depends on:** M03, M16.

Show the estimate, method, feature cutoff, support, and uncertainty together. Distinguish a bootstrap model-estimate range from the chance of the match outcome. Do not call a high win probability “high confidence.”

~~~tsx
export function ForecastCard({ probability, range, n, method }: {
  probability: number; range: [number, number] | null;
  n: number; method: string;
}) {
  const pct = (p: number) => (100 * p).toFixed(1) + "%";
  return <article className="card">
    <h3>Estimated win probability</h3>
    <p className="forecast-number">{pct(probability)}</p>
    <p>{method} · {n} relevant historical matches</p>
    <p>{range ? "Model-estimate range: " + pct(range[0]) + "–" + pct(range[1])
      : "No validated uncertainty estimate available."}</p>
    <p>This is a forecast, not a guaranteed result.</p>
  </article>;
}
~~~

Validate probability/range inputs before rendering; specify resampling method and nominal interval in the API.

**Done when:** the support definition and uncertainty method are documented, ranges are not invented from edge tiers, and sparse players have a visible caveat.

## D10 — Accessible charts with text and tables

**Priority: P1 · Effort: M · Target:** Elo, calibration, odds and 180 charts. **Depends on:** real underlying observations.

Provide a caption, explanatory summary, keyboard-accessible table, and non-color distinctions. Retain simple SVG charts where they suffice; lazy-load larger chart packages on the research page.

~~~tsx
export function ProbabilityTrend({ points }: {
  points: Array<{ at: string; p: number }>;
}) {
  if (!points.length) return <p>No saved observations.</p>;
  const y = (p: number) => 90 - 80 * p;
  const coordinates = points.map((point, i) =>
    (10 + 180 * i / Math.max(1, points.length - 1)) + "," + y(point.p)).join(" ");
  return <figure>
    <svg viewBox="0 0 200 100" role="img" aria-label="Saved implied probability trend">
      <polyline points={coordinates} fill="none" stroke="currentColor" strokeWidth="2" />
    </svg>
    <figcaption>{points.length} saved observations; connections do not show intraday prices.</figcaption>
    <details><summary>View observations as a table</summary>
      <table><thead><tr><th>Collected at</th><th>Probability</th></tr></thead>
        <tbody>{points.map(point => <tr key={point.at}>
          <td>{point.at}</td><td>{(100 * point.p).toFixed(1)}%</td></tr>)}</tbody>
      </table>
    </details>
  </figure>;
}
~~~

**Done when:** screen-reader users can retrieve every chart value, sparse one-point histories do not imply a trend, and visual alternatives are tested in both themes.

## D11 — Consistent page geometry and density

**Priority: P1 · Effort: S · Target:** Shell and all page roots. **Depends on:** none.

The Matches page adds its own large padding inside the shared shell. Establish a shared PageHeader and layout grid; remove competing page-level max-width/padding. Offer compact/comfortable table density locally if research users need it.

~~~css
.main-content {
  width: 100%;
  max-width: 1280px;
  padding: clamp(1rem, 2.5vw, 2rem);
}
.research-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 22rem), 1fr));
  gap: var(--biq-space-4, 1rem);
}
.page-header h1 { font-size: clamp(1.4rem, 2.8vw, 2rem); line-height: 1.2; }
.table-wrap[data-density="compact"] :is(td, th) { padding: .4rem .6rem; }
.table-wrap[data-density="comfortable"] :is(td, th) { padding: .75rem; }
~~~

**Done when:** titles, gutters and table padding align across six routes at all supported sizes, with readable content at 200% zoom.

## D12 — A truthful timeline for sparse snapshots

**Priority: P1 · Effort: S · Target:** Odds movement. **Depends on:** F09, B15.

Daily snapshots should look like discrete observations with gaps, not a continuous high-frequency feed. Display source time, book, and price in an ordered timeline. Use “last observed pre-start price,” not “closing price,” unless provenance supports that designation.

~~~tsx
export function SnapshotTimeline({ quotes }: {
  quotes: Array<{ id: string; at: string; book: string; odds: string }>;
}) {
  return <ol className="snapshot-timeline" aria-label="Saved odds observations">
    {quotes.map(quote => <li key={quote.id}>
      <time dateTime={quote.at}>{new Date(quote.at).toLocaleString()}</time>
      <p>{quote.book} · {quote.odds}</p>
    </li>)}
  </ol>;
}
~~~

**Done when:** actual observation intervals are visible, no chart implies observations between overnight runs, and histories never blend different books without labeling.

## D13 — Evidence drawers instead of unexplained grades

**Priority: P2 · Effort: M · Target:** forecast cards. **Depends on:** F03, B15.

Expand “why this estimate?” into a compact evidence panel: facts, model contributions, unknowns, cutoff, and links. Prefer deterministic templates generated offline over invented explanations.

~~~tsx
type Evidence = { label: string; value: string; sourceUrl?: string };
export function EvidenceDrawer({ facts, unknowns }: {
  facts: Evidence[]; unknowns: string[];
}) {
  return <details className="card">
    <summary>Inspect the evidence</summary>
    <dl>{facts.map(fact => <div key={fact.label}>
      <dt>{fact.label}</dt><dd>{fact.value}{" "}
        {fact.sourceUrl && <a href={fact.sourceUrl}>Source</a>}
      </dd></div>)}</dl>
    <h4>Uncertainty and missing information</h4>
    <ul>{unknowns.map(item => <li key={item}>{item}</li>)}</ul>
  </details>;
}
~~~

Validate source URLs as https links to approved provenance; explanatory association is not evidence of causation.

**Done when:** every statement is grounded in saved facts or clearly described as a model association, and caveats remain visible on small screens.

## D14 — Consistent timezone and odds-format controls

**Priority: P1 · Effort: M · Target:** formatters, schedule, ToolsPage. **Depends on:** B10.

Show local time with a UTC alternative. Offer American/decimal odds as local preferences; preserve raw decimal prices where possible. Missing times remain unknown instead of fabricated noon or midnight.

~~~typescript
export function instantLabel(iso: string | null, timeZone?: string): string {
  if (!iso || !/(Z|[+-]\d{2}:\d{2})$/.test(iso)) return "Time not confirmed";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "Time not confirmed";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium", timeStyle: "short", timeZone,
  }).format(date);
}
export function decimalFromAmerican(odds: number): number {
  if (!Number.isFinite(odds) || Math.abs(odds) < 100)
    throw new Error("Invalid conventional American moneyline");
  return odds > 0 ? 1 + odds / 100 : 1 + 100 / Math.abs(odds);
}
~~~

**Done when:** New York/London users see the same instant, daylight-saving transitions are tested, and odds display changes never recalculate provider data. Inspiration: odds formats on [OddsPortal](https://www.oddsportal.com/darts/).

## D15 — Editorial event hubs with real coverage

**Priority: P2 · Effort: M · Target:** TournamentsPage. **Depends on:** B06, F16.

Turn generic cards into an event dossier: current edition, verified rules, prize metadata with season/source, participating players, research coverage and a snapshot briefing. Replace static “2000–2026” and book-coverage ticks with measured coverage.

~~~python
def coverage_summary(matches):
    dated = [m["match_date"] for m in matches if m.get("match_date")]
    return {
        "match_rows": len(matches),
        "first_date": min(dated).isoformat() if dated else None,
        "last_date": max(dated).isoformat() if dated else None,
        "verified_formats": sum(m.get("format_verified", False) for m in matches),
        "measured_averages": sum(m.get("avg_p1") is not None for m in matches),
    }
~~~

Pure aggregation over validated datetime rows; compute offline and render the saved output.

**Done when:** coverage derives from data, edition metadata has sources, and unverified prize funds/format descriptions are not presented as current facts. Inspiration: event reports on [Darts Orakel](https://dartsorakel.com/).

## D16 — Focus, reduced motion, and legible interaction states

**Priority: P1 · Effort: S · Target:** Shell, index.css, controls. **Depends on:** D01, D02.

Add a skip link, visible focus, touch-sized controls, reduced animation, and a clear hierarchy of h1/h2/h3. Replace literal escaped Unicode text with actual icons that are hidden from screen readers when decorative.

~~~tsx
export function SkipLink() {
  return <a className="skip-link" href="#research-main">Skip to research content</a>;
}
// Shell's main element becomes: <main id="research-main" tabIndex={-1}>…</main>
~~~

~~~css
.skip-link { position: absolute; left: .5rem; top: -5rem; z-index: 1000; }
.skip-link:focus { top: .5rem; background: var(--biq-bg2); padding: .75rem; }
:is(button, a, input, select, summary):focus-visible {
  outline: 3px solid var(--biq-accent); outline-offset: 3px;
}
:is(button, summary, .sidebar-nav a) { min-height: 44px; }
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
  html { scroll-behavior: auto; }
}
~~~

**Done when:** keyboard-only navigation is complete, focus is not hidden behind sticky elements, and automated accessibility checks are supplemented by a manual pass. Source: [WCAG 2.2](https://www.w3.org/TR/WCAG22/).
