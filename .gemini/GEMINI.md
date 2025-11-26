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

## 🧠 Lessons Learned & Guidelines
- **Statistical Rigor:**
    - **Directionality:** Always report 'Fail Low' (Over-predicted) vs 'Fail High' (Under-predicted) explicitly. 'Bias' alone hides the story.
    - **Visuals:** Use histograms to validate distribution shapes. Summary stats (KS, RMSE) can be misleading without context.
    - **Data Integrity:** `NaN`s in simulation data are critical bugs, not valid zeros. Filter them before aggregation.
    - **Sanity Checks:** If a metric implies a broken reality (e.g., 27% coverage), assume a code bug first.
- **Core Philosophies:**
    - **Empiricism:** Avoid "magic numbers" or arbitrary coin flips (like fixed breakaway chances). Model behavior should be derived from measured data (KDEs, regressions). If the model is wrong, fix the data source or the statistical model, don't patch it with heuristics.
    - **Speed as a Feature:** Simulation speed directly impacts iteration cycle time. Prioritize vectorization and batching (e.g., pre-sampling KDEs) over per-loop calculations. Slow benchmarks kill development velocity.
- **Documentation:** Always update relevant documentation (e.g., `README.md`, `BENCHMARKS.md`, `ROADMAP.md`) after delivering improvements or significant changes.
- **Workflow:** Prioritize "Robustness" and "Correctness" over quick hacks. Always verify backtesting actually produces metrics.
- **Coding Style:** Use Enums (`PlayType`, `Position`) instead of strings. Use Pydantic for config. Avoid magic numbers.
- **Testing:** Validating `Calibration` (PIT Histograms) is the preferred acceptance test.
- **Pandas:** Avoid boolean indexing on non-boolean columns (e.g., use `df.loc[df.col == 1]`, not `df.loc[df.col]`).
- **Data:** Historical data loading requires `season-1` context.