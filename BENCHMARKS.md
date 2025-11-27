# 📊 Benchmarking & Calibration

This document establishes the "Gold Standard" for evaluating the Fantasy Football Projections Engine. We use a standardized backtesting suite to measure the model's accuracy and reliability.

## 🏆 Gold Standard Metrics

To evaluate a model version, we look at three key indicators:

1.  **Calibration (KS Test & PIT Uniformity):**
    *   *Goal:* A uniform distribution of Probability Integral Transform (PIT) values.
    *   *Metric:* **KS Statistic** (lower is better, target < 0.05).
    *   *Meaning:* Are our probability buckets accurate? (e.g., Does a 30% probability event happen 30% of the time?)

2.  **Interval Coverage (Reliability):**
    *   *Goal:* Our X% confidence intervals should capture the actual score X% of the time.
    *   *Metric:* **Coverage 90%** (target = 0.90).
    *   *Meaning:* Are we capturing the true range of outcomes, or are we over/under-confident?

3.  **Bias (Accuracy):**
    *   *Goal:* Zero mean error.
    *   *Metric:* **Bias** (target = 0.0).
    *   *Meaning:* On average, are our projections too high (positive) or too low (negative)?

---

## 📜 Benchmark History

### v409: Probabilistic Injury Injection (Nov 26, 2025)
**Change:** Added stochastic simulation for "Questionable" (Q) players.
*   25% of sims: Player is removed (Inactive).
*   75% of sims: Player volume (`target_share`, `carry_share`) is reduced by 20% (Active but Limited/Decoy).
**Outcome:** **Significant Improvement.**
*   **RMSE:** Dropped to **15.03**.
*   **Fail High:** Improved to **26.8%**. By forcing backups to play 100% of snaps in 25% of worlds, we unlocked their "Boom" potential.
*   **Coverage:** Improved to **64.7%**.

| Metric | Value | Delta (v408) | Interpretation |
| :--- | :--- | :--- | :--- |
| **RMSE** | **15.03** | -0.18 | ✅ Improvement. |
| **Bias** | **+0.07** | -0.01 | ✅ Improvement. |
| **Coverage (90%)** | **64.7%** | +0.9% | ✅ Improvement. |
| **Fail High** | **26.8%** | -1.2% | ✅ Better at capturing Booms (Backups). |
| **Fail Low** | **8.5%** | +0.3% | Slight increase in "Busts" (Starters benching), which is realistic. |

### v408: Empirical Clock Management (Nov 26, 2025)
**Change:** Implemented an empirical look-up table for clock runoff based on score/time/play type. Replaces hardcoded 35s runoff.
**Outcome:** Neutral to slight degradation. While mechanically superior (capturing hurry-up vs clock-killing), the net effect on total play volume was negligible.

### v407: Overtime Logic (Nov 26, 2025)
**Change:** Implemented Overtime state machine (Coin toss, Sudden Death).
**Outcome:** Slight improvement in Bias and Fail High rate.

### v406: Verification & Full Optimization (Nov 26, 2025)
**Change:** Full vectorization of `stats/players.py` combined with "De-Pandas" engine optimization.
**Outcome:** **7.5x End-to-End Speedup** (12s/week vs 90s/week). Metrics confirmed stable against baseline.

---

## 🧠 Lessons Learned

*   **Uncertainty is Key:** Simply adding variance to *efficiency* (v403) failed. Adding variance to *opportunity* (Injury Injection v409) succeeded. This suggests that **Role Uncertainty** is a bigger driver of fantasy variance than **Play Uncertainty**.
*   **Clock Logic:** The empirical lookup table is "pragmatic and likely an improvement," but a static average per bucket misses the *variance* of clock management (e.g., some teams are exceptionally slow/fast).
    *   *Future Improvement:* Train a regression model (or KDE) to predict `runoff` given `score_diff`, `time_remaining`, and `team_tendencies`. This would capture team-specific tempo (e.g., Chip Kelly vs Sean McVay).
*   **The "Boom" Barrier:** The **Censored Boom Hypothesis** (field length constraints) remains the top suspect for the remaining 26.8% "Fail High" rate.

---

## 🏃 How to Run Benchmarks

```bash
# Run the full suite (approx 30 seconds)
poetry run python benchmark.py --simulations 50 --version v410_candidate
```

This will save results to `benchmarks/results_v410_candidate.json` and a detailed CSV.
