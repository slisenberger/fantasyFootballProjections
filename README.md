# Fantasy Football Projections Engine 🏈

A sophisticated Monte Carlo simulation engine for NFL games, designed to generate fantasy football projections using advanced play-by-play data and machine learning models.

## 🚀 Overview

Unlike traditional projection systems that rely on simple averages (e.g., `Projected Points = Avg Pts * Matchup Factor`), this engine **simulates entire NFL games play-by-play**.

It uses a suite of machine learning models to make decisions at every snap:
*   **Playcalling:** Will the team Run, Pass, Punt, or Kick? (Logistic Regression)
*   **Rushing:** How many yards will the carrier gain? (Kernel Density Estimation to model "boom/bust" potential)
*   **Passing:** Will the pass be completed? How many air yards? (Regression + KDE)
*   **Scoring:** Touchdowns, Field Goals, and Extra Points are modeled probabilistically.

By running these simulations thousands of times (Monte Carlo method), we generate a probability distribution of outcomes for every player, capturing correlations (e.g., if a QB throws for 400 yards, his WR1 likely scored highly) and game scripts.

## 🛠️ Installation

This project uses [Poetry](https://python-poetry.org/) for dependency management.

### Prerequisites
*   Python 3.10+
*   Poetry (`pipx install poetry`)

### Setup
1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd fantasyFootballProjections
    ```
2.  Install dependencies:
    ```bash
    poetry install
    ```

## 🎮 Usage

The application exposes a Command Line Interface (CLI) via `main.py`.

### Basic Run
Run the engine with default settings (Current Season, Current Week, 5 simulations):
```bash
poetry run python main.py
```

### Advanced Options
Customize the simulation parameters:

```bash
poetry run python main.py --season 2023 --week 5 --simulations 100 --version v1.0
```

### Command Line Arguments
| Argument | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--season` | `int` | 2024 | The NFL season to project. |
| `--week` | `int` | 2 | The week number to start projecting from. |
| `--simulations` | `int` | 5 | Number of Monte Carlo simulations to run per game. Higher = more accuracy but slower. |
| `--version` | `str` | "402" | A custom version string to tag output files (e.g., `v1.0`). |

**View Help:**
```bash
poetry run python main.py --help
```

## 🏗️ Architecture

### Directory Structure
*   **`main.py`**: The entry point. Handles CLI parsing, orchestrates data loading, model training, and simulation loops.
*   **`engine/`**: Contains the core game loop (`game.py`). This module manages the `GameState` (score, down, distance, clock) and executes plays.
*   **`models/`**: Machine Learning definitions.
    *   `playcall.py`: Predicts offensive play choice.
    *   `rushers.py`: Models rushing yardage distributions.
    *   `completion.py`: Estimates completion probability.
    *   `kicking.py`: Predicts Field Goal success.
*   **`stats/`**: Logic for aggregating raw Play-by-Play (PBP) data into usable player and team statistics (e.g., `players.py`, `teams.py`).
*   **`data/`**: Stores raw CSV data fetched via `nfl_data_py`.

### Key Concepts
*   **Estimators:** The system uses Exponentially Weighted Moving Averages (EWMA) to estimate team and player talent levels (e.g., `offense_pass_oe_est` for Pass Over Expected).
*   **Contextual Adjustment:** Models adjust baselines based on the opponent. A WR facing a strong defense will have their target share and catch rate damped.

## 📊 Data Source

Data is sourced from the [nfl_data_py](https://github.com/cooperdff/nfl_data_py) library, which provides access to granular NFL Play-by-Play data. The engine automatically downloads necessary data for the requested seasons.

## 🧪 Testing & Validation

The system includes a backtesting module (currently simplified in `main.py`) that allows running projections against historical weeks to compare predicted distributions vs. actual fantasy scores.

## 📝 License

[Insert License Here]
