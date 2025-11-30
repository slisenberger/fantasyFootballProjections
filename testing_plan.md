# Action Plan: Testing Infrastructure Modernization (Refined)

This plan addresses the shortcomings in the testing infrastructure, specifically targeting the shallowness of the current suite and the difficulty of testing stochastic code. It places a heavy emphasis on statistical validation to ensure model integrity.

## Phase 1: Foundation & Determinism
**Goal:** Establish a robust base for testing by ensuring tests are reliable, reproducible, and fast.

### Step 1.1: Deterministic Fixtures (`conftest.py`)
*   **Critique Addressal:** "conftest.py: Defines fixtures... good practice."
*   **Action:** Enhance `conftest.py` to support deterministic testing of stochastic components.
*   **Details:**
    *   **Mock Sampler:** Create a `mock_sampler` fixture. This fixture should return a mocked version of the new `engine/sampler.py` (from the Architecture plan) that returns fixed sequences of numbers instead of random values. This is *crucial* for unit testing game mechanics.
    *   **Seed Fixture:** Create a `fixed_seed` autouse fixture that resets `random.seed` and `numpy.random.seed` before every test to ensure reproducibility even in "random" tests.
    *   **Enhanced Mock Data:** Expand `mock_pbp_data` to cover edge cases (e.g., players with 0 stats, empty depth charts) to stress-test the data pipeline.

### Step 1.2: Property-Based Testing (Hypothesis)
*   **Critique Addressal:** "need for specialized approaches (Hypothesis testing)."
*   **Action:** Integrate the `hypothesis` library.
*   **Details:**
    *   Add `hypothesis` to dev dependencies.
    *   **Target:** `score.py` (Expand existing tests) and the new `engine/strategies/` (Run/Pass logic).
    *   **Example Strategy:**
        *   *Input:* Generate random yard lines (0-100), down (1-4), distance (1-99).
        *   *Invariant:* "A run play should never result in a yard line < 0 or > 100" (conceptually).
        *   *Invariant:* "A touchdown must always result in 6 points."

---

## Phase 2: Core Engine Testing (`tests/engine/`)
**Goal:** Move beyond "smoke tests" to deep functional verification of the simulation logic.

### Step 2.1: Strategy Unit Tests
*   **Critique Addressal:** "core engine is not [well-tested]... difficulty of testing stochastic code".
*   **Action:** Create `tests/engine/test_strategies.py`.
*   **Details:**
    *   Test each strategy (`RunStrategy`, `PassStrategy`) in isolation using the `mock_sampler`.
    *   **Scenario:** "Given a `PassStrategy` and a sampler that returns `is_complete=True` and `yards=15`, verify that the result object indicates a completed pass for 15 yards."
    *   **Scenario:** "Given a `RunStrategy` and a sampler that triggers a fumble, verify the turnover result."

### Step 2.2: State Transition Tests
*   **Critique Addressal:** "core engine is not [well-tested]".
*   **Action:** Create `tests/engine/test_state.py`.
*   **Details:**
    *   Test `GameState.apply(result)`.
    *   **Scenario:** "Apply a 10-yard gain result on 1st & 10. Assert new state is 1st & 10 at new yard line."
    *   **Scenario:** "Apply a 5-yard gain result on 3st & 10. Assert new state is 4th & 5."
    *   **Scenario:** "Apply a Touchdown result. Assert score updates and state resets for kickoff."

---

## Phase 3: Data Pipeline Testing (`tests/stats/`)
**Goal:** Verify the integrity of the data transformation pipeline.

### Step 3.1: Calculator Unit Tests
*   **Critique Addressal:** "shallow... test_smoke.py... focuses on execution paths".
*   **Action:** Create `tests/stats/test_calculators.py`.
*   **Details:**
    *   Test the new modular calculators (`calculate_passing_stats`, etc.) with small, handcrafted DataFrames.
    *   **Verify:** Correct aggregation of yards, attempts, and derived metrics (e.g., completion %).
    *   **Verify:** Handling of empty inputs (e.g., a QB with no passes).

### Step 3.2: Estimator Unit Tests
*   **Action:** Create `tests/stats/test_estimators.py`.
*   **Details:**
    *   Test the "pure" math functions (`compute_air_yards_estimator`, etc.).
    *   **Verify:** Bayesian updating logic (e.g., "Does a rookie with 0 history regress to the prior?").
    *   **Verify:** Vectorized operations handle `NaN`s correctly without crashing.

---

## Phase 4: Statistical Validation & Drift Detection
**Goal:** "Deep dive" into the statistical assumptions. Organized by ROI to prioritize structural integrity over fluctuating football trends.

### Tier 1: Critical Invariants (High ROI / Blocking)
*These tests verify the mathematical correctness of the engine. If these fail, the code is objectively broken. They must pass for any merge.*

#### Step 4.1: Input Data Invariants (Schema Validation)
*   **Why:** Garbage In, Garbage Out. Protective layer against scraper errors or data corruption.
*   **Action:** Create `tests/validation/schemas.py` using `pandera`.
*   **Details:**
    *   **Strict Checks:** `pass_attempts` >= `completions`, no `NaN`s in keys (`player_id`, `week`).
    *   **Loose Checks:** `air_yards` between -20 and 110 (allow outliers but catch corruption).

#### Step 4.2: Estimator Behavior (The "Secret Sauce")
*   **Why:** Verifies the Bayesian math (`stats/util.py`) works as intended. This is independent of NFL trends.
*   **Action:** Create `tests/validation/test_estimator_math.py`.
*   **Details:**
    *   **Prior Dominance:** Assert that for N=0 observations, result == Prior.
    *   **Convergence:** Assert that as N -> Infinity, result -> Observed Average.
    *   **Lag Test:** Assert that `span=10` adapts to a step-change in signal faster than `span=1000`.

#### Step 4.3: Sampler Fidelity (KDE Correctness)
*   **Why:** Verifies the `Sampler` class accurately reproduces the distribution it was trained on.
*   **Action:** Create `tests/validation/test_sampler_fidelity.py`.
*   **Details:**
    *   **KS Test:** Compare Training Data vs. Generated Sample (N=100,000).
    *   **Pass Condition:** p-value > 0.01 (loosened slightly to avoid flaky false positives on minor noise).
    *   **Tail Check:** Assert 99th percentile of sample is within 10% of training data (prevents "Fail High" regressions).

### Tier 2: Heuristic Monitors (Advisory / Non-Blocking)
*These tests monitor "Football Truths." Failures here might indicate code bugs OR legitimate shifts in the NFL meta (e.g., passing depression). These should trigger **warnings**, not build failures.*

#### Step 4.4: Simulation Sanity Monitors
*   **Why:** Catch "impossible" physics without being brittle to era adjustments.
*   **Action:** Create `tests/validation/test_sanity_monitors.py`.
*   **Details:**
    *   **The "Mahomes" Monitor:** Simulate top-tier QB. Warning if Mean Yards < 200 or > 400 (Wide bounds).
    *   **The "Explosion" Monitor:** Warning if > 0.1% of games result in > 800 yards or < -100 yards.
    *   **Stacking Monitor:** Warning if Correlation(QB_Pts, WR1_Pts) < 0.2 (Should be positive).

#### Step 4.5: Model Rationality Checks
*   **Why:** Ensure baseline models generally respect physics, but allow for strategic shifts.
*   **Action:** Add to `tests/validation/test_models.py`.
*   **Details:**
    *   **Directional Checks:** Warning if `air_yards` coefficient in Completion Model is *positive* (easier to catch deep passes?).
    *   **Shootout Check:** Warning if `total_score` feature impact is effectively zero (Confirming Hypothesis H2, but alerting us if we *intended* to fix it).

---

## Phase 5: Integration & System Tests
**Goal:** Verify the system works as a whole.

### Step 5.1: The Golden Master (Refined)
*   **Action:** Formalize the "Golden Master" test described in the Architecture Plan into `tests/integration/test_simulation_stability.py`.
*   **Details:**
    *   This test runs the full loop (Builder -> Runner) with a fixed seed.
    *   It guards against *unintended* changes to the simulation outcome.

### Step 5.2: Performance Gate
*   **Action:** Create `tests/performance/test_speed.py`.
*   **Details:**
    *   Benchmark the time to simulate 1,000 games.
    *   Assert it stays within a defined budget (e.g., < 2 seconds). Prevent slow code creep.

---

## Execution Order
1.  **Phase 1.1:** `conftest.py` (Immediate).
2.  **Phase 4.1:** Schema validation (protects the data pipe).
3.  **Phase 3.1 & 3.2:** Test modular stats (TDD).
4.  **Phase 4.3:** Verify Estimators (math check).
5.  **Phase 2:** Engine Refactor & Tests.
6.  **Phase 4.2 & 4.4:** Deep statistical validation of the new engine.
7.  **Phase 5:** Final integration.

## Git Commit Strategy

### Phase 1: Foundation & Determinism
- **Commit 1.1:** `test(fixtures): add deterministic mock_sampler and seed fixtures`
- **Commit 1.2:** `test(hypothesis): add property-based tests for score.py`

### Phase 2: Core Engine Testing
- **Commit 2.1:** `test(engine): add unit tests for Run/Pass strategies`
- **Commit 2.2:** `test(engine): add state transition verification tests`

### Phase 3: Data Pipeline Testing
- **Commit 3.1:** `test(stats): add unit tests for modular calculators`
- **Commit 3.2:** `test(stats): add pure math tests for estimators`

### Phase 4: Statistical Validation
- **Commit 4.1:** `test(validation): add Tier 1 data schema and estimator logic tests`
- **Commit 4.2:** `test(validation): add Tier 1 sampler fidelity tests`
- **Commit 4.3:** `test(validation): add Tier 2 simulation monitor warnings`

### Phase 5: Integration & System Tests
- **Commit 5.1:** `test(integration): formalize full simulation stability check`
- **Commit 5.2:** `test(perf): add simulation speed benchmark gate`