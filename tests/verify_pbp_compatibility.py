import pandas as pd
from data import nfl_client
from models import playcall
import joblib
import os

YEARS = [2023] # Test with one year
PBP_CSV_PATH = f"data/pbp_{YEARS[0]}.csv.gz"
PLAYCALL_MODEL_PATH = "models/trained_models/playcall_regression_model"

def verify_pbp_compatibility():
    print(f"--- Verifying New PBP Data Compatibility with Existing Models (Year {YEARS[0]}) ---")
    
    # 1. Load the new PBP data (in memory, NOT saving to disk yet)
    print("Loading PBP data via nfl_client (in memory)...")
    new_pbp_data = nfl_client.load_pbp_data(YEARS)
    
    # 2. Load the existing PBP data from disk
    print(f"Loading PBP data from existing CSV: {PBP_CSV_PATH}...")
    try:
        old_pbp_data = pd.read_csv(PBP_CSV_PATH, compression='gzip', low_memory=False)
    except FileNotFoundError:
        print(f"Error: Existing PBP CSV not found at {PBP_CSV_PATH}. Cannot compare.")
        return
        
    # 3. Apply the same filtering/dropping logic as clean_and_save_data
    print("Applying column filtering and roster merge logic...")
    
    def apply_clean_logic(df, use_nfl_client_roster=False):
        if 'season_type' not in df.columns:
            print("Warning: 'season_type' not in dataframe. Assuming already filtered or client data.")
        else:
            df = df.loc[df.season_type == "REG"]
            
        drop_cols = [
            "total_home_epa", "total_away_epa", "total_home_rush_epa", "total_away_rush_epa",
            "total_home_pass_epa", "total_away_pass_epa", "air_epa", "yac_epa",
            "comp_air_epa", "comp_yac_epa", "drive_first_downs", "drive_inside20",
            "drive_ended_with_score", "drive_quarter_start", "drive_quarter_end",
            "lateral_sack_player_id", "lateral_sack_player_name", "total_home_comp_air_epa",
            "total_away_comp_air_epa", "total_home_comp_yac_epa", "total_home_raw_air_epa",
            "total_away_raw_air_epa", "total_home_raw_yac_epa", "total_away_raw_yac_epa",
            "wp", "def_wp", "home_wp", "away_wp", "wpa", "vegas_wpa", "vegas_home_wpa",
            "home_wp_post", "away_wp_post", "vegas_wp", "vegas_home_wp",
            "total_home_rush_wpa", "total_away_rush_wpa", "total_home_pass_wpa",
            "total_away_pass_wpa", "replay_or_challenge", "replay_or_challenge_result",
            "safety_player_name", "safety_player_id", "series", "series_success",
            "series_result", "order_sequence", "nfl_api_id", "play_deleted",
            "play_type_nfl", "special_teams_play", "st_play_type", "fixed_drive",
            "fixed_drive_result", "drive_real_start_time", "drive_play_count",
            "drive_play_count", "div_game", "surface", "temp", "wind", "home_coach",
            "away_coach", "aborted_play", "stadium_id", "game_stadium",
            "passer_jersey_number", "rusher_jersey_number", "receiver_jersey_number",
            "desc", "fantasy_player_name", "fantasy", "fantasy_player_id",
            "jersey_number", "qb_epa", "xyac_epa", "xyac_success", "xyac_fd",
            "drive_start_transition", "drive_end_transition", "quarter_end", "drive",
            "game_half", "lateral_receiver_player_id", "lateral_receiver_player_name",
            "lateral_rusher_player_id", "lateral_rusher_player_name", "old_game_id",
            "lateral_rush", "lateral_return", "lateral_recovery", "td_team",
            "td_player_id", "td_player_name", "no_score_prob", "opp_fg_prob",
            "opp_safety_prob", "opp_td_prob", "fg_prob", "safety_prob", "td_prob",
            "extra_point_prob", "two_point_conversion_prob",
        ]
        
        # Ensure we only try to drop columns that exist
        cols_to_drop = [col for col in drop_cols if col in df.columns]
        df = df.drop(cols_to_drop, axis=1)

        roster_data = None
        if use_nfl_client_roster:
            roster_data = nfl_client.import_seasonal_rosters(YEARS, columns=["player_id", "position"])
        else: # Legacy roster import
            # Patch nfl_data_py to be the actual legacy library for this specific call
            import nfl_data_py # Assuming it's still installed for this test
            roster_data = nfl_data_py.import_seasonal_rosters(YEARS, columns=["player_id", "position"])

        receiver_roster_data = roster_data.rename(
            columns={"position": "position_receiver", "player_id": "receiver_player_id"}
        )[["position_receiver", "receiver_player_id"]].dropna()
        
        df = df.merge(receiver_roster_data, on="receiver_player_id", how="left")
        return df

    cleaned_old_pbp = apply_clean_logic(old_pbp_data.copy(), use_nfl_client_roster=False)
    cleaned_new_pbp = apply_clean_logic(new_pbp_data.copy(), use_nfl_client_roster=True) # Use new client for its rosters

    # 4. Compare relevant columns for Playcall Model
    print("\n--- Comparing Relevant Columns for Playcall Model ---")
    playcall_feature_cols = [
        "down", "ydstogo", "score_differential", "quarter_seconds_remaining",
        "qtr", "yardline_100", "play_type", "two_point_attempt"
    ]
    
    # Ensure all feature columns exist in both dataframes
    missing_in_old = [col for col in playcall_feature_cols if col not in cleaned_old_pbp.columns]
    missing_in_new = [col for col in playcall_feature_cols if col not in cleaned_new_pbp.columns]
    
    if missing_in_old or missing_in_new:
        print(f"CRITICAL ERROR: Missing columns in PBP data for Playcall Model.")
        if missing_in_old: print(f"  Missing in Old PBP: {missing_in_old}")
        if missing_in_new: print(f"  Missing in New PBP: {missing_in_new}")
        return

    # Select only the relevant data for comparison
    old_model_data = cleaned_old_pbp[playcall_feature_cols].dropna()
    new_model_data = cleaned_new_pbp[playcall_feature_cols].dropna()
    
    print(f"Old Model Data Shape: {old_model_data.shape}")
    print(f"New Model Data Shape: {new_model_data.shape}")

    # Check dtypes
    for col in playcall_feature_cols:
        if old_model_data[col].dtype != new_model_data[col].dtype:
            print(f"CRITICAL WARNING: Dtype mismatch for column '{col}': Old={old_model_data[col].dtype}, New={new_model_data[col].dtype}")
    
    # Simple value comparison - this is tricky due to possible row order/number differences
    # Focus on distributions
    for col in playcall_feature_cols:
        if not old_model_data[col].equals(new_model_data[col]):
            print(f"WARNING: Values differ for column '{col}'. Max abs diff: {(old_model_data[col] - new_model_data[col]).abs().max()}")
            
    # 5. Test Inference with existing Playcall Model
    print("\n--- Testing Playcall Model Inference ---")
    if not os.path.exists(PLAYCALL_MODEL_PATH):
        print(f"CRITICAL ERROR: Playcall model not found at {PLAYCALL_MODEL_PATH}. Cannot test inference.")
        return
        
    try:
        playcall_model = joblib.load(PLAYCALL_MODEL_PATH)
        print("Playcall model loaded successfully.")
        
        # Take a small sample of the new data for inference testing
        sample_new_data = new_model_data.sample(min(100, len(new_model_data)), random_state=42)
        
        # Prepare features, similar to how models/playcall.py does
        feature_cols_playcall = ["down", "ydstogo", "score_differential", "quarter_seconds_remaining", "qtr", "yardline_100"]
        X_sample = sample_new_data[feature_cols_playcall]
        
        # Check if the model can predict without error
        _ = playcall_model.predict_proba(X_sample.values)
        print("Playcall model successfully ran inference on new PBP data sample!")
        print("PBP data migration is likely safe to proceed.")
        
    except Exception as e:
        print(f"CRITICAL ERROR during Playcall model inference: {e}")
        import traceback
        traceback.print_exc()
        print("PBP data migration is NOT safe to proceed without model retraining.")

if __name__ == "__main__":
    verify_pbp_compatibility()
