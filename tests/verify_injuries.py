from stats import injuries
import pandas as pd

def test_injury_import():
    print("Testing injury import...")
    df = injuries.get_season_injury_data(2023)
    print(f"Injuries Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    
    assert not df.empty
    assert "team" in df.columns
    assert "gsis_id" in df.columns or "player_id" in df.columns
    
if __name__ == "__main__":
    test_injury_import()
