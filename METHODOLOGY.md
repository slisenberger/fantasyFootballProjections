# 🧠 Methodology: How It Works

The **Fantasy Football Projections Engine** is a stochastic simulation model (Monte Carlo). Instead of predicting a single number (e.g., "Tyreek Hill will get 15 points"), it simulates the game of football thousands of times to generate a *range of outcomes*.

This document explains the "Physics" of the simulation and the statistical choices behind it.

---

## 1. The Core Philosophy: Why Simulation?

Most fantasy projections use **regression**:
> *Average Targets x Catch Rate x Yards/Catch + TDs = Points.*

This gives you a good **Median** (average outcome), but it fails to capture **Variance** (Boom/Bust potential).
*   It assumes "average" things happen every play.
*   It cannot model **Game Script**. (e.g., If the Bills go up 21-0 early, they stop passing. Regression misses this correlation).

**Our Approach:**
We simulate the game play-by-play.
*   If the Bills go up 21-0 in the sim, the **Playcall Model** sees the score and switches to "Run".
*   If a game goes to **Overtime**, the players get extra volume.
*   If a player is **Questionable**, we simulate the risk of them being benched.

This captures the "Tails" of the distribution—the weeks that win you championships.

---

## 2. The Simulation Loop: A Play-by-Play Walkthrough

For every single play in a simulated game, the engine makes a series of decisions based on historical data:

### Step 1: The Context
We know the current state: *1st & 10 on the 25-yard line, 10:00 left in Q2, Score is 7-7.*

### Step 2: The Play Call (Run vs. Pass)
We ask a **Logistic Regression Model**: *"Given this Down, Distance, Score, and Time, what do teams usually do?"*
*   *Adjustment:* We nudge this probability based on Team Tendencies (Pass Rate Over Expected). If it's the Chiefs, we boost the odds of a Pass.

### Step 3: The Outcome
*   **If Pass:**
    *   **Sack?** Calculated based on QB's historical sack rate vs Defense's pressure rate.
    *   **Target:** Who gets the ball? Chosen based on projected **Target Share** (weighted EWMA).
    *   **Completion?** A model predicts `P(Catch)` based on Air Yards and Field Position.
        *   *Adjustment:* We factor in QB accuracy (CPOE) and Receiver hands.
    *   **Yards:** We sample from **Kernel Density Estimators (KDEs)**.
        *   *Air Yards:* How deep was the throw?
        *   *YAC:* How much did he run after the catch?
*   **If Run:**
    *   **Carrier:** Who runs it? (Based on Carry Share).
    *   **Yards:** Sampled from Rushing KDEs.

### Step 4: The Clock
Time runs off the clock based on an **Empirical Clock Model**.
*   *Neutral:* ~35 seconds.
*   *Hurry Up:* If trailing late, ~15 seconds.
*   *Kill Clock:* If leading late, ~40 seconds.

This repeats until the game ends (or Overtime ends).

---

## 3. The Models: The "Brain" of the Engine

We use specific statistical tools for specific problems.

### A. Kernel Density Estimation (KDE) for Yards
**Problem:** "How many yards does a run go for?"
**Why not Average?** An average of 4.5 yards tells you nothing. Is it 4 runs of 4.5, or 3 runs of 0 and one run of 18?
**Solution:** KDEs create a smooth curve of probability based on history. We can sample from this curve to get realistic variance (lots of 2-yard runs, occasional 50-yard breakaways).

**The "Censored Boom" Fix:**
A major innovation in v410 was handling the **Red Zone**.
*   A 5-yard TD run looks like a "short run" in the stats, but physically, the runner *could* have gone further if the endzone wasn't there.
*   If we train our model on Red Zone runs, we underestimate a player's open-field speed.
*   **Fix:** We split the Rushing Model into **Open Field (>20 yds)** and **Red Zone (<=20 yds)**. When a player breaks into the open field, we sample from the "Unconstrained" model, unlocking their true ceiling.

### B. Logistic Regression for Decisions
**Problem:** "Will they pass?" or "Will he catch it?"
**Solution:** We use Logistic Regression, which outputs a probability (0.0 to 1.0).
*   *Inputs:* Down, Distance, Field Position, Air Yards (for catching).
*   *Why:* It handles the interaction of variables well (e.g., 3rd & Long is very different from 1st & 10).

### C. Exponential Weighted Moving Average (EWMA) for Shares
**Problem:** "How much of the offense goes to Tyreek Hill?"
**Solution:** We look at his target share over the last ~17 games, but we **weight recent games more heavily**.
*   If he had 30% last week and 10% last year, the model effectively "learns" he is currently a focal point.

---

## 4. The Adjustors: Capturing Nuance

Raw stats aren't enough. We apply "Bayesian-style" adjustments.

### Team Adjustments
*   **Pass Rate Over Expected (PROE):** We calculate how much a team passes *compared to league average* in similar situations. We simply add this % to the Playcall Model's output.
*   **Defensive Strength:**
    *   *Sack Rate:* If a defense gets 2x more sacks than average, we boost the Sack Probability.
    *   *YPC Allowed:* If a defense allows 3.0 YPC (very good), we apply a multiplier (e.g., 0.8x) to the Rushing KDE samples.

### Uncertainty Adjustments (The "Secret Sauce")
*   **Probabilistic Injury Injection (v409):**
    *   If a player is `Questionable`, we don't just project "Average Points".
    *   In 25% of simulations, we force them to be **Inactive** (0 points).
    *   In 75% of simulations, we reduce their volume by 20% (Decoy/Re-injury risk).
    *   *Result:* This correctly models the "Bust" risk of Q players and the "Boom" potential of their backups who get the start in 25% of worlds.

---

## 5. Known Limitations & Future Work

*   **Kickers:** Currently treated as generic. We plan to add "FG% Over Expected" to distinguish Justin Tucker from replacement level.
*   **Game Script Clusters:** We simulate game script dynamically, but we don't explicitly model "This week will be a Shootout". We rely on the team stats to naturally create that environment.
*   **Depth Chart:** We rely on `nfl_data_py` for depth charts. Early in the week, this data can be stale.

---
