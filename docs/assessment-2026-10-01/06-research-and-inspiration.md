# Research, sites, repositories, and expert perspectives

Sources were inspected during October 1–2, 2026. This report distinguishes observed product patterns, repository documentation, and published findings from BullzIQ's proposed implementations. Code in the recommendation reports is original illustrative code, not copied implementations.

Public visibility does not establish permission to scrape, redistribute data, or reuse code. Any future integration needs its own source-access and license review. No accounts were created, providers refreshed, repositories installed, or experts contacted for this assessment.

## Product inspiration

| Source inspected | Useful pattern | BullzIQ adaptation | Recommendation IDs |
|---|---|---|---|
| [Darts Orakel](https://dartsorakel.com/) | Navigation organized around events, player statistics, head-to-head comparisons, rankings, and specialist analysis; event-oriented information | A match passport joining evidence that currently lives in separate pages; player comparison with genuine coverage and sample counts | F04, F05, F14, D15 |
| [DartConnect](https://www.dartconnect.com/) | Scoring, player information, match history, and organization around participants and events | Stable player identity, a useful saved research shortlist, and complete event dossiers | B05, F10, F16 |
| [OddsPortal darts](https://www.oddsportal.com/darts/) | Odds comparison, historical results, favorites, and multiple odds formats | Comparable saved book quotes, visible collection times, and user-selectable display units | F08, F09, D14 |

These are interface observations, not audits of their internal algorithms or data quality. BullzIQ should preserve its overnight architecture: DartConnect-style participant organization does not imply a real-time feed, and OddsPortal-style comparison does not imply intraday collection.

The creative opportunity is to combine **forecast replay, a public audit trail, and darts-specific format exploration**. A user could bookmark a matchup, inspect the exact overnight evidence, test a hypothetical format, and later see how the frozen forecast scored. This gives the site an identity beyond another leaderboard or list of picks.

## GitHub inspiration

Repository pages and available README material were reviewed. None of these projects was installed, executed, or independently benchmarked.

| Repository | Observed direction | Practical adaptation | Limits |
|---|---|---|---|
| [matt24ck/darts-predictor](https://github.com/matt24ck/darts-predictor) | README/tree describe darts ingestion, Elo, 180 prediction, format parameters, Parquet outputs, and rating experiments | Separate ingestion, rating experiments, props experiments, and published artifacts; compare rating alternatives instead of assuming Elo is optimal | README claims are not verified forecast performance. Attempts to inspect some raw model files were unsuccessful; this assessment does not claim a line-by-line model audit |
| [TanStack Query](https://github.com/TanStack/query) | Server-state caching and query lifecycle tools | Version-keyed saved-data cache and lazy loading | Defaults must be changed to disable focus/reconnect refetch and intervals under this repository's policy |
| [Radix Primitives](https://github.com/radix-ui/primitives) | Reusable accessible interaction primitives | Single-owner tabs, keyboard behavior, evidence drawers | A library does not automatically make labels, contrast, or charts accessible; custom styling still needs verification |
| [FastAPI full-stack template](https://github.com/fastapi/full-stack-fastapi-template) | Structured API/frontend configuration and deployment patterns | Environment-specific API origins, typed contracts, reproducible checks | Do not import unnecessary authentication, databases, or services into a small read-only research app |
| [Pandera](https://github.com/unionai-oss/pandera) | Dataframe schema validation | Offline checks for ranges, nullability, source definitions, and schema drift | Semantic provenance and point-in-time correctness need additional checks |
| [MLflow](https://github.com/mlflow/mlflow) | Experiment and model lifecycle tracking | Save model hash, feature schema, cutoff, metrics, and source batch in a lightweight registry | A continuously running tracking service is unnecessary for the first version; JSON/Actions artifacts can suffice |
| [FiveThirtyEight data](https://github.com/fivethirtyeight/data) | Published data accompanying analysis | Downloadable forecast/evaluation datasets with a data dictionary | Open data is not a proof that another model is accurate, and repository licensing must be inspected before copying |

Official implementation guidance also supports these proposals:

- [TanStack Query important defaults](https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults): use explicit query lifecycle settings rather than inheriting background refetch behavior. B11 disables intervals, focus refetch, and reconnect refetch.
- [SQLite online backup API](https://www.sqlite.org/backup.html): publish from a consistent snapshot instead of copying a potentially active database file. B02 adds validation, hashing, and immutable deployment around that building block.
- [GitHub Actions concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency): coordinate writers and avoid overlapping publication. Concurrency alone does not establish the required stage order; B13/B14 also require explicit dependencies.
- [WAI-ARIA tabs pattern](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/): keyboard navigation, selected state, and panel relationships inform D02.
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/): keyboard, contrast, reflow, focus, and target-size checks inform D01/D06/D16. Source review is not a conformance certification.
- [Scikit-learn probability calibration](https://scikit-learn.org/stable/modules/calibration.html): calibration needs data separated from estimator training. M03 adds chronological separation, not just a calibration wrapper.
- [Odds API documentation](https://docs.odds-api.io/): provider-specific identifiers and capabilities should drive adapters. Do not infer this account's entitlement, available books, or historical coverage from general documentation.

## Papers and what they actually justify

### 1. Empirical Bayes skill models for darts

**Martin B. Haugh and Chun Wang, “An Empirical Bayes Approach for Estimating Skill Models for Professional Darts Players.”** Preprint 2023, revised 2024; journal publication 2024. Primary sources: [arXiv](https://arxiv.org/abs/2302.10750), [journal article](https://www.degruyterbrill.com/document/doi/10.1515/jqas-2023-0084/html).

The study uses a 2019 elite-player cohort and pools dart-outcome information through an empirical Bayes approach. It evaluates predictive distributions with proper scores. It supports hierarchical pooling and a possible target-specific skill-map research direction.

**Adaptation:** M10 and M15. **Boundary:** BullzIQ lacks target/hit-level observations. The paper does not prove an edge at saved sportsbook prices, nor provide a license or pipeline for this app's data acquisition.

### 2. First-mover advantage in asymmetric darts contests

**Daniel Goller, “Analysing a built-in advantage in asymmetric darts contests using causal machine learning.”** Preprint 2020; Annals of Operations Research publication 2023. Primary source: [arXiv paper](https://arxiv.org/abs/2008.07165).

The study estimates a first-mover advantage, with heterogeneity across contests. Its reported aggregate effect is evidence to investigate starter information, not a coefficient that should be copied into BullzIQ.

**Adaptation:** M09 and the starter-conditioned M08 kernel. **Boundary:** known starter, event rules, and player controls are required. An unknown bull-off result must remain unknown or be marginalized under a stated prior.

### 3. Hot-hand effects deserve caution

**Marius Ötting, Roland Langrock, Christian Deutscher, and Vianey Leos-Barajas, “The Hot Hand in Professional Darts.”** Journal of the Royal Statistical Society: Series A, 183(2), 2020, 565–580; first published online 2019. Primary source: [journal article](https://academic.oup.com/jrsssa/article/183/2/565/7056303).

The study analyzes 167,492 throws with a latent state-space approach and finds weak evidence for a hot hand. It does not support treating a short winning streak as a reliably persistent change in ability.

**Adaptation:** test opponent-adjusted form in M11, and reserve latent performance models for richer data. **Boundary:** match-level wins are a different observation process from individual throws.

### 4. Calibration needs empirical validation

**Chuan Guo, Geoff Pleiss, Yu Sun, and Kilian Q. Weinberger, “On Calibration of Modern Neural Networks.”** ICML 2017. Primary source: [PMLR](https://proceedings.mlr.press/v70/guo17a.html).

The paper shows that accuracy and calibration differ and studies temperature scaling on neural-network tasks. It motivates measuring probability quality.

**Adaptation:** M03, M04, D09. **Boundary:** it does not establish that temperature scaling, isotonic regression, or a neural network improves darts forecasts. The simple chronological sigmoid challenger in M03 must earn adoption through testing.

### 5. Leakage can invalidate apparent progress

**Sayash Kapoor and Arvind Narayanan, “Leakage and the Reproducibility Crisis in Machine-Learning-based Science.”** 2022 preprint. Primary source: [arXiv](https://arxiv.org/abs/2207.07048).

The authors examine leakage and reproducibility failures in machine-learning research. This is directly relevant when current player summaries appear inside historical training rows.

**Adaptation:** M01, M02, B15, F03. **Boundary:** this assessment identifies a leakage risk in current code, not a measured estimate of how much accuracy it inflated. Rebuilding features is needed to quantify the effect.

### 6. Rating deviation and inactivity

**Mark E. Glickman, “Example of the Glicko-2 system.”** Primary technical note: [Glicko-2 PDF](https://www.glicko.net/glicko/glicko2.pdf).

Glicko-2 includes rating, rating deviation, and volatility, with uncertainty changes during inactivity. Its worked example is a useful implementation reference.

**Adaptation:** M06. **Boundary:** rating deviation is not automatically a confidence interval for next-match probability. A full implementation includes volatility solving and rating-period updates beyond the two building blocks shown in M06.

### 7. Forecast scores should reward honest probabilities

**Ryan Tibshirani, “Forecast Scoring and Calibration,” Berkeley statistical learning lecture.** Primary teaching source: [lecture PDF](https://www.stat.berkeley.edu/~ryantibs/statlearn-s23/lectures/calibration.pdf).

The lecture connects proper scoring and calibration. It supports evaluating forecasts with more than win rate.

**Adaptation:** M04, F02, F15. **Boundary:** scores still need a clearly defined eligible population, temporal evaluation, and sample uncertainty; they do not directly measure betting profitability.

### 8. Conformal prediction is conditional on assumptions

**Anastasios N. Angelopoulos and Stephen Bates, “A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification.”** 2021 preprint. Primary source: [arXiv](https://arxiv.org/abs/2107.07511).

Conformal methods provide prediction sets under stated assumptions, including exchangeability for standard guarantees. Darts outcomes are temporally dependent and the player population changes.

**Adaptation:** optional uncertainty diagnostics in M16. **Boundary:** a prediction set is not a probability-parameter confidence interval, and distribution-free language must not be applied without the required assumptions.

## Expert review that would be valuable before advanced adoption

These are areas of expertise to seek, not endorsements or consultations that occurred:

| Question to resolve | Relevant expertise/source | Deliverable to request |
|---|---|---|
| Is the outcome likelihood appropriate for observed dart targets? | Haugh and Wang's empirical Bayes work | Data-definition review and held-out distribution evaluation plan |
| Does the rating updater correctly handle sparse activity? | Glickman's rating-system methodology | Reference-case audit and rating-period sensitivity analysis |
| Can throw-order effects be identified with these sources? | Goller's asymmetric-contest analysis | Starter availability audit and controls for selection/format |
| Are probabilities scored and calibrated honestly? | Tibshirani's forecast-scoring material | Paired temporal comparison, reliability plot, uncertainty methodology |
| Are “form” and “streak” features defensible? | Ötting and coauthors' state-space analysis | Observation-level model review and simpler baseline comparison |
| Does any historical feature see the future? | Kapoor and Narayanan's leakage framework | Reproducibility and cutoff audit |

An analyst familiar with PDC formats and a source/data-rights owner would also be valuable. Correct event rules and lawful usable observations often matter more than a more complicated estimator.

## Research intentionally not treated as established

- A Metaculus scoring-help page was attempted but was unavailable during inspection; no recommendation relies on a claimed walkthrough of it.
- Some darts-predictor raw-file requests failed; README architecture is used as inspiration only.
- No outside site's private model, subscription tool, source reliability, or prospective profit record was independently verified.
- No paper establishes that BullzIQ should deploy deep learning, reinforcement learning, a hot-hand bonus, or a universal throw-order adjustment today.
- No public source substitutes for this app's own prospective forecast ledger and data-access agreement.

## Recommended research order

1. Establish point-in-time data and honest scores.
2. Compare neutral Elo and regularized paired comparisons on identical future folds.
3. Add calibrated probability and saved market benchmarks.
4. Source actual formats and measured denominators before props models.
5. Run uncertainty-aware and hierarchical challengers offline.
6. Pursue dartboard policy research only after visit-level data is available and validated.
