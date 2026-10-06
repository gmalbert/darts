# Current-site assessment

## Scope and evidence

Inspected the current working tree, including the Streamlit entrypoint and pages, React pages and shared controls, FastAPI routes and queries, ORM schema, seed and scraper paths, overnight workflows, model classes, calculator parity fixtures, and earlier roadmaps.

Read the running local API at http://127.0.0.1:8001 and visited all six React routes at http://127.0.0.1:5173. Examined the home Model Info panel, player profile, tournament detail, and odds movement tabs. Checked desktop navigation at 1280 × 900 and mobile navigation at 390 × 844. Restored the temporary viewport override afterward.

Queried the local SQLite file using mode=ro. No provider requests, production credentials, heavy scraping, historical rebuilding, or model training were used. Production Cloudflare/Render deployment state and production data were not verified; these findings apply to the checked-out implementation and running local preview.

The Streamlit skill discovery could not resolve a project interpreter with its bundled reference documents. The available bundled Python can inspect SQLite and run dependency-free examples, but has no pytest, SQLAlchemy, scikit-learn, SciPy, or Streamlit. No installation was necessary for the assessment. Legacy findings are based on inspected source, not a new full Streamlit walkthrough.

## Database observed during inspection

| Measurement | Local observation | Implication |
|---|---:|---|
| Players | 813 | Adequate population for a searchable player browser |
| Tournaments | 9 | Major-event focus, not all PDC tours |
| Match rows | 6,548 | Includes 7 rows marked upcoming; do not call all rows completed |
| Historical rows by upcoming flag | 6,541 | This flag alone does not prove a valid settled outcome |
| Missing winner IDs | 141 | Includes upcoming rows; historical unknown outcomes must be excluded or resolved |
| Rows with player-one match average missing | 6,548 | No observed per-match averages to support recent-average models |
| Rows with sets_to_win populated | 0 | Set-format models cannot rely on current ORM metadata |
| Persisted format | Every row: legs_to_win=6, sets_to_win=NULL | Format displays reflect defaults, not reliable historical rules |
| Players with averages/checkout/180-rate fields | 23 for each field | These are imported hard-coded metadata, not fresh measured form |
| PlayerStatsCache rows | 0 | All per-player stats-cache requests are expected to find no record |
| Picks / settled picks | 0 / 0 | No prospective forecast ledger or measured ROI |
| Odds snapshots | 4 | Very limited market history |
| Latest odds timestamp | July 22, 2026, 01:41 UTC | Approximately 72 days old at inspection |
| Latest match timestamp | July 26, 2026, 13:30 | Data is well behind the assessment date |
| SQLite quick_check | ok | Structural integrity passed; semantic accuracy is a separate issue |
| SQLite foreign_key_check | No rows returned | No current foreign-key violations; this does not establish enforcement on writes |

These are a point-in-time inspection of the local file. The running API health counts matched the read-only database counts.

## Strengths to retain

1. React, TypeScript, and FastAPI provide a practical separation of presentation and data access.
2. The existing six-page organization covers the essential darts research tasks.
3. The provider guard requires GitHub Actions and a dedicated refresh flag.
4. Continuous odds scheduling has explicitly been disabled.
5. Odds collection writes snapshots only when prices are present.
6. Historical import and Elo processing are already suited to offline execution.
7. The theme tokens provide a useful light/dark design foundation.
8. A calculator parity suite and visual comparison harness already exist.
9. The original query layer and ported API make implementation targets easy to identify.
10. Earlier model-audit documents correctly recognize the absence of frozen predictions.

## Confirmed findings

| ID | Priority | Finding and evidence | Consequence | Linked work |
|---|---|---|---|---|
| A01 | P0 | [FastAPI query](../../backend/api/queries.py#L495) and [Streamlit query](../../db/queries.py#L450) return 47 wins, 31 losses, 8.4% ROI and 0.221 Brier when no picks are settled. The preview showed these exact numbers. | Invented performance is presented as measured history. | F02, D04, M04 |
| A02 | P0 | Both record functions treat a winning negative American price as abs(odds) profit. At -150, a 100-unit stake should earn 66.67 units, not 150. Brier remains constant even when picks exist. | Future recorded ROI and Brier would still be wrong after removing fallback data. | M04, B04 |
| A03 | P0 | [Players](../../frontend/src/pages/PlayersPage.tsx#L85), [Tournaments](../../frontend/src/pages/TournamentsPage.tsx#L62), and [Odds](../../frontend/src/pages/OddsPage.tsx#L67) pass the first tab's active key into inner panels. Shared Tabs selects a child, but that child keeps a hidden class. Browser clicks confirmed blank profile, tournament detail, and line-movement panels. | Features described as complete cannot be used. | D02 |
| A04 | P0 | [Odds](../../frontend/src/pages/OddsPage.tsx#L146) and [Players](../../frontend/src/pages/PlayersPage.tsx#L171) append a percent sign to 0–1 fractions. The browser displayed 0.4% for an implied probability of 0.4. Odds bar widths also use raw fractions. | Probabilities and checkout rates are off by a factor of 100; bars misrepresent them. | D03, B10 |
| A05 | P0 | [CSS](../../frontend/src/index.css#L324) hides the sidebar below 992px; Shell has no replacement menu. Confirmed at 390px and the default narrow preview. | Mobile users cannot navigate between pages. | D01 |
| A06 | P0 | [Upcoming query](../../backend/api/queries.py#L186) filters by an upper cutoff, but not a lower time bound. Current odds uses the upcoming flag without a date guard. July fixtures appeared in the October preview. | Expired fixtures and old prices look relevant to the next seven days. | B07, F01 |
| A07 | P0 | [Seed](../../db/seed_real.py#L201) imports averages and player priors from demo-era PLAYER_DATA. Its Elo initialization uses those hard-coded ratings before replaying history. | The real-data flag proves neither field provenance nor point-in-time validity. | B06, M01 |
| A08 | P0 | The historical Match constructor does not persist the calculated legs value or set metadata. The database confirms defaults on every row. | Match format labels and downstream models cannot be trusted. | B06, M08 |
| A09 | P0 | [Seed](../../db/seed_real.py#L145) drops every ORM table even during an incremental refresh; those include odds, picks and history. Separate 03:00 and 07:00 workflows both write the same Git-tracked SQLite file without a shared concurrency strategy. | Saved forecasts/odds can be erased; overlapping publication can lose updates or fail pushes. | B02, B14 |
| A10 | P0 | [API client](../../frontend/src/api/client.ts#L1) hard-codes http://127.0.0.1:8001. CORS allows local dev origins only. Docs acknowledge that Git updates do not automatically synchronize a Render persistent database. | Deployment requires a real API origin and tested snapshot publication. | B02, B12 |
| A11 | P1 | [Players](../../frontend/src/pages/PlayersPage.tsx#L52) requests stats for every player through one Promise.all, then silently ignores failures. All cache rows are absent locally. | 813 unnecessary requests; one 404 rejects the batch and loses successful results too. | B09 |
| A12 | P1 | Home loads all Elo history, era statistics and yearly history on mount, regardless of the selected tab. | A simple picks view pays the payload/computation cost of hidden research panels. | B11, D07 |
| A13 | P1 | Most pages discard loading/error fields from useApi. Missing prices get “Lines not open yet” copy without collection status. | A failed API, stale snapshot, unsupported book, and unopened market are conflated. | D04, F01 |
| A14 | P0 | [H2H query](../../backend/api/queries.py#L146) counts any row not won by player one as a player-two win. | Missing/invalid winner IDs bias H2H evidence. | B07 |
| A15 | P1 | [Date serialization](../../backend/api/queries.py#L51) returns naive timestamps without Z or offset; queries use host-local datetime.now(). | Displayed match/snapshot times may shift according to the client or server timezone. | B10, D14 |
| A16 | P0 | The export computes Elo picks to JSON, while /picks reads Pick rows. The observed Pick table is empty. The scheduled paths do not visibly train the logistic model or populate the complete forecast/settlement lifecycle. | Grid export and the site's picks page can disagree; the presence of a model class does not establish a trained deployed model. | B03, B04 |
| A17 | P1 | Tournament page claims 2000–2026 coverage while local data begins in 2015, and labels all events DK-covered based on seed metadata. Provider metadata disagrees across README and scraper. | Coverage and book attribution overstate the observed evidence. | F08, B06, D15 |
| A18 | P1 | Shared tabs lack ARIA tab semantics and directional keyboard behavior. Many labels are unassociated; charts lack text summaries. Literal Unicode escape sequences appear in some headings. | Accessibility and visual polish need a component-level pass. | D02, D08, D10 |
| A19 | P0 | API startup calls ensure_seeded, which creates tables; generic errors expose str(exc), and public health exposes an absolute database path. | Serving is not truly read-only and exposes unnecessary implementation details. | B01, B12 |
| A20 | P1 | Calculator math is duplicated in Python and TypeScript; Tools still makes multiple backend calls for arithmetic. Integer 180 lines have no explicit push outcome; parlay probabilities assume independence. | Apparent precision hides unsupported assumptions and inconsistent states. | B10, M13, M16 |

Source links identify integration locations; #L anchors render on GitHub, while local editors may ignore them. File names and function names are the reliable anchors for this local report.

## Model-specific assessment

The inspected logistic class uses a single stats_cache for every historical training row. That creates leakage if the cache contains facts unavailable at each match. Its scaler is fit before five-fold calibration, so calibration folds share preprocessing fitted on their data. Integer cv=5 does not impose tournament/time separation. Isotonic calibration can be unstable with small samples.

The predictor's feature list and comments do not fully agree: the documented crowd advantage is not actually used in build_features. Hard-coded city assumptions should not substitute for timestamped venue/context data.

The inspected PDC ingestion adapter assigns the tournament start date to matches when an exact match timestamp is absent. Its raw event identifier is a tournament identifier, not a globally unique fixture key. Treat those rows as event/date precision, not exact forecast cutoffs or calendar times. B05/B06/B15 are required before reliable intraday replay or settlement ordering.

Elo remains a sensible baseline after neutral initialization, chronological ordering, valid outcome filtering, and parameter selection on earlier data. The current match-format function is a heuristic transformation of a match probability, not a generative leg/set model. It cannot establish reliable correct-score or props distributions.

The checkout model's normal approximation assumes a known number of attempts. The current data does not include those attempts. The 180 model multiplies a hard-coded rate by 1.6 × legs_to_win; that ignores uncertainty in match duration and rate provenance.

## Release assessment by capability

| Capability | Current judgment | Evidence needed next |
|---|---|---|
| Historical result browser | Useful prototype with semantic data issues | Valid winners, canonical identities, reliable rules, coverage timestamps |
| Elo research rankings | Exploratory | Neutral historical priors, inactive-player filters, chronological benchmark |
| Upcoming fixtures/odds | Not release-ready locally | Stale-fixture filtering, last-success manifest, book provenance, fresh publication |
| Measured model record | Not supported | Frozen predictions, deterministic settlement, audited metric calculations |
| Player profiles/H2H | Broken interaction plus sparse evidence | Tab fix, stats-cache build, unknown-outcome handling |
| Calculators | Educational prototype | Valid inputs, clear assumptions, unit consistency, push/dependence semantics |
| Production hosting | Deployment preparation incomplete | API origin, CORS, immutable snapshot import, read-only startup |
| Advanced models | Research only | Data availability audit and tournament-forward evidence |

## Relationship to older plans

The earlier [NEXT_FEATURES](../NEXT_FEATURES.md), [model audit](../CURRENT_MODEL_BACKTEST_AUDIT_2026.md), [frontier blueprint](../FRONTIER_ENHANCEMENT_BLUEPRINT.md), and [roadmap](../12_MONTH_ROADMAP.md) include some overlapping ideas. This assessment adds concrete integration code, observed UI failures, publication contracts, explicit data dependencies, and acceptance criteria.

The existing handoff claims full parity and strong speed improvements. Its benchmark numbers are historical local measurements, not a new production performance guarantee. The current blank tabs contradict a claim of usable parity. A working route and a successful build do not establish correct content or behavior.

The existing frontend calculator parity fixture also fails at calculateEdge: the test expects camelCase fields, while the implementation returns snake_case fields. The parlay fixture has the same naming mismatch by source inspection. The test was exercised through TypeScript transpilation and Node's assertions after the usual test launcher encountered an environment error; details and limits are in [verification](08-verification.md). This is an existing contract/test defect, not a failure introduced by the assessment.
