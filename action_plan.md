# Action Plan: Architecture Modernization (Refined & Verified)

This plan outlines the steps to modernize the `fantasyFootballProjections` codebase. It has been refined to prioritize safety (regression testing), clarity (separation of concerns), and testability, while strictly adhering to the provided architectural critique.

## Phase 0: The Safety Net (Critical Prerequisite)
**Goal:** Create a "Golden Master" test to guarantee that refactoring does not alter the simulation outcomes deterministically. Relying solely on full benchmarks is too slow for the feedback loop needed during refactoring.

### Step 0.1: Create Golden Master Test
*   **Action:** Create `tests/golden_master.py`.
*   **Details:**
    *   Set a fixed random seed (`random.seed(42)`, `np.random.seed(42)`).
    *   Instantiate `GameState` with a specific, hardcoded scenario (e.g., KC vs SF, Week 1 2024).
    *   Run `play_game()` once.
    *   Capture the **exact** `play_log` and final `fantasy_points` dictionary.
    *   Save this output to `tests/fixtures/golden_master_output.json`.
*   **Verification:** The test asserts that the current run matches the JSON fixture exactly. This test must run in < 1 second.

### Step 0.2: Pin Environment
*   **Action:** Freeze dependencies.
*   **Why:** To ensure `scikit-learn` or `pandas` version changes don't introduce variance during our architectural work.

---

## Phase 1: The Stats Calculator (`stats/players.py`)
**Goal:** Transform `stats/players.py` from a procedural script into a modular pipeline. The current monolithic `calculate` function hides data integrity issues.

### Step 1.1: Configuration Injection
*   **Critique Addressal:** Addresses "hardcoded module-level constants".
*   **Action:** Define `StatsConfig` in `settings.py`.
*   **Details:** Move hardcoded hyperparameters (e.g., `passer_span = 1000`, `receiver_span = 150`) into this config object.
*   **Refactor:** Update `stats/players.py` signatures to accept `config: StatsConfig`.

### Step 1.2: Extract Modular Calculators
*   **Critique Addressal:** Addresses "Breaking this into calculate_passing_stats, etc.".
*   **Action:** Create `stats/calculators/` package.
*   **Details:** 
    *   Create specialized modules: `passing.py`, `rushing.py`, `receiving.py`, `kicking.py`.
    *   Move logic from the monolithic `calculate` function into these focused modules (e.g., `calculate_passing_stats(data, config)`).
    *   Move the `compute_*_estimator` functions into these modules.
    *   Ensure these functions are "pure" (DataFrame in -> DataFrame out).
*   **Test:** Unit tests for these calculators are easier to write than full integration tests.

### Step 1.3: The `StatsBuilder` Class
*   **Critique Addressal:** Addresses "Data dependencies... join logic (inner vs. outer) is critical... explicit handling (and logging)".
*   **Action:** Create `stats/builder.py` to orchestrate the new modular calculators.
*   **Details:**
    *   The `StatsBuilder` initializes with raw data.
    *   It calls the modular `calculate_*_stats` functions from Step 1.2.
    *   **Crucial:** Implement explicit "Data Integrity Checks" during the merging of these partial stats.
        *   *Check:* "Did we lose any starting QBs after merging with depth charts?"
        *   *Check:* "Are there NaNs in critical columns like `air_yards_est`?"
    *   Replaces the implicit `how='outer'` merges with explicitly managed joins.

---

## Phase 2: The Core Engine (`engine/game.py`)
**Goal:** Decouple "Game Logic" (Rules) from "Game State" (Data).

### Step 2.0: Parallel Test Scaffolding (The "TDD" Bridge)
*   **Action:** Create `tests/scaffolding/game_mocks.py`.
*   **Details:**
    *   Create a `MockGameState` class that mimics the interface of the *future* `GameState` (simple data container).
    *   Create a `MockSampler` that allows injecting deterministic values (e.g., "Next sample is 10 yards").
    *   **Why:** This allows us to write and verify the new `PlayStrategy` classes (Step 2.3) *before* we dismantle the existing `engine/game.py`. We verify the new logic works in isolation before integrating it.

### Step 2.1: The `GameBuilder` (Fixing `__init__`)
*   **Critique Addressal:** Addresses "`__init__`: Performs heavy data transformation... belongs in a GameBuilder".
*   **Action:** Create `engine/builder.py`.
    *   Move all dataframe-to-dict conversion logic here.
    *   `GameBuilder.build()` returns a `GameState` instance that is "ready to play".
    *   `GameState` becomes a simple data container (mostly).

### Step 2.2: The `Sampler` Abstraction
*   **Critique Addressal:** Addresses "`_get_sample`: ... modulo operation ... non-standard. Dedicated Sampler class...".
*   **Action:** Create `engine/sampler.py`.
    *   Class `Sampler` holds the pre-calculated buffers (`air_yards_samples`, etc.).
    *   It implements `get_air_yards(player_type)` etc., replacing the `_get_sample` helper.
    *   **Implementation:** Evaluate replacing the custom modulo indexing with standard efficient generation (e.g., `numpy.random.choice` or proper generators) if performance metrics allow.

### Step 2.3: Strategy Pattern & `PlayResult`
*   **Critique Addressal:** Addresses "`advance_snap`: ... massive switch statement ... Refactoring this into a Strategy pattern".
*   **Action:** Introduce `PlayResult` and Strategies in `engine/strategies/`.
    *   Define `PlayResult` (Dataclass): `grams: yards_gained, is_touchdown, turnover_type, clock_runoff`.
    *   Create concrete strategies: `RunStrategy`, `PassStrategy`, `PuntStrategy`, `FieldGoalStrategy`.
    *   **Validation:** Develop these using the `MockGameState` and `MockSampler` from Step 2.0. Verify edge cases (e.g., Safety logic, Touchback logic) in isolation.
    *   `PlayStrategy.execute(state, sampler) -> PlayResult`.
    *   `GameState.apply(result)`: Updates score, yard line, down, clock based on the result.

### Step 2.4: The Game Loop (`GameRunner`)
*   **Critique Addressal:** Addresses "`play_game`: ... 'Main Loop' pattern ... placed in a Simulator or Runner class".
*   **Action:** Extract the `while` loop into `engine/runner.py`.
    *   `GameRunner` takes a `GameState` and a `StrategySelector`.
    *   It runs the loop `while not state.game_over`.
    *   Allows for future "DebugRunner" (step-by-step printing).

---

## Phase 3: Orchestration & Performance (`main.py`)
**Goal:** Improve scalability and separation of concerns.

### Step 3.1: Optimized Parallelism
*   **Critique Addressal:** Addresses "serialization cost ... using joblib's memory mapping features".
*   **Action:** Optimize `project_week` in `main.py`.
    *   Use `joblib` with `mmap_mode='r'` for the large static data (Models, KDE samples) to share memory across processes.
    *   Ensure the `GameBuilder` (or the data definitions it needs) is lightweight enough to be efficiently pickled.

### Step 3.2: Decouple Reporting
*   **Critique Addressal:** Addresses "Reporting: It calls html_generator directly... separate reporting step".
*   **Action:** Split `main.py` commands.
    *   `simulate`: Runs games -> Outputs raw data (Parquet/CSV) to `data/output/raw/`.
    *   `report`: Reads `data/output/raw/` -> Generates HTML/CSV to `data/output/reports/`.
*   **Benefit:** Enables re-generating reports (e.g., changing CSS) without re-running expensive simulations.

---

## Verification & Quality Control

### Quality Gates
1.  **Type Hinting:** All new/refactored modules must use Python type hints.
2.  **Docstrings:** Public methods must have docstrings explaining *why*, not just *what*.
3.  **Test Coverage:** New logic (Estimators, Strategies) must have >90% unit test coverage.

### Execution Order
1.  **Phase 0** (Immediate - Safety Net)
2.  **Phase 2.1 & 2.2** (Clean up `GameState` creation).
3.  **Phase 1** (Fix the data pipeline).
4.  **Phase 2.3 & 2.4** (Refactor the game mechanics).
5.  **Phase 3** (Scale and Optimize).

## Git Commit Strategy

### Phase 0: The Safety Net
- **Commit 0.1:** `test(golden): add golden master test and fixture`
- **Commit 0.2:** `build: pin dependencies in uv.lock`

### Phase 1: Stats Calculator Refactor
- **Commit 1.1:** `feat(config): add StatsConfig to settings`
- **Commit 1.2:** `refactor(stats): extract modular calculators`
- **Commit 1.3:** `feat(stats): implement StatsBuilder with integrity checks`

### Phase 2: Core Engine Refactor
- **Commit 2.0:** `test(engine): add MockGameState and parallel scaffolding`
- **Commit 2.1:** `feat(engine): add GameBuilder for state initialization`
- **Commit 2.2:** `feat(engine): add Sampler class for KDE buffers`
- **Commit 2.3:** `feat(engine): implement PlayStrategy pattern`
- **Commit 2.4:** `refactor(engine): extract GameRunner loop`

### Phase 3: Orchestration & Performance
- **Commit 3.1:** `perf(main): optimize joblib with mmap`
- **Commit 3.2:** `feat(cli): split simulation and reporting commands`
