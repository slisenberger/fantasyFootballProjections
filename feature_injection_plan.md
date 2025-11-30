## 5. Go For It Estimator (4th Down Aggressiveness)
*Target: Refine playcalling decisions on 4th downs based on team-specific tendencies.*

### Step 5.1: Calculate Go For It Rate Estimator (`stats/teams.py`)
*   **Status:** **[Done]**
*   **Action:** Implement `compute_offense_go_for_it_rate_estimator`.
*   **Logic:** EWMA of a team's tendency to `RUN`/`PASS` vs `PUNT`/`FIELD_GOAL` on 4th downs, relative to league average.

### Step 5.2: Simulate with Go For It Estimator (`engine/game.py`)
*   **Status:** **[Done]**
*   **Hook Point:** `choose_playcall` method.
*   **Action:** On 4th down, adjust the `playcall_model`'s probabilities by shifting mass between `PUNT`/`FIELD_GOAL` and `RUN`/`PASS` based on `offense_go_for_it_rate_est`.