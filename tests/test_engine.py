import pytest
import pandas as pd
from engine.game import GameState
from settings import ScoringSettings

def test_game_state_initialization(mock_models_for_game_state, mock_player_stats, mock_team_stats):
    """Test that GameState initializes without errors."""
    rules = ScoringSettings()
    home_team = "BUF"
    away_team = "MIA"
    
    # Filter player and team stats for the specific game
    home_player_stats = mock_player_stats[mock_player_stats['team'] == home_team]
    away_player_stats = mock_player_stats[mock_player_stats['team'] == away_team]
    home_team_stats = mock_team_stats[mock_team_stats['team'] == home_team]
    away_team_stats = mock_team_stats[mock_team_stats['team'] == away_team]

    game_state = GameState(
        mock_models_for_game_state,
        home_team,
        away_team,
        home_player_stats,
        away_player_stats,
        home_team_stats,
        away_team_stats,
        rules=rules
    )

    assert game_state.home_team == home_team
    assert game_state.away_team == away_team
    assert game_state.rules == rules
    assert not game_state.game_over
    assert game_state.home_score == 0
    assert game_state.away_score == 0
    assert isinstance(game_state.fantasy_points, dict)

def test_game_state_play_game_basic(mock_models_for_game_state, mock_player_stats, mock_team_stats):
    """
    Test a very basic game simulation to ensure it runs without crashing
    and produces fantasy points.
    """
    rules = ScoringSettings()
    home_team = "BUF"
    away_team = "MIA"
    
    home_player_stats = mock_player_stats[mock_player_stats['team'] == home_team]
    away_player_stats = mock_player_stats[mock_player_stats['team'] == away_team]
    home_team_stats = mock_team_stats[mock_team_stats['team'] == home_team]
    away_team_stats = mock_team_stats[mock_team_stats['team'] == away_team]

    game_state = GameState(
        mock_models_for_game_state,
        home_team,
        away_team,
        home_player_stats,
        away_player_stats,
        home_team_stats,
        away_team_stats,
        rules=rules
    )
    
    # For a basic test, we'll force the game to end quickly
    # by setting a very short quarter time or limiting plays
    game_state.sec_remaining = 1 # Force game_over quickly

    fantasy_points = game_state.play_game()
    assert isinstance(fantasy_points, dict)
    assert len(fantasy_points) > 0 # Should have at least defensive points
