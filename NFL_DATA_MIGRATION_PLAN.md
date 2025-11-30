# Refined Migration Plan: `nfl_data_py` -> `nflreadpy` (Piecemeal Strategy)

## 1. Assessment: Scale of Change

**Verdict: Major Refactoring Required (But Automatable).**

Initial analysis revealed that `nfl_data_py` is not just used in `data/loader.py`. It is deeply embedded in:
*   `main.py` (Schedules, Rosters)
*   `stats/players.py` (Rosters, Depth Charts)
*   `stats/injuries.py` (Injuries, ID Mapping)
*   `models/receivers.py`
*   `check_teams.py`
*   Tests & Benchmarks

**The Good News:** `nflreadpy` supports all the required features.
**The Complication:** `nflreadpy` returns **Polars** DataFrames (via PyArrow) and has slight column name mismatches (e.g., `gsis_id` vs `player_id`, `display_name` vs `name`).

**Strategy Update:** Due to calibration regressions in previous attempts, we will adopt a **Piecemeal Migration Strategy**. We will build a parallel adapter, verify it against the legacy library, and migrate one consumer at a time.

---

## 2. Prerequisites

1.  **Install Dependencies:**
    ```bash
    uv add nflreadpy pyarrow pandas
    # Keep nfl_data_py installed for validation
    ```

---

## 3. The "Adapter" Strategy

To avoid rewriting logic in 10+ files at once, we will create an **Adapter Module** (`data/nfl_client.py`) that mimics the old library's API but calls the new library and handles all column renaming.

### Step 1: Create `data/nfl_client.py` (The Adapter)

This file acts as the translation layer.

```python
import nflreadpy as nfl
import pandas as pd

def to_pandas(df):
    """Helper to ensure we return Pandas DataFrames."""
    if hasattr(df, "to_pandas"):
        return df.to_pandas()
    return df

def import_seasonal_rosters(years, columns=None):
    """Mimics nfl_data_py.import_seasonal_rosters"""
    df = to_pandas(nfl.load_rosters(years))
    
    # MAPPING: nflreadpy uses 'gsis_id', legacy uses 'player_id'
    if 'gsis_id' in df.columns:
        df = df.rename(columns={'gsis_id': 'player_id'})
        
    if columns:
        # Ensure filtered columns exist (handle renames first)
        available_cols = [c for c in columns if c in df.columns]
        df = df[available_cols]
        
    return df

def import_schedules(years):
    return to_pandas(nfl.load_schedules(years))

def import_depth_charts(years):
    """Mimics nfl_data_py.import_depth_charts"""
    df = to_pandas(nfl.load_depth_charts(years))
    # nflreadpy already has 'depth_team' and 'position', which matches
    # what stats/players.py expects in its "modern" block.
    return df

def import_injuries(years):
    return to_pandas(nfl.load_injuries(years))

def import_ids(columns=None):
    """Mimics nfl_data_py.import_ids"""
    df = to_pandas(nfl.load_players())
    
    # MAPPING: Fix column mismatches for stats/injuries.py
    rename_map = {
        'display_name': 'name',
        'latest_team': 'team',
        'gsis_id': 'player_id' # Some modules might expect this
    }
    df = df.rename(columns=rename_map)
    
    if columns:
         # Strict filtering like legacy lib
         available_cols = [c for c in columns if c in df.columns]
         df = df[available_cols]
    return df

def load_pbp_data(years):
    """New helper for loader.py"""
    return to_pandas(nfl.load_pbp(years))
```

---

## 4. Piecemeal Migration Steps

### Phase 1: Adapter & Verification
1.  **Install:** `uv add nflreadpy pyarrow`
2.  **Create Adapter:** Write `data/nfl_client.py`.
3.  **Validation Script:** Create `tests/verify_migration.py` to compare outputs of `nfl_data_py` vs `data/nfl_client` for key functions (rosters, schedules, injuries). Ensure data types and column names are identical.

### Phase 2: Targeted Migration (Low Risk)
1.  **Stats/Injuries:** Update `stats/injuries.py` to use `data/nfl_client`. Run tests.
2.  **Stats/Players:** Update `stats/players.py`. Run tests.
3.  **Main/Schedules:** Update `main.py` (schedule loading only).

### Phase 3: The Data Loader (High Risk)
1.  **Refactor Loader:** Rewrite `data/loader.py` to use `data/nfl_client`.
2.  **Regression Test:** Run benchmarks and compare against baseline. Check for `NaN` propagation or missing players.

### Phase 4: Cleanup
1.  **Update Tests:** Update mocks in `tests/test_smoke.py`.
2.  **Remove Legacy:** `uv remove nfl_data_py`.

## 5. Known Mappings (Resolved)

| Data Type | Legacy Column | nflreadpy Column | Handled By |
| :--- | :--- | :--- | :--- |
| **Rosters** | `player_id` | `gsis_id` | Adapter (`import_seasonal_rosters`) |
| **IDs** | `name` | `display_name` | Adapter (`import_ids`) |
| **IDs** | `team` | `latest_team` | Adapter (`import_ids`) |
| **Depth** | `depth_team` | `depth_team` | Native Match |
| **Depth** | `position` | `position` | Native Match |
