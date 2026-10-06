# Prioritized delivery roadmap

## Recommendation

Build a trustworthy overnight research product before expanding betting markets. The first release should let a user navigate on mobile, inspect correctly formatted saved evidence, understand missing data, and verify that public results are calculated from frozen forecasts.

The strongest next differentiator is a **shareable match passport with forecast replay**, supported by an auditable record. Tournament path simulation and player scouting can follow once the required formats and measured statistics exist.

Priority indicates importance, not that an item can start without prerequisites. Effort definitions: S = 0.5–2 engineering days; M = 3–7 days; L = 2–4 weeks. Work overlaps across categories; do not add all estimates as independent projects. Historical reconstruction, data licensing, and prospective evaluation can take substantially longer.

## First ten coordinated work packages

| Rank | Work package | Items | Why it comes here | Release evidence |
|---|---|---|---|---|
| 1 | Remove invented records and fix metric math | F02 empty state, M04, B04 | Current public claims are unsupported; negative-price returns are wrong | Zero picks → unavailable scores; −150/$100 → $66.67 winning profit |
| 2 | Repair navigation and panels | D01, D02, D16 | Mobile navigation is absent and detail tabs are blank | All routes and panels usable at 390px and by keyboard |
| 3 | Normalize units and states | D03, D04, B10 | Probabilities are displayed 100× too small; errors look like missing markets | 0.4 → 40%; API error, no data, unsupported, and stale are distinct |
| 4 | Correct time semantics | B07, D14, minimal F01 | Old fixtures appear upcoming and naive times shift | UTC serialization; lower/upper schedule bounds; original collection time visible |
| 5 | Make deployment reproducible | B01, B02, B12, B13 | Local API origin and snapshot publication are incomplete | Staged frontend/API work together; read-only startup; failed publication keeps previous release |
| 6 | Repair identities, rules, and import persistence | B05, B06, B08, B14 | Rebuilds can erase history, and defaults masquerade as real formats | Reimport preserves forecasts; unknown formats remain unknown; source keys stable |
| 7 | Reconstruct honest model inputs | B15, M01, M02, M05 | Current seed priors/cache risk future information leakage | Future-data perturbation test; event-separated temporal evaluation |
| 8 | Start a prospective ledger | B03, B04, F02, M04, B16 | Forecast generation, export, and site need one source of truth | Every public forecast frozen before its cutoff; deterministic settlement/export reconciliation |
| 9 | Improve research speed and clarity | B09, B11, D05–D08, D10–D11 | 813 requests and hidden-tab loads waste work | One bounded stats request; inactive panels lazy; accessible charts and selection |
| 10 | Ship the flagship research experience | F03, F04, F08, F10, D09, D13 | Stable, replayable evidence makes the product distinctive | Bookmark survives imports; replay cannot see future evidence; saved quotes retain provenance |

Packages 1–4 can remove misleading behavior immediately, while the ledger and historical reconstruction proceed. There is no need to wait for a complex model to show honest unavailable states.

## Delivery phases

### Phase A — Correctness and usable interface

Illustrative horizon: first 1–2 weeks for a focused initial slice, depending on existing uncommitted work.

Deliver metric/empty-state fixes, tab repair, mobile navigation, unit formatting, clear error states, and UTC/stale-fixture guards. Remove unsupported coverage claims and literal escape sequences. Start deployment configuration and source audits.

**Gate:** manually exercise Home, Players, Tournaments, Matches, Odds, and Tools at desktop and mobile widths. Verify all detail tabs with populated and absent data. Empty metrics must not imply a record. No provider refresh is part of acceptance testing.

### Phase B — Durable data and hosted snapshots

Illustrative horizon: next 3–6 weeks or more; canonical IDs and source repairs may dominate.

Create non-destructive imports, rules/provenance, semantic validation, credential isolation, and one ordered publication pipeline. Build a read-only versioned serving artifact and stage the exact artifact used in release. Add the forecast/settlement ledger and model manifest.

**Gate:** running the same source batch twice does not duplicate results or erase odds/forecasts. A failed source, invalid schema, hash mismatch, or partial artifact never replaces the last valid release. API startup cannot write data or contact providers. Only the dedicated overnight odds job has credentials and refresh permission.

### Phase C — Honest evaluation and useful research

Illustrative horizon: another 3–6 weeks of engineering, with prospective evidence accumulating over later weeks/months.

Rebuild point-in-time Elo, event-grouped validation, calibration challengers, and proper metrics. Add bounded stats delivery, lazy loading, match passports, replay, cached-book comparison, and local watchlists.

**Gate:** models are compared on identical test fixtures with a separately reported market-covered subset. Retrospective and prospective records are distinct. Features lacking valid observations remain unavailable.

### Phase D — Differentiating experiments

Conditional horizon: later cycles after data/evaluation gates.

Add actual format/duration modeling, tournament scenarios, opponent-adjusted scouting, measured props, and sensitivity tools. Treat each as an independently evaluated experiment. Dartboard policies remain a research option until legitimate throw-level data exists.

**Gate:** adopt a challenger only if it improves the predefined evaluation target with useful uncertainty evidence, without unacceptable calibration or coverage regressions. Do not decide solely on historical selected-bet ROI.

## Complete feature backlog

| ID | Enhancement | Priority | Effort | Sequence/dependency gate |
|---|---|---|---|---|
| F01 | Overnight briefing/data passport | P0 | M | Minimal timestamps now; full manifest after B02/B15 |
| F02 | Public forecast audit center | P0 | M | Honest empty state now; B03/B04/M04 for measured record |
| F03 | Forecast replay | P1 | M | Frozen ledger and point-in-time lineage |
| F04 | Shareable match passports | P1 | M | Canonical IDs, formats, typed response |
| F05 | Multi-player comparisons | P1 | M | B09 and measured stats |
| F06 | Tournament path simulation | P2 | L | Verified bracket/rules and M08 |
| F07 | Format/throw-order laboratory | P1 | M | Supported leg model; hypothetical assumptions visible |
| F08 | Cached book comparison | P1 | M | Comparable saved selections and provenance |
| F09 | Overnight movement digest | P2 | M | Persisted multiple snapshots; no intraday claims |
| F10 | Local watchlists | P1 | S | Stable IDs |
| F11 | Calendar export | P2 | S | Verified exact fixture times |
| F12 | Private paper journal | P1 | M | Ledger contracts and correct settlement |
| F13 | Sensitivity explorer | P2 | M | Calibrated estimates and uncertainty policy |
| F14 | Scouting fingerprints | P2 | L | Measured denominators and sufficient cohort coverage |
| F15 | Forecast practice challenge | P3 | M | Real resolved outcomes and proper scoring |
| F16 | Event research downloads | P2 | M | Versioned artifact, provenance, data dictionary |

See [feature code and acceptance criteria](02-feature-enhancements.md).

## Complete design backlog

| ID | Enhancement | Priority | Effort | Sequence/dependency gate |
|---|---|---|---|---|
| D01 | Mobile navigation | P0 | S | Start immediately |
| D02 | Functional accessible tabs | P0 | M | Start immediately; replace double visibility ownership |
| D03 | Consistent probability units | P0 | S | B10 unit contract |
| D04 | Honest loading/error/missing/stale states | P0 | M | Contract/state definitions; minimal timestamps first |
| D05 | Research-first homepage | P1 | S | F01/F02 |
| D06 | Semantic contrast tokens | P1 | M | Verify actual rendered themes |
| D07 | Responsive research tables | P1 | M | B09/B10 bounded data |
| D08 | Searchable labeled player selection | P1 | M | Stable identities |
| D09 | Evidence-aware probability cards | P1 | M | M03/M16 and honest bounds |
| D10 | Accessible charts | P1 | M | Genuine observations and text equivalent |
| D11 | Consistent page geometry | P1 | S | Can proceed with Phase A |
| D12 | Sparse-snapshot timelines | P1 | S | F09/B15; preserve gaps |
| D13 | Evidence drawers | P2 | M | F03/B15 |
| D14 | Timezone and odds display controls | P1 | M | UTC and price-unit contract |
| D15 | Event hubs with real coverage | P2 | M | Rules/provenance and research packs |
| D16 | Focus/reduced-motion interaction | P1 | S | Coordinate with D01/D02 |

See [design code and acceptance criteria](03-design-enhancements.md).

## Complete backend backlog

| ID | Enhancement | Priority | Effort | Sequence/dependency gate |
|---|---|---|---|---|
| B01 | Read-only serving/readiness | P0 | M | Verified serving schema and snapshot |
| B02 | Immutable snapshot publication | P0 | L | B08/B13; deployment artifact contract |
| B03 | Canonical forecast ledger | P0 | L | IDs, rule coverage, point-in-time inputs |
| B04 | Idempotent settlement/corrections | P0 | M | Ledger and valid winners |
| B05 | Canonical player/fixture/market IDs | P0 | L | Source-ID mapping and ambiguity review |
| B06 | Measured provenance/format rules | P0 | L | Source metadata; unknowns retained |
| B07 | Time guards/valid outcomes | P0 | M | Immediate patch plus B06 metadata |
| B08 | Publication quality gates | P0 | M | Identity/rule semantics |
| B09 | Bounded batch player stats | P1 | M | Stable stored stats/lineage |
| B10 | Typed API/unit/input contract | P1 | M | Start with Phase A |
| B11 | Versioned cache/lazy loads | P1 | M | B02 snapshot version |
| B12 | API origin/CORS/safe errors | P0 | M | Actual deployment hostnames |
| B13 | Reproducible CI/credential isolation | P0 | M | Start immediately |
| B14 | Non-destructive incremental imports | P0 | L | Canonical identities; schema migration |
| B15 | Availability time/source lineage | P1 | L | Start early because M01 depends on it |
| B16 | Publication/model observability | P1 | M | Snapshot and forecast manifests |

See [backend code and acceptance criteria](04-backend-enhancements.md). B15 is strategically early despite P1: prioritize the minimum lineage needed by M01; extend the research-facing API later.

## Complete model backlog

| ID | Enhancement | Priority | Effort | Sequence/dependency gate |
|---|---|---|---|---|
| M01 | Point-in-time features/neutral priors | P0 | L | Source availability, IDs, rule precision |
| M02 | Grouped temporal validation | P0 | M | M01; complete event boundaries |
| M03 | Chronological calibration | P1 | M | Separate train/calibration/test support |
| M04 | Measured proper scores/ROI | P0 | M | Immediate metric fix; ledger for real reporting |
| M05 | Tuned/audited Elo baseline | P1 | M | M01/M02 |
| M06 | Rating uncertainty/Glicko challenger | P2 | L | Verified updater/reference cases |
| M07 | Regularized Bradley–Terry | P1 | L | Valid chronological outcomes/IDs |
| M08 | Leg/set formats and duration | P1 | L | Real rules and leg-level estimates |
| M09 | Starter-conditioned advantage | P2 | L | Observed throw order |
| M10 | Hierarchical sparse-stat shrinkage | P1 | L | Measured counts and denominators |
| M11 | Opponent-adjusted form | P2 | M | Pre-match baseline history |
| M12 | De-vigged market benchmarks | P1 | M | Comparable two-sided saved quotes |
| M13 | Overdispersed 180/duration model | P2 | L | Counts, exposure, duration distribution |
| M14 | Attempt-aware checkout model | P2 | L | Actual attempt denominator |
| M15 | Dartboard skill/policy research | P3 | L+ | Lawful target/hit/visit-level data |
| M16 | Abstention/robust recommendation policy | P1 | M | Honest scores, calibrated uncertainty, provenance |

See [model code and acceptance criteria](05-model-enhancements.md). M08/M10 are valuable but blocked by data quality today; P1 does not mean an engineering-only fix can create missing observations.

## Evaluation and release scorecard

| Dimension | Evidence to retain | Decision rule |
|---|---|---|
| Forecast quality | Brier, log loss, calibration bins with counts, paired event-cluster uncertainty | Compare against prespecified baselines on identical out-of-time populations |
| Market comparison | Same-book/time two-sided probabilities and coverage | Keep market-covered subset separate; do not cherry-pick winning selections |
| Paper returns | Frozen offered price, stake policy, settlement/corrections, voids | Reconcile every result; no return claims without eligible rows |
| Data quality | Unresolved IDs, missing winners, rule/date precision, measured-stat coverage | Unsupported inputs abstain; critical validation failure prevents publication |
| Publication | Version/hash, source times, last attempt/success, previous valid artifact | Failed run preserves prior artifact and original timestamps |
| Usability | All routes/tabs, 390px reflow, keyboard, labels, chart equivalents | Required research actions remain usable without a pointer |
| Efficiency | Player request count, inactive-tab payload, API timings, artifact size | Remove known redundant work; measure before inventing latency targets |

Planning targets such as “30 measured matches” in a snippet are illustrative policies, not statistically sufficient sample guarantees. Prospective score precision depends on event mix, correlation, and forecast variation; report uncertainty rather than promising a fixed number of weeks proves skill.

## Scope and cost choices

- Prefer local watchlists and a local paper journal before user accounts, email alerts, or a payments system.
- Prefer a JSON artifact registry before operating a separate MLflow service.
- Prefer one validated immutable SQLite snapshot before introducing a database cluster.
- Prefer interpretable Elo/paired-comparison baselines before a large neural model.
- Prefer measured unavailable states before simulated “real-looking” statistics.
- Budget source acquisition and historical cleanup explicitly; advanced checkout/180 research may require the most expensive work in this plan.

The deliverable is this assessment and implementation backlog. Application changes, migrations, new provider subscriptions, and deployment remain separate work.
