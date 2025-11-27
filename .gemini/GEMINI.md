# Project Context: Fantasy Football Projections

## 🏗️ Architecture & Stack
- **Domain:** Monte Carlo simulation of NFL games for fantasy projections.
- **Stack:** Python 3.10+, Poetry, Pandas, Scikit-Learn, Joblib (Parallelism).
- **Key Components:**
    - `engine/game.py`: The core physics engine (God Class). Implements "Trilogy of Simulation".
    - `main.py`: Orchestrator with CLI subcommands.
    - `settings.py`: Pydantic configuration.
    - `stats/`: Data processing pipeline (Teams, Players, Estimators).
    - `models/`: Machine Learning models (KDEs, Regressions).
    - `benchmark.py`: Validation harness.

## 📐 The "Trilogy of Simulation" Philosophy
We model interactions using three layers to balance physical realism with player talent:
1.  **Physics (Global KDE):** Captures the fundamental shape of an event (e.g., Scramble yards distribution).
2.  **Skill (Relative Estimator):** Shifts/Scales the KDE based on player history relative to league average.
    *   *Note:* For signed metrics (Air Yards), we use **Shifted Multiplicative Scaling** to prevent sign-flip explosions.
3.  **Matchup (Team Estimator):** Adjusts for opponent strength (e.g., Defense Yards allowed).

`Result = ((Sample + Shift) * Player_Mult) - Shift` (where Shift=0 for strictly positive metrics).

## 🔬 Scientific Workflow
1.  **Hypothesize:** Formulate falsifiable theory (e.g., "QBs fail high because of linear passing scaling").
2.  **Instrument:** Create diagnostic scripts (`tests/diagnose_*.py`) to measure the specific mechanism.
3.  **Experiment:** Run benchmarks (`vXXX`).
4.  **Analyze:** Compare metrics (RMSE, Bias, Fail High) against baseline.
5.  **Verify:** Ensure no regression in data integrity (NaNs, Zero Weights).

## 🧠 Lessons Learned & Guidelines
- **Data Integrity is King:** 
    - **EWMA Sorting:** Must sort by `['season', 'week']` to prevent interleaving years.
    - **NaN Poisoning:** Aggregators must handle `NaN` keys/values to avoid dropping valid players.
    - **Zero Weights:** Always provide a fallback for `random.choices` if weights sum to zero.
- **Simulation Physics:**
    - **Multiplicative vs Additive:** Multiplicative scaling preserves tail skew (Good for Upside) but is dangerous for signed metrics (Air Yards). Use Shifted Multiplicative for signed metrics.
    - **PlayType Enums:** Never use strings for internal logic. Use Enums (`PlayType.RUN`) to prevent silent failures.
- **Benchmarking:**
    - **Sample Size:** `n` must be > 100 per position to be significant.
    - **Granularity:** Aggregate metrics hide position-specific failures (e.g., QB Boom vs Kicker Safety).
- **Warning Triage:** Do not ignore warnings. `SettingWithCopy` often indicates real data flow bugs. `InconsistentVersion` requires model rebuilding.

## 🎯 Roadmap
1.  **QB Ceiling (Active):** Mobile QBs still under-projected (33% Fail High). Needs Split KDEs or Conditional Modeling.
2.  **Shootout Logic:** High-scoring games under-projected (55% Fail High). Needs Pace/Volume variance.
3.  **DST Calibration:** Defense scoring is highly volatile; needs dedicated model or acceptance of variance.
