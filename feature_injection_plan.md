# Action Plan: Feature Injection (Hook Points)

This plan details the specific code modifications required to inject the new high-value features (Pressure, Weather, Vegas, Tempo) into the existing model architecture.

## 1. The Play Call Model (`models/playcall.py` & `engine/game.py`)
*Target: Better decision making in "Shootout" vs "Blowout" scripts.*

### Step 1.1: Train with New Features (`models/playcall.py`)
*   **Status:** **[Pending]**
*   **Hook Point:** `feature_cols` list in `build_playcall_model`.
*   **Action:** Append new features.
    ```python
    # Current
    feature_cols = ["down", "ydstogo", "score_differential", "quarter_seconds_remaining", "qtr", "yardline_100"]
    
    # New
    feature_cols = [
        "down", "ydstogo", "score_differential", "quarter_seconds_remaining", "qtr", "yardline_100",
        "total_line",       # Vegas (Game Script)
        "spread_line",      # Vegas (Game Script)
        "drive_play_count"  # Tempo (Fatigue/Pace)
    ]
    ```
*   **Data Loading:** Ensure `loader.load_data` provides these columns (already identified in `data_inventory.md` as existing and now loaded).

### Step 1.2: Simulate with New Features (`engine/game.py`)
*   **Status:** **[Pending]**
*   **Hook Point:** `choose_playcall` method.
*   **Action:** Update `model_input` construction.
    ```python
    # Current
    model_input = [self.down, self.yds_to_go, self.score_differential(), self.sec_remaining, self.quarter, self.yard_line]
    
    # New
    model_input = [
        self.down, self.yds_to_go, self.score_differential(), self.sec_remaining, self.quarter, self.yard_line,
        self.vegas_total,   # Passed into GameState
        self.vegas_spread,  # Passed into GameState
        self.drive_play_count
    ]
    ```

---

## 2. The Completion Model (`models/completion.py` & `engine/game.py`)
*Target: Better accuracy on "Checkdowns" vs "Deep Shots" under pressure.*

### Step 2.1: Train with New Features (`models/completion.py`)
*   **Status:** **[Done]**
*   **Hook Point:** `feature_cols` list in `build_completion_model`.
*   **Action:** Append Weather features (Wind, Outdoors).
    ```python
    # New
    feature_cols = ["down", "ydstogo", "yardline_100", "air_yards", "wind", "is_outdoors"]
    ```

### Step 2.2: Simulate with New Features (`engine/game.py`)
*   **Status:** **[Done]**
*   **Hook Point:** `is_complete` method.
*   **Action:** Update `model_input`.
    ```python
    # New
    model_input = [..., self.wind, self.is_outdoors]
    ```

---

## 3. The Kicking Model (`models/kicking.py` & `engine/game.py`)
*Target: Realistic Field Goal percentage in bad weather.*

### Step 3.1: Train with New Features (`models/kicking.py`)
*   **Status:** **[Done]**
*   **Hook Point:** `feature_cols` list.
*   **Action:** Add Environmental features.
    ```python
    # New
    feature_cols = [..., "kick_distance", "wind", "is_outdoors"]
    ```

### Step 3.2: Simulate with New Features (`engine/game.py`)
*   **Status:** **[Done]**
*   **Hook Point:** `field_goal` method.
*   **Action:** Update `model_input`.
    ```python
    # New
    model_input = [..., kicking_yards, self.wind, self.is_outdoors]
    ```

---

## 4. Infrastructure Upgrades (The Glue)
*These changes are required to transport the data from `main.py` to the `GameState`.*

### Step 4.1: `GameState` Constructor
*   **Status:** **[Done]**
*   **File:** `engine/game.py`
*   **Action:** Add `game_info` dictionary to `__init__`.

### Step 4.2: `GameBuilder`
*   **Status:** **[Done]**
*   **File:** `main.py`.
*   **Action:** Extract these fields from the Schedule/PBP dataframe and pass them to `GameState`.

## Git Commit Strategy
*   **Commit 1:** `feat(models): add Vegas/Tempo features to playcall model training`
*   **Commit 2:** `feat(models): add Pressure features to completion model training`
*   **Commit 3:** `feat(models): add Weather features to kicking model training`
*   **Commit 4:** `refactor(engine): update GameState to accept and use new features`