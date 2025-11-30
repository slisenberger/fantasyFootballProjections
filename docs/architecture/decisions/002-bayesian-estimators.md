# 2. Use of Bayesian Estimators for Player Stats

Date: 2025-11-30

## Status

Accepted

## Context

Projecting player performance requires estimating their skill level (e.g., `target_share`, `yards_per_carry`) based on historical data.
*   **Problem:** Small sample sizes (e.g., a rookie with 1 game, or a veteran with 2 games in a new season) lead to wild variance if we use raw averages. A player with 1 target and 1 catch has a 100% catch rate, which is predictive garbage.
*   **Naive Solution:** Minimum sample thresholds (e.g., "Must have 50 attempts"). This excludes too many relevant players (rookies, backups).

## Decision

We use **Bayesian Inference (Empirical Bayes)** to estimate all "Rate" and "Efficiency" metrics.

*   **Mechanism:** We calculate a "Prior" (League Average for the position) and update it with "Likelihood" (Observed stats).
*   **Implementation:** We use Exponentially Weighted Moving Averages (EWMA) seeded with the Prior.
    *   `Prior` is injected as a "ghost game" at $t=-1$.
    *   `Span` (e.g., 500 attempts) controls the "Stickiness" of the prior vs. the signal.

**Formula:**
Effectively, the estimator $\hat{\theta}$ approaches:
$$ \hat{\theta} = \frac{n \cdot \bar{x} + m \cdot \mu_{prior}}{n + m} $$
Where $n$ is observed volume and $m$ is the "strength" of the prior (controlled by span).

## Consequences

### Positive
*   **Stability:** Projections for low-sample players are anchored to realistic league averages, preventing outlier explosions ("Fail High" on rookies).
*   **Coverage:** We can generate projections for *every* player on the roster, not just starters.
*   **Adaptability:** The EWMA adapts to recent performance changes (breakouts/declines) while the Bayesian anchor prevents overreaction to a single game.

### Negative
*   **Opacity:** It is harder to explain to a user why a player's projected catch rate is 60% when their season average is 70% (due to regression to the mean).
*   **Tuning:** The `span` parameter is a hyperparameter that requires calibration.

## Compliance
All new rate statistics (e.g., `sack_rate`, `pressure_rate`) must use the `_compute_estimator_vectorized` utility in `stats/util.py` rather than raw `mean()`.
