# Analysis Plan: Diagnosing QB Fail High

**Objective:** Reduce QB "Fail High" rate (currently ~28%) to acceptable levels (~10%).
**Problem:** The model consistently under-predicts the ceiling outcomes for Quarterbacks. "Boom" games happen far more often in reality (28%) than the simulation predicts (<5% theoretically).

## Phase 1: Data Diagnosis
*Goal: Identify the shared characteristics of QBs who break the model.*

### Findings (from `diagnose_qb_fail_high.py`)
*   **Fail High Population:** ~13% of QBs fail high by >10 points.
*   **Primary Driver:** **Passing TDs** (Corr -0.31) and **Big Pass Plays** (Corr -0.26).
    *   Lamar Jackson (5 TDs), Tom Brady (3 Pass TDs + 1 Rush TD), Patrick Mahomes (5 TDs).
    *   Max Pass > 50 yards is common in boom weeks.
*   **Secondary Driver:** **Rushing Efficiency/TDs** (Corr -0.23).
    *   Daniel Jones (91 yds, 2 TDs), Taysom Hill (63 yds, 2 TDs).
*   **Conclusion:** The model under-predicts the **variance of TD production** and the likelihood of **explosive plays** (both passing and rushing).

### Step 1.1: Quantitative Breakdown (`diagnose_qb_fail_high.py`)
*   **Input:** `benchmarks/details_v444_gfi.csv` (latest benchmark).
*   **Filter:** Select all rows where `position == 'QB'`.
*   **Definition of Fail High:** `actual > (mean + 2 * std)` (approx 95th percentile, though we use PIT directly). Specifically `pit > 0.90` or `pit > 0.95`.
*   **Analysis Dimensions:**
    1.  **Archetype:** Are they "Mobile" (>X rush yards/game) or "Pocket" (<X rush yards)?
    2.  **Component:** Did they boom on **Passing Yards**, **Passing TDs**, **Rushing Yards**, or **Rushing TDs**?
        *   *Note:* We need to join with `actuals` breakdown (Pass Yds/TDs) which isn't in `details.csv`. We might need to re-calculate or load raw `pbp`.
    3.  **Context:** Did they boom in "Shootouts" (High Total) or "Blowouts"?

### Step 1.2: Component Isolation
*   Compare `Simulated Distribution` vs `Actual Distribution` for:
    *   Pass Attempts (Volume)
    *   Pass Yards per Attempt (Efficiency)
    *   Pass TD Rate (Scoring)
    *   Rush Yards (Mobility)
    *   Rush TDs (Mobility Scoring)

## Phase 2: Hypotheses & Experiments

### Hypothesis A: The "Konami Code" Variance (Rushing)
*   **Theory:** Our `scramble_yards_kde` and `design_run_kde` for QBs are too "smooth". They capture the *average* scramble (e.g., 7 yards) but miss the *tail events* (e.g., 40-yard TD run) that define a QB boom week.
*   **Test:** Compare the Kurtosis/Skew of Simulated QB Rushing Yards vs Actuals.
*   **Fix:** Split QB Rushing KDE into "Standard" and "Breakaway", or use a heavy-tailed distribution (e.g., Cauchy/Levy) mixture.

### Hypothesis B: The "TD Bunching" (Scoring)
*   **Theory:** Passing TDs are modeled as independent events per play. In reality, "hot streaks" or red-zone efficiency might be correlated within a game.
*   **Test:** Check if we under-predict 3+ and 4+ TD games.
*   **Fix:** Conditional TD probability boost if previous drive was a TD? (Hot hand). Or simply variance injection into `pass_td` scoring?

### Hypothesis C: The "Shootout" Volume Cap
*   **Theory:** Even with the new "Vegas" features, the Playcall model might be reverting to the mean too aggressively on high-volume passing days.
*   **Test:** Check Fail High QBs vs `pass_attempts`. Are we under-projecting attempts in boom weeks?

## Phase 3: Execution
1.  Run Diagnosis Script.
2.  Select top Hypothesis.
3.  Implement Fix (e.g., Update KDE, Modify Game Engine).
4.  Verify with `benchmark.py`.