# BullzIQ comprehensive assessment and enhancement plan

Inspection began October 1, 2026; reports completed October 2, 2026, America/New_York. The folder retains the inspection start date. Snapshot ages in the initial audit refer to that inspection.

## Recommendation

Make BullzIQ a **transparent overnight darts research desk**: one place to understand a matchup, inspect the evidence, explore scenarios, and verify forecasts after the result. The strongest differentiator is a reproducible prediction history with honest uncertainty, combined with excellent darts-specific analysis.

The app has useful foundations, but its current preview is not ready to support claims of measured predictive or betting performance. It displays a hard-coded 47–31 record and +8.4% ROI with zero picks in the local database. Some detail tabs render blank, probability units are wrong in several views, and July fixtures remain in the upcoming view in October.

Resolve those issues before increasing the number of markets or adding complex models. A well-calibrated, auditable baseline will create more value than an unvalidated neural model.

## Deliverables

There are **64 recommendations: 16 features, 16 design enhancements, 16 backend enhancements, and 16 model enhancements**. Every numbered recommendation includes code, a priority, an effort estimate, integration targets, dependencies, and a way to assess completion.

| Report | Contents |
|---|---|
| [01 — Current-site assessment](01-current-site-assessment.md) | Verified behavior, database audit, architectural risks, strengths, and limitations |
| [02 — Features](02-feature-enhancements.md) | F01–F16: product ideas and implementation sketches |
| [03 — Design](03-design-enhancements.md) | D01–D16: interaction, visual, mobile, and accessibility improvements |
| [04 — Backend](04-backend-enhancements.md) | B01–B16: publication, data integrity, API, reliability, and operations |
| [05 — Models](05-model-enhancements.md) | M01–M16: forecasting, evaluation, calibration, and experimental directions |
| [06 — Research and inspiration](06-research-and-inspiration.md) | Sites, GitHub repositories, papers, experts, and source limitations |
| [07 — Prioritized roadmap](07-prioritized-roadmap.md) | All 64 items in one backlog, delivery sequence, gates, and tradeoffs |
| [08 — Verification](08-verification.md) | Document checks, numerical checks, and what was not executed |

## How to interpret the recommendations

- **P0 — Correctness or release blocker:** fix before a public production release or publishing performance claims.
- **P1 — Next delivery cycle:** high-value foundation or a useful feature after its dependencies.
- **P2 — Subsequent experiment:** valuable differentiator, conditional on data and validation.
- **P3 — Research option:** potentially distinctive, but unsuitable for the critical path.

Effort is an estimate for an engineer familiar with this repository: **S = 0.5–2 engineering days**, **M = 3–7 days**, **L = 2–4 weeks**. These are planning ranges, not quotes; source licensing, data acquisition, and prospective evaluation can take much longer.

Priorities reflect observed defects, user benefit, dependency order, evidence availability, and maintenance cost. They do not assert that a feature will increase profit or prediction accuracy.

The same underlying improvement may appear in several categories because it has distinct deliverables: F02 defines the public scorecard, B03 defines its durable ledger, M04 defines its statistics, and D04 defines its honest empty state. They are one coordinated initiative, not four unrelated projects.

## Architectural contract

~~~text
Historical sources       Odds provider
       |                      |
GitHub Actions data job   Dedicated overnight odds job
       |                      |  credentials + refresh permission only here
       +------ validated data + forecasts + manifest -------+
                              |
                 Versioned immutable serving snapshot
                              |
                 Render: read-only FastAPI routes
                              |
                 Cloudflare: React frontend
                              |
                  Local interactive calculators
~~~

Serve cached prices from the previous successful overnight run. Publish collection timestamps and failed-run status. There are **no visitor-triggered provider calls, startup refreshes, browser polling, continuous odds workers, request-time Elo rebuilds, or request-time training** in these proposals. Browser navigation may request saved data; it never initiates provider collection.

If the overnight job fails, preserve the last valid snapshot and label its age. Do not relabel that snapshot as current, and do not infer that missing prices mean sportsbooks have not opened markets.

## What the included code represents

The code is original **proposed implementation material**, not production changes. Pure functions can be used as starting implementations; UI and workflow examples require the stated integration, schemas, dependencies, and tests. The verification report distinguishes syntax checks and numerical exercises from end-to-end testing.

No application source, data snapshot, GitHub workflow, or existing plan was intentionally changed for this assessment. No deployment, provider refresh, scrape, training run, commit, or push was requested or performed. Existing uncommitted work was present and is outside the new report folder.

## Read first

Start with the findings in report 01, then the P0/P1 delivery sequence in report 07. Use reports 02–05 as implementation briefs. Report 06 records exactly what the outside research supports; the sources are inspiration and evidence, not proof that these models will work on BullzIQ.
