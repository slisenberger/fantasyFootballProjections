# Data Asset Inventory: The Gold Mine

An audit of the project's dependencies and data pipelines reveals a wealth of untapped data assets.

## 1. Active & Ingested (The "Unlocked" Tier)
*These assets are now reachable via `data/nfl_client.py` and returned by `data/loader.py`.*

| Feature | Source | Strategic Value | Status |
| :--- | :--- | :--- | :--- |
| **Snap Counts** | `import_snap_counts()` | **Role Verification.** Confirm if a "Backup" is actually playing 40% of snaps. | **[Done]** |
| **Participation** | `import_participation_data()` | **The Holy Grail.** Row-by-row list of `offense_players` (IDs on field) and `defense_coverage_type`. Solves the "Who is eligible?" problem. | **[Done]** |
| **Vegas Lines** | `spread_line`, `total_line` (PBP) | **Game Script Priors.** Anchors simulation to market expectations. | **[Done]** |
| **Weather** | `temp`, `wind`, `roof` (PBP) | **Environmental Physics.** Impacts kicking/passing. | **[Done]** |
| **Tempo** | `drive_play_count` (PBP) | **Pace Modeling.** Essential for predicting total play volume. | **[Done]** |
| **Pressure** | `qb_hit` (PBP) | Calculate **Pressure Rate**. Far more stable than Sack Rate. | **[Done]** |
| **Direction** | `pass_location`, `run_gap` (PBP) | **Directional Defense.** "Team X is weak against Runs to the Left." | **[Done]** |


## 2. Library Unlocks (Pending)
*Functions available in `nfl_data_py` / `nflreadpy` we haven't called yet.*

| Feature | Function | Strategic Value | Status |
| :--- | :--- | :--- | :--- |
| **Next Gen** | `import_ngs_data()` | **Player Physics.** `time_to_throw`, `avg_separation`. | Pending |
| **Combine** | `import_combine_data()` | **Rookie Priors.** 40-yard dash times for Bayesian priors. | Pending |

## 3. "Need to Invent" (Derived Metrics)
*Metrics we must calculate ourselves from the above components.*

*   **Defensive Archetypes:** Clustering defenses based on Participation/Coverage frequencies (Blitz Heavy vs Zone Shell).
*   **Injury Severity:** Requires NLP or external feed.

## Strategic Recommendation
1.  **Immediate:** Begin implementing features using the newly ingested data.
2.  **Short Term:** Focus on integrating `Participation` data for Target Share.
3.  **Medium Term:** Explore `Next Gen Stats` for YACOE analysis.