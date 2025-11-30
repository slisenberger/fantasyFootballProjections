# Master Plan: Fantasy Physics 2.0 (ML-First Strategy)

This document supersedes individual plans as the primary execution schedule. It prioritizes **Machine Learning Modernization** (XGBoost) over manual refactoring, recognizing that a smarter model solves many "heuristic" problems (Vegas bias, Garbage time) automatically.

## Phase 0: The Foundation (Safety, Data, & Context)
*Prerequisites for everything. Do not skip.*

1.  **Type Hints (Doc Plan 1.1):** Retrofit `engine/` and `stats/` with strict typing.
    *   **Status:** **[Done]**
    *   *Why:* Essential for understanding data flow before modifying it.
2.  **Golden Master Test (Arch Plan 0.1):** Establish a regression baseline.
    *   **Status:** **[Done]**
    *   *Why:* Ensures we detect if we accidentally break the simulation.
3.  **AI Context Map (`llms.txt`) [Critical Handoff Artifact]:**
    *   **Status:** **[Done]**
    *   **Ref:** `documentation_plan.md` (Tier 1)
    *   **Action:** Create `llms.txt` summarizing the "Trilogy of Simulation", file structure, and key patterns.
    *   *Why:* Drastically reduces "Context Loading" time for future AI agents.
4.  **Data Ingestion (The "Gold Mine"):**
    *   **Status:** **[Done]**
    *   **Ref:** `data_inventory.md`
    *   **Action:** Update `loader.py` to:
        *   Stop dropping: `temp`, `wind`, `drive_play_count`, `pass_location`.
        *   Load new sources: `import_snap_counts`, `import_participation_data`, `spread_line`.

## Phase 1: The ML Core (The Intelligence Upgrade)
*Goal: Replace "Linear & Heuristic" with "Gradient Boosted & Contextual".*

### 1.1 The XGBoost Play Caller (XGBoost Plan)
*   **Status:** **[Done]**
*   **Next Step:** **Feature Injection.**
    *   *Input:* Vegas Lines, Score Diff, Down, Dist, Time.
    *   *Action:* Update `models/playcall.py` feature list and `engine/game.py` input vector.
    *   *Value:* Naturally learns "Shootout" pace and "Kill Clock" run rates.

### 1.2 Snap Share Estimator (Snap Plan)
*   **Ref:** `snap_share_plan.md`
*   **Status:** **[Done]**
*   **Input:** Historical Snap Counts (Now available in loader).
*   **Output:** `snap_share_est` (Probability of being on the field).
*   **Value:** Immediate fix for "WR5 gets random targets" bug. Prerequisite for Target Share.

### 1.3 Kicker FGOE Estimator
*   **Ref:** (New - currently undocumented in a specific plan)
*   **Status:** **[Done]**
*   **Action:** Implement a Field Goal Over Expected (FGOE) estimator for kickers to calibrate their individual skill.
*   **Value:** Improved kicker calibration and fixing a critical bug where missed FGs were incorrectly scoring points.

### 1.4 The Contextual Target Share (Target Plan)
*   **Ref:** `target_share_plan.md`
*   **Technique:** "Base Margin" XGBoost.
*   **Input:** `EWMA_Share` (Base), Participation Data (Who is on field?), Win Prob (Garbage Time).
*   **Value:** Naturally learns "Checkdown Funnel" and "Prevent Defense" targeting shifts.

## Phase 2: The Physics (Outcome Realism)
*Goal: Enforce physical constraints that ML decision-making cannot solve.*

### 2.1 Volume Decay (Fatigue)
*   **Ref:** `statistical_plan.md` (Workstream A)
*   **Logic:** `-0.03 YPC` per carry after N=15.
*   **Why:** XGBoost predicts *who* gets the ball, but Physics determines *how far* they go. Tired legs are physics.

### 2.2 Conditional Outcome Distributions
*   **Ref:** `statistical_plan.md` (Phase 2)
*   **Logic:** Split KDEs for "Desperate" vs "Standard" air yards.
*   **Why:** Even if XGBoost correctly predicts a pass, we need to know if it's a Hail Mary (high variance) or a Stick route (low variance).

## Phase 3: The Architecture (Debt Paydown)
*Goal: Clean up the "God Class" after the logic is modernized.*

### 3.1 Refactor `GameState`
*   **Ref:** `action_plan.md` (Phase 2)
*   **Action:** Split into `GameBuilder`, `GameRunner`, and `State`.
*   **Timing:** Easier to do *after* we know exactly what inputs the new XGBoost models need.

### 3.2 Stats Modularization
*   **Ref:** `action_plan.md` (Phase 1)
*   **Action:** Break `calculate()` into `calculators/`.

## Reference Documents
*   [Architecture Plan](action_plan.md)
*   [Testing Plan](testing_plan.md)
*   [Statistical Plan](statistical_plan.md)
*   [XGBoost Plan](xgboost_migration_plan.md)
*   [Target Share Plan](target_share_plan.md)
*   [Snap Share Plan](snap_share_plan.md)
*   [Data Inventory](data_inventory.md)
*   [Vegas Prior Plan](vegas_prior_plan.md)
*   [Feature Injection Plan](feature_injection_plan.md)
*   [Data Enrichment Plan](data_enrichment_plan.md)
*   [Documentation Plan](documentation_plan.md)

## Combined Git Commit Strategy (Next 10 Steps)

1.  `docs(context): add llms.txt for AI agent handoff`
2.  `test(golden): add golden master test and fixture`
3.  `feat(stats): implement EWMA snap_share_estimator`
4.  `feat(engine): implement probabilistic eligibility filter based on snap share`
5.  `feat(models): inject Vegas/Tempo features into XGBoost playcall training`
6.  `refactor(engine): pass game info (Vegas/Weather) to playcall prediction`
7.  `feat(stats): prepare participation data for target share training`
8.  `exp(targets): train XGBoost 'Base Margin' target share model`
9.  `feat(physics): implement volume decay logic for RB fatigue`
10. `refactor(arch): extract Sampler class from GameState`