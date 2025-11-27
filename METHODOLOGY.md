# Methodology

## 1. The Core Loop (Physics Engine)
The simulation runs on a play-by-play basis (`engine/game.py`).
*   **State:** Tracks down, distance, score, time, timeouts.
*   **Play Call:** Logistic Regression (`models/playcall.py`) predicts Run/Pass/Kick based on game state.
*   **Execution:**
    *   **Run:** Carrier chosen based on share. Yards sampled from **Bimodal KDE** (Open Field vs Red Zone).
    *   **Pass:** Target chosen. Completion probability (Logistic Reg). Air Yards (KDE). YAC (KDE).
*   **Clock:** Empirical runoff model based on play type and game state.

## 2. The "Trilogy of Simulation"
We avoid training unique models per player. Instead, we compose:
1.  **Global KDE:** The base physical distribution of the event (e.g., "All Passes").
2.  **Player Estimator:** A Bayesian-weighted EWMA of the player's efficiency relative to league average.
    *   **Shifted Multiplicative Scaling:** Used for Air Yards to handle negative baselines (RBs) without inverting the distribution.
    *   `Base_Scaled = ((Base + 15) * Multiplier) - 15`
3.  **Matchup Estimator:** A factor based on the opponent's defensive weakness.

## 3. Bayesian Priors & EWMA
We calculate player/team stats (`stats/players.py`, `stats/teams.py`) using an Exponentially Weighted Moving Average (EWMA).
*   **Priors:** Seeded with league average (or position average) to stabilize early-season predictions.
*   **Vectorized Calculation:** Sorts data by `[season, week]` to ensure temporal integrity across multiple years.

## 4. Models
*   **KDE (Kernel Density Estimation):** Used for continuous variables (Yards).
    *   **Split Models:** `rush_open` (field) vs `rush_rz` (inside 20) to capture different physical constraints.
*   **Logistic Regression:** Used for binary outcomes (Completion, Play Call).

## 5. Calibration & Benchmarking
We validate using **Probability Integral Transform (PIT)** histograms.
*   **Ideal:** Uniform distribution (flat histogram).
*   **Metric:** `Fail High` (Actual > 90th Percentile). Ideally 10%.
    *   If > 10%, we are **Under-Confident** (Missing Booms).
    *   If < 10%, we are **Over-Confident** (Too wide/high).
*   **Current State (v425):**
    *   RB: 12.9% (Excellent)
    *   WR: 16.6% (Good)
    *   QB: 33.6% (Under-Projected Upside)
