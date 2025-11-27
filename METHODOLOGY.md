# 📘 The Physics of Fantasy: A Methodology Guide

*How the Fantasy Football Projections Engine simulates the game of football.*

---

## 1. Introduction

Most fantasy football projections use **regression-based models**. They predict:
> *"Tyreek Hill averages 9 targets per game, catches 70% of them, and averages 14 yards per catch. Therefore, he will score 16 points."*

This approach is excellent for predicting the **Median** (the most likely outcome). However, fantasy matchups are often decided by **Variance**—the "Boom" weeks where a player scores 30 points, or the "Bust" weeks where they score 5. Regression models tend to "smooth out" these extremes, underestimating the chaos of football.

**This Engine is different.** It is a **Monte Carlo Simulation**. It does not predict "points." It plays the game of football, snap-by-snap, thousands of times.

*   It simulates the coin toss.
*   It simulates the play call (Run vs. Pass).
*   It simulates the outcome (Catch, Drop, Sack, Penalty).
*   It simulates the clock ticking down.

By aggregating thousands of these simulated games, we generate a **Probability Distribution** for every player. This allows us to answer questions like: *"What are the odds Tyreek Hill scores > 25 points?"* (his Ceiling) or *"What are the odds he scores < 5 points?"* (his Floor).

---

## 2. The Data Pipeline

To simulate the future, we must understand the past.

### Sources
We rely on `nfl_data_py`, an open-source library that aggregates Play-by-Play (PBP) data, Rosters, and Depth Charts.

### Context Window
We load data from `Season - 1` to provide context.
*   *Why?* In Week 1 of a new season, we have no data. By loading the previous season, our models have a "Prior" belief about team and player talent.
*   *Smoothing:* As the season progresses, the weight of the "Prior" fades, and the current season's data takes over.

### The Estimators (EWMA)
We don't just use "Season Average." We use **Exponential Weighted Moving Averages (EWMA)**.
*   **Spans:**
    *   **Players:** Span of ~150 plays (targets/carries). This captures "Recent Form" while respecting "Class."
    *   **Teams:** Span of ~500 plays. Team tendencies change slower than player streaks.
*   **Vectorization:** Calculating this for 2,000 players row-by-row is slow. We use vectorized Pandas operations (sorting by time) to calculate the rolling form of every player in the league in milliseconds.

---

## 📐 The "Trilogy of Simulation" Philosophy

The engine does not train a unique model for every player (insufficient data). Instead, it composes three layers to generate a result for every interaction:

1.  **The Physics (Global KDE):**
    *   *What:* A Kernel Density Estimation of *all* plays of that type (e.g., "All Rushing Plays", "All Deep Passes").
    *   *Why:* Captures the fundamental shape, variance, and physical constraints of the sport (e.g., the probability of an 80-yard TD vs a 2-yard loss).
    *   *Code:* `models['rush_open_samples']`, `models['scramble_samples']`.

2.  **The Skill (Relative Estimator):**
    *   *What:* A Bayesian-weighted estimator of a player's efficiency relative to the league average (e.g., "Lamar Jackson averages 1.5x the league yards per scramble").
    *   *Why:* Shifts the Global KDE to match the specific talent of the player without losing the "Physics" of the distribution.
    *   *Code:* `player_stats['relative_yards_per_scramble_est']`, `player_stats['relative_yac_est']`.

3.  **The Matchup (Team Adjustment):**
    *   *What:* An adjustment factor based on the opponent's defensive weakness (e.g., "The Broncos allow 1.2x yards per carry").
    *   *Why:* Contextualizes the event to the specific game environment.
    *   *Code:* `team_stats['defense_relative_ypc_est']`.

**Formula:**
`Result = Sample(Global_KDE) * Player_Skill * Matchup_Factor`

*Note: This pattern explains why we use Global KDEs. We don't need a "Lamar Jackson KDE"; we need a "Scramble KDE" scaled by "Lamar's Efficiency".*

## 3. The Simulation Loop (The "Physics Engine")

The heart of the system is `engine/game.py`. It functions like a text-based video game.

### The State Machine
The engine tracks the "State" of the game:
*   `down` (1, 2, 3, 4)
*   `distance` (Yards to Go)
*   `yard_line` (0 to 100)
*   `score` (Home vs. Away)
*   `clock` (Seconds remaining)

### Step-by-Step Execution (`advance_snap`)

1.  **Play Calling:**
    *   **Model:** Logistic Regression.
    *   **Inputs:** Down, Distance, Score Differential, Time Remaining, Field Position.
    *   **Adjustment:** We calculate a team's **Pass Rate Over Expected (PROE)**. If the Buffalo Bills pass 5% more than the average team in this situation, we boost the model's "Pass" probability by 5%.
    *   **Decision:** The engine rolls a die to pick `Run` or `Pass`.

2.  **The Pass:**
    *   **Sack?** Calculated using an **Odds Ratio** combining the QB's Sack Rate (how often he holds the ball) vs the Defense's Sack Rate (pressure).
    *   **Scramble?** Calculated from the QB's Scramble Rate.
    *   **Target?** Who gets the ball?
        *   We use a weighted lottery based on **Projected Target Share**.
        *   *Nuance:* We fixed a "Smoothing Bug" where low-volume players were artificially boosted. Now, elite WRs demand their fair share.
    *   **Completion?**
        *   **Model:** Logistic Regression (Inputs: Air Yards, Down, Distance).
        *   **Adjustment:** **CPOE (Completion % Over Expected)**. We combine the QB's accuracy and the Receiver's hands to adjust the base probability.
    *   **Yards:**
        *   **Air Yards:** Sampled from a **Kernel Density Estimator (KDE)** trained on that player's history.
        *   **YAC:** Sampled from a YAC KDE.

3.  **The Run:**
    *   **Carrier:** Chosen based on projected Carry Share.
    *   **Yards:** Sampled from Rushing KDEs.
    *   **The "Censored Boom" Fix:** A 5-yard TD run looks like a "short run" in the stats, but the runner *could* have gone 50 yards if the endzone wasn't there. To fix this, we split our Rushing Models into **Open Field** (>20 yards) and **Red Zone** (<=20 yards). Open Field samples are unconstrained, allowing for true "Boom" runs.

4.  **The Clock:**
    *   **Model:** Empirical Lookup Table.
    *   We analyzed 2 years of play data to determine exactly how much time runs off the clock in every situation.
    *   *Hurry Up:* Trailing teams in the 4th quarter snap the ball in ~15 seconds.
    *   *Clock Kill:* Leading teams take ~40 seconds.
    *   This creates natural variance: Shootouts have more plays; Blowouts have fewer.

5.  **Overtime:**
    *   If the score is tied after 4 quarters, we simulate a coin toss and play Modified Sudden Death rules.

---

## 4. Key Mathematical Concepts

### Kernel Density Estimation (KDE)
Instead of assuming yards are Normally Distributed (Bell Curve)—which they aren't—we use KDEs. A KDE builds a "smooth shape" over the player's actual history. If De'Von Achane frequently rips off 40+ yard runs, his KDE will have a "fat tail," and the simulation will occasionally generate those game-breaking plays.

### The Odds Ratio Method
How do you calculate the probability of a Sack when a QB who takes a lot of sacks plays a Defense that gets a lot of sacks?
We use the **Odds Ratio Formula**:
$$
OR = \frac{P_{off} / (1 - P_{off}) \times P_{def} / (1 - P_{def})}{P_{lg} / (1 - P_{lg})}
$$
$$P_{adjusted} = \frac{OR}{1 + OR}
$$ 
This statistically rigorous method ensures that we don't just "add percentages" (which could exceed 100%) but combine the relative strengths of both units compared to the league average.

---

## 5. Handling Uncertainty

The model accounts for uncertainty in two ways:

1.  **Matchup Uncertainty:** By simulating the game, we naturally capture how Game Script impacts volume.
2.  **Role Uncertainty (Injuries):**
    *   If a player is marked **Questionable**, we don't just predict "Average".
    *   In **25%** of simulations, we force them to be **Inactive** (0 points).
    *   In **75%** of simulations, we reduce their volume by **20%** (Simulating "Decoy" status or re-injury).
    *   This accurately captures the "Bust" risk of starting an injured player and the "Boom" potential of their backup.

---

## 6. Known Limitations

*   **Kickers:** Currently modeled using a league-average probability curve. We plan to implement **FGOE (Field Goal % Over Expected)** to distinguish elite kickers.
*   **Rookies:** Rookies have no history (`Season - 1`). The model relies on a generic "Rookie Prior" until they accumulate stats. Week 1 projections for rookies are often conservative.
*   **Defense/Special Teams:** Touchdowns (Pick-6, Punt Return TD) are modeled via low-probability samples from the "Int Return" KDE, but are highly volatile.

---