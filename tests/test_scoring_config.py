import pytest
import os
import yaml
from settings import AppConfig, ScoringSettings

TEST_CONFIG_PATH = "config/test_scoring.yaml"

@pytest.fixture
def clean_config_file():
    if os.path.exists(TEST_CONFIG_PATH):
        os.remove(TEST_CONFIG_PATH)
    yield
    if os.path.exists(TEST_CONFIG_PATH):
        os.remove(TEST_CONFIG_PATH)

def test_load_defaults_when_file_missing():
    """Verify we get defaults if config file doesn't exist."""
    # Point to a non-existent file
    config = AppConfig.load(scoring_file="non_existent.yaml")
    
    # Check a few defaults
    assert config.scoring.pass_td == 4.0
    assert config.scoring.rush_td == 6.0
    assert config.scoring.reception == 0.5

def test_load_from_yaml(clean_config_file):
    """Verify we can load custom rules from YAML."""
    
    # Create a "PPR + 6pt Passing TD" config
    custom_rules = {
        "name": "Full PPR + 6pt Pass TD",
        "pass_td": 6.0,
        "reception": 1.0,
        "rush_yard": 0.5 # Crazy high for testing
    }
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(TEST_CONFIG_PATH), exist_ok=True)
    
    with open(TEST_CONFIG_PATH, "w") as f:
        yaml.dump(custom_rules, f)
        
    config = AppConfig.load(scoring_file=TEST_CONFIG_PATH)
    
    assert config.scoring.name == "Full PPR + 6pt Pass TD"
    assert config.scoring.pass_td == 6.0
    assert config.scoring.reception == 1.0
    assert config.scoring.rush_yard == 0.5
    
    # Check that unspecified values remain defaults
    assert config.scoring.rec_td == 6.0 # Default

def test_load_partial_yaml(clean_config_file):
    """Verify partial config merges with defaults."""
    partial_rules = {
        "def_sack": 5.0
    }
    
    os.makedirs(os.path.dirname(TEST_CONFIG_PATH), exist_ok=True)
    with open(TEST_CONFIG_PATH, "w") as f:
        yaml.dump(partial_rules, f)
        
    config = AppConfig.load(scoring_file=TEST_CONFIG_PATH)
    
    assert config.scoring.def_sack == 5.0
    assert config.scoring.pass_td == 4.0 # Default intact
