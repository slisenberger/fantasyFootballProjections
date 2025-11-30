import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock
from types import SimpleNamespace

from settings import AppConfig, RuntimeSettings
from enums import Position

@pytest.fixture
def mock_pbp_data():
    """Provides a minimal mock PBP DataFrame for testing."""
    data = {
        'season': [2024, 2024, 2018, 2018, 2017], # Add a 2018 entry with week < 8
        'week': [1, 1, 1, 8, 17], # Week 1 for 2018
        'game_id': ['2024_01_BUF_MIA', '2024_01_BUF_MIA', '2018_01_GEN_ERI', '2018_08_GEN_ERI', '2017_17_OLD_NEW'],
        'play_id': [1, 2, 1, 1, 1],
        'home_team': ['MIA', 'MIA', 'ERI', 'ERI', 'NEW'],
        'away_team': ['BUF', 'BUF', 'GEN', 'GEN', 'OLD'],
        'posteam': ['BUF', 'MIA', 'GEN', 'GEN', 'OLD'],
        'pass_touchdown': [0, 0, 0, 0, 0],
        'rush_touchdown': [1, 0, 1, 1, 1],
        'receiving_yards': [0, 0, 0, 0, 0],
        'rushing_yards': [5, 0, 8, 8, 10],
        'passing_yards': [0, 0, 0, 0, 0],
        'passer_player_id': [None, None, None, None, None],
        'receiver_player_id': [None, None, None, None, None],
        'rusher_player_id': ['RB_BUF', None, 'RB_GEN', 'RB_GEN', 'RB_OLD'],
        'play_type': ['run', 'pass', 'run', 'run', 'run'],
        'interception': [0, 0, 0, 0, 0],
        'fumble_lost': [0, 0, 0, 0, 0],
        'two_point_conv_result': [None, None, None, None, None],
        'sack': [0, 0, 0, 0, 0],
        'field_goal_attempt': [0, 0, 0, 0, 0],
        'extra_point_attempt': [0, 0, 0, 0, 0],
        'kickoff_attempt': [0, 0, 0, 0, 0],
        'punt_attempt': [0, 0, 0, 0, 0],
        'safety': [0,0,0,0,0], 
        'kicker_player_id': [None, None, None, None, None],
        'fumbled_1_player_id': [None, None, None, None, None],
        'kickoff_returner_player_id': [None, None, None, None, None], # Added
        'punt_returner_player_id': [None, None, None, None, None], # Added
        'return_touchdown': [0,0,0,0,0], # Added
        'defteam': ['BUF', 'BUF', 'GEN', 'GEN', 'OLD'], # Added
        'field_goal_result': [None, None, None, None, None], # Added
        'kick_distance': [None, None, None, None, None], # Added
        'extra_point_result': [None, None, None, None, None], # Added
        'total_away_score': [0, 7, 0, 0, 0], # Scores after play
        'total_home_score': [7, 7, 7, 7, 10],
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_nfl_data_py_roster():
    """Mocks nfl_data_py.import_seasonal_rosters to return a minimal roster."""
    roster_data = {
        'player_id': ['QB_BUF', 'RB_BUF', 'WR_BUF', 'QB_MIA', 'RB_MIA', 'RB_GEN', 'RB_OLD', 'RB_ERI', 'QB_GEN', 'QB_ERI', 'DEF_GEN', 'DEF_ERI'],
        'position': ['QB', 'RB', 'WR', 'QB', 'RB', 'RB', 'RB', 'RB', 'QB', 'QB', 'DEF', 'DEF'],
        'player_name': ['Josh Allen', 'James Cook', 'Stefon Diggs', 'Tua Tagovailoa', 'Raheem Mostert', 'Generic RB', 'Old RB', 'Erie RB', 'Generic QB', 'Erie QB', 'Generic D/ST', 'Erie D/ST'],
        'team': ['BUF', 'BUF', 'BUF', 'MIA', 'MIA', 'GEN', 'OLD', 'ERI', 'GEN', 'ERI', 'GEN', 'ERI'],
    }
    return pd.DataFrame(roster_data)


@pytest.fixture
def mock_app_config():
    """Provides a default AppConfig for testing."""
    return AppConfig(
        runtime=RuntimeSettings( # Use RuntimeSettings here
            season=2024,
            week=1,
            n_simulations=1,
            use_parallel=False,
            version="test"
        )
    )

@pytest.fixture
def mock_player_stats():
    """A mock DataFrame for player statistics."""
    data = {
        'player_id': ['QB_BUF', 'RB_BUF', 'WR_BUF', 'QB_MIA', 'RB_MIA', 'WR_MIA', 'TE_BUF', 'K_BUF', 'DEF_BUF', 'RB_GEN', 'RB_OLD', 'RB_ERI', 'QB_GEN', 'QB_ERI', 'DEF_GEN', 'DEF_ERI'],
        'player_name': ['Josh Allen', 'James Cook', 'Stefon Diggs', 'Tua Tagovailoa', 'Raheem Mostert', 'Tyreek Hill', 'Dawson Knox', 'Tyler Bass', 'Bills D/ST', 'Generic RB', 'Old RB', 'Erie RB', 'Generic QB', 'Erie QB', 'Generic D/ST', 'Erie D/ST'],
        'position': ['QB', 'RB', 'WR', 'QB', 'RB', 'WR', 'TE', 'K', 'DEF', 'RB', 'RB', 'RB', 'QB', 'QB', 'DEF', 'DEF'],
        'team': ['BUF', 'BUF', 'BUF', 'MIA', 'MIA', 'MIA', 'BUF', 'BUF', 'BUF', 'GEN', 'OLD', 'ERI', 'GEN', 'ERI', 'GEN', 'ERI'],
        'status': ['Active'] * 16,
        'exp_return': [None] * 16,
        'relative_air_yards_est': [1.0] * 16,
        'target_share_est': [0.0, 0.1, 0.2, 0.0, 0.1, 0.3, 0.1, 0.0, 0.0, 0.1, 0.1, 0.1, 0.0, 0.0, 0.0, 0.0], # RB_GEN, RB_OLD, RB_ERI can also be targets
        'redzone_target_share_est': [0.0, 0.05, 0.1, 0.0, 0.05, 0.15, 0.05, 0.0, 0.0, 0.05, 0.05, 0.05, 0.0, 0.0, 0.0, 0.0],
        'target_percentage': [0.1, 0.1, 0.2, 0.1, 0.1, 0.3, 0.1, 0.0, 0.0, 0.1, 0.1, 0.1, 0.1, 0.1, 0.0, 0.0], # Example non-zero values
        'targets': [0] * 16,
        'relative_yac': [1.0] * 16,
        'relative_yac_est': [1.0] * 16,
        'receiver_cpoe_est': [0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        'carry_share_est': [0.0, 0.5, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.5, 0.5, 0.5, 0.0, 0.0, 0.0, 0.0], # RB's can carry
        'redzone_carry_share_est': [0.0, 0.2, 0.0, 0.0, 0.2, 0.0, 0.0, 0.0, 0.0, 0.2, 0.2, 0.2, 0.0, 0.0, 0.0, 0.0],
        'goal_line_carry_share_est': [0.0, 0.2, 0.0, 0.0, 0.2, 0.0, 0.0, 0.0, 0.0, 0.2, 0.2, 0.2, 0.0, 0.0, 0.0, 0.0], # Added
        'carry_percentage': [0.1, 0.5, 0.0, 0.1, 0.5, 0.0, 0.0, 0.0, 0.0, 0.5, 0.5, 0.5, 0.0, 0.0, 0.0, 0.0], # Example non-zero values
        'carries': [0] * 16,
        'relative_ypc': [1.0] * 16, # Corrected length
        'relative_ypc_est': [1.0] * 16, # Corrected length
        'cpoe_est': [1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0], # Corrected length
        'pass_attempts': [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0], # Corrected length
        'scramble_rate_est': [0.1, 0.0, 0.0, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.1, 0.0, 0.0], # Corrected length
        'yards_per_scramble_est': [5.0, 0.0, 0.0, 5.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 5.0, 5.0, 0.0, 0.0], # Corrected length
        'relative_yards_per_scramble_est': [1.0] * 16,
        'snap_share_est': [1.0] * 16, 
        'fgoe_est': [0.0] * 16,
        'is_mobile': [0] * 16, # Added
        'starting_qb': [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0], # Corrected length
        'kick_attempts': [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0], # Corrected length
        'starting_k': [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0], # Corrected length
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_team_stats():
    """A mock DataFrame for team statistics."""
    data = {
        'team': ['BUF', 'MIA', 'GEN', 'OLD', 'ERI'],
        'defense_relative_ypc_est': [1.0, 1.0, 1.0, 1.0, 1.0],
        'defense_relative_yac_est': [1.0, 1.0, 1.0, 1.0, 1.0],
        'defense_relative_air_yards': [1.0, 1.0, 1.0, 1.0, 1.0],
        'defense_cpoe_est': [1.0, 1.0, 1.0, 1.0, 1.0],
        'defense_int_rate_est': [0.02, 0.02, 0.02, 0.02, 0.02],
        'offense_sacks_per_dropback': [0.05, 0.05, 0.05, 0.05, 0.05],
        'defense_sacks_per_dropback': [0.05, 0.05, 0.05, 0.05, 0.05],
        'offense_sack_rate_est': [0.05, 0.05, 0.05, 0.05, 0.05],
        'defense_sack_rate_est': [0.05, 0.05, 0.05, 0.05, 0.05],
        'lg_sack_rate': [0.05, 0.05, 0.05, 0.05, 0.05],
        'offense_pass_oe_est': [0.0, 0.0, 0.0, 0.0, 0.0],
        'defense_pass_oe_est': [0.0, 0.0, 0.0, 0.0, 0.0],
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_snap_data():
    """A mock DataFrame for snap counts."""
    data = {
        'game_id': ['2024_01_BUF_MIA'],
        'pfr_game_id': ['202409080mia'],
        'season': [2024],
        'week': [1],
        'game_type': ['REG'],
        'team': ['BUF'],
        'player': ['Josh Allen'],
        'pfr_player_id': ['AlleJo02'],
        'position': ['QB'],
        'offense_snaps': [60],
        'offense_pct': [1.0],
        'defense_snaps': [0],
        'defense_pct': [0.0],
        'st_snaps': [0],
        'st_pct': [0.0],
    }
    return pd.DataFrame(data)


@pytest.fixture
def mock_models_for_game_state():
    """Provides mock models suitable for GameState initialization."""
    mock_model = MagicMock()
    # Configure playcall_model for choose_playcall logic
    mock_playcall_model = MagicMock()
    # Ensure classes_ order matches expected indices in engine/game.py
    mock_playcall_model.classes_ = ['field_goal', 'pass', 'punt', 'run'] 
    # Provide a probability distribution matching the number of classes
    mock_playcall_model.predict_proba.return_value = np.array([[0.25, 0.25, 0.25, 0.25]])
    
    mock_kde = MagicMock()
    mock_kde.sample.return_value = np.array([[10]]) # Default yardage
    
    mock_samples = np.array([5.0] * 100)

    mock_field_goal_model = MagicMock()
    mock_field_goal_model.classes_ = ['made', 'missed']
    mock_field_goal_model.predict_proba.return_value = np.array([[0.8, 0.2]]) # 80% chance to make FG

    mock_completion_model = MagicMock()
    mock_completion_model.classes_ = [1, 0] # 1=Complete, 0=Incomplete
    mock_completion_model.predict_proba.return_value = np.array([[0.7, 0.3]]) # 70% chance to complete pass
    
    return {
        "playcall_model": mock_playcall_model,
        "rush_open_model": mock_kde,
        "rush_rz_model": mock_kde,
        "scramble_model": mock_kde,
        "completion_model": mock_completion_model,
        "field_goal_model": mock_field_goal_model,
        "int_return_model": mock_kde,
        "air_yards_RB": mock_kde,
        "air_yards_TE": mock_kde,
        "air_yards_WR": mock_kde,
        "air_yards_ALL": mock_kde,
        "yac_RB": mock_kde,
        "yac_TE": mock_kde,
        "yac_WR": mock_kde,
        "yac_ALL": mock_kde,
        
        # Samples
        "rush_open_samples": mock_samples,
        "rush_rz_samples": mock_samples,
        "scramble_samples": mock_samples,
        "scramble_samples_mobile": mock_samples,
        "scramble_samples_pocket": mock_samples,
        "int_return_samples": mock_samples,
        "air_yards_RB_samples": mock_samples,
        "air_yards_TE_samples": mock_samples,
        "air_yards_WR_samples": mock_samples,
        "air_yards_ALL_samples": mock_samples,
        "yac_RB_open_samples": mock_samples,
        "yac_RB_rz_samples": mock_samples,
        "yac_WR_open_samples": mock_samples,
        "yac_WR_rz_samples": mock_samples,
        "yac_TE_open_samples": mock_samples,
        "yac_TE_rz_samples": mock_samples,
        "yac_ALL_open_samples": mock_samples,
        "yac_ALL_rz_samples": mock_samples,
    }