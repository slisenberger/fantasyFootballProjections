import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from main import project_week, run_projections, run_backtest
from settings import AppConfig, RuntimeSettings
from types import SimpleNamespace

# Fixtures for mocking external dependencies
@pytest.fixture
def mock_external_data_and_models(mock_models_for_game_state, mock_pbp_data, mock_player_stats, mock_team_stats):
    """
    Mocks various external data loading and model fetching functions
    to allow project_week to run in isolation for a smoke test.
    """
    with (patch('nfl_data_py.import_schedules') as mock_schedules, 
          patch('nfl_data_py.import_seasonal_rosters') as mock_rosters,
          patch('stats.injuries.get_injury_data') as mock_injuries,
          patch('stats.players.calculate') as mock_players_calc,
          patch('stats.teams.calculate') as mock_teams_calc,
          patch('main.get_models', return_value=mock_models_for_game_state),
          patch('data.loader.load_data', return_value=mock_pbp_data)): # Ensure pbp data is available for any season


        # Mock schedule
        mock_schedules.return_value = pd.DataFrame([
            {'season': 2024, 'week': 1, 'gameday': '2024-09-08', 'home_team': 'MIA', 'away_team': 'BUF', 'game_id': '2024_01_BUF_MIA'},
            {'season': 2018, 'week': 8, 'gameday': '2018-10-21', 'home_team': 'ERI', 'away_team': 'GEN', 'game_id': '2018_08_GEN_ERI'}
        ])

        # Mock roster data
        mock_rosters.return_value = pd.DataFrame({
            'player_id': ['QB_BUF', 'RB_BUF', 'WR_BUF', 'QB_MIA', 'RB_MIA'],
            'position': ['QB', 'RB', 'WR', 'QB', 'RB'],
            'player_name': ['Josh Allen', 'James Cook', 'Stefon Diggs', 'Tua Tagovailoa', 'Raheem Mostert'],
            'team': ['BUF', 'BUF', 'BUF', 'MIA', 'MIA'],
        })

        # Mock injuries data
        mock_injuries.return_value = None # No injuries for simplicity

        # Mock players and teams calculate functions
        mock_players_calc.return_value = mock_player_stats
        mock_teams_calc.return_value = mock_team_stats
        
        yield

@pytest.fixture
def mock_app_config_smoke():
    """Provides a minimal AppConfig for smoke testing."""
    return AppConfig(
        runtime=RuntimeSettings( # Use RuntimeSettings here
            season=2024,
            week=1,
            n_simulations=1, # Very fast run
            use_parallel=False, # Disable parallel for testing simplicity
            version="smoke_test"
        )
    )

def test_project_week_smoke_test(
    mock_pbp_data, mock_models_for_game_state, mock_app_config_smoke, mock_external_data_and_models
):
    """
    Smoke test for project_week function: ensures it runs without crashing
    and returns a DataFrame.
    """
    config = mock_app_config_smoke
    proj_df = project_week(
        mock_pbp_data, mock_models_for_game_state, config.runtime.season, config.runtime.week, config
    )
    assert isinstance(proj_df, pd.DataFrame)
    assert not proj_df.empty # Should have some projection data

def test_run_projections_smoke_test(
    mock_pbp_data, mock_app_config_smoke, mock_external_data_and_models
):
    """
    Smoke test for the run_projections main entry point.
    Ensures it completes and attempts to write files.
    """
    config = mock_app_config_smoke
    
    # Mock os.makedirs and pandas.DataFrame.to_csv to prevent actual file writing during test
    with patch('os.makedirs'), \
         patch('pandas.DataFrame.to_csv') as mock_to_csv:
        
        run_projections(mock_pbp_data, config)
        mock_to_csv.assert_called() # Verify that to_csv was called (i.e., files were "written")

def test_run_backtest_smoke_test(
    mock_pbp_data, mock_app_config_smoke, mock_external_data_and_models
):
    """
    Smoke test for the run_backtest main entry point.
    Ensures it completes and attempts to write files.
    """
    config = mock_app_config_smoke
    config.runtime.season = 2018 # Set to a backtest year
    
    # Mock calibration plot to prevent GUI popup
    with patch('os.makedirs'), \
         patch('pandas.DataFrame.to_csv') as mock_to_csv, \
         patch('main.plot_predictions'), \
         patch('evaluation.calibration.plot_pit_histogram'):

        run_backtest(mock_pbp_data, config)
        mock_to_csv.assert_called() # Verify that to_csv was called
