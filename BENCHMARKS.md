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

### v404: Optimization & Reversion (Nov 26, 2025)
**Change:** Reverted "magic number" variance injection (v403). Implemented KDE pre-sampling to optimize speed. Fixed `ZeroDivisionError` for early season weeks.
**Outcome:** Performance returned to baseline (v402) levels, confirming the variance injection was ineffective. Speed improved slightly (~87s/week), but overhead remains elsewhere.

| Metric | Value | Delta (v402) | Interpretation |
| :--- | :--- | :--- | :--- |
| **RMSE** | **15.14** | -0.04 | Stable. |
| **Bias** | **+0.08** | 0.00 | Stable under-prediction. |
| **Coverage (90%)** | **64.9%** | -0.9% | Still over-confident. |
| **Fail High** | **27.7%** | +0.6% | Still missing "boom" weeks. |
| **Speed** | **~87s** | -3s | Pre-sampling helped, but Python loop overhead dominates. |

### v402: Baseline (Nov 26, 2025)
**Suite:** Weeks 8 & 17 of 2022-2023.
**Sample Size:** 646 Player-Games.

| Metric | Value | Target | Status | Interpretation |
| :--- | :--- | :--- | :--- | :--- |
| **RMSE** | **15.18** | 0 | ℹ️ | Average error magnitude. |
| **Bias** | **+0.08** | 0.0 | ⚠️ | Slight under-prediction bias (Actuals > Sims). |
| **Coverage (90%)** | **65.8%** | 90% | ❌ | **Over-confident.** Actual scores fall outside our 90% range 34% of the time. |
| **Fail Low** | **7.1%** | 5% | ⚠️ | Slightly high. We over-predicted ~7% of players (Actual < 5th percentile). |
| **Fail High** | **27.1%** | 5% | ❌ | **Major Miss.** We massively under-predicted boom weeks. 27% of players scored *above* our 95th percentile. |
| **KS Stat** | **0.219** | < 0.05 | ❌ | Poor calibration. Skewed towards under-prediction. |

### Segment Analysis (v402)

| Segment | Weeks | Bias | Cov 90% | Fail High | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Early** | 1-4 | N/A | N/A | N/A | *Currently failing to generate due to historical data loading gaps.* |
| **Mid** | 5-12 | +0.05 | 65.4% | 26.1% | Significant under-prediction of ceilings. |
| **Late** | 13-18 | +0.11 | 66.2% | 28.0% | Highest bias and "boom" miss rate. |

### 🧠 Insights & Next Steps

1.  **The "Boom" Problem:** The model's biggest failure is missing the ceiling. Nearly 30% of players are scoring above our *maximum* expected outcome. This implies our simulation lacks the "long tail" events (long TDs, overtime, shootouts).
    *   *Attempted Fix (v403):* Artificial variance injection. Failed (negligible impact).
    *   *Correction (v404):* Reverted to empirical modeling. Next steps must focus on improved tail modeling in KDEs or game clock management (more plays).
2.  **Bias Drift:** The bias creeps up to +0.11 in the late season, suggesting we are systematically underestimating scoring as the season progresses.
3.  **Speed:** Pre-sampling KDEs (v404) improved architecture but didn't solve the speed bottleneck. Profiling suggests the core `for` loop in `advance_snap` is the limit.

---

## 🏃 How to Run Benchmarks

```bash
# Run the full suite (approx 5-10 mins)
poetry run python benchmark.py --simulations 50 --version v405_candidate
```

This will save results to `benchmarks/results_v405_candidate.json` and a detailed CSV.