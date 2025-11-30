# 🗺️ Project Roadmap

This document captures the vision and feature backlog for the Fantasy Football Projections Engine.

> **Goal:** To build the most statistically rigorous, flexible, and automated fantasy football simulation engine available open-source.

---

## 🧠 Core Modeling (Data Science)

*   **Kicker Probability Models:**
    *   *Current:* Generic model for all kickers.
    *   *Future:* Individual models based on kicker accuracy history (e.g., Justin Tucker vs replacement level).
*   **Defensive Modeling:**
    *   *Current:* Rudimentary adjustments based on team-level "Pass OE" allowed.
    *   *Future:* Player-level matchups (CB vs WR), pressure rates vs O-Line grades.
*   **Overtime Logic:**
    *   *Current:* Not explicitly modeled?
    *   *Future:* Implement NFL overtime rules (coin toss, modified sudden death) to accurately capture extra fantasy production.
*   **Injury Logic:**
    *   *Current:* "Questionable" players are binary (active/inactive) or rely on external API.
    *   *Future:* Probabilistic injury impact (e.g., "Active but snap count limited to 60%").

## 🏗️ System Architecture (Engineering)

*   **Smart Data Loading:**
    *   *Current:* Heuristic loading based on `season - 1`.
    *   *Future:* A `DataManager` that intelligently caches data, checks for updates, and loads exactly what is needed for the requested simulation window.
*   **Control Flow Separation:**
    *   *Current:* `do_projections` runs future sims AND backtesting.
    *   *Future:* Explicit CLI modes:
        *   `python main.py project --week 5`
        *   `python main.py backtest --range 2018-2022`
        *   `python main.py calibrate`
*   **Optimization:**
    *   *Current:* Parallelized inner loop (simulations per game).
    *   *Future:* Verify if backtesting outer loop (weeks/seasons) can be parallelized for massive scale. Vectorized simulation (numpy) for 100x speedup.

## ✨ Features (Product)

*   **Configurable Scoring Rules:**
    *   *Current:* Hardcoded Half-PPR (approx).
    *   *Future:* Support for Standard, PPR, TE-Premium, 6pt Passing TD via config file (`scoring.yaml`).
*   **Value Over Replacement (VOR):**
    *   *Future:* Calculate VOR metrics to contextualize raw points (e.g., "How much better is this QB than the waiver wire option?").
*   **Web / HTML Output:**
    *   *Current:* CSV files.
    *   *Future:* Generate a static HTML report with interactive charts (Plotly/Altair) or a simple Streamlit/Dash app.
*   **Automation:**
    *   *Future:* GitHub Actions or Cron job to run projections every Tuesday morning and commit the results to a `history/` branch.

## 📉 Evaluation (Trust)

*   **Scale Backtesting:**
    *   *Current:* 1 week smoke test.
    *   *Future:* Run full-season backtests (Weeks 1-17) for 2018-2023 to establish a reliable baseline of accuracy (RMSE, Calibration).
