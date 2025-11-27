# Project Context: Fantasy Football Projections

## 🏗️ Architecture & Stack
- **Domain:** Monte Carlo simulation of NFL games for fantasy projections.
- **Stack:** Python 3.10+, Poetry, Pandas, Scikit-Learn, Joblib (Parallelism).
- **Key Components:**
    - `engine/game.py`: The core physics engine (God Class, refactoring in progress).
    - `main.py`: Orchestrator with CLI subcommands (`project`, `backtest`).
    - `settings.py`: Pydantic configuration (Scoring, Runtime).
    - `evaluation/calibration.py`: Truth harness (PIT metrics).
- **Philosophy:** Probabilistic distributions > Point estimates. Calibration is the primary metric of success.

## 🔬 Scientific Workflow (Mandatory)
When debugging complex behaviors (like calibration errors or statistical anomalies), adhere to this loop:
1.  **Hypothesize:** Formulate clear, falsifiable hypotheses about the root cause. (e.g., "QBs fail high because we underestimate rushing variance").
2.  **Instrument & Measure:** Create specific diagnostic scripts or metrics to test the hypothesis *before* applying a fix. Do not guess. (e.g., "Measure QB Rushing Yard Variance in Sims vs Actuals").
3.  **Experiment:** Run the simulation with the instrumentation. Collect data.
4.  **Analyze:** Compare Empirical Data against the Hypothesis.
5.  **Refine/Fix:** Only implement code changes once the mechanism is understood.
6.  **Verify:** Run the Benchmark suite (`v419` or newer) to confirm the global impact.

## 🧠 Lessons Learned & Guidelines
- **Workflow:** Prioritize "Robustness" and "Correctness" over quick hacks. Always verify backtesting actually produces metrics.
- **Coding Style:** Use Enums (`PlayType`, `Position`) instead of strings. Use Pydantic for config. Avoid magic numbers.
- **Testing:** Validating `Calibration` (PIT Histograms) is the preferred acceptance test.
- **Pandas:** Avoid boolean indexing on non-boolean columns.
- **Data:** 
    - Historical data loading requires `season-1` context.
    - **NaN Handling:** Aggregation loops must rigorously check for `NaN` keys or values to prevent poisoning entire datasets.
- **Benchmarking:** Always ensure `n` (sample size) is statistically significant (>50 per position) before drawing conclusions.