# Project Context: Fantasy Football Projections

## 🏗️ Architecture & Stack
- **Domain:** Monte Carlo simulation of NFL games for fantasy projections.
- **Stack:** Python 3.10+, Poetry, Pandas, Scikit-Learn, Joblib (Parallelism).
- **Key Components:**
    - `engine/game.py`: The core physics engine (God Class). Optimized for O(1) execution in hot loops.
    - `main.py`: Orchestrator with CLI subcommands (`project`, `backtest`).
    - `settings.py`: Pydantic configuration (Scoring, Runtime).
    - `evaluation/calibration.py`: Truth harness (PIT metrics).
    - `stats/players.py`: Vectorized statistical feature engineering.
- **Philosophy:** Probabilistic distributions > Point estimates. Calibration is the primary metric of success.

## 🧠 Lessons Learned & Guidelines
- **Statistical Rigor:**
    - **Directionality:** Always report 'Fail Low' (Over-predicted) vs 'Fail High' (Under-predicted) explicitly. 'Bias' alone hides the story.
    - **Visuals:** Use histograms to validate distribution shapes. Summary stats (KS, RMSE) can be misleading without context.
    - **Data Integrity:** `NaN`s in simulation data are critical bugs, not valid zeros. Filter them before aggregation.
    - **Sanity Checks:** If a metric implies a broken reality (e.g., 27% coverage), assume a code bug first.
- **Core Philosophies:**
    - **Empiricism:** Avoid "magic numbers". Model behavior should be derived from measured data (KDEs, regressions).
    - **Speed as a Feature:** Simulation speed directly impacts iteration cycle time. 
    - **Performance Optimization:**
        - **Pandas is Poison (in loops):** Never access DataFrame values (e.g., `df.loc[x].values[0]`) inside a hot loop. It incurs a ~1000x overhead vs native Python types.
        - **Vectorize Everything:** Replace `groupby().apply(custom_func)` with vectorized alternatives like `groupby().transform()`, `pd.concat`, or `groupby().ewm()`.
        - **Pre-Computation:** Resolve all lookups, filters, and weights *before* the simulation loop starts.
- **Documentation:** Always update relevant documentation (e.g., `README.md`, `BENCHMARKS.md`, `ROADMAP.md`) after delivering improvements or significant changes.
- **Workflow:** Prioritize "Robustness" and "Correctness" over quick hacks. Always verify backtesting actually produces metrics.
- **Coding Style:** Use Enums (`PlayType`, `Position`) instead of strings. Use Pydantic for config. Avoid magic numbers.
- **Testing:** Validating `Calibration` (PIT Histograms) is the preferred acceptance test.
- **Pandas:** Avoid boolean indexing on non-boolean columns (e.g., use `df.loc[df.col == 1]`, not `df.loc[df.col]`).
- **Data:** Historical data loading requires `season-1` context.
