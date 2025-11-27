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

### v410: Censored Boom Fix (Rushing) (Nov 26, 2025)
**Change:** Split Rushing KDEs into two zones: **Open Field** (yardline > 20) and **Red Zone** (yardline <= 20).
*   *Theory:* Training on all runs suppresses "breakaway" potential because 5-yard TDs in the Red Zone look like 5-yard runs, polluting the distribution. By training Open Field KDEs only on unconstrained runs, we learn the true shape of "Boom" plays.
**Outcome:** **Success.**
*   **Fail High:** Dropped to **25.9%** (Lowest yet).
*   **Bias:** Improved to **+0.06**.
*   **Trade-off:** Slight increase in "Fail Low" (9.3%), possibly due to tighter Red Zone distributions creating more goal-line stands.

| Metric | Value | Delta (v409) | Interpretation |
| :--- | :--- | :--- | :--- |
| **RMSE** | **15.02** | -0.01 | Neutral. |
| **Bias** | **+0.06** | -0.01 | ✅ Improvement. |
| **Coverage (90%)** | **64.9%** | +0.2% | ✅ Improvement. |
| **Fail High** | **25.9%** | -0.9% | ✅ Unlocked more long runs. |
| **Fail Low** | **9.3%** | +0.8% | ⚠️ More busts. |

### v409: Probabilistic Injury Injection (Nov 26, 2025)
**Change:** Added stochastic simulation for "Questionable" (Q) players.
**Outcome:** **Significant Improvement.**
*   **Fail High:** 26.8%
*   **Coverage:** 64.7%

### v408: Empirical Clock Management (Nov 26, 2025)
**Outcome:** Neutral. Better physics, same calibration.

---

## 🧠 Lessons Learned

*   **Censoring Matters:** Field position acts as a hard clamp on yardage distributions. Splitting models by zone ("Contextual KDEs") is a viable path to fixing the "Fail High" rate.
    *   *Next Step:* Apply this same logic to **Receiving Models** (Air Yards, YAC), which suffer from the same endzone constraints.
*   **Uncertainty is Key:** (v409 Finding) Modeling role uncertainty (injuries) is crucial.

---

## 🏃 How to Run Benchmarks

```bash
# Run the full suite (approx 30 seconds)
poetry run python benchmark.py --simulations 50 --version v411_candidate
```