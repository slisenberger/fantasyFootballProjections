# Action Plan: Advanced Data Enrichment (Defensive Schematics)

This plan addresses the "Average of Averages" trap by enriching our dataset with schematic and derived metrics. The goal is to move beyond scalar defensive rankings (e.g., "15th ranked pass defense") to matchup-specific modeling (e.g., "Weak against Deep Passes", "High Pressure Rate").

## Phase 1: Derived Metrics (Computational Enrichment)
**Goal:** Squeeze more signal out of our *existing* Play-by-Play (PBP) data without needing new external scrapers yet. We can calculate proxies for coverage shells and pressure.

### Step 1.1: "Air Yards Allowed" Granularity
*   **Status:** **[Pending]**
*   **Current State:** We calculate `defense_relative_air_yards` as a single scalar.
*   **Action:** Split defensive passing stats into "Depth Buckets" in `stats/teams.py`.
    *   `def_short_comp_rate` (0-10 yards)
    *   `def_inter_comp_rate` (10-20 yards)
    *   `def_deep_comp_rate` (20+ yards)
*   **Hypothesis:** A "Two-High" defense will have a *high* allowed completion rate for Short passes but a *very low* rate for Deep passes.

### Step 1.2: Pressure Rate Proxy
*   **Status:** **[Pending]** (Data `qb_hit` is now available)
*   **Problem:** "Sack Rate" is an outcome, "Pressure" is a process. Sacks are rare/noisy; Pressure is stable.
*   **Action:** Calculate `pressure_proxy` in `stats/teams.py`.
    *   **Formula:** `(Sacks + QB Hits + Hurries) / Dropbacks`.
    *   **Implementation:** Update `models/playcall.py` to use `pressure_rate_differential`.

### Step 1.3: "YAC Allowed" Profile
*   **Status:** **[Pending]** (Data `xyac_mean_yardage` is now available)
*   **Action:** Calculate `def_yac_per_completion` separately from `def_air_yards`.
*   **Integration:** Feed this into the `compute_yac` function in `engine/game.py`.

---

## Phase 2: External Data Integration (Charting Data)
**Goal:** Ingest "Ground Truth" schematic data.

### Step 2.1: Ingest Charting Data
*   **Status:** **[Done]** (`import_participation_data` covers key needs).
*   **Action:** No direct action needed for `import_ftn_data` as `participation` data now provides `defense_man_zone_type` and `offense_personnel`.

### Step 2.2: Defensive Personality Clustering
*   **Status:** **[Pending]**
*   **Action:** Train a K-Means clusterer in `stats/defense_clustering.py`.
*   **Features:** Blitz Rate, Man Coverage Rate (from `participation`), Light Box Rate.

---

## Phase 3: The "Matchup Engine" (Engine Integration)
**Goal:** Apply these new metrics to the simulation logic.

### Step 3.1: Route-Level Adjustments (Simplified)
*   **Status:** **[Pending]**
*   **Action:** Adjust `target_share` based on "Archetype vs Player Type" using available `def_coverage_type`.

### Step 3.2: Dynamic D/ST Scoring
*   **Status:** **[Pending]**
*   **Action:** Refactor D/ST scoring in `engine/game.py`.
*   **Change:** Simulate `pressure_event` on every dropback (using the Pressure Proxy).

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