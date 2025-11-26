import pytest
from settings import AppConfig, ScoringSettings

def test_default_scoring_settings():
    scoring = ScoringSettings()
    assert scoring.name == "Half PPR"
    assert scoring.rush_td == 6.0
    assert scoring.reception == 0.5
    assert scoring.pass_td == 4.0
    assert scoring.intercept == -1.5

def test_custom_scoring_settings():
    scoring = ScoringSettings(
        name="Full PPR",
        reception=1.0,
        pass_td=6.0,
        def_sack=3.0
    )
    assert scoring.name == "Full PPR"
    assert scoring.reception == 1.0
    assert scoring.pass_td == 6.0
    assert scoring.def_sack == 3.0
    # Ensure other defaults are maintained
    assert scoring.rush_td == 6.0
    assert scoring.intercept == -1.5

def test_app_config_defaults():
    config = AppConfig()
    assert config.runtime.season == 2024
    assert config.runtime.week == 1
    assert config.runtime.n_simulations == 5
    assert config.scoring.name == "Half PPR"

def test_app_config_runtime_override():
    config = AppConfig(runtime={"season": 2023, "week": 10, "n_simulations": 100})
    assert config.runtime.season == 2023
    assert config.runtime.week == 10
    assert config.runtime.n_simulations == 100
    assert config.scoring.name == "Half PPR" # Scoring settings should remain default

def test_app_config_scoring_override():
    config = AppConfig(scoring={"name": "Standard", "reception": 0.0})
    assert config.scoring.name == "Standard"
    assert config.scoring.reception == 0.0
    assert config.runtime.season == 2024 # Runtime settings should remain default
