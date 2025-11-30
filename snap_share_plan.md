# Action Plan: Snap Share & Participation

This plan details the integration of snap count data to move from "Roster Assumption" to "Participation Probability." This is a foundational step for the Target Share model and Fatigue Logic.

## 1. Data Ingestion (Complete)
*   **Done:** `data/loader.py` now loads `import_snap_counts` and returns `player_season_snaps`.
*   **Context:** We have granular snap data (snaps per game) which we aggregated to season totals in the loader.

## 2. Statistical Estimation (`stats/players.py`)
**Goal:** Create a `snap_share_est` metric for every player, similar to `target_share_est`.

### Step 2.1: Calculate Weekly Snap Share
*   **Action:** In `calculate_weekly`, merge the raw `snap_counts` (per game) with the player's weekly stats.
*   **Metric:** `snap_percentage = player_snaps / team_offensive_snaps`.
*   **Challenge:** We need `team_offensive_snaps` for every game.
    *   *Source:* `nfl_data_py.import_schedules` often has this, or we aggregate `snap_counts` for all offensive players in a game and take the max (usually the Center or QB snap count = 100%).

### Step 2.2: The Bayesian Snap Estimator
*   **Action:** Create `compute_snap_share_estimator` in `stats/players.py`.
*   **Logic:** Use the standard EWMA logic (`stats/util.py`).
*   **Prior:**
    *   *Rookies:* Based on Draft Capital (1st Round = 0.70, 7th Round = 0.05).
    *   *Vets:* Previous season average.
*   **Span:** Use a relatively short span (e.g., 4 weeks) because snap roles change fast (injuries, benchings).

## 3. Simulation Integration (`engine/game.py`)
**Goal:** Use `snap_share_est` to influence who is on the field.

### Step 3.1: The Participation Check
*   **Action:** In `GameState`, before `choose_target`:
*   **Logic:**
    *   For every eligible receiver, roll `random() < snap_share_est`.
    *   *Filter:* Only keep players who "passed" the check as eligible for this target.
*   **Fallback:** If 0 players pass (unlikely), fallback to top 3 depth chart.

### Step 3.2: Fatigue Integration (Cross-over)
*   **Action:** Link `snap_share` with the `Volume Decay` plan.
*   **Logic:** If a player's `snap_count_in_sim` exceeds their average `total_snaps`, apply a penalty to their `snap_share_est` for the rest of the game (Tiring out).

## Git Commit Strategy

- **Commit 1:** `feat(stats): calculate weekly snap percentages in players.py`
- **Commit 2:** `feat(stats): implement EWMA snap_share_estimator`
- **Commit 3:** `feat(engine): implement probabilistic eligibility filter based on snap share`
