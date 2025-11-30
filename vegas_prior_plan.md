# Action Plan: The Vegas Prior (Game Script Anchoring)

This plan leverages betting market data (`spread_line`, `total_line`) to anchor the simulation's starting state and strategic tendencies. This prevents the "Upset Bias" where the model treats a 14-point underdog as an equal peer.

## 1. Data Ingestion (Complete)
*   **Status:** **[Done]** (on master)
*   **Action:** `spread_line` and `total_line` are now preserved in `loader.py` and available.

## 2. The "Effective Score" Logic (`engine/game.py`)
**Goal:** Trick the `PlayCall` model into "knowing" who is the favorite without retraining it immediately.

### Step 2.1: The Initial State
*   **Status:** **[Pending]**
*   **Concept:** A game starting 0-0 with a -7.0 spread isn't really "Tied." The favorite is "Ahead by expectation."
*   **Action:** Modify `GameState.score_differential()`:
    ```python
    def effective_score_differential(self):
        actual_diff = self.home_score - self.away_score
        # Decay the spread influence as the game progresses
        time_decay = self.sec_remaining / 3600.0 # 1.0 at start, 0.0 at end
        spread_influence = -self.vegas_spread * time_decay 
        
        return actual_diff + spread_influence
    ```
*   **Impact:**
    *   **Favorite (Home, -7):** Starts with `diff = +7`. The PlayCall model sees "Leading by 7." Result: Runs more, passes efficiently.
    *   **Underdog (Away, +7):** Starts with `diff = -7`. The PlayCall model sees "Trailing by 7." Result: Passes more, higher volatility.
*   **Why Decay?** As the game ends (`sec_remaining -> 0`), the *actual* score matters more than the pre-game line. In the final 2 minutes, we must play the actual score.

### Step 2.2: The "Shootout" Prior (Total Line)
*   **Status:** **[Pending]**
*   **Concept:** A `Total=54.0` game implies higher efficiency/tempo than `Total=38.0`.
*   **Action:** Adjust `Tempo` (Seconds per play) and `Aggressiveness` (4th Down attempts).
    *   *Implementation:* `tempo_modifier = (self.vegas_total - 45.0) / 45.0`.
    *   In `advance_clock`: `runoff -= runoff * tempo_modifier`.
    *   *Result:* High totals -> Less clock runoff -> More plays -> More fantasy points.

## 3. Retraining (Long Term)
*   Once `xgboost_migration_plan.md` is active, we feed `spread_line` and `total_line` directly as features. The model will learn the optimal weighting itself, replacing the manual "Decay" logic.
*   *Immediate Value:* The manual logic works with the *current* Logistic Regression model today.

## Git Commit Strategy
- **Commit 1:** `feat(data): expose spread/total in GameState`
- **Commit 2:** `refactor(engine): implement effective_score_differential with spread decay`
- **Commit 3:** `feat(engine): implement tempo_modifier based on vegas total`