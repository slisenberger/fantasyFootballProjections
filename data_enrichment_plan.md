# Action Plan: Advanced Data Enrichment (Defensive Schematics)

This plan addresses the "Average of Averages" trap by enriching our dataset with schematic and derived metrics. The goal is to move beyond scalar defensive rankings (e.g., "15th ranked pass defense") to matchup-specific modeling (e.g., "Weak against Deep Passes", "High Pressure Rate").

## Phase 1: Derived Metrics (Computational Enrichment)
**Goal:** Squeeze more signal out of our *existing* Play-by-Play (PBP) data without needing new external scrapers yet. We can calculate proxies for coverage shells and pressure.

### Step 1.1: "Air Yards Allowed" Granularity
*   **Current State:** We calculate `defense_relative_air_yards` as a single scalar.
*   **Action:** Split defensive passing stats into "Depth Buckets" in `stats/teams.py`.
    *   `def_short_comp_rate` (0-10 yards)
    *   `def_inter_comp_rate` (10-20 yards)
    *   `def_deep_comp_rate` (20+ yards)
*   **Hypothesis:** A "Two-High" defense will have a *high* allowed completion rate for Short passes but a *very low* rate for Deep passes. This fingerprint allows the simulation to force QBs into "Checkdown Hell" rather than just "Bad Day."

### Step 1.2: Pressure Rate Proxy
*   **Problem:** "Sack Rate" is an outcome, "Pressure" is a process. Sacks are rare/noisy; Pressure is stable.
*   **Action:** Calculate `pressure_proxy` in `stats/teams.py`.
    *   **Formula:** `(Sacks + QB Hits + Hurries) / Dropbacks` (Note: `QB Hits` are in standard PBP. `Hurries` might require nflverse `ftn_charting` or similar if available, otherwise rely on `qb_hit`).
    *   **Implementation:** Update `models/playcall.py` to use `pressure_rate_differential` (Offense Line Allow Rate vs Defense Line Generate Rate).
    *   **Impact:** High pressure rates should increase `checkdown_probability` and `scramble_probability`.

### Step 1.3: "YAC Allowed" Profile
*   **Action:** Calculate `def_yac_per_completion` separately from `def_air_yards`.
*   **Context:** Some defenses (Bend-Don't-Break) allow high completions but tackle instantly (Low YAC). Others play aggressive Man (High Sack, but if beaten, High YAC).
*   **Integration:** Feed this into the `compute_yac` function in `engine/game.py`.

---

## Phase 2: External Data Integration (nflverse/ftn_charting)
**Goal:** Ingest "Ground Truth" schematic data if accessible via `nfl_data_py`.
*Note: `nfl_data_py` provides access to `ftn_charting` (FTN Data) for recent seasons.*

### Step 2.1: Ingest Charting Data
*   **Action:** Create `data/charting_client.py`.
*   **Source:** `nfl_data_py.import_ftn_data(years=[2023, 2024])`.
*   **Key Metrics to Extract:**
    *   `is_man_coverage` / `is_zone_coverage`
    *   `is_blitz`
    *   `is_pressure` (True/False on play level)
    *   `run_gap` (already used, but refine usage).

### Step 2.2: Defensive Personality Clustering
*   **Action:** Train a K-Means clusterer in `stats/defense_clustering.py`.
*   **Features:** Blitz Rate, Man Coverage Rate, Light Box Rate.
*   **Output:** Assign each defense a "Archetype":
    *   *Cluster A:* "Aggressive Man-Blitz" (High Variance, High Sack, High Big Play Allowed).
    *   *Cluster B:* "Soft Zone Shell" (Low Variance, Low ADOT Allowed, High Completion %).
*   **Usage:** The Simulation Engine uses the Archetype to adjust the *shape* of the outcome distributions (e.g., Cluster A widens the variance of the Passing KDE).

---

## Phase 3: The "Matchup Engine" (Engine Integration)
**Goal:** Apply these new metrics to the simulation logic.

### Step 3.1: Route-Level Adjustments (Simplified)
*   **Problem:** We don't simulate individual routes.
*   **Proxy Solution:** Adjust `target_share` based on "Archetype vs Player Type".
    *   **Logic:**
        *   IF Defense = "Soft Zone Shell" AND Player = "Deep Threat WR" (High ADOT):
        *   THEN `target_share_multiplier = 0.8` (He gets taken away).
        *   AND `yac_multiplier = 1.2` (Checkdown options get boosted).

### Step 3.2: Dynamic D/ST Scoring
*   **Action:** Refactor D/ST scoring in `engine/game.py`.
*   **Change:** Instead of just "Points Allowed" buckets at the end:
    *   Simulate `pressure_event` on every dropback (using the Pressure Proxy).
    *   Sacks and Turnovers become the primary drivers of D/ST variance.
    *   Points Allowed becomes a secondary dampener.

---

## Git Commit Strategy

### Phase 1: Computational Enrichment
- **Commit 1.1:** `feat(stats): implement depth-bucketed defensive passing stats`
- **Commit 1.2:** `feat(stats): calculate qb_hit/pressure proxies`
- **Commit 1.3:** `feat(engine): integrate defensive YAC profiles into YAC logic`

### Phase 2: Charting Data
- **Commit 2.1:** `feat(data): add charting_client for FTN/nflverse data`
- **Commit 2.2:** `feat(ml): implement defensive clustering (Man/Zone archetypes)`

### Phase 3: Matchup Logic
- **Commit 3.1:** `feat(engine): implement archetype-based target share adjustments`
- **Commit 3.2:** `refactor(engine): dynamic D/ST scoring based on pressure events`
