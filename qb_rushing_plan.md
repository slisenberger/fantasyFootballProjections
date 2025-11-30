# Action Plan: Calibration of Rushing QBs

**Objective:** Reduce the "Fail High" rate for Rushing QBs (currently +447% Rush TDs vs Normal).
**Strategy:** Move from a "One Size Fits All" physics model to "Archetype-Specific" distributions.

## 1. Split KDEs (The "Konami" Fix)
*   **Ref:** `MASTER_PLAN.md` Phase 2.2.
*   **Problem:** Current `scramble_yards_kde` blends Tom Brady (2 yards) with Lamar Jackson (50 yards), creating a "mushy" middle and killing the tail.
*   **Action:**
    1.  **Classify QBs:** In `models/rushers.py`, calculate `rush_yards_per_game` for each QB. Define "Mobile" threshold (e.g., > 20 yds/g). **[Done]**
    2.  **Train Split Models:** **[Done]**
        *   `scramble_yards_kde_mobile` (High Variance, Heavy Tail).
        *   `scramble_yards_kde_pocket` (Low Variance, Short Tail).
        *   *Bonus:* `rush_open_kde_qb` (Separate QBs from RBs for designed runs).
    3.  **Engine Integration:** **[Done]**
        *   Load new models.
        *   In `compute_scramble_yards`, check `qb['is_mobile']` (or similar stat) and sample from the correct KDE.

## 2. Red Zone QB Usage
*   **Ref:** Analysis Finding (+447% Rush TDs).
*   **Problem:** We likely under-project QBs calling their own number at the goal line (Zone Read/Sneak).
*   **Action:**
    *   Check `redzone_carry_share_est` logic.
    *   Maybe boost QB carry probability inside the 5-yard line?

## 3. Data Hygiene
*   **Action:** Update `models/rushers.py` to use `loader.load_data` instead of manual CSV reading (consistent with recent fixes).