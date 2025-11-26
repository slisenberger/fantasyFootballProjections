# Fantasy Football Projections Engine 🏈

**A Monte Carlo Simulation Engine for NFL Fantasy Football.**

> **Status:** Active / Modernized (Nov 2025)
> **Tech Stack:** Python 3.10+, Pandas, Scikit-Learn, Poetry, Joblib

---

## 📖 Executive Summary

Most fantasy football projections provide a single number (e.g., "Josh Allen: 22.4 points"). This engine **simulates the actual game of football**, play-by-play, thousands of times (Monte Carlo).

By simulating game mechanics (down, distance, clock) and using ML models for every decision, we generate a **distribution of outcomes**, capturing:
*   **Boom/Bust Potential:** Quantify the probability of a player scoring >30 points.
*   **Correlations:** How a QB's performance organically lifts his WRs.
*   **Game Scripts:** How blowing out an opponent shifts playcalling to the run.

---

## 🎮 Usage

### 1. Quick Start
Run 5 simulations for the current week (defaults to 2024 Week 2):
```bash
poetry run python main.py
```

### 2. Custom Simulation
Run 100 simulations for a specific past week:
```bash
poetry run python main.py --season 2023 --week 5 --simulations 100
```

### 3. CLI Arguments
| Argument | Default | Description |
| :--- | :--- | :--- |
| `--season` | 2024 | NFL Season year. |
| `--week` | 2 | Week number (1-18). |
| `--simulations` | 5 | Number of Monte Carlo runs per game. Higher = more precision. |
| `--version` | "402" | Label for output files. |

---

## 🧪 Calibration & Backtesting

The engine includes a **Calibration Harness** to scientifically measure reliability.

### How it works
1.  **Backtest:** The system simulates past games (e.g., 2018 Week 8).
2.  **PIT Calculation:** For every player, we calculate the **Probability Integral Transform (PIT)**.
    *   *Definition:* The percentile of the *Actual Score* within the *Predicted Distribution*.
    *   *Example:* If we predicted a range of 10-20 points, and the player scored 18, the PIT might be 0.80.
3.  **Metrics:**
    *   **Mean PIT:** Should be `0.50`.
        *   `> 0.5`: Model Under-predicts (Actuals are higher than expected).
        *   `< 0.5`: Model Over-predicts (Actuals are lower than expected).
    *   **Uniformity:** A flat histogram indicates perfect calibration.

### Running a Calibration Check
Run with a high simulation count (e.g., 96) to get smooth distributions:
```bash
poetry run python main.py --simulations 96 --version "calibration_test"
```
Results will be saved to `projections/calibration_metrics_v{version}.csv`.

---

## 🏗️ Architecture

*   **`main.py`**: Orchestrator. Handles CLI, data loading, parallel execution (`joblib`), and backtesting.
*   **`engine/game.py`**: The Physics Engine. Enforces NFL rules (downs, clock, scoring) and manages state. Refactored to use Enums (`PlayType`, `Position`).
*   **`models/`**: ML Layer.
    *   `playcall.py`: Logistic Regression for Run/Pass decisions.
    *   `rushers.py` / `receivers.py`: KDE (Kernel Density Estimation) for yardage distributions.
*   **`stats/`**: Feature Engineering. Calculates "Talent Estimators" (EWMA) for players and teams.
*   **`evaluation/`**: Analysis tools.
    *   `calibration.py`: Implementation of PIT and Reliability diagrams.

---

## 🗺️ Development Roadmap

See [ROADMAP.md](ROADMAP.md) for the detailed feature backlog and future vision.

Key Priorities:
1.  **Accuracy:** Fix bias in calibration (currently under-predicting).
2.  **Architecture:** Decouple scoring rules and control flow.
3.  **Scale:** Enable massive historical backtesting.

---

## 🛠️ Setup & Development

1.  **Install:**
    ```bash
    git clone <repo>
    pipx install poetry
    poetry install
    ```
2.  **Format Code:**
    ```bash
    poetry run ruff format .
    ```
