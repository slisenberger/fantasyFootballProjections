import pytest
import joblib
import random
import numpy as np
from engine import game
from settings import AppConfig

# Define fixture path relative to the test execution root
FIXTURE_DIR = "tests/fixtures"

def test_golden_master_simulation():
    """
    Verifies that the simulation engine produces deterministic output
    given a fixed set of inputs (Golden Master).
    
    This test ensures that refactoring the engine or data pipeline
    does not accidentally change the simulation logic or outcomes.
    """
    try:
        inputs = joblib.load(f"{FIXTURE_DIR}/golden_inputs.pkl")
        expected_output = joblib.load(f"{FIXTURE_DIR}/golden_output.pkl")
    except FileNotFoundError:
        pytest.fail("Golden Master fixtures not found. Run 'python generate_golden_master.py' first.")

    # 1. Setup
    random.seed(42)
    np.random.seed(42)
    
    models = inputs["models"]
    player_stats = inputs["player_stats"]
    team_stats = inputs["team_stats"]
    home = inputs["home"]
    away = inputs["away"]
    config = inputs["config"]
    
    home_player_stats = player_stats[player_stats["team"].isin([home])]
    away_player_stats = player_stats[player_stats["team"].isin([away])]
    home_team_stats = team_stats[team_stats["team"].isin([home])]
    away_team_stats = team_stats[team_stats["team"].isin([away])]
    
    # 2. Execution
    game_machine = game.GameState(
        models,
        home,
        away,
        home_player_stats,
        away_player_stats,
        home_team_stats,
        away_team_stats,
        rules=config.scoring,
        trace=False 
    )
    scores, _ = game_machine.play_game()
    
    # 3. Assertion
    # Compare scores (dictionary of float)
    expected_scores = expected_output["scores"]
    
    # Check keys match
    assert set(scores.keys()) == set(expected_scores.keys())
    
    # Check values match (with tolerance for floating point issues)
    for key in scores:
        assert scores[key] == pytest.approx(expected_scores[key], abs=1e-9), \
            f"Score mismatch for {key}: Expected {expected_scores[key]}, Got {scores[key]}"
