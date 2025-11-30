# Data Asset Inventory: The Gold Mine

An audit of the project's dependencies and data pipelines reveals a wealth of untapped data assets. We do not need to scrape new data; we simply need to stop dropping it or start calling the library functions already installed.

## 1. Immediate Access (The "Stop Dropping" Tier)
*These columns exist in the raw PBP data today but are either explicitly dropped in `loader.py` or ignored.*

| Feature | Column Name(s) | Strategic Value |
| :--- | :--- | :--- |
| **Pressure** | `qb_hit`, `sack` | Calculate **Pressure Rate** (Sacks + Hits / Dropbacks). A far more stable metric for Defensive Line strength than Sack Rate alone. |
| **Direction** | `pass_location`, `run_gap` | **Directional Defense.** "Team X is weak against Runs to the Left" or "Weak against Middle Passes." |
| **Weather** | `temp`, `wind`, `roof`, `surface` | **Environmental Physics.** High wind suppresses deep passing. Turf increases speed/injuries. currently *dropped* by loader. |
| **Vegas** | `spread_line`, `total_line` | **Game Script Priors.** Use the Spread to inform the "Shootout" probability. A 50.5 total implies a very different game than a 38.0 total. |
| **Exp. YAC** | `xyac_mean_yardage`, `xyac_median_yardage` | **YAC Over Expectation (YACOE).** Benchmarking players against `xyac` isolates pure playmaker ability from scheme/blocking. |
| **Tempo** | `drive_play_count`, `drive_time_of_possession` | **Pace Modeling.** currently *dropped*. Essential for predicting total play volume (The "Shootout" factor). |

## 2. Library Unlocks (The "Import" Tier)
*The `nfl_data_py` (and `nflreadpy`) library has functions we are not calling.*

| Feature | Function | Strategic Value |
| :--- | :--- | :--- |
| **Schematics** | `import_ftn_data()` | **The Holy Grail.** Contains `is_man_coverage`, `is_zone_coverage`, `is_blitz`. Allows true "Matchup Modeling" (e.g., "QB vs Man Coverage"). |
| **Next Gen** | `import_ngs_data()` | **Player Physics.** `time_to_throw` (O-Line health), `avg_separation` (WR talent), `completion_probability_above_expectation` (CPOE ground truth). |
| **Snap Counts** | `import_snap_counts()` | **Role Verification.** Confirm if a "Backup" is actually playing 40% of snaps (Gadget player) vs 0% (Bench warmer). |
| **Combine** | `import_combine_data()` | **Rookie Priors.** Use 40-yard dash times to set the "Speed" prior for rookies with no NFL stats. |

## 3. "Need to Invent" (Derived Metrics)
*Metrics we must calculate ourselves from the above components.*

*   **Defensive Archetypes:** Clustering defenses based on FTN data (Blitz Heavy, Soft Zone, etc.).
*   **WR/CB Matchups:** We do *not* have specific "Who covered Whom" tracking data row-by-row. We must rely on "LWR vs RCB" proxies using `pass_location`.
*   **Injury Severity:** We have `report_status` (Questionable), but not "High Ankle Sprain vs Soreness." requires manual NLP or external feed.

## Strategic Recommendation
1.  **Immediate:** Modify `loader.py` to **stop dropping** `temp`, `wind`, `drive_play_count`, and `pass_location`.
2.  **Short Term:** Use `qb_hit` to build the `pressure_rate` estimator.
3.  **Medium Term:** Integrate `import_ftn_data` to build the Defensive Archetype system.
