# 🧪 Research Hypotheses

## Current Focus: The "QB Ceiling" Problem (30% Fail High)

**Status:** Active
**Metric:** QBs exceed their 90th percentile projection 30.5% of the time.
**Goal:** Reduce QB Fail High to ~10%.

### H1: The "Konami Code" Hypothesis (Rushing Variance)
**Theory:** We significantly underestimate the variance of QB Rushing production.
**Mechanism:**
*   Our `scramble_model` (KDE) captures average scrambles.
*   It might miss "Designed Runs" (Power Reads, Draws) for mobile QBs.
*   It might miss the "Broken Play" ceiling where a QB runs for 50+ yards multiple times.
**Prediction:** The error correlates with `QB Rushing Yards`. High rushing QBs have higher Fail High rates than Pocket Passers.
**Test:** Compare `Fail High` rate of Mobile QBs (Allen, Hurts, Lamar) vs Pocket QBs (Burrow, Tua, Goff).

### H2: The "Shootout" Hypothesis (Volume Stacking)
**Theory:** In high-scoring games ("Shootouts"), passing volume (Attempts) scales non-linearly.
**Mechanism:**
*   Our `playcall_model` uses Score Differential.
*   In a "Shootout" (both teams scoring fast), the score differential stays close (0-7 pts).
*   Does our model know that "Close Game + High Total Score = Massive Passing"? Or does it just see "Close Game = Balanced Playcall"?
**Prediction:** We under-predict Pass Attempts in games with Total Score > 50.
**Test:** Plot `Projected Pass Attempts` vs `Actual` for games with >50 total points.

### H3: The "Touchdown Variance" Hypothesis
**Theory:** Passing TDs are highly volatile and we smooth them too much.
**Mechanism:**
*   `cpoe` and `pass_oe` models predict completion/efficiency.
*   TDs are often a result of Red Zone efficiency.
*   If we use "Season Average" RZ efficiency, we miss the "4 TD Game" variance.
**Prediction:** The distribution of Simulated TDs is narrower than Actual TDs.

---

## Closed Hypotheses

### H_Scrub: The "Scrub Boom" Hypothesis
**Status:** Solved (Nov 2025).
**Finding:** "Scrub Booms" (Fail High 66%) were driven by **DSTs** (Defensive TDs) and **Backup RBs** (Goal Line Vultures).
**Action:** Filtered DST/K from primary calibration metrics. RB calibration is now excellent (11%).

### H_Mahomes: The "Missing QB" Bug
**Status:** Solved (Nov 2025).
**Finding:** A data pipeline bug caused players with ANY `NaN` scoring component (e.g., play with no receiver ID) to be dropped from the "Actuals" dataset.
**Action:** Fixed `calculate_fantasy_leaders` to handle `NaN` keys safely. QB sample size restored.