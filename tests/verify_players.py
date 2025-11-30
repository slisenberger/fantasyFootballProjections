from data import loader
from stats import teams, players
import pandas as pd

def test_players_calculate():
    print("Loading data...")
    # Load just one year for speed
    data = loader.load_data([2023])
    
    print("Calculating team stats...")
    team_stats = teams.calculate(data, 2023)
    
    print("Calculating player stats...")
    # This calls stats.players.calculate which uses nfl_client for rosters/depth
    player_stats = players.calculate(data, team_stats, 2023, 1)
    
    print(f"Player Stats Shape: {player_stats.shape}")
    print(f"Columns: {player_stats.columns.tolist()}")
    
    assert not player_stats.empty
    assert "target_share_est" in player_stats.columns
    # Check for roster merge success
    assert "player_name" in player_stats.columns
    assert not player_stats["player_name"].isnull().all()

if __name__ == "__main__":
    test_players_calculate()
