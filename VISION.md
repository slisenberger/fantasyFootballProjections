# 🌌 Project Vision & Master Roadmap

This document serves as the "Canvas" for the future of the Fantasy Football Projections Engine. It integrates the existing roadmap with a broader exploration of the fantasy landscape and modern software engineering practices.

---

## 🏆 The North Star
**To build an autonomous, self-correcting, and highly customizable simulation engine that outperforms consensus rankings by leveraging game-theory optimal decision making and rigorous probabilistic modeling.**

---

## 1. 🧠 Data Science & Modeling (The "Brain")

The core value proposition is *better predictions*.

### 🟢 Short Term (High ROI)
*   **Calibrated Kicker Models:** Replace the generic "coin flip" model with a distance-decay model per kicker (e.g., Justin Tucker's 50+ yd % vs League Avg).
*   **Defense-Adjusted Fantasy Points (DAFP):** Instead of just "Defense Pass OE", explicitly model how much a defense suppresses fantasy points by position (e.g., "The Jets allow 20% fewer points to WRs than average").
*   **Overtime Logic:** Add a simple state machine for OT (coin toss, modified sudden death) to capture that extra 10 minutes of production potential.

### 🟡 Medium Term
*   **Gradient Boosting Models (XGBoost/LightGBM):** Replace Logistic Regressions for playcalling and completion probability. Tree-based models handle non-linear interactions (e.g., "3rd & Long + Trailing by 4 + 4th Quarter") much better than linear regression.
*   **Hyperparameter Tuning (Optuna):** Automate the tuning of `clock_burn`, `sack_rates`, and `bandwidth` for KDEs to minimize the Calibration Error (PIT).
*   **Injury Probabilities:** Instead of `Active/Inactive`, model `Health %`. If a player is "Questionable", simulate them playing only 50% of snaps in 50% of worlds.

### 🔴 Long Term (Research)
*   **Player Embeddings:** Use matrix factorization or neural networks to learn latent representations of players (e.g., "Deep Threat WR", "Satellite Back") to better predict interactions with QBs.
*   **Game Script Clustering:** Classify historical games into "Scripts" (Shootout, Grind-it-out, Blowout) and probabilistically assign the upcoming matchup to a script cluster.

---

## 2. 🏗️ Engineering & Architecture (The "Chassis")

The engine needs to be robust, fast, and modular.

### 🟢 Short Term (High ROI)
*   **Configuration System (Pydantic):** **CRITICAL.** Move all magic numbers (`n_sims`, `scoring_values`, `year`) into a strongly-typed configuration object. This enables "Custom Leagues" immediately.
*   **Smart Data Caching (DuckDB):** Replace the CSV loading with a local DuckDB file.
    *   *Benefit:* Instant startup (0.1s vs 10s).
    *   *Benefit:* Query specific weeks without loading 10 years of data into RAM.
*   **Refactored `do_projections`:** Split the monolithic "Run Everything" function into discrete pipelines: `EtlPipeline`, `SimulationPipeline`, `EvaluationPipeline`.

### 🟡 Medium Term
*   **Vectorized Simulation:** Rewrite the `Game` class to simulate 1,000 games simultaneously using `numpy` arrays instead of Python objects.
    *   *Impact:* 100x speedup. Allows running `n=100,000` for DFS variance analysis.
*   **Reproducibility:** Strict seeding of random number generators to ensure that if you run the same config twice, you get the exact same results.

### 🔴 Long Term
*   **API Server (FastAPI):** Expose the engine as a REST API.
    *   `POST /simulate { "home": "BUF", "away": "MIA" }` -> Returns JSON distribution.
*   **Distributed Backtesting:** Use AWS Lambda or Ray to run 10 years of backtests in minutes.

---

## 3. ✨ Product & Features (The "Utility")

How you actually interact with the system.

### 🟢 Short Term (High ROI)
*   **Value Over Replacement (VOR) & WAR:** Implement VOR calculation. Raw points don't matter; points *above the waiver wire* matter. This is essential for draft guides.
*   **Custom Scoring Support:** Allow users to define `ppr: 0.5` or `passing_td: 6` in a config file.
*   **Tiered Output:** Output "Starters", "Bench", "Sleepers", and "Busts" based on their range of outcomes (e.g., High Ceiling/Low Floor = Sleeper).

### 🟡 Medium Term
*   **Streamlit Dashboard:** A local web app to browse projections.
    *   Features: "Who do I start?" comparison tool showing the two probability distributions overlapping.
*   **DFS Optimizer:** Use the simulation outputs to generate optimal DraftKings/FanDuel lineups that correlate (e.g., Stack QB + WR).

### 🔴 Long Term
*   **Draft Assistant:** A real-time tool that updates VORPs as players are picked during your draft.
*   **Automated Reports:** A GitHub Action that runs every Tuesday, generates the projections, and emails you a PDF/HTML "Game Plan".

---

## 4. 📉 Validation & Trust (The "Audit")

### 🟢 Short Term
*   **Automated Backtest Report:** A script that runs the `calibration` module on the last 3 seasons and outputs a `scorecard.md` with RMSE and Bias per position.
*   **Unit Test Suite:** Cover the core NFL rules (Down/Distance logic) with tests to ensure we aren't simulating "5th Downs".

---

## 🚀 Prioritized Execution Plan

Based on "ROI" (Impact / Effort), here is the recommended attack order:

1.  **Config System (`settings.py`):** We cannot do "Custom Scoring" or "Smart Backtesting" without a clean way to pass settings around.
    *   *Impact:* High. Unlocks multiple features.
    *   *Effort:* Low.
2.  **Data Layer (DuckDB):** The iteration cycle is slow because of data loading. Fixing this makes every future task faster.
    *   *Impact:* High (Speed).
    *   *Effort:* Medium.
3.  **Value Over Replacement (VOR):** The most useful metric for decision making.
    *   *Impact:* High (Utility).
    *   *Effort:* Low (Math on top of existing outputs).
4.  **Calibration Loop Automation:** We have the harness, now we need to script the "Full History Run".
    *   *Impact:* High (Trust).
    *   *Effort:* Medium (Requires downloading data).

---
