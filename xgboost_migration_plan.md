# Action Plan: The XGBoost Migration (In-Place Fast Fix)

This plan prioritizes **Development Velocity**. We will perform an in-place swap of `LogisticRegression` with `XGBClassifier` within the existing `models/playcall.py`. This solves the slow build times immediately without requiring architectural changes.

## Phase 1: The In-Place Swap (Speed Boost)
**Goal:** Reduce model training time from minutes to seconds while maintaining 100% compatibility with the current engine.

### Step 1.1: Dependency Management
*   **Action:** Add `xgboost` to the project.
*   **Command:** `poetry add xgboost`

### Step 1.2: Replace the Estimator
*   **File:** `models/playcall.py`
*   **Action:**
    *   Import `xgboost.XGBClassifier`.
    *   Replace `LogisticRegression(max_iter=10000)` with `XGBClassifier(n_estimators=100, max_depth=4, eval_metric='mlogloss')`.
    *   **Crucial:** Keep `feature_cols` exactly the same.
*   **Benefit:** `XGBClassifier` implements the same scikit-learn `fit/predict_proba` interface. `engine/game.py` won't know the difference, but training will be 10x faster.

### Step 1.3: Verify Sanity
*   **Action:** Run `python models/playcall.py` (if runnable) or a simple script to train it.
*   **Check:** Ensure `predict_proba` still returns valid probabilities.

---

## Phase 2: Feature Injection (Calibration Fix)
**Goal:** Now that training is fast, we add the "Shootout" features to fix the "Fail High" variance.

### Step 2.1: Add Game Script Features
*   **File:** `models/playcall.py`
*   **Action:** Update `feature_cols`.
    *   Add: `total_line`, `spread_line`.
*   **Note:** This *will* require updating `engine/game.py` to pass these values (as detailed in `feature_injection_plan.md`).

### Step 2.2: Retrain & Validate
*   **Action:** Re-run the build.
*   **Expectation:** "Shootout" games should now show higher pass rates.

---

## Phase 3: Optimization (Bayesian Tuning)
**Goal:** Squeeze the last 5% of log-loss performance out.

### Step 3.1: Tuning Pipeline
*   **Action:** Introduce `BayesSearchCV` or `RandomizedSearchCV` to optimize `learning_rate` and `max_depth`.
*   **Timing:** Do this only after the model is integrated and working.

## Git Commit Strategy

### Phase 1: The Swap
- **Commit 1.1:** `build: add xgboost dependency`
- **Commit 1.2:** `refactor(models): replace LogisticRegression with XGBClassifier in playcall.py`

### Phase 2: The Features
- **Commit 2.1:** `feat(models): add vegas features to playcall model`
- **Commit 2.2:** `refactor(engine): pass game info to playcall prediction`
