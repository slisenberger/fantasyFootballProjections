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

### v408: Empirical Clock Management (Nov 26, 2025)
**Change:** Implemented an empirical look-up table for clock runoff based on score/time/play type. Replaces hardcoded 35s runoff.
**Outcome:** Neutral to slight degradation. While mechanically superior (capturing hurry-up vs clock-killing), the net effect on total play volume was negligible. This reinforces that clock variance alone is not the primary driver of the missing "Boom" weeks.

| Metric | Value | Delta (v407) | Interpretation |
| :--- | :--- | :--- | :--- |
| **RMSE** | **15.21** | +0.06 | Neutral. |
| **Bias** | **+0.08** | 0.00 | Neutral. |
| **Coverage (90%)** | **63.8%** | -0.6% | Slight degradation (over-confident). |
| **Fail High** | **28.0%** | +0.4% | Still missing "boom" weeks. |
| **Speed** | **~12s** | 0s | No impact on speed. |

### v407: Overtime Logic (Nov 26, 2025)
**Change:** Implemented Overtime state machine (Coin toss, Sudden Death).
**Outcome:** Slight improvement in Bias and Fail High rate.

### v406: Verification & Full Optimization (Nov 26, 2025)
**Change:** Full vectorization of `stats/players.py` combined with "De-Pandas" engine optimization.
**Outcome:** **7.5x End-to-End Speedup** (12s/week vs 90s/week). Metrics confirmed stable against baseline.

---

## 🧠 Lessons Learned

*   **Clock Logic:** The empirical lookup table is "pragmatic and likely an improvement," but a static average per bucket misses the *variance* of clock management (e.g., some teams are exceptionally slow/fast).
    *   *Future Improvement:* Train a regression model (or KDE) to predict `runoff` given `score_diff`, `time_remaining`, and `team_tendencies`. This would capture team-specific tempo (e.g., Chip Kelly vs Sean McVay).
*   **The "Boom" Barrier:** Neither Variance Injection (v403), OT (v407), nor Clock Management (v408) significantly dented the 28% "Fail High" rate. The **Censored Boom Hypothesis** (field length constraints) remains the top suspect.

---

## 🏃 How to Run Benchmarks

```bash
# Run the full suite (approx 30 seconds)
poetry run python benchmark.py --simulations 50 --version v409_candidate
```

This will save results to `benchmarks/results_v409_candidate.json` and a detailed CSV.