# Fantasy Football Projections Engine 🏈

**A Monte Carlo Simulation Engine for NFL Fantasy Football.**

> **Status:** Active / Modernized (Nov 2025)
> **Tech Stack:** Python 3.10+, Pandas, Scikit-Learn, Poetry

---

## 📖 Executive Summary

Most fantasy football projections provide a single number (e.g., "Josh Allen: 22.4 points"). This is often calculated using simple averages: `Projected Plays * Share % * Efficiency`.

**This engine is different.** It does not project points directly. Instead, it **simulates the actual game of football**, play-by-play, thousands of times.

By simulating the game mechanics (down, distance, clock, score) and using machine learning to make decisions at every snap, we generate a **distribution of outcomes**. This allows us to answer questions standard projections cannot:
*   *"What is the probability this RB scores 0 points vs 30 points?"* (Boom/Bust potential).
*   *"If the Bills blow out the Dolphins, how does that affect the WR2's target volume?"* (Game Script correlation).

---

## 🧠 Methodology & Data Science

The system operates on a three-stage pipeline: **Data Engineering**, **Modeling**, and **Simulation**.

### 1. Data Engineering: The "Talent Estimators"
Raw play-by-play data (sourced from `nfl_data_py`) is too noisy to use directly. We process this data to create **Estimators** using **Exponentially Weighted Moving Averages (EWMA)**.

*   **Why EWMA?** Recent performance matters more than performance 3 years ago. We apply a decay span (e.g., `span=1000` plays) to weigh recent data heavily while keeping historical context.
*   **Contextual Adjustments:** We don't just look at raw stats. We calculate **Relative** stats.
    *   *Example:* If a RB averages 5.0 YPC against a defense that allows 5.5 YPC, he isn't "good"; he is performing *below expectation*.
    *   The engine calculates `relative_ypc_est` (Player vs League Avg) and `defense_relative_ypc_est` (Defense vs League Avg) and multiplies them to predict specific matchups.

### 2. The Modeling Layer
We do not use a single model. We use a suite of specialized models for different aspects of the game.

| Component | Model Type | Purpose | Inputs |
| :--- | :--- | :--- | :--- |
| **Playcalling** | Logistic Regression | Predicts `Run`, `Pass`, `Punt`, `FG`. | Down, Distance, Score Diff, Time Remaining, Field Position. |
| **Completion** | Logistic Regression | Predicts probability of a catch. | Air Yards, QB CPOE (Completion % Over Expected), Defense CPOE. |
| **Rushing** | **Kernel Density Estimation (KDE)** | Generates yardage for a run. | Historical distribution of RB carries. |
| **Passing Yards** | **Kernel Density Estimation (KDE)** | Generates `Air Yards` and `YAC`. | Historical distribution of target depths per position (WR/TE/RB). |
| **Scoring** | Probabilistic | Touchdowns/FGs. | Field position and probabilistic success rates. |

> **Why KDE?** Linear regression tends to predict the "mean" (e.g., 4.2 yards). But RBs rarely run for 4.2 yards. They run for 2 yards, -1 yards, or 50 yards. KDE allows us to sample from a realistic *shape* of outcomes, capturing the "homerun" ability of explosive players.

### 3. The Simulation Engine (`engine/game.py`)
The core loop (`GameState`) represents the physics and rules of the NFL.

1.  **State Initialization:** Load Home/Away teams, rosters, and computed Estimators.
2.  **The Loop:** While `time_remaining > 0`:
    *   **Context:** Where are we? (e.g., 3rd & 8 on the 40).
    *   **Play Call:** Ask the `PlayCallModel` what the team does.
    *   **Player Selection:** If Pass, who is the target? (Weighted by `target_share_est`). If Run, who is the carrier?
    *   **Execution:**
        *   If Pass: Calculate `Air Yards`. Check `CompletionModel`. If caught, Calculate `YAC`.
        *   If Run: Sample `RushModel` for yards.
    *   **Physics:** Update Down, Distance, Score, and Clock.
    *   **Fantasy Scoring:** Accrue points for the players involved.
3.  **Aggregation:** Repeat `N` times (e.g., 100 sims). Aggregate results to find Median, Ceiling (90th percentile), and Floor (10th percentile).

---

## 🏗️ Architecture

*   **`main.py`**: CLI entry point. Manages data loading and the simulation loop.
*   **`engine/`**: Contains the physics engine.
    *   `game.py`: The `GameState` class that enforces NFL rules and tracks state.
*   **`models/`**: Wrappers for `scikit-learn` models.
    *   `playcall.py`, `rushers.py`, `receivers.py`, etc.
*   **`stats/`**: Feature engineering logic.
    *   `players.py`: Calculates player-level EWMA estimators.
    *   `teams.py`: Calculates team-level tendencies (Pass OE, Sack Rates).
*   **`data/`**: Local storage for compressed CSVs (`.csv.gz`).
*   **`enums.py`**: Centralized constants for Type Safety.

---

## 🎮 Usage

The application handles data download automatically.

### 1. Run Projections (Quick Start)
Run the simulation for the current week with default settings (5 sims):
```bash
poetry run python main.py
```

### 2. Custom Simulation
Run 100 simulations for Week 5 of the 2023 season:
```bash
poetry run python main.py --season 2023 --week 5 --simulations 100 --version v2.0
```

### 3. CLI Arguments
*   `--season`: (int) Year to project (e.g., `2024`).
*   `--week`: (int) Week number (e.g., `1`).
*   `--simulations`: (int) Number of games to simulate. Higher = more stable percentiles but slower.
*   `--version`: (str) Tag for output filenames.

---

## 📊 Output

Results are saved to the `projections/` directory.

*   **`w{week}_v{version}_all.csv`**: Raw projection data for all players.
*   **`w{week}_v{version}_flex.csv`**: Filtered view for Flex positions (RB/WR/TE).
*   **`v{version}_ros_mean.csv`**: Rest-of-Season projections (if running ROS mode).

**Columns Explained:**
*   `median`: The 50th percentile outcome (most likely score).
*   `percentile_88`: The "Ceiling" (a roughly 1-in-8 outcome). High ceiling indicates a good tournament play.
*   `percentile_12`: The "Floor".

---

## 🛠️ Development

### Setup
```bash
git clone <repo>
pipx install poetry
poetry install
```

### Code Style
This project uses `ruff` for linting and formatting.
```bash
poetry run ruff format .
poetry run ruff check --fix .
```