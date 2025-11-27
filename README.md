# 🏈 Fantasy Football Projections Engine

A probabilistic, play-by-play simulation engine for NFL Fantasy Football.

> **Why Simulation?** Most projections give you an average. This engine simulates the game 1,000 times to tell you the **Range of Outcomes** (Ceiling, Floor, and Median).

![Report Screenshot](https://raw.githubusercontent.com/slisenberger/fantasyFootballProjections/master/docs/report_preview.png) 
*(Screenshot placeholder - check `projections/v.../report.html`)*

---

## 🚀 Getting Started

### Prerequisites
*   Python 3.10+
*   Poetry

### Installation
```bash
git clone https://github.com/slisenberger/fantasyFootballProjections.git
cd fantasyFootballProjections
poetry install
```

### Running Projections
Generate projections for the current week (e.g., 2025 Week 13):

```bash
poetry run python main.py project --season 2025 --week 13 --simulations 1000
```

This will produce:
1.  **HTML Report:** `projections/v416.../week_13/report.html` (Visual rankings & boom/bust charts).
2.  **CSV Data:** `projections/v416.../week_13/summary.csv` (Raw data).

### Running Rest-of-Season (ROS)
To simulate the rest of the season (from current week to Week 18):

```bash
poetry run python main.py project --season 2025 --week 13 --simulations 1000
```
(It automatically runs ROS loops and generates `ros/ros_report.html`).

---

## 🧠 How It Works

This isn't just a spreadsheet calculator. It simulates every snap of the game.

*   **Play Calling:** Uses Logistic Regression to decide Run vs. Pass based on down, distance, and score.
*   **Yardage:** Samples from Kernel Density Estimators (KDEs) to model realistic yardage distributions (including the "Censored Boom" fix for open-field runs).
*   **Game Script:** Accurately models "Hurry Up" offense (trailing teams play faster) and "Clock Killing" (leading teams play slower).
*   **Uncertainty:** Stochastic modeling of Injuries (Questionable players have a risk of being benched in the sim).

👉 **[Read the Full Methodology](METHODOLOGY.md)** for a deep dive into the physics and statistics.

---

## 📊 Benchmarks (v416)

We hold ourselves to a "Gold Standard" of calibration.

*   **RMSE:** ~15.0
*   **Bias:** +0.06 (Nearly zero mean error)
*   **Coverage (90% Interval):** ~65% (Target 90% - still refining tails)
*   **Fail High (Missed Booms):** 25.9% (Best in class)

---

## 🛠️ Contributing

1.  Check `ROADMAP.md` for upcoming features.
2.  Run tests: `poetry run python -m unittest discover tests`
3.  Submit PRs against `master`.

---