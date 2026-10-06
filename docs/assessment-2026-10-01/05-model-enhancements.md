# Model enhancements — 16 proposals

All training, feature rebuilding, calibration, simulation batches, and evaluation below belong in GitHub Actions. Render serves the resulting artifacts and saved forecasts. Lightweight hypothetical calculators may execute locally; they must identify their assumptions.

Current data limits are decisive: all 6,548 matches lack recorded averages, every match has a default race-to-six format, none has a set format, and the 23 populated player-stat profiles come from hard-coded seed metadata. There is no prospective pick ledger. Do not manufacture observations to unlock a model.

Code is proposed implementation material. Numerical sketches are deliberately explicit about assumptions. Third-party scientific dependencies must be pinned and validated in the offline environment; their presence is not implied by these snippets. Research references and their limitations are in [report 06](06-research-and-inspiration.md).

## M01 — Point-in-time feature reconstruction

**Priority P0 · Effort L.** Targets: db/seed_real.py, models/predictor.py, future offline feature builder. Dependencies: B05, B06, B15.

Current seeding initializes historical ratings using today's curated player metadata; the predictor can read one current stats cache for every historical match. This can leak future information. Start historical Elo with a documented neutral prior and only use observations available before each forecast cutoff. Save the feature cutoff and source version with every row.

~~~python
from datetime import datetime

def latest_known(observations, player_id: int, cutoff: datetime):
    """Rows contain timezone-aware available_at and measured_at."""
    eligible = [
        row for row in observations
        if row["player_id"] == player_id
        and row["available_at"] < cutoff
        and row["measured_at"] < cutoff
    ]
    return max(eligible, key=lambda row: row["measured_at"], default=None)

def initial_rating(player_id: int, ratings: dict[int, float]) -> float:
    # No career summary or present-day seed metadata enters the historical prior.
    return ratings.setdefault(player_id, 1500.0)

def historical_features(match, observations, ratings):
    cutoff = match["forecast_cutoff"]
    return {
        "elo_difference": initial_rating(match["p1"], ratings)
                          - initial_rating(match["p2"], ratings),
        "p1_stats": latest_known(observations, match["p1"], cutoff),
        "p2_stats": latest_known(observations, match["p2"], cutoff),
        "cutoff": cutoff.isoformat(),
    }
~~~

When the source supplies only an event date, process the entire date/event group as a batch: make all forecasts before applying any outcomes in that group. An inferred within-day order would recreate leakage.

**Done when:** perturbing observations after a cutoff cannot change that historical forecast; every feature has traceable availability time, and a neutral-prior baseline is reproducible.

## M02 — Grouped, expanding temporal validation

**Priority P0 · Effort M.** Targets: models/predictor.py and offline evaluation. Dependencies: M01 and reliable event/date groups.

Replace random cross-validation with chronological train → calibration → test windows. Keep complete events together, leave ambiguous boundary events out, and never tune on the final test window. Report performance by era, event type, format, and coverage.

~~~python
def temporal_fold(rows, train_end, calibration_end, test_end):
    """All boundaries and row timestamps are aware UTC datetimes."""
    groups = {}
    for row in rows:
        groups.setdefault(row["event_group"], []).append(row)
    split = {"train": [], "calibration": [], "test": []}
    for group in groups.values():
        first = min(r["forecast_cutoff"] for r in group)
        last = max(r["result_available_at"] for r in group)
        if last < train_end:
            split["train"].extend(group)
        elif first >= train_end and last < calibration_end:
            split["calibration"].extend(group)
        elif first >= calibration_end and last < test_end:
            split["test"].extend(group)
        # A group spanning a boundary is excluded from this fold.
    assert not (
        {r["event_group"] for r in split["train"]}
        & {r["event_group"] for r in split["test"]}
    )
    return split
~~~

Repeat with expanding training windows and later test blocks. Keep the same folds across candidates so score differences are paired. Missing result-availability timestamps require an explicit conservative policy, not inferred exact times.

**Done when:** no event or post-cutoff observation crosses a boundary, hyperparameter selection is isolated, and held-out forecasts are saved independently of tuning.

## M03 — Conservative chronological probability calibration

**Priority P1 · Effort M.** Targets: models/predictor.py calibration and offline artifacts. Dependencies: M01–M02.

The current scaler is fitted before CalibratedClassifierCV, and isotonic calibration uses five folds without demonstrated temporal isolation. Fit preprocessing exclusively on training data. Compare uncalibrated probabilities, regularized sigmoid calibration, and isotonic calibration using a later test window. Small datasets often cannot support a flexible curve.

~~~python
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

def logit_column(probabilities):
    p = np.clip(np.asarray(probabilities, dtype=float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p)).reshape(-1, 1)

def fit_chronological_model(x_train, y_train, x_cal, y_cal):
    base = make_pipeline(
        StandardScaler(with_mean=False),  # Preserve paired-feature antisymmetry.
        LogisticRegression(C=0.5, fit_intercept=False,
                           max_iter=1000, random_state=7),
    )
    base.fit(x_train, y_train)
    calibration_p = base.predict_proba(x_cal)[:, 1]
    # Zero intercept preserves p(A,B) = 1 - p(B,A) for antisymmetric features.
    calibrator = LogisticRegression(
        C=0.25, fit_intercept=False, max_iter=1000, random_state=7
    )
    calibrator.fit(logit_column(calibration_p), y_cal)
    return base, calibrator

def calibrated_prediction(base, calibrator, x):
    raw = base.predict_proba(x)[:, 1]
    return calibrator.predict_proba(logit_column(raw))[:, 1]
~~~

This version expects antisymmetric paired features: swapping players negates each feature. Use both classes and adequate temporal support in the calibration window. Regularization and the intercept constraint are choices to validate, not universally optimal settings. If the model has throw-order features, swapping players must swap those features too.

**Done when:** calibration improves a prespecified held-out proper score with useful uncertainty evidence, or the uncalibrated model remains the default.

## M04 — Measured proper scores and correctly settled returns

**Priority P0 · Effort M.** Targets: backend/api/queries.py, db/queries.py, new evaluation module. Dependencies: B03–B04.

Remove the fabricated 47–31 record, fixed Brier score, and fallback ROI. Compute Brier and log loss over the complete eligible forecast population. Compute financial returns separately over settled paper selections, with voids excluded from risked stake. A favorable selected subset cannot establish general probability quality.

~~~python
import math

def forecast_scores(rows):
    eligible = [r for r in rows if r["outcome"] in (0, 1)]
    if not eligible:
        return {"n": 0, "brier": None, "log_loss": None}
    for row in eligible:
        if not 0 <= row["probability"] <= 1:
            raise ValueError("Probability outside [0, 1]")
    brier = sum((r["probability"] - r["outcome"]) ** 2
                for r in eligible) / len(eligible)
    loss = 0.0
    for row in eligible:
        p = min(1 - 1e-12, max(1e-12, row["probability"]))
        loss -= row["outcome"] * math.log(p)
        loss -= (1 - row["outcome"]) * math.log1p(-p)
    return {"n": len(eligible), "brier": brier,
            "log_loss": loss / len(eligible)}

def net_profit(american: float, stake: float, won: bool) -> float:
    if stake < 0 or not math.isfinite(stake):
        raise ValueError("Invalid stake")
    if not math.isfinite(american) or abs(american) < 100:
        raise ValueError("Invalid American odds")
    return stake * (american / 100 if american > 0 else 100 / -american) \
        if won else -stake

def paper_roi(settled):
    risk = sum(r["stake"] for r in settled if r["status"] in ("won", "lost"))
    profit = sum(net_profit(r["american"], r["stake"], r["status"] == "won")
                 for r in settled if r["status"] in ("won", "lost"))
    return None if risk == 0 else profit / risk
~~~

Winning −150 with a $100 stake yields $66.67 net profit. Retrospective forecasts must have a separate label and must never enter a prospective record.

**Done when:** empty data yields unavailable metrics; score populations and settlement rules are visible; −150/+150 losses, wins, pushes, and voids reconcile to the ledger.

## M05 — Tune and audit a transparent Elo baseline

**Priority P1 · Effort M.** Targets: models/elo.py and db/seed_real.py. Dependencies: M01–M02.

Before adding complexity, test K, regression toward the population mean, recency, and event weighting. Avoid multiplying every historical rating by a present-day fame score. Log the before/after rating and reason for every update. Inactivity decay is a candidate, not a presumed skill decline.

~~~python
import math

def elo_probability(a, b, scale=400.0):
    return 1 / (1 + 10 ** ((b - a) / scale))

def decay_to_mean(rating, inactive_days, half_life_days=None, mean=1500):
    if half_life_days is None:
        return rating
    if half_life_days <= 0 or inactive_days < 0:
        raise ValueError("Invalid decay configuration")
    return mean + (rating - mean) * 2 ** (-inactive_days / half_life_days)

def elo_update(a, b, outcome_a, k=24.0):
    if outcome_a not in (0, 1) or k <= 0:
        raise ValueError("Invalid outcome or K")
    p = elo_probability(a, b)
    delta = k * (outcome_a - p)
    return a + delta, b - delta

EXPERIMENT_GRID = [
    {"k": k, "half_life_days": decay}
    for k in (12, 24, 40) for decay in (None, 365, 730)
]
~~~

The grid is illustrative. Select it inside temporal validation; keep a simple no-decay reference. Date-only matches require grouped updates or sensitivity analysis to ordering.

**Done when:** a reproducible Elo forecast is available for every supported matchup and any extra weighting beats its unweighted reference out of time.

## M06 — Rating uncertainty for inactive and sparsely observed players

**Priority P2 · Effort L.** Targets: models/elo.py or new rating engine. Dependencies: M02, stable player IDs.

Evaluate Glicko-2 or another uncertainty-aware rating system against Elo. Display rating deviation separately from outcome probability uncertainty. The snippet implements two Glicko-scale building blocks; it is not a full Glicko-2 updater.

~~~python
import math

GLICKO_SCALE = 173.7178

def glicko_expected(rating, opponent_rating, opponent_rd):
    mu = (rating - 1500) / GLICKO_SCALE
    opponent_mu = (opponent_rating - 1500) / GLICKO_SCALE
    phi = opponent_rd / GLICKO_SCALE
    g = 1 / math.sqrt(1 + 3 * phi * phi / math.pi ** 2)
    return 1 / (1 + math.exp(-g * (mu - opponent_mu)))

def inflate_rd(rd, volatility, inactive_periods, maximum_rd=350):
    """Volatility is on Glicko-2's internal scale; periods are configured."""
    if min(rd, volatility, inactive_periods) < 0:
        raise ValueError("Negative uncertainty input")
    phi = rd / GLICKO_SCALE
    inflated = GLICKO_SCALE * math.sqrt(
        phi * phi + inactive_periods * volatility * volatility
    )
    return min(maximum_rd, inflated)
~~~

Use Glickman's published numerical example to verify the complete volatility iteration, rating periods, and multiple-opponent updates before adoption. Do not label this RD as a 95% interval for winning the next match.

**Done when:** the implementation matches reference calculations and improves held-out forecasts or provides demonstrably useful uncertainty information.

## M07 — Regularized Bradley–Terry player strengths

**Priority P1 · Effort L.** Targets: new offline strength model. Dependencies: M01–M02, B05.

A regularized paired-comparison model is a useful interpretable challenger. Sparse players shrink toward a shared reference; unknown players receive a documented neutral encoding. Later add format, throw order, and time-varying strengths only when observed.

~~~python
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.linear_model import LogisticRegression

def matchup_matrix(matches, player_index):
    rows, columns, values = [], [], []
    for row_index, match in enumerate(matches):
        for player, sign in ((match["p1"], 1), (match["p2"], -1)):
            if player in player_index:
                rows.append(row_index)
                columns.append(player_index[player])
                values.append(sign)
    return csr_matrix(
        (values, (rows, columns)), shape=(len(matches), len(player_index))
    )

def fit_strengths(training_matches, player_index):
    x = matchup_matrix(training_matches, player_index)
    y = np.array([m["winner"] == m["p1"] for m in training_matches])
    model = LogisticRegression(
        C=0.5, fit_intercept=False, max_iter=2000, random_state=7
    )
    return model.fit(x, y)
~~~

Build the player index on training data and reject unresolved outcomes. Both unknown players map to 50%, which should trigger an insufficient-evidence label. A neutral encoding is not evidence they are equally skilled.

**Done when:** player swapping complements the prediction and the challenger is compared with Elo on identical future folds.

## M08 — Actual leg/set format probabilities and duration

**Priority P1 · Effort L.** Targets: models/props.py, tournament metadata, Tools format explorer. Dependencies: B06 and genuine leg-level estimates.

Current format adjustments stretch a match probability heuristically; 180 duration uses a fixed multiplier. Model the scoring process directly once formats and leg probabilities are known. The kernel below handles a straight race to N with alternating first throw and returns the complete final-score distribution.

~~~python
from functools import lru_cache

def leg_race_distribution(target, p_a_starts, p_b_starts, a_starts=True):
    """Both p values describe A winning a leg, conditional on its starter."""
    if target < 1 or not all(0 <= p <= 1 for p in (p_a_starts, p_b_starts)):
        raise ValueError("Invalid race inputs")

    @lru_cache(None)
    def visit(a, b):
        if a == target or b == target:
            return {(a, b): 1.0}
        starter_a = a_starts if (a + b) % 2 == 0 else not a_starts
        p = p_a_starts if starter_a else p_b_starts
        result = {}
        for next_score, weight in (((a + 1, b), p), ((a, b + 1), 1 - p)):
            for final_score, mass in visit(*next_score).items():
                result[final_score] = result.get(final_score, 0.0) + weight * mass
        return result

    return visit(0, 0)

def summarize_race(distribution, target):
    return {
        "p_a_wins": sum(p for (a, b), p in distribution.items() if a == target),
        "expected_legs": sum((a + b) * p
                             for (a, b), p in distribution.items()),
    }
~~~

Do not use an Elo match probability as the per-leg input. Set play needs an outer set-state recursion that carries the correct starter and event-specific rules. Two-clear-leg rules, sudden death, and bull-off rules require distinct verified transitions; unsupported formats should return unavailable.

**Done when:** distributions sum to one, symmetric cases behave correctly, documented event formats match scoring rules, and duration predictions beat a constant-length reference.

## M09 — Throw-order advantage with honest unknown handling

**Priority P2 · Effort L.** Targets: feature builder, M08 transitions. Dependencies: source-supported first-throw observations.

Goller's work makes throw order a plausible model input, not a universal fixed bonus. Estimate an effect chronologically with format and player controls. If the starter is unknown, marginalize over a documented prior and expose that uncertainty.

~~~python
import math

def logistic(value):
    return 1 / (1 + math.exp(-value))

def conditional_leg_probability(skill_difference, throw_coefficient, a_starts):
    sign = 1 if a_starts else -1
    return logistic(skill_difference + sign * throw_coefficient)

def leg_probability_unknown_starter(skill_difference, throw_coefficient,
                                    probability_a_starts=0.5):
    if not 0 <= probability_a_starts <= 1:
        raise ValueError("Invalid starter prior")
    on = conditional_leg_probability(skill_difference, throw_coefficient, True)
    off = conditional_leg_probability(skill_difference, throw_coefficient, False)
    return probability_a_starts * on + (1 - probability_a_starts) * off
~~~

For matches, marginalize complete starter-conditioned match distributions, rather than averaging per-leg probabilities before a nonlinear race calculation. A 50/50 prior is an assumption unless supported by bull-off data.

**Done when:** estimated effects have out-of-time support, unavailable starters remain explicitly unknown, and swapping both player identity and starter preserves symmetry.

## M10 — Hierarchical shrinkage for thin player statistics

**Priority P1 · Effort L.** Targets: player-stat pipeline, models/props.py. Dependencies: measured counts and denominators.

Avoid treating three observations as a stable player rate. Pool sparse checkout counts or comparable binary events toward a historical cohort prior; publish effective sample size. Priors must come from earlier data and compatible definitions.

~~~python
def beta_binomial_posterior(successes, attempts, prior_mean, prior_strength):
    if not 0 <= successes <= attempts or attempts < 0:
        raise ValueError("Invalid measured count")
    if not 0 < prior_mean < 1 or prior_strength <= 0:
        raise ValueError("Invalid prior")
    alpha = successes + prior_mean * prior_strength
    beta = attempts - successes + (1 - prior_mean) * prior_strength
    return {
        "alpha": alpha,
        "beta": beta,
        "mean": alpha / (alpha + beta),
        "variance": alpha * beta / (
            (alpha + beta) ** 2 * (alpha + beta + 1)
        ),
        "observed_attempts": attempts,
        "prior_equivalent_attempts": prior_strength,
    }
~~~

Do not apply this formula to three-dart averages or 180 counts without a suitable likelihood and denominator. A percentage alone cannot recover checkout attempts. Infer prior strength within training data, not by intuition after inspecting test results.

**Done when:** sparse estimates behave sensibly, source definitions agree, and shrinkage improves held-out scores over raw rates.

## M11 — Opponent-adjusted recent form

**Priority P2 · Effort M.** Targets: offline feature builder. Dependencies: M01, stable chronological forecasts.

A 7–3 record against weak opposition differs from 7–3 against elite players. Use recent outcome residuals relative to the pre-match baseline, with recency weighting and shrinkage. Keep measured scoring form separate if those statistics later become available.

~~~python
import math

def adjusted_form(history, cutoff, half_life_days=90, prior_weight=5):
    weighted_sum, total_weight = 0.0, 0.0
    for match in history:
        if match["result_available_at"] >= cutoff:
            continue
        age = (cutoff - match["result_available_at"]).total_seconds() / 86400
        weight = math.exp(-math.log(2) * age / half_life_days)
        residual = match["outcome"] - match["pre_match_probability"]
        weighted_sum += weight * residual
        total_weight += weight
    return {
        "form": weighted_sum / (prior_weight + total_weight),
        "weighted_matches": total_weight,
    }
~~~

The baseline probability must have been generated without that match's result. Tune decay and shrinkage inside training folds. Winning residuals do not identify changes in technique or psychology.

**Done when:** the feature adds stable value beyond Elo and raw win rate, and disappears gracefully for players without history.

## M12 — Consistent de-vigged market benchmarks

**Priority P1 · Effort M.** Targets: odds analytics, offline evaluation. Dependencies: B03, B15 and contemporaneous two-sided quotes.

Separate bookmaker margin from model disagreement. Calculate a baseline from both sides of the same book, market, and snapshot. Compare model scores against that baseline on matched coverage. Use actual offered odds for expected return; normalized probabilities are a benchmark.

~~~python
def american_to_decimal(price):
    if abs(price) < 100:
        raise ValueError("Invalid American price")
    return 1 + (price / 100 if price > 0 else 100 / -price)

def proportional_devig(price_a, price_b):
    raw_a = 1 / american_to_decimal(price_a)
    raw_b = 1 / american_to_decimal(price_b)
    total = raw_a + raw_b
    return {"p_a": raw_a / total, "p_b": raw_b / total,
            "overround": total - 1}

def expected_net_return(probability, offered_price):
    decimal = american_to_decimal(offered_price)
    return probability * decimal - 1
~~~

Proportional de-vigging is one assumption; test alternatives without cherry-picking. Reject mismatched times, suspended prices, incompatible market rules, and unresolved selections. Daily observations can support a **last observed pre-match price** metric, not a claim of true closing-line value.

**Done when:** market/model comparisons use identical eligible fixtures and price provenance is reproducible.

## M13 — Overdispersed 180 counts mixed over match duration

**Priority P2 · Effort L.** Targets: models/props.py and offline props evaluation. Dependencies: measured 180 counts, legs played, M08.

A Poisson count assumes variance equals the mean and the current expected-duration heuristic is unvalidated. Compare Poisson with a negative-binomial count model, mixed over the possible match lengths. Include pushes for integer lines and do not count them as unders.

~~~python
import math
from scipy.stats import nbinom

def count_market_by_duration(duration_mass, rate_per_leg, alpha, line):
    """Variance conditional on duration is mu + alpha * mu**2."""
    if rate_per_leg < 0 or alpha <= 0 or line < 0:
        raise ValueError("Invalid count-market inputs")
    if not math.isclose(sum(duration_mass.values()), 1.0, abs_tol=1e-8):
        raise ValueError("Duration distribution must sum to one")
    result = {"over": 0.0, "under": 0.0, "push": 0.0}
    for legs, weight in duration_mass.items():
        if legs < 0 or weight < 0:
            raise ValueError("Invalid duration mass")
        mu = rate_per_leg * legs
        if mu == 0:
            over, under, push = 0.0, float(line > 0), float(line == 0)
        else:
            r = 1 / alpha
            p = r / (r + mu)
            over = nbinom.sf(math.floor(line), r, p)
            under = nbinom.cdf(math.ceil(line) - 1, r, p)
            push = nbinom.pmf(int(line), r, p) if float(line).is_integer() else 0
        result["over"] += weight * over
        result["under"] += weight * under
        result["push"] += weight * push
    return result
~~~

Estimate rates and dispersion from earlier measured exposure. Duration, winner, and 180 counts may share latent performance factors; same-match parlays need joint simulation rather than multiplication of marginal probabilities.

**Done when:** count calibration and integer-line settlement reconcile; a new likelihood improves held-out distribution scores over the simple reference.

## M14 — Checkout counts conditional on actual attempts

**Priority P2 · Effort L.** Targets: models/props.py and source parser. Dependencies: observed checkout successes AND attempts.

The current normal approximation to a percentage lacks attempt counts. A beta-binomial predictive count gives a coherent finite denominator and can represent uncertainty in the underlying success rate. Model attempts separately when they are not fixed.

~~~python
import math

def log_beta(a, b):
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)

def checkout_count_distribution(attempts, alpha, beta):
    if attempts < 0 or not isinstance(attempts, int) or min(alpha, beta) <= 0:
        raise ValueError("Invalid checkout inputs")
    mass = {}
    for successes in range(attempts + 1):
        log_choose = (math.lgamma(attempts + 1)
                      - math.lgamma(successes + 1)
                      - math.lgamma(attempts - successes + 1))
        mass[successes] = math.exp(
            log_choose + log_beta(successes + alpha, attempts - successes + beta)
            - log_beta(alpha, beta)
        )
    return mass
~~~

For percentage markets, convert the settlement threshold using the bookmaker's exact rules and denominator. Double attempts, checkout visits, and legs won are different quantities. Retire the market from the published forecast list until the required denominator is sourced.

**Done when:** the zero-attempt case and grading rules are explicit, and predictive scores improve on a fixed historical rate.

## M15 — Empirical Bayes dartboard skill maps and checkout policies

**Priority P3 · Effort L plus substantial data acquisition.** Targets: a separate research module. Dependencies: legitimate visit/dart-level targets, hit regions, remaining score, and match state.

Haugh and Wang offer a distinctive longer-term direction: learn player-specific hit distributions while borrowing information from peers. Use them to explain checkout routes and compare scoring policies. The present repository cannot support this; do not infer dartboard dispersion from match wins.

~~~python
def posterior_hit_probabilities(hit_counts, cohort_pseudocounts):
    """For one intended target; outcome categories include misses/bust effects."""
    outcomes = set(hit_counts) | set(cohort_pseudocounts)
    counts = {
        region: hit_counts.get(region, 0) + cohort_pseudocounts.get(region, 0)
        for region in outcomes
    }
    if any(value < 0 for value in counts.values()) or sum(counts.values()) <= 0:
        raise ValueError("Invalid multinomial posterior")
    total = sum(counts.values())
    return {region: value / total for region, value in counts.items()}

def best_target(target_distributions, transition_values):
    """Transition values come from an offline rules-aware state solver."""
    action_values = {
        target: sum(probability * transition_values[target][region]
                    for region, probability in distribution.items())
        for target, distribution in target_distributions.items()
    }
    return max(action_values, key=action_values.get), action_values
~~~

Learn pseudocounts only from historical training data and verify legal finishing/bust transitions. The example is a building block, not a reproduction of the published model. No guaranteed strategy improvement follows from publishing a colorful board.

**Done when:** lawful data access exists, held-out dart-region predictions improve proper scores, and an independently checked state solver supports explanations.

## M16 — Abstention and uncertainty-aware recommendations

**Priority P1 · Effort M.** Targets: best-bet exporter, model metadata, UI confidence labels. Dependencies: B03, M02–M04, M12.

Replace arbitrary A/B/C edge grades with a decision that can say “insufficient evidence.” Gate selections on compatible formats, measured coverage, age, and a conservative probability estimate. Estimate uncertainty offline by resampling event groups and refitting the whole pipeline; keep model disagreement visible.

~~~python
def assess_selection(probability_low, decimal_price, snapshot_age_hours,
                     supported_format, evidence_matches,
                     max_age_hours=36, minimum_matches=30, minimum_ev=0.02):
    # Policy constants are proposed defaults to validate, not safety guarantees.
    if not 0 <= probability_low <= 1 or decimal_price <= 1:
        raise ValueError("Invalid probability or price")
    reasons = []
    if not supported_format:
        reasons.append("Unsupported format")
    if evidence_matches < minimum_matches:
        reasons.append("Sparse measured history")
    if snapshot_age_hours < 0 or snapshot_age_hours > max_age_hours:
        reasons.append("Snapshot outside publication age policy")
    conservative_ev = probability_low * decimal_price - 1
    if conservative_ev < minimum_ev:
        reasons.append("No robust advantage at saved price")
    return {"publish_paper_selection": not reasons,
            "conservative_ev": conservative_ev, "reasons": reasons}
~~~

A bootstrap lower bound is not a guarantee of profit, especially under changing schedules and selective coverage. Conformal classification sets can be another research diagnostic, but serially dependent darts outcomes do not automatically satisfy exchangeability. A predictive set is also different from a confidence interval for the probability parameter.

For parlays, estimate joint event frequency from a validated joint simulator or disclose the independence assumption. Same-event probabilities must not be multiplied while silently claiming correlation was modeled.

**Done when:** unsupported cases abstain predictably, coverage and abstention rates are reported alongside scores, and thresholds are fixed before prospective evaluation.

## Adoption rule

Maintain three offline references: neutral-prior Elo, a regularized paired-comparison model, and the saved de-vigged market where coverage exists. A complex challenger enters production only after reproducible out-of-time improvement, calibrated probabilities, source-compatible coverage, artifact verification, and a prospective shadow period. Better historical ROI alone is insufficient.
