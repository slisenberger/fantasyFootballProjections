import pandas as pd
import numpy as np
from main import project_game, get_models
from data import loader
from stats import players, teams
from settings import AppConfig
from engine import game

def debug_negative_scores():
    print("--- Debugging Negative Scores ---")
    
    # Config
    SEASON = 2023
    WEEK = 1
    TARGET_PLAYER_ID = "00-0036360" # Bijan Robinson (or verify ID)
    # Josh Allen ID: 00-0034857
    
    # Load Data
    print("Loading Data...")
    # Need historical data for stats calculation
    pbp = loader.load_data([SEASON, SEASON-1])
    
    season_data = pbp.loc[
        (pbp.season == SEASON - 1) | ((pbp.season == SEASON) & (pbp.week < WEEK))
    ].copy() # Ensure copy
    
    print("Calculating Stats...")
    team_stats = teams.calculate(season_data, SEASON)
    player_stats = players.calculate(season_data, team_stats, SEASON, WEEK)
    
    # Setup Game: BUF vs NYJ (Week 1 2023)
    HOME = "NYJ"
    AWAY = "BUF"
    TARGET_NAME = "Josh Allen"
    
    # Filter Stats
    game_player_stats = player_stats[player_stats["team"].isin([HOME, AWAY])].copy()
    game_team_stats = team_stats[team_stats["team"].isin([HOME, AWAY])].copy()
    
    # Verify
    target = game_player_stats[game_player_stats['player_name'] == TARGET_NAME]
    if not target.empty:
        print(f"Target Player Found: {target.iloc[0]['player_name']} ({target.iloc[0]['player_id']})")
        TARGET_PLAYER_ID = target.iloc[0]['player_id']
    else:
        print(f"Target {TARGET_NAME} not found!")
        print("Available players:", game_player_stats['player_name'].unique())
        return

    print("Loading Models...")
    models = get_models()
    config = AppConfig.load()
    
    print("Running 100 Simulations with Trace...")
    
    worst_score = 100
    worst_log = []
    
    for i in range(100):
        # Initialize Game with Trace=True
        
        # Helper to filter
        home_p = game_player_stats[game_player_stats["team"] == HOME]
        away_p = game_player_stats[game_player_stats["team"] == AWAY]
        home_t = game_team_stats[game_team_stats["team"] == HOME]
        away_t = game_team_stats[game_team_stats["team"] == AWAY]
        
        g = game.GameState(
            models, HOME, AWAY, home_p, away_p, home_t, away_t, 
            rules=config.scoring, trace=True
        )
        
        scores, logs = g.play_game()
        
        p_score = scores.get(TARGET_PLAYER_ID, 0)
        
        if p_score < worst_score:
            worst_score = p_score
            worst_log = logs
            
    print(f"\n--- Diagnosis for {target.iloc[0]['player_name']} ---")
    print(f"Worst Score: {worst_score}")
    
    print("\n--- Play Log for Worst Game ---")
    # Filter log for plays involving this player
    df_log = pd.DataFrame(worst_log)
    
    # Fix: logs might be empty if player never touched ball
    if df_log.empty:
        print("Log is empty.")
    else:
        player_plays = df_log[df_log['player_id'] == TARGET_PLAYER_ID]
        if player_plays.empty:
            print("Player had no touches in this game.")
        else:
            print(player_plays[['qtr', 'time', 'play_type', 'yards', 'is_complete']])
            print("\nTotal Stats:")
            print(f"Carries: {len(player_plays[player_plays['play_type'] == 'RUN'])}")
            print(f"Targets: {len(player_plays[player_plays['play_type'] == 'PASS'])}")
            print(f"Yards Sum: {player_plays['yards'].sum()}")

if __name__ == "__main__":
    debug_negative_scores()
