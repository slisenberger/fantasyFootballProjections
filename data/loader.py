import pandas as pd
from data import nfl_client as nfl_data_py


# Load a year range of pbp data.
def load_data(years):
    # Load PBP data directly from nfl_client (which uses nflreadpy's cache)
    data = nfl_data_py.load_pbp_data(years)
    
    # Apply the same column filtering and roster merge logic as clean_and_save_data
    # (The following code is copied from clean_and_save_data to ensure consistent processing)
    if 'season_type' not in data.columns:
        print("Warning: 'season_type' not in dataframe. Assuming already filtered or client data.")
    else:
        data = data.loc[data.season_type == "REG"]
        
        drop_cols = [
        
            "total_home_epa", "total_away_epa", "total_home_rush_epa", "total_away_rush_epa",
        
            "total_home_pass_epa", "total_away_pass_epa", "air_epa", "yac_epa",
        
            "comp_air_epa", "comp_yac_epa", "drive_first_downs", "drive_inside20",
        
            "drive_ended_with_score", "drive_quarter_start", "drive_quarter_end",
        
            "lateral_sack_player_id", "lateral_sack_player_name", "total_home_comp_air_epa",
        
            "total_away_comp_air_epa", "total_home_comp_yac_epa", "total_away_comp_yac_epa",
        
            "total_home_raw_air_epa", "total_away_raw_air_epa", "total_home_raw_yac_epa",
        
            "total_away_raw_yac_epa", "wp", "def_wp", "home_wp", "away_wp", "wpa", "vegas_wpa", "vegas_home_wpa",
        
            "home_wp_post", "away_wp_post", "vegas_wp", "vegas_home_wp",
        
            "total_home_rush_wpa", "total_away_rush_wpa", "total_home_pass_wpa",
        
            "total_away_pass_wpa", "replay_or_challenge", "replay_or_challenge_result",
        
            "safety_player_name", "safety_player_id", "series", "series_success",
        
            "series_result", "order_sequence", "nfl_api_id", "play_deleted",
        
            "play_type_nfl", "special_teams_play", "st_play_type", "fixed_drive",
        
            "fixed_drive_result", "drive_real_start_time", 
        
            "div_game", "surface", "home_coach",
        
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
    cols_to_drop = [col for col in drop_cols if col in data.columns]
    data = data.drop(cols_to_drop, axis=1)

    roster_data = nfl_data_py.import_seasonal_rosters(
        years, columns=["player_id", "position", "season"]
    )
    receiver_roster_data = roster_data.rename(
        columns={"position": "position_receiver", "player_id": "receiver_player_id"}
    )[["position_receiver", "receiver_player_id", "season"]].dropna()
    data = data.merge(receiver_roster_data, on=["receiver_player_id", "season"], how="left")

    data.reset_index(drop=True, inplace=True)
    return data


def load_snap_counts(years):
    """Loads snap count data via nfl_client."""
    return nfl_data_py.import_snap_counts(years)


def load_participation_data(years):
    """Loads participation data via nfl_client."""
    return nfl_data_py.import_participation_data(years)


# Downloads the pbp data to a local file. Updates
# This function is now deprecated, as load_data handles live loading
def clean_and_save_data(years=[]):
    print("DEPRECATED: clean_and_save_data is no longer needed; data is loaded and cached by nflreadpy via load_data().")
    pass
