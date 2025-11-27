# Benchmarks

## Summary of Progress

| Version | Date | Description | RMSE | Bias | Coverage 90% | Fail High |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline** | 2025-11-25 | Initial v402 | 14.04 | +0.05 | 45.8% | 32.6% |
| **v419 Fixed** | 2025-11-26 | Audit + Fix (n=1305) | **11.85** | **+0.06** | **70.6%** | **21.6%** |

*Note: Fail High Target is 10%. Ideally 5-10%.*

## Calibration by Position (v419 Fixed)

| Position | RMSE | Bias | Fail High | Status |
| :--- | :--- | :--- | :--- | :--- |
| **QB** | 8.03 | +0.16 | **30.5%** | 🔴 Under-Projected Upside. Needs Scramble/TD work. |
| **RB** | 6.99 | +0.02 | **11.1%** | 🟢 **Perfect Calibration.** |
| **WR** | 7.60 | +0.02 | 13.2% | 🟡 Good. Slightly conservative. |
| **TE** | 5.82 | +0.04 | 16.0% | 🟡 Okay. High variance. |
| **K** | 4.94 | -0.20 | 2.0% | 🔵 Over-Projected. Needs FGOE. |

## Key Insights
1.  **RB Model is Solid:** The Bimodal (Open/RedZone) split for rushing solved the RB calibration issues.
2.  **QB Upside Missing:** QBs hit their 90th percentile projection 30% of the time. We are likely under-estimating Rushing production or "Shootout" passing volume for elite QBs.
3.  **Kicker Safety:** Kickers are more predictable and lower-ceiling than our model currently assumes.
4.  **DST Variance:** (Excluded from table but analyzed separately) DSTs account for the majority of "Scrub Booms" due to random TDs.

## Methodology
*   **Simulations:** 50 per game.
*   **Weeks:** 2022 (W1, W8, W17), 2023 (W1, W8, W17).
*   **Metric:** PIT (Probability Integral Transform) Calibration.
