import pytest
import pandas as pd
import nfl_data_py
from data import nfl_client

YEARS = [2023]

def test_roster_fidelity():
    print("\n--- Testing Roster Fidelity ---")
    legacy = nfl_data_py.import_seasonal_rosters(YEARS)
    new = nfl_client.import_seasonal_rosters(YEARS)
    
    print(f"Legacy Shape: {legacy.shape}")
    print(f"New Shape: {new.shape}")
    print(f"New Columns: {new.columns.tolist()}")
    
    # Check critical columns
    assert "player_id" in new.columns, "player_id missing in new roster"
    assert "position" in new.columns, "position missing in new roster"
    assert "player_name" in new.columns, "player_name missing in new roster" # Legacy usually has this
    
    # Check subset equality (if possible)
    # Note: Sort orders might differ
    legacy_sorted = legacy.sort_values("player_id").reset_index(drop=True)
    new_sorted = new.sort_values("player_id").reset_index(drop=True)
    
    # Check overlap of IDs
    common_ids = set(legacy['player_id']).intersection(set(new['player_id']))
    print(f"Common IDs: {len(common_ids)}")
    assert len(common_ids) > 0
    
def test_schedule_fidelity():
    print("\n--- Testing Schedule Fidelity ---")
    legacy = nfl_data_py.import_schedules(YEARS)
    new = nfl_client.import_schedules(YEARS)
    
    print(f"Legacy Shape: {legacy.shape}")
    print(f"New Shape: {new.shape}")
    
    assert "game_id" in new.columns
    assert "week" in new.columns
    assert "home_team" in new.columns

def test_depth_fidelity():
    print("\n--- Testing Depth Chart Fidelity ---")
    legacy = nfl_data_py.import_depth_charts(YEARS)
    new = nfl_client.import_depth_charts(YEARS)
    
    print(f"Legacy Shape: {legacy.shape}")
    print(f"New Shape: {new.shape}")
    print(f"New Columns: {new.columns.tolist()}")
    
    # Legacy columns used in stats/players.py
    # 'week', 'depth_team', 'position', 'gsis_id' (mapped to 'player_id'?)
    
    assert "depth_team" in new.columns
    assert "position" in new.columns

def test_ids_fidelity():
    print("\n--- Testing IDs Fidelity ---")
    legacy = nfl_data_py.import_ids()
    new = nfl_client.import_ids()
    
    print(f"Legacy Shape: {legacy.shape}")
    print(f"New Shape: {new.shape}")
    
    # Check renames
    assert "name" in new.columns, "'name' column missing (should be mapped from display_name)"
    assert "team" in new.columns, "'team' column missing (should be mapped from latest_team)"
    assert "gsis_id" in new.columns or "player_id" in new.columns

if __name__ == "__main__":
    # Manual run
    try:
        test_roster_fidelity()
        test_schedule_fidelity()
        test_depth_fidelity()
        test_ids_fidelity()
        print("\nSUCCESS: All fidelity checks passed.")
    except Exception as e:
        print(f"\nFAILURE: {e}")
        raise e
