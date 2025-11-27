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

### v405: The "Surgical Strike" Optimization (Nov 26, 2025)
**Change:** Removed Pandas overhead from the hot simulation loop (`advance_snap`). Implemented pre-filtering of player lists and dictionary-based stat lookups in `GameState.__init__`.
**Outcome:** **Massive speedup.** Simulation core logic is ~9x faster. End-to-end runtime improved by ~3x (bottleneck shifted to `joblib`/IO overhead). Metrics remain statistically identical to baseline.

| Metric | Value | Delta (v402) | Interpretation |
| :--- | :--- | :--- | :--- |
| **RMSE** | **15.15** | -0.03 | Stable. |
| **Bias** | **+0.08** | 0.00 | Stable. |
| **Coverage (90%)** | **65.6%** | -0.2% | Stable. |
| **Fail High** | **26.8%** | -0.3% | Stable. |
| **Speed** | **~30s** | -60s | **3x Faster.** (From ~90s to ~30s per week). |

### v404: Optimization & Reversion (Nov 26, 2025)
**Change:** Reverted "magic number" variance injection (v403). Implemented KDE pre-sampling.
**Outcome:** Performance returned to baseline (v402). Speed improved slightly (~87s/week).

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

---

## 🏃 How to Run Benchmarks

```bash
# Run the full suite (approx 2-3 mins)
poetry run python benchmark.py --simulations 50 --version v406_candidate
```

This will save results to `benchmarks/results_v406_candidate.json` and a detailed CSV.
