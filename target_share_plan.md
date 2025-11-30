# Action Plan: The Unified Target Share Model

This plan outlines the development of a sophisticated, unified Target Share Model. The goal is to replace static, season-level averages with a dynamic probability surface that reacts to game state, roster hierarchy, and player trends.

## 1. Core Objectives (The "Why")

The current model (`random.choices(weights=season_avg)`) fails in three critical ways:
1.  **Context Blindness:** It treats 3rd & 20 the same as 1st & Goal.
2.  **Roster Ignorance:** It doesn't understand that if the WR1 is injured, the WR2 *and* TE1 usually absorb the volume, not the WR5.
3.  **Trend Lag:** It relies on a slowly decaying season average, missing "Breakout" players or "Benched" starters until weeks later.

## 2. The Feature Space (The "How")

To capture the nuance of NFL target distribution, we need five distinct feature categories:

### A. Hierarchy & Depth (The "Who")
*   **Positional Rank:** Is this player the WR1, WR2, TE1, or RB1 *on this specific roster*?
*   **Depth Chart Status:** Is the starter active? If WR1 is out, does the WR2 inherit "WR1 Usage Patterns"?
*   **Personnel Grouping:** (Requires `ftn_data`) Is this 11 Personnel (3 WR) or 12 Personnel (2 TE)? A TE2 gets targets in 12 personnel but 0 targets in 11 personnel.

### B. Game State Context (The "When")
*   **Win Probability / Score Diff:** Captures "Garbage Time" funneling (RB/TE checkdowns) vs "Shootout" funneling (WR1/WR2 deep shots).
*   **Down & Distance:** 3rd & 2 targets the Slot WR/TE. 3rd & 15 targets the Deep Threat or Checkdown RB.
*   **Red Zone / Goal Line:** Drastic shift in usage (Fade routes to tall WRs, Flat routes to TEs/RBs).

### C. Relationship & Stacking (The "With Whom")
*   **QB Tendency:** Does this QB favor TEs (e.g., Mahomes/Kelce, Jackson/Andrews)?
    *   *Metric:* `qb_positional_target_share_vs_league_avg`.
*   **WR Core Correlation:** Negative correlation (Cannibalization) vs Positive Correlation (Gravity).
    *   *Feature:* `teammate_quality_score` (Does having a Chase help a Higgins?).

### D. Recent Trend (The "Hot Hand")
*   **Last 4 Weeks Share:** Weighted heavier than season average.
*   **In-Game Volume:** "Feed the beast." If WR1 has 5 catches in Q1, does he get force-fed in Q2?

### E. Defensive Matchup (The "Against Whom")
*   **Coverage Archetype:** Man Coverage favors elite separators (WR1). Zone favors "hole sitters" (TE/Slot).
*   **Pressure Rate:** High pressure forces targets closer to the line of scrimmage (RB/TE).

---

## 3. Modeling Architecture: The Hybrid "Base + Context" Model

We will not throw away the EWMA baseline. Instead, we will use XGBoost to learn a **Contextual Adjustment** that shifts the EWMA probability up or down based on the specific play situation.

### The "Base Margin" Technique
We use the player's historical `target_share_est` (EWMA) as the **Base Margin** (initial guess) for the XGBoost model.
1.  Calculate Log-Odds of the Prior: `margin = ln(ewma_share / (1 - ewma_share))`
2.  Train XGBoost: `model.fit(X, y, base_margin=margin)`
3.  **Result:** The model focuses 100% of its learning capacity on *correcting* the prior based on game state, rather than relearning that "Justin Jefferson is good."

### Step 3.0: Data Ingestion (The "Participation" Unlock)
*   **Action:** Update `data/loader.py` to pull `import_participation_data`.
*   **Details:**
    *   Call `nfl_client.import_participation_data(years)`.
    *   Join this with the PBP data on `(nflverse_game_id, play_id)`.
    *   This gives us row-by-row access to `offense_players` (Who is on field?) and `defense_coverage_type` (Man vs Zone?).

### Step 3.1: Feature Engineering (The "X" Matrix)
The model receives **only** context features, no player ID or historical volume stats (since those are in the Margin).

*   **Game State:**
    *   `down` (Categorical), `ydstogo`, `yardline_100`.
    *   `score_differential`, `quarter_seconds_remaining`, `qtr`.
    *   `vegas_spread` (Implied Game Script).
*   **Receiver Role & Personnel:**
    *   `personnel_grouping`: Extracted from `offense_personnel` (e.g., "11", "12").
    *   `position`: (One-Hot: WR, TE, RB).
    *   `depth_chart_rank`: (1, 2, 3 - crucial for differentiating WR1 vs WR4).
    *   `is_slot`: (Proxy or derived from route data if available).
*   **Defensive Environment:**
    *   `def_coverage_type`: (Man, Zone, etc. from `defense_man_zone_type`).
    *   `def_pressure_rate_season`: (Does pressure force checkdowns?).

### Step 3.2: Training Pipeline
*   **Objective:** `binary:logistic` (Is Targeted?).
*   **Data:** Historical PBP joined with Participation (2016-2023).
*   **Rows:** One row *per eligible receiver per pass play*.
    *   **Crucial:** Use `offense_players` list to identify the EXACT set of 5 eligible receivers on the field. No guessing.
*   **Target:** 1 if this receiver got the ball, 0 otherwise.

### Step 3.3: Inference (Simulation)
1.  Retrieve `ewma_share` for all active receivers.
2.  Calculate `base_margin` for each.
3.  Construct `X` matrix for the current play (e.g., 3rd & 10).
4.  `raw_scores = model.predict(X, base_margin=base_margin, output_margin=True)`.
5.  **Softmax:** Convert raw scores to probabilities that sum to 1.0.
    `Prob_i = exp(Score_i) / sum(exp(Score_j))`

This system gives us the stability of the EWMA with the IQ of a situational model.

---

## 4. Git Commit Strategy (Implementation Steps)

### Phase 1: Data Prep & Feature Engineering
- **Commit 1.1:** `feat(features): implement Positional Rank and Depth Chart features`
- **Commit 1.2:** `feat(features): implement QB Tendency and Recent Trend features`
- **Commit 1.3:** `feat(features): join Game State context (WP, Down, Dist)`

### Phase 2: Model Training (Offline)
- **Commit 2.1:** `exp(targets): train XGBoost 'Utility' model on 2016-2023 data`
- **Commit 2.2:** `benchmark(targets): compare Softmax(XGB) vs Season_Avg baseline`

### Phase 3: Engine Integration
- **Commit 3.1:** `feat(engine): implement DynamicTargetAllocator class`
- **Commit 3.2:** `refactor(game): replace random.choices with Allocator.select_target()`
