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

## 🏃 How to Run Benchmarks

```bash
# Run the full suite (approx 5-10 mins)
poetry run python benchmark.py --simulations 50 --version v403_candidate
```

This will save results to `benchmarks/results_v403_candidate.json` and a detailed CSV.

---

## 🧪 Testing

The project now includes a test harness using `pytest` to ensure code quality and prevent regressions.

*   **Unit Tests:** Located in `tests/test_*.py`, these validate individual components like scoring logic and configuration loading.
*   **Smoke Tests:** Essential for verifying the end-to-end pipeline functionality with minimal data, ensuring the system runs without crashing.

To run the tests:
```bash
poetry run pytest
```

---

## 📊 Benchmarking & Calibration

A formal benchmarking process has been established to measure the model's calibration and accuracy. Detailed results, methodology, and ongoing analysis are available in [BENCHMARKS.md](BENCHMARKS.md).

**Key Finding:** The current model (v402 baseline) is **significantly over-confident**, meaning its predicted ranges of outcomes are too narrow, even though its average predictions (bias) are accurate. This highlights a need to introduce more simulated variance (e.g., injuries, big plays) into the core game engine.

---

## 🏗️ Architecture

*   **`main.py`**: Orchestrator. Handles CLI, data loading, parallel execution (`joblib`), and backtesting.
*   **`engine/game.py`**: The Physics Engine. Enforces NFL rules (downs, clock, scoring) and manages state. Refactored to use Enums (`PlayType`, `Position`).
*   **`models/`**: ML Layer.
    *   `playcall.py`: Logistic Regression for Run/Pass decisions.
    *   `rushers.py` / `receivers.py`: KDE (Kernel Density Estimation) for yardage distributions.
*   **`stats/`**: Feature Engineering. Calculates "Talent Estimators" (EWMA) for players and teams.
*   **`evaluation/`**: Analysis tools.
    *   `calibration.py`: Implementation of PIT, Reliability diagrams, KS Test, and Bias calculation.

---

## 🗺️ Development Roadmap

See [ROADMAP.md](ROADMAP.md) for the detailed feature backlog and future vision.

Key Priorities:
1.  **Configurable Scoring Rules:** Implement support for various fantasy scoring formats via configuration.
2.  **Increase Simulation Variance:** Address the model's over-confidence by incorporating more realistic game variability (e.g., mid-game injuries, big play probabilities).
3.  **Early Season Data Loading Fix:** Resolve issues preventing Week 1 data from being properly processed in backtests.

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
