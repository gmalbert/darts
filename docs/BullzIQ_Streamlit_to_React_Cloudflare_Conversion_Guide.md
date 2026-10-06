# BullzIQ Darts: Streamlit → React + Cloudflare Conversion Guide

## Purpose

Convert `gmalbert/darts` from its current Streamlit application into a React application with a Cloudflare-native serving architecture while preserving **full feature parity and strict design parity**.

This migration is not a redesign.

The React application must reproduce the current BullzIQ product as faithfully as practical, including:

- page hierarchy;
- navigation structure;
- logo placement;
- colors;
- spacing;
- cards;
- charts;
- tables;
- warnings and legal notices;
- column proportions;
- responsive behavior;
- terminology;
- model outputs;
- odds behavior;
- filters;
- calculators;
- theme behavior.

The new implementation may improve technical architecture, routing, performance, maintainability, and responsiveness, but it must not materially alter the current visual language or user-facing behavior unless explicitly documented and approved.

---

# 1. Target Architecture

Use a Cloudflare-first architecture.

Preferred production architecture:

```text
Historical / modeling / seeding jobs
Python + GitHub Actions
        │
        ├─ historical PDC data scraping
        ├─ Elo calculations
        ├─ model training / calibration
        ├─ database refreshes
        ├─ prediction generation
        └─ best-bets export
        │
        ▼
Cloudflare D1 / R2
        │
        ▼
Cloudflare Worker API
TypeScript preferred
        │
        ▼
React + TypeScript + Vite
served through Cloudflare Workers/static assets
```

The current Streamlit app should not be recreated as a long-running Python web server unless a specific endpoint genuinely requires Python.

For the initial conversion:

- React replaces Streamlit.
- D1 replaces the tracked SQLite serving database.
- Cloudflare Worker API replaces `db/queries.py` as the public serving/query layer.
- GitHub Actions retains Python scraping/modeling jobs where practical.
- Cloudflare Cron may replace lightweight APScheduler jobs where appropriate.
- Python-heavy historical/model tasks stay in Python.

---

# 2. Preserve Existing Data/Model Responsibilities

Do not rewrite the analytical model merely because the UI is changing.

Preserve:

- Elo ratings;
- Elo history;
- logistic-regression match predictor;
- calibrated probabilities;
- recent-form calculations;
- 3-dart average features;
- checkout percentage features;
- 180-rate features;
- H2H;
- tournament-specific form;
- PDC ranking differential;
- format effects;
- model edge;
- confidence grading;
- steam-move detection;
- odds movement;
- model-record reporting;
- best-bets export semantics.

Any calculation that currently produces user-visible numbers must be validated numerically against the existing Streamlit version.

---

# 3. Current Application Hierarchy

Preserve the current primary information architecture.

Current top-level product structure:

```text
Home / Predictions
Players
Matches
Tournaments
Odds
Tools
```

The React router should map this into real URLs:

```text
/
/players
/players/:playerId
/matches
/matches/:matchId
/tournaments
/tournaments/:tournamentId
/odds
/tools
```

Do not reorder or rename primary destinations unless the current Streamlit app already does so.

Sub-tabs and section ordering must also be preserved.

---

# 4. Strict Visual Parity Requirement

The migration must achieve **visual parity**, not merely feature parity.

The React version should match the Streamlit application in:

- page hierarchy;
- navigation structure;
- page order;
- tab order;
- section order;
- logo placement;
- logo dimensions;
- spacing above/below logo;
- page widths;
- container widths;
- horizontal spacing;
- vertical rhythm;
- card borders;
- border radii;
- internal card padding;
- card background colors;
- text colors;
- muted text colors;
- accent colors;
- success/positive colors;
- negative colors;
- divider placement;
- button size;
- button placement;
- button colors;
- table headers;
- table striping/backgrounds;
- chart palettes;
- chart backgrounds;
- chart margins;
- warning boxes;
- informational boxes;
- gambling notices;
- affiliate notices;
- footers;
- typography scale;
- column proportions;
- desktop behavior;
- tablet behavior;
- mobile behavior.

Do not substitute a generic component-library visual style.

Do not "modernize" BullzIQ into a different design system.

React should feel like the same site implemented with a better frontend architecture.

---

# 5. Visual Reference Document

Before implementing React, create:

```text
docs/STREAMLIT_VISUAL_REFERENCE.md
```

This document is mandatory.

It must inventory every current page and important state.

For every screen, document:

```text
Page name
Route equivalent
Streamlit source file
Primary sections
Tab names
Column layout
Column ratios
Logo placement
Card structure
Table structure
Chart structure
Warning/info boxes
Filters
Buttons
Empty states
Theme differences
Responsive observations
```

Include screenshots wherever possible.

Recommended structure:

```markdown
# BullzIQ Streamlit Visual Reference

## Global Shell
- Sidebar/navigation width
- Logo placement
- footer
- theme
- page margins

## Home
### Header
### Metric Row
### Today's Picks
### Schedule
### Steam Moves
### Model Info
### Historical

## Players
...

## Matches
...

## Tournaments
...

## Odds
...

## Tools
...
```

The visual reference document becomes the acceptance baseline for the React implementation.

---

# 6. Screenshot Baseline Requirement

Before React development:

1. run the current Streamlit application;
2. populate it with a known-good snapshot of real data;
3. capture screenshots of every page;
4. capture every major tab;
5. capture representative populated states;
6. capture empty/no-lines/no-data states;
7. capture warnings;
8. capture both day and night themes.

Store baseline screenshots under something like:

```text
parity/
  streamlit/
    desktop/
    tablet/
    mobile/
```

Do not rely on memory or manually written notes alone.

---

# 7. Required Viewports

Screenshot parity must be tested across multiple viewport sizes.

Minimum required sizes:

```text
Desktop wide:     1440 x 1000
Desktop standard: 1280 x 800
Tablet:            768 x 1024
Mobile large:      430 x 932
Mobile standard:   390 x 844
Mobile narrow:     375 x 812
```

Additional sizes may be added.

Do not validate only on desktop.

---

# 8. Screenshot-Based Parity Tests

Create automated visual parity tooling using Playwright.

Recommended files:

```text
parity/
  capture_streamlit.ts
  capture_react.ts
  compare.ts
  config.ts
  streamlit/
  react/
  diff/
```

For each defined viewport:

1. launch/open Streamlit;
2. navigate to the required screen;
3. wait for charts/tables/fonts/data;
4. capture a screenshot;
5. capture the same screen in React;
6. generate a visual diff;
7. save the diff artifact.

Visual diff failures must be reviewable.

Where exact pixel parity is impossible because Streamlit itself renders browser/platform-specific widgets, document the exception.

Do not use that exception to excuse general spacing/layout mismatch.

---

# 9. Visual Acceptance Criteria

A page is not complete merely because all content appears.

A page passes visual acceptance only when:

- primary sections are in the same order;
- logo is in the correct location;
- navigation is structurally equivalent;
- cards have materially matching widths/heights;
- card internal padding is materially equivalent;
- columns use the same relative proportions;
- charts use equivalent dimensions;
- charts use matching theme tokens;
- charts use equivalent legends/labels;
- tables contain the same visible columns;
- tables use equivalent density;
- warning/info boxes appear in the same contextual positions;
- footer/disclaimer placement is equivalent;
- desktop spacing is equivalent;
- mobile stacking preserves the intended hierarchy;
- no section appears unexpectedly compressed or expanded;
- text does not wrap materially differently because of incorrect column widths;
- no major visual element shifts to another part of the page.

If screenshots show an obvious visual mismatch, the page is not finished.

---

# 10. Responsive Parity

React should preserve the current desktop composition while making mobile behavior deliberate.

Do not simply let CSS collapse unpredictably.

For each desktop column layout, define how it should behave on smaller screens.

Example:

```text
Desktop:
3 : 1 card layout

Tablet:
2 : 1

Mobile:
1 column
```

Preserve information priority.

For cards with multiple statistics:

```text
Desktop:
4 columns

Mobile:
2 x 2 grid
```

Do not remove data merely to make mobile easier.

Tables may:

- become horizontally scrollable;
- collapse lower-priority columns;
- switch to card views;

but any such deviation must be documented in `STREAMLIT_VISUAL_REFERENCE.md` and justified by mobile usability.

---

# 11. Theme Parity

BullzIQ currently uses automatic time-based themes.

Preserve:

```text
Day:
Light - Sky Glass

Night:
Dark - Petrol
```

Do not add a manual theme dropdown unless explicitly requested.

Theme selection must use browser-local time.

The exact current transition window must be confirmed from the code/reference baseline and reproduced.

Preserve existing CSS variables/tokens conceptually.

Create React theme tokens equivalent to:

```text
background
card background
hover/input background
text
muted
border
accent
secondary accent
positive
negative
tab active
sidebar/navigation background
```

Do not hard-code unrelated colors inside individual components.

---

# 12. Navigation Parity

Preserve the current navigation hierarchy.

React may use:

- desktop sidebar;
- responsive drawer on mobile;
- equivalent selected-state highlighting.

Requirements:

- same primary page order;
- same logo relationship to navigation;
- equivalent spacing;
- equivalent selected-state visual treatment;
- mobile navigation must remain obvious and reachable.

Do not replace the existing information architecture with a dashboard-only layout.

---

# 13. Home Page Parity

Preserve the current homepage structure.

Key elements include:

```text
BullzIQ logo
divider

Top metrics:
- 30-Day Record
- Model ROI (30d)
- Active Picks Today
- Best Edge Today

Tabs:
- Today's Picks
- Schedule
- Steam Moves
- Model Info
- Historical
```

Preserve these labels unless the current app changes.

## Today's Picks

Preserve:

- minimum edge filter;
- sort control;
- pick cards;
- model disclaimer;
- matchup;
- tournament;
- round;
- match time;
- edge badge;
- confidence badge;
- Pick metric;
- DK Odds;
- Model Probability;
- DK Implied;
- reasoning expander;
- DraftKings CTA;
- warning/disclaimer context.

## Schedule

Preserve:

- days-ahead filter;
- tournament grouping;
- match date/time;
- round;
- player names;
- odds;
- "Lines not open yet" state.

## Steam Moves

Preserve:

- threshold explanation;
- steam badge;
- direction;
- odds movement;
- probability-point movement;
- timestamp;
- no-steam empty state.

## Model Info

Preserve:

- Elo explanation;
- tournament multipliers;
- margin/format explanation;
- logistic regression description;
- feature list;
- edge explanation;
- 30-day performance summary;
- Brier explanation.

## Historical

Preserve all current charts/tables/filter behavior discovered in the existing implementation.

---

# 14. Players Page

Preserve current player functionality.

Expected areas include:

- Elo ranking list;
- player lookup;
- player profile;
- nationality;
- nickname if present;
- PDC ranking;
- current Elo;
- 3-dart average;
- checkout percentage;
- 180 rate;
- recent form;
- Elo history chart;
- recent match history;
- H2H relationships where available.

Use stable player IDs in routes:

```text
/players/:playerId
```

Do not use player names as persistent IDs.

---

# 15. Matches Page

Preserve:

- upcoming matches;
- recent results;
- odds where available;
- tournament;
- round;
- date/time;
- participants;
- result;
- match-level analytics;
- H2H where present;
- odds movement where present.

Create stable:

```text
/matches/:matchId
```

Detail pages may improve navigation, but must retain existing information and visual language.

---

# 16. Tournaments Page

Preserve:

- tournament listing;
- tournament metadata;
- prestige tier;
- format;
- prize fund;
- covered status;
- relevant matches/results;
- tournament-level charts/statistics currently visible.

Use:

```text
/tournaments/:tournamentId
```

---

# 17. Odds Page

Preserve:

- current lines;
- implied probabilities;
- bookmaker labels;
- movement charts;
- opening/current odds;
- steam feed;
- missing-market state;
- "Lines not open yet" messaging;
- explanatory text around steam movement.

Current provider constraints must remain visible in behavior:

```text
odds-api.io
sport = darts
current provider/bookmaker availability
100 request/hour limit
```

The UI must not imply odds exist when the provider has not posted a market.

---

# 18. Tools Page

Preserve the existing tab structure:

```text
Edge Calculator
180s Calculator
Format Variance
Parlay Edge
```

These tools should preferably run client-side where feasible.

## Edge Calculator

Preserve:

- player selectors;
- favorite/underdog semantics;
- legs-to-win selector;
- DraftKings odds input;
- Elo probability;
- format-adjusted probability;
- implied probability;
- edge;
- expected value;
- grade;
- Elo context;
- manual entry mode;
- explanation panel.

## 180s Calculator

Preserve:

- player selector;
- legs-to-win input;
- line input;
- over odds;
- under odds;
- player average 180s/leg;
- override input;
- expected 180s;
- Poisson probabilities;
- over/under edge;
- grades;
- Poisson chart;
- explanatory note.

## Format Variance

Preserve:

- base probability slider;
- supported format set;
- favorite probability series;
- underdog probability series;
- 50% reference line;
- reference table;
- explanatory text;
- tournament-format table.

## Parlay Edge

Preserve all existing current functionality and display structure from Streamlit.

---

# 19. Cards

Do not replace existing BullzIQ cards with generic framework cards.

Create reusable components that mimic the current card language.

Suggested components:

```text
PickCard
ScheduleCard
SteamCard
MetricCard
ResultCard
WarningCard
InfoCard
PlayerCard
MatchCard
TournamentCard
```

Match:

- border tone;
- border thickness;
- radius;
- background;
- padding;
- spacing between cards;
- text hierarchy;
- badge positioning.

---

# 20. Column Proportions

Current Streamlit `st.columns()` ratios must be documented and mirrored with CSS Grid/Flexbox.

Examples from current implementation include ratios like:

```text
3 : 1
2 : 1
3 : 2 : 2 : 1.5
2 : 1.5 : 0.3 : 1.5 : 1.5
```

Do not flatten these into equal-width columns.

Where React uses CSS Grid, translate ratios directly:

```css
grid-template-columns: 3fr 1fr;
```

etc.

This requirement is part of design parity.

---

# 21. Charts

Preserve Plotly visual behavior wherever possible.

Preferred:

```text
react-plotly.js
```

Preserve:

- chart titles;
- series;
- line colors;
- bar colors;
- backgrounds;
- grid colors;
- hover behavior;
- legends;
- axes;
- reference lines;
- dimensions;
- margins;
- theme switching.

Do not substitute a different chart library unless parity can be demonstrated.

---

# 22. Tables

Preserve:

- visible columns;
- column order;
- labels;
- formatting;
- sorting behavior;
- density;
- color treatment.

Preferred React tool:

```text
TanStack Table
```

If a table must become a card view on narrow screens, preserve all important information.

---

# 23. Warning / Legal / Gambling Notices

Preserve all responsible-gambling and disclosure content.

Current elements include:

- 21+ notice;
- gambling-risk notice;
- 1-800-GAMBLER;
- NCPG link;
- affiliate/material-connection disclosure;
- model disclaimer;
- DraftKings CTA disclosure;
- Betting Oracle footer;
- informational-only language.

Do not hide or de-emphasize these during migration.

Placement must match current contextual usage.

---

# 24. Footer

Preserve the Betting Oracle footer:

- separator;
- "Powered by Betting Oracle";
- link;
- logo;
- sports prediction analytics text;
- informational-purpose disclaimer;
- responsible-wagering language.

Match spacing and hierarchy.

---

# 25. API Layer

Create versioned endpoints:

```text
/api/v1
```

Suggested endpoints:

```text
GET /api/v1/health
GET /api/v1/meta

GET /api/v1/players
GET /api/v1/players/:id
GET /api/v1/players/:id/elo-history
GET /api/v1/players/:id/matches

GET /api/v1/matches
GET /api/v1/matches/:id

GET /api/v1/tournaments
GET /api/v1/tournaments/:id

GET /api/v1/odds
GET /api/v1/matches/:id/odds-history

GET /api/v1/picks
GET /api/v1/model/record
GET /api/v1/steam
```

Use query parameters for filtering.

Example:

```text
/api/v1/matches?upcoming=true&days=7
/api/v1/picks?min_edge=1.0
/api/v1/steam?hours=24
```

---

# 26. D1 Migration

Convert the current SQLite schema to D1.

Existing tables include:

```text
players
tournaments
matches
odds_snapshots
elo_history
player_stats_cache
picks
steam_events
```

Create D1 migrations.

Preserve:

- IDs;
- foreign-key relationships where practical;
- column meaning;
- timestamps;
- uniqueness constraints;
- lookup semantics.

Do not keep a tracked `bullziq.db` as the production serving database.

The SQLite file may remain as a local/offline intermediate during migration.

---

# 27. db/queries.py Migration

The current query layer mixes:

```text
SQLAlchemy
Pandas
Streamlit cache decorators
```

Do not port this file mechanically.

Instead:

```text
React
  ↓
Worker API
  ↓
D1
```

Convert each public query into:

- D1 SQL;
- Worker service logic;
- JSON response schema.

Remove `st.cache_data` from serving concerns.

Use HTTP/cache controls where appropriate.

---

# 28. Odds Ingestion

Preserve the current `odds-api.io` semantics.

Current important rules:

- sport = darts;
- request budget;
- events-list caching;
- bookmaker filtering;
- placeholder-player filtering;
- near-term fixture filtering;
- batched `/odds/multi`;
- odds conversion;
- implied-probability conversion;
- missing-market handling.

Do not regress to per-event unbatched requests.

---

# 29. Scheduler Migration

Current jobs:

```text
Odds refresh
Steam detection
Nightly stats rebuild
```

Preferred migration:

```text
Cloudflare Cron Triggers
```

for lightweight D1/API work.

Keep GitHub Actions for:

- historical scraping;
- full reseeding;
- model training;
- large Python jobs.

Do not force every scheduled job into Workers.

---

# 30. Historical Data Seeding

Historical scraping may remain in GitHub Actions/Python.

Current sources include PDC/dartsdatabase-related scraping.

Preserve:

- real-data-first behavior;
- no silent demo fallback;
- failure visibility;
- incremental refresh;
- full rebuild option.

After successful seeding, publish/update D1.

Do not require the React app to perform historical scraping.

---

# 31. Model Training

Keep Python for training initially.

Pipeline:

```text
historical matches
    ↓
feature generation
    ↓
scikit-learn model
    ↓
calibration
    ↓
predictions / picks
    ↓
D1
```

Do not run scikit-learn inside ordinary Worker HTTP requests.

---

# 32. Client-Side Calculators

Where calculations are deterministic and lightweight, port them to TypeScript.

Candidates:

- American odds conversion;
- implied probability;
- edge calculation;
- expected value;
- Elo probability;
- format adjustment;
- 180 Poisson probabilities;
- parlay edge math.

Create parity tests against existing Python outputs.

Do not change formulas.

---

# 33. Component Architecture

Recommended structure:

```text
frontend/
  src/
    app/
      router.tsx
      providers.tsx

    components/
      layout/
      cards/
      charts/
      tables/
      badges/
      legal/
      controls/

    pages/
      HomePage.tsx
      PlayersPage.tsx
      PlayerDetailPage.tsx
      MatchesPage.tsx
      MatchDetailPage.tsx
      TournamentsPage.tsx
      TournamentDetailPage.tsx
      OddsPage.tsx
      ToolsPage.tsx

    api/
    hooks/
    types/
    utils/
    theme/
```

Avoid giant page files.

---

# 34. Design Tokens

Create:

```text
src/theme/tokens.ts
```

Mirror the Streamlit theme configuration.

Do not scatter hex values.

Use CSS variables.

Example:

```css
--biq-bg
--biq-bg2
--biq-bg3
--biq-text
--biq-muted
--biq-border
--biq-accent
--biq-accent2
--biq-pos
--biq-neg
--biq-tab
--biq-sidebar
```

---

# 35. Loading States

Streamlit hides much of its rerender lifecycle.

React must implement explicit states.

For every data surface support:

```text
loading
success
empty
error
stale
```

Do not allow large blank regions while requests are pending.

Loading states should visually fit BullzIQ.

---

# 36. Empty States

Preserve current copy wherever possible.

Examples:

```text
No picks meet the current edge filter.
No upcoming matches in the database.
No steam moves detected in the last 24 hours.
Lines not open yet.
```

Do not replace meaningful sports-specific empty states with generic "No data".

---

# 37. Error States

Errors should distinguish:

```text
API unavailable
odds unavailable
historical data unavailable
provider rate limited
no market posted
database empty
model outputs unavailable
```

Do not collapse everything into:

```text
Something went wrong
```

---

# 38. Performance

React should improve perceived performance.

Use:

- route-level code splitting;
- TanStack Query;
- sensible caching;
- pagination;
- server-side filtering;
- D1 indexes;
- lazy chart loading where helpful.

Do not load the entire historical dataset into the browser.

---

# 39. Accessibility

Maintain or improve accessibility without changing the visual design.

Require:

- semantic navigation;
- keyboard-accessible controls;
- visible focus states;
- sufficient contrast;
- form labels;
- chart context;
- accessible tables;
- button/link distinction.

---

# 40. Testing

## Backend / Worker

Test:

- query filters;
- odds conversion;
- implied probability;
- steam calculation;
- empty markets;
- API response schemas;
- time/date handling.

## Model parity

Compare:

- Elo;
- probability outputs;
- edge;
- confidence;
- expected value;
- grades.

## Frontend

Test:

- filters;
- navigation;
- cards;
- tabs;
- calculators;
- empty states;
- legal notices;
- responsive layout.

## End-to-end

Use Playwright for:

```text
Home
Players
Player detail
Matches
Match detail
Tournaments
Odds
Tools
```

---

# 41. Numerical Parity

For fixed test fixtures, outputs must match Streamlit/Python.

Set explicit tolerances.

Recommended:

```text
odds conversion: exact
implied probability: <= 1e-6
edge: <= 1e-6
Elo calculation: <= 1e-6
format adjustment: <= 1e-6
Poisson probability: <= 1e-6
display rounding: same displayed value
```

---

# 42. Visual Parity Checklist

For each page verify:

- [ ] same page hierarchy
- [ ] same navigation order
- [ ] same page title
- [ ] logo matches position
- [ ] logo matches visual size
- [ ] same top spacing
- [ ] same section sequence
- [ ] equivalent dividers
- [ ] equivalent card widths
- [ ] equivalent card heights
- [ ] equivalent card padding
- [ ] same border radius
- [ ] matching colors
- [ ] same muted text treatment
- [ ] same warning placement
- [ ] same table column order
- [ ] same chart order
- [ ] same chart size
- [ ] same chart colors
- [ ] same tab ordering
- [ ] same labels
- [ ] same control ranges/defaults
- [ ] same empty states
- [ ] same disclaimers
- [ ] same footer
- [ ] same desktop column ratios
- [ ] appropriate mobile stacking
- [ ] no horizontal overflow
- [ ] screenshots reviewed
- [ ] visual diffs accepted

---

# 43. Desktop Visual Acceptance

At 1280px and 1440px:

- content width must visually match Streamlit;
- major cards must line up;
- header/logo must not drift;
- metric rows must preserve proportions;
- columns must preserve ratios;
- charts must occupy equivalent vertical space;
- tables must not become unnecessarily sparse;
- whitespace must not materially expand or contract.

---

# 44. Mobile Visual Acceptance

At 375–430px:

- navigation remains available;
- logo remains visible and proportionate;
- cards stack cleanly;
- controls are usable;
- text does not overflow;
- metric grids reflow deliberately;
- tables remain usable;
- tabs remain reachable;
- disclaimers remain readable;
- no chart is wider than viewport;
- no content is clipped;
- visual hierarchy remains consistent with desktop.

---

# 45. Migration Phases

## Phase 0 — Freeze Baseline

- capture current screenshots;
- capture day/night themes;
- capture populated/empty states;
- capture desktop/mobile;
- record data outputs;
- store known-good DB snapshot;
- document current bugs separately.

## Phase 1 — Visual Reference

Create:

```text
docs/STREAMLIT_VISUAL_REFERENCE.md
```

No React implementation should begin before this document is usable.

## Phase 2 — D1 Schema

Translate SQLite schema to D1.

## Phase 3 — Data Publishing

Update GitHub workflows to populate D1.

## Phase 4 — Worker API

Implement core endpoints.

## Phase 5 — React Shell

Implement:

- navigation;
- themes;
- layout;
- logo;
- footer;
- responsive shell.

Validate shell screenshots before page work.

## Phase 6 — Home Page

Implement all home tabs with strict screenshot parity.

## Phase 7 — Players

Implement list/detail.

## Phase 8 — Matches

Implement list/detail.

## Phase 9 — Tournaments

Implement list/detail.

## Phase 10 — Odds

Implement current lines/history/steam.

## Phase 11 — Tools

Port calculators with numerical parity.

## Phase 12 — Responsive Pass

Validate all required viewport sizes.

## Phase 13 — Screenshot Diff Gate

No page is complete without accepted diffs.

## Phase 14 — Parallel Run

Run Streamlit and React concurrently.

## Phase 15 — Cutover

Move public traffic after parity acceptance.

---

# 46. Definition of Done

The migration is complete only when all of the following are true:

1. Every Streamlit feature exists in React.
2. Every primary page has an equivalent React route.
3. D1 replaces SQLite for production serving.
4. Heavy Python work remains outside HTTP request paths.
5. Model outputs match.
6. Calculators match.
7. Odds semantics match.
8. Warning/empty states match.
9. Responsible-gambling content is preserved.
10. Theme behavior matches.
11. Page hierarchy matches.
12. Navigation matches.
13. Logo placement matches.
14. Colors match.
15. Spacing matches.
16. Cards match.
17. Charts match.
18. Tables match.
19. Warnings match.
20. Column proportions match.
21. Desktop screenshots pass review.
22. Tablet screenshots pass review.
23. Mobile screenshots pass review.
24. Visual-reference documentation is complete.
25. Screenshot diffs are stored and reviewable.
26. Streamlit can be removed without losing functionality.

---

# 47. Coding-Agent Master Prompt

Use this prompt when handing the work to a coding model:

> Convert the BullzIQ darts repository from Streamlit to React + TypeScript + Vite with a Cloudflare-native backend architecture. Preserve complete feature parity and strict visual/design parity. Do not redesign the product. Match the existing page hierarchy, navigation, logo placement, colors, theme behavior, spacing, cards, charts, tables, warnings, legal notices, column proportions, responsive behavior, tab ordering, control defaults, labels, empty states, and footer. Before implementation, create `docs/STREAMLIT_VISUAL_REFERENCE.md` documenting every current page, tab, section, layout ratio, visual token, important component, responsive behavior, and screenshot baseline. Capture current Streamlit screenshots at desktop, tablet, and mobile sizes, including both Sky Glass day and Petrol night themes. Build automated Playwright screenshot capture for both Streamlit and React and produce visual diffs. A page is not complete until its screenshots have been reviewed and major layout/style discrepancies are resolved. Preserve all current model, Elo, odds, edge, confidence, steam, and calculator semantics. Use numerical parity tests against fixed fixtures. Move the serving database from tracked SQLite to Cloudflare D1 while keeping heavy historical scraping/modeling in Python/GitHub Actions. Use a Cloudflare Worker API for lightweight queries and odds-serving logic. Do not run scikit-learn or other heavy Python ML inside ordinary Worker HTTP requests. Preserve odds-api.io batching and rate-limit protections. Preserve all responsible-gambling, affiliate, model-disclaimer, DraftKings CTA, and Betting Oracle footer content. React may improve implementation quality, routing, accessibility, caching, and responsive mechanics, but it must visually and functionally remain BullzIQ.

---

# 48. Non-Negotiable Principle

This project is:

```text
A framework migration
not
A redesign
```

The target result should look and behave like BullzIQ, not like a new product inspired by BullzIQ.
