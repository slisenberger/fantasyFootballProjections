# Action Plan: Statistical Modernization (Hypothesis-Driven)

This plan outlines a series of high-value experiments designed to overcome the "Limits of Linearity" and "Static Density" problems inherent in the current architecture. Instead of blindly refactoring, we will treat each upgrade as a scientific experiment: **Hypothesize -> Implement -> Benchmark -> Decide**.

## Phase 1: The "Non-Linear" Reality (Play Calling)
**Problem:** Logistic Regression fails to capture interaction effects (e.g., Time * ScoreDiff), leading to a "mushy middle" simulation that underestimates game script volatility.
**Hypothesis:** Tree-based models (XGBoost/LightGBM) will better capture situational play-calling (e.g., killing clock, desperate catch-up), reducing "Fail High" errors in game scores.

### Experiment 1.1: Tree-Based Play Caller
*   **Action:** Train an `XGBClassifier` for play type prediction (`Pass` vs `Run` vs `Punt` vs `FG`).
*   **Library:** `xgboost` (Add via `poetry add xgboost`).
*   **Training Pipeline:**
    *   **Data Split:** Time-series split (Train: 2016-2022, Val: 2023, Test: 2024). NEVER random split (leakage).
    *   **Hyperparameter Tuning:** Use `RandomizedSearchCV` (scikit-learn wrapper) to optimize:
        *   `learning_rate` (0.01 - 0.3)
        *   `max_depth` (3 - 10)
        *   `subsample` (0.5 - 1.0)
        *   `colsample_bytree` (0.5 - 1.0)
    *   **Regularization:** Use `early_stopping_rounds=50` on the Validation set to prevent overfitting.
    *   **Serialization:** Save using `model.save_model("model.json")` (Native JSON format is safer than Pickle across versions).
*   **Features:** Add `total_score` (Shootout potential) and interaction proxies (e.g., `seconds_remaining` * `score_differential` implicitly handled by trees).
*   **Sanity Check:** Inspect `model.feature_importances_`. If `score_differential` is near zero, the model failed to learn the game script.
*   **Control:** The existing `LogisticRegression` model.
*   **Success Criteria:**
    *   **Metric:** Lower `log_loss` on a holdout set (2023 season).
    *   **Simulation:** Run 1,000 sims of known "Shootout" games (e.g., BUF vs KC). Assert variance of total score increases vs Control.

### Experiment 1.2: The "Momentum" Features (Feature Engineering)
*   **Action:** Before jumping to Transformers, explicitly engineer sequence features for the XGBoost model.
*   **Features:**
    *   `prev_play_type`: Was the last play a run or pass?
    *   `consecutive_runs`: How many runs in a row?
    *   `drive_momentum`: Yards gained on this drive so far.
*   **Hypothesis:** Teams have "tendencies" (e.g., establishing the run) that stateless models miss.
*   **Success Criteria:** Significant feature importance score for sequence features in the XGBoost model.

---

## Phase 2: The "Dynamic Density" (Outcome Modeling)
**Problem:** Static KDEs smooth out variance and ignore context (e.g., 3rd & 15 vs 1st & 10 use the same Air Yards distribution).
**Hypothesis:** Conditional probability models will capture "Boom/Bust" modes (bimodal distributions) that static KDEs miss.

### Experiment 2.1: Quantile Regression Forests (QRF)
*   **Action:** Replace the `rush_open_kde` with a `QuantileRegressor` (e.g., LightGBM with `objective='quantile'`).
*   **Task:** Predict 10th, 50th, and 90th percentiles of `rushing_yards` based on `down`, `distance`, and `defensive_strength`.
*   **Sampling:** In simulation, sample from a generic distribution (e.g., Skew Normal) fitted to these predicted quantiles.
*   **Success Criteria:**
    *   **Calibration:** The predicted 90th percentile should actually capture 90% of observed outcomes in the test set.
    *   **Physics:** On 3rd & 1, the median prediction should shift closer to 1 yard (short yardage package) compared to 1st & 10.

### Experiment 2.2: Conditional Air Yards (The "Situational" KDE)
*   **Action:** Instead of a full MDN (complex), try a "Bin-Conditional KDE".
*   **Method:** Train separate KDEs for:
    *   *Desperate:* Trailing by >8, < 5 mins left.
    *   *Standard:* Neutral game script.
    *   *Conservative:* Leading by >8, < 5 mins left.
*   **Hypothesis:** The *Desperate* KDE will have a much fatter tail (more Hail Marys), solving the "Safe Simulation" bias.
*   **Success Criteria:** "Fail High" rate on QB Passing Yards decreases in backtesting.

---

## Phase 3: The "Konami Code" (Mobile QB Variance)
**Problem:** Designed runs and broken-play scrambles are lumped together, averaging out the extreme variance of mobile QBs.

### Experiment 3.1: Split Scramble Distributions
*   **Action:** Split `scramble_kde` into two:
    1.  `designed_run_kde` (QB Power/Read Option): Lower variance, higher mean.
    2.  `scramble_kde` (Broken Play): High variance, high skew.
*   **Trigger:** Use a new classifier (or simple heuristic based on `time_to_throw` data if available, or `down/dist`) to decide which KDE to sample from.
*   **Hypothesis:** Simulating distinct "Broken Plays" will create the massive 80+ yard QB rushing games that current models censor.
*   **Success Criteria:** Backtest against Lamar Jackson / Josh Allen 2023 games. Compare the 95th percentile of simulated rushing yards against reality.

---

## Execution Strategy (The "Champion/Challenger" Model)

We will not replace code immediately. We will build **Challenger Models**.

1.  **Create `models/experimental/`:** A sandbox for XGBoost/QRF models.
2.  **Update `settings.py`:** Add flags: `use_xgboost_playcall: bool`, `use_dynamic_rushing: bool`.
3.  **Benchmark:** Run the `benchmark.py` suite with flags `True` vs `False`.
4.  **Promote:** If a Challenger beats the Champion (Current Baseline) on `log_loss` AND Simulation Calibration (KS Test), it becomes the new default.

## Git Commit Strategy

### Phase 1: Play Calling Experiments
- **Commit 1.1:** `feat(ml): add xgboost dependency and experimental module`
- **Commit 1.2:** `exp(playcall): train XGBClassifier challenger model`
- **Commit 1.3:** `benchmark(playcall): compare XGB vs LogReg on 2023 holdout`

### Phase 2: Dynamic Density Experiments
- **Commit 2.1:** `exp(rushing): implement Quantile Regression wrapper`
- **Commit 2.2:** `feat(engine): add support for conditional distribution sampling`
- **Commit 2.3:** `benchmark(rushing): validate QRF calibration`

### Phase 3: Mobile QB Experiments
- **Commit 3.1:** `exp(qb): train separate KDEs for designed runs vs scrambles`
- **Commit 3.2:** `feat(engine): implement split-logic for QB rushing`
