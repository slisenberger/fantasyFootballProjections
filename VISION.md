# 🌌 Project Vision & Master Roadmap

This document captures the vision and feature backlog for the Fantasy Football Projections Engine.

> **Goal:** To build the most statistically rigorous, flexible, and automated fantasy football simulation engine available open-source.

---

## 🧠 Data Science & Modeling (The "Brain")

The core value proposition is *better predictions*.

### 🟢 Short Term (High ROI)
*   **Probabilistic Injury Impact:** Model "Questionable" players with a bimodal distribution (Active/Inactive) or reduced snap count distribution, rather than a binary flag.
*   **Clock Runoff Regression:**
    *   *Current:* Empirical lookup table (mean runoff per context bucket).
    *   *Future:* Train a regression model to predict `runoff` based on score, time, and *team tempo* stats. This would capture the variance between fast-paced and slow-paced offenses.

### 🟡 Medium Term
*   **The "Censored Boom" Problem (KDE Refinement):**
    *   *Hypothesis:* Our current KDEs train on observed yards (e.g., a 10-yard TD runs is recorded as 10 yards). In simulation, a player at their own 20 might roll a "10 yard run" from the KDE that *would have been* a 50-yard breakaway if not for the endzone. This artificially suppresses ceiling outcomes.
    *   *Solution:* Train split KDEs: one for "Open Field" (unconstrained potential) and one for "Red Zone" (space constrained).
*   **Gradient Boosting Models (XGBoost):** Replace Logistic Regressions for playcalling. Tree-based models capture non-linear "Game Script" interactions better.

### 🔴 Long Term (Research)
*   **Player Embeddings:** Use matrix factorization to learn latent representations (e.g., "Deep Threat WR").
*   **Game Script Clustering:** Classify historical games into scripts (Shootout, Defensive Struggle) and simulate the *type* of game first.

---

## 🏗️ Engineering & Architecture (The "Chassis")

### 🟢 Short Term (High ROI)
*   **Optimization (Completed v406):** The simulation loop is now 9x faster and O(1) per play. Data prep is 18x faster.
*   **Smart Data Caching (DuckDB):** Replace CSV loading with DuckDB for instant startup.

### 🟡 Medium Term
*   **Vectorized Simulation (Numpy):** Rewrite `Game` to simulate 10,000 games in parallel using array operations, removing the Python loop entirely.

---

## ✨ Product & Features (The "Utility")

### 🟢 Short Term
*   **Value Over Replacement (VOR):** Contextualize raw points.
*   **Custom Scoring Support:** (Completed v403).

### 🟡 Medium Term
*   **Web Dashboard:** Interactive Streamlit app to visualize probability distributions (not just point estimates).

---

## 📉 Evaluation (Trust)

*   **Scale Backtesting:** Run the full 2018-2023 history to generate a comprehensive "Scorecard" of model accuracy.
