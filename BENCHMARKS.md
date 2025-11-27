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

### v418: Aggressive YAC (Open Field Global) (Nov 26, 2025) - CURRENT GOLD STANDARD
**Change:** Trained YAC models *only* on Open Field data (>20 yards), but applied them *globally* (even in Red Zone).
*   *Theory:* A player's ability to break tackles (YAC) is best measured in the open field. In the Red Zone, we should sample from their "Open Field Potential" and let the engine mechanically cap the yards at the goal line. Using a "Red Zone" model double-penalizes them (statistical shortness + mechanical cap).
**Outcome:** **The Winner.**
*   **Fail High:** 25.8% (Matches best).
*   **RMSE:** 14.88 (Solid).
*   **Coverage:** 65.4% (Best yet).

| Metric | Value | Delta (v417) | Interpretation |
| :--- | :--- | :--- | :--- |
| **RMSE** | **14.88** | +0.17 | Acceptable trade-off. |
| **Bias** | **+0.08** | +0.01 | Neutral. |
| **Coverage (90%)** | **65.4%** | +0.3% | ✅ Best yet. |
| **Fail High** | **25.8%** | -0.5% | ✅ Unlocked boom plays. |
| **Fail Low** | **8.8%** | +0.2% | Stable. |

### v417: Split YAC (Nov 26, 2025)
**Change:** Split YAC into Open/RZ (using RZ model for RZ plays).
**Outcome:** Good RMSE (14.71) but slightly worse Ceiling (26.3%). The RZ model likely suppressed "breakaway TD" potential.

### v410: Censored Boom Fix (Rushing) (Nov 26, 2025)
**Change:** Split Rushing KDEs into Open/RZ.
**Outcome:** Big win for Ceiling (25.9%).

---

## 🧠 Lessons Learned

*   **Censoring Matters:** Field position acts as a hard clamp on yardage distributions.
*   **Mechanical vs Statistical Constraints:**
    *   For **Rushing**, the RZ is a different physical environment (wall of bodies). Splitting models (Open vs RZ) works best.
    *   For **Receiving (YAC)**, the RZ constraint is primarily the endzone itself. Using an "Open Field" model globally and letting the engine cap the yards works best.
*   **Uncertainty is Key:** Modeling role uncertainty (injuries) is crucial.

---

## 🏃 How to Run Benchmarks

```bash
# Run the full suite (approx 30 seconds)
poetry run python benchmark.py --simulations 50 --version v419_candidate
```