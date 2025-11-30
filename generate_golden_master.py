import pandas as pd
import joblib
import random
import numpy as np
from settings import AppConfig
from data import loader
from data import nfl_client
from stats import players, teams, injuries
from models import int_return, kicking, completion, playcall, receivers, rushers

# Define the Golden Scenario
SEASON = 2023
WEEK = 1
HOME = "KC"
AWAY = "DET"
FIXTURE_DIR = "tests/fixtures"

def get_models():
    # Matches main.py structure
    models = {
        "playcall_model": playcall.build_or_load_playcall_model(fast=True),
        "rush_open_model": rushers.build_or_load_rush_open_kde(fast=True),
        "rush_rz_model": rushers.build_or_load_rush_rz_kde(fast=True),
        "scramble_model": rushers.build_or_load_scramble_kde(fast=True),
        "completion_model": completion.build_or_load_completion_model(),
        "field_goal_model": kicking.build_or_load_kicking_model(),
        "int_return_model": int_return.build_or_load_int_return_kde(fast=True),
    }

    models.update(receivers.build_or_load_all_air_yards_kdes(fast=True))
    models.update(receivers.build_or_load_all_yac_kdes(fast=True))
    
    # Add Pre-Sampling (Critical for speed/engine compatibility if engine expects arrays)
    SAMPLE_SIZE = 100000
    models["rush_open_samples"] = models["rush_open_model"].sample(SAMPLE_SIZE).flatten()
    models["rush_rz_samples"] = models["rush_rz_model"].sample(SAMPLE_SIZE).flatten()
    
    # Scramble Sampling (Split)
    scramble_kde_dict = models["scramble_model"]
    models["scramble_samples"] = scramble_kde_dict["default"].sample(SAMPLE_SIZE).flatten()
    models["scramble_samples_mobile"] = scramble_kde_dict["mobile"].sample(SAMPLE_SIZE).flatten()
    models["scramble_samples_pocket"] = scramble_kde_dict["pocket"].sample(SAMPLE_SIZE).flatten()
    
    models["int_return_samples"] = models["int_return_model"].sample(SAMPLE_SIZE).flatten()
    
    # Receiver Models (Air Yards & YAC) - Matches main.py loop
    for pos in ["RB", "WR", "TE", "ALL"]:
        # Air Yards (Global)
        key_ay = f"air_yards_{pos}"
        if key_ay in models:
            models[f"{key_ay}_samples"] = models[key_ay].sample(SAMPLE_SIZE).flatten()
        
        # YAC (Split)
        for zone in ["open", "rz"]:
            key_yac = f"yac_{pos}_{zone}"
            if key_yac in models:
                models[f"{key_yac}_samples"] = models[key_yac].sample(SAMPLE_SIZE).flatten()
    
    return models

def generate():
    print(f"--- Generating Golden Master for {SEASON} W{WEEK} {AWAY}@{HOME} ---")
    
    # 1. Config
    config = AppConfig()
    
    # 2. Models
    print("Loading Models...")
    models = get_models()
    
    # 3. Data
    print("Loading Data...")
    pbp_data = loader.load_data([SEASON, SEASON-1]) # Need context
    snap_counts = loader.load_snap_counts([SEASON, SEASON-1])
    rosters = nfl_client.import_seasonal_rosters([SEASON])
    depth_charts = nfl_client.import_depth_charts([SEASON])
    schedules = nfl_client.import_schedules([SEASON])
    injuries_data = injuries.load_historical_data([SEASON])
    
    # 4. Calculate Stats
    print("Calculating Stats...")
    team_stats = teams.calculate(pbp_data, SEASON)
    player_stats = players.calculate(pbp_data, snap_counts, team_stats, SEASON, WEEK)
    
    # 5. Save Inputs
    print("Saving Inputs...")
    inputs = {
        "models": models, # This might be large, but ensures exact model version
        "player_stats": player_stats,
        "team_stats": team_stats,
        "home": HOME,
        "away": AWAY,
        "week": WEEK,
        "config": config
    }
    joblib.dump(inputs, f"{FIXTURE_DIR}/golden_inputs.pkl")
    
    # 6. Run Simulation (Single Run)
    print("Running Simulation...")
    # Seed must be set right before execution
    random.seed(42)
    np.random.seed(42)
    
    # We import game here to ensure clean state?
    from engine import game
    
    # Filter stats for the game
    home_player_stats = player_stats[player_stats["team"].isin([HOME])]
    away_player_stats = player_stats[player_stats["team"].isin([AWAY])]
    home_team_stats = team_stats[team_stats["team"].isin([HOME])]
    away_team_stats = team_stats[team_stats["team"].isin([AWAY])]
    
    # Extract Game Info from Schedule
    game_row = schedules.loc[(schedules.week == WEEK) & (schedules.home_team == HOME)].iloc[0]
    game_info = {
        "wind": float(game_row.get("wind", 0)) if pd.notna(game_row.get("wind")) else 0.0,
        "is_outdoors": 1 if game_row.get("roof") in ['outdoors', 'open'] else 0,
        "total_line": float(game_row.get("total_line", 45.0)) if pd.notna(game_row.get("total_line")) else 45.0,
        "spread_line": float(game_row.get("spread_line", 0.0)) if pd.notna(game_row.get("spread_line")) else 0.0,
    }
    
    game_machine = game.GameState(
        models,
        HOME,
        AWAY,
        home_player_stats,
        away_player_stats,
        home_team_stats,
        away_team_stats,
        rules=config.scoring,
        game_info=game_info,
        trace=False # No trace for golden master, just output
    )
    scores, log = game_machine.play_game()
    
    # 7. Save Output
    print("Saving Output...")
    output = {
        "scores": scores,
        "log": log # Optional: Save log to verify game script
    }
    joblib.dump(output, f"{FIXTURE_DIR}/golden_output.pkl")
    
    print(f"Done. Files saved to {FIXTURE_DIR}")
    print(f"Score: {scores}")

if __name__ == "__main__":
    generate()
