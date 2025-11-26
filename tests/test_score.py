import pytest
import pandas as pd
from types import SimpleNamespace
from score import score_from_play, points_from_score
from settings import ScoringSettings

@pytest.fixture
def default_scoring_rules():
    return ScoringSettings()

@pytest.fixture
def mock_play_base():
    """A base mock play object with common attributes."""
    return SimpleNamespace(
        pass_touchdown=0, rush_touchdown=0, kickoff_attempt=0, punt_attempt=0,
        return_touchdown=0, receiving_yards=0, passing_yards=0, rushing_yards=0,
        interception=0, fumble_lost=0, two_point_conv_result=None, sack=0,
        field_goal_attempt=0, extra_point_attempt=0, safety=0,
        passer_player_id=None, receiver_player_id=None, rusher_player_id=None,
        kickoff_returner_player_id=None, punt_returner_player_id=None,
        fumbled_1_player_id=None, kicker_player_id=None, defteam=None,
        kick_distance=None
    )

def test_score_from_play_passing_td(default_scoring_rules, mock_play_base):
    play = mock_play_base
    play.pass_touchdown = 1
    play.passer_player_id = "QB1"
    play.receiver_player_id = "WR1"
    
    scores = score_from_play(play, default_scoring_rules)
    assert scores["QB1"] == default_scoring_rules.pass_td
    assert scores["WR1"] == default_scoring_rules.rec_td

def test_score_from_play_rushing_td(default_scoring_rules, mock_play_base):
    play = mock_play_base
    play.rush_touchdown = 1
    play.rusher_player_id = "RB1"
    
    scores = score_from_play(play, default_scoring_rules)
    assert scores["RB1"] == default_scoring_rules.rush_td

def test_score_from_play_receiving_yards_and_reception(default_scoring_rules, mock_play_base):
    play = mock_play_base
    play.receiving_yards = 10
    play.receiver_player_id = "WR1"
    
    scores = score_from_play(play, default_scoring_rules)
    expected_score = (default_scoring_rules.rec_yard * 10) + default_scoring_rules.reception
    assert scores["WR1"] == expected_score

def test_score_from_play_passing_yards(default_scoring_rules, mock_play_base):
    play = mock_play_base
    play.passing_yards = 250
    play.passer_player_id = "QB1"
    
    scores = score_from_play(play, default_scoring_rules)
    assert scores["QB1"] == default_scoring_rules.pass_yard * 250

def test_score_from_play_rushing_yards(default_scoring_rules, mock_play_base):
    play = mock_play_base
    play.rushing_yards = 50
    play.rusher_player_id = "RB1"
    
    scores = score_from_play(play, default_scoring_rules)
    assert scores["RB1"] == default_scoring_rules.rush_yard * 50

def test_score_from_play_interception(default_scoring_rules, mock_play_base):
    play = mock_play_base
    play.interception = 1
    play.passer_player_id = "QB1"
    play.defteam = "DEF1"
    
    scores = score_from_play(play, default_scoring_rules)
    assert scores["QB1"] == default_scoring_rules.intercept
    assert scores["DEF1"] == default_scoring_rules.def_int

def test_score_from_play_fumble_lost(default_scoring_rules, mock_play_base):
    play = mock_play_base
    play.fumble_lost = 1
    play.fumbled_1_player_id = "RB1"
    play.defteam = "DEF1" # Assuming defteam gets points for recovery
    
    scores = score_from_play(play, default_scoring_rules)
    assert scores["RB1"] == default_scoring_rules.fumble_lost
    assert scores["DEF1"] == default_scoring_rules.def_fumble_rec

def test_score_from_play_2pt_conversion_rush(default_scoring_rules, mock_play_base):
    play = mock_play_base
    play.two_point_conv_result = "success"
    play.rusher_player_id = "RB1"
    play.receiver_player_id = pd.NA # Not a receiving 2pt
    
    scores = score_from_play(play, default_scoring_rules)
    assert scores["RB1"] == default_scoring_rules.two_pt_conv

def test_score_from_play_2pt_conversion_pass(default_scoring_rules, mock_play_base):
    play = mock_play_base
    play.two_point_conv_result = "success"
    play.rusher_player_id = pd.NA
    play.receiver_player_id = "WR1"
    play.passer_player_id = "QB1"
    
    scores = score_from_play(play, default_scoring_rules)
    assert scores["WR1"] == default_scoring_rules.two_pt_conv
    assert scores["QB1"] == default_scoring_rules.two_pt_conv

def test_score_from_play_sack(default_scoring_rules, mock_play_base):
    play = mock_play_base
    play.sack = 1
    play.passer_player_id = "QB1"
    play.defteam = "DEF1"
    
    scores = score_from_play(play, default_scoring_rules)
    assert scores["QB1"] == default_scoring_rules.sack
    assert scores["DEF1"] == default_scoring_rules.def_sack

def test_score_from_play_fg_made_short(default_scoring_rules, mock_play_base):
    play = mock_play_base
    play.field_goal_attempt = 1
    play.field_goal_result = "made"
    play.kick_distance = 35
    play.kicker_player_id = "K1"
    
    scores = score_from_play(play, default_scoring_rules)
    assert scores["K1"] == default_scoring_rules.fg_0_39

def test_score_from_play_fg_made_medium(default_scoring_rules, mock_play_base):
    play = mock_play_base
    play.field_goal_attempt = 1
    play.field_goal_result = "made"
    play.kick_distance = 45
    play.kicker_player_id = "K1"
    
    scores = score_from_play(play, default_scoring_rules)
    assert scores["K1"] == default_scoring_rules.fg_40_49

def test_score_from_play_fg_made_long(default_scoring_rules, mock_play_base):
    play = mock_play_base
    play.field_goal_attempt = 1
    play.field_goal_result = "made"
    play.kick_distance = 55
    play.kicker_player_id = "K1"
    
    scores = score_from_play(play, default_scoring_rules)
    assert scores["K1"] == default_scoring_rules.fg_50_plus

def test_score_from_play_pat_made(default_scoring_rules, mock_play_base):
    play = mock_play_base
    play.extra_point_attempt = 1
    play.extra_point_result = "made"
    play.kicker_player_id = "K1"
    
    scores = score_from_play(play, default_scoring_rules)
    assert scores["K1"] == default_scoring_rules.pat_made

def test_score_from_play_safety(default_scoring_rules, mock_play_base):
    play = mock_play_base
    play.safety = 1
    play.defteam = "DEF1"
    
    scores = score_from_play(play, default_scoring_rules)
    assert scores["DEF1"] == default_scoring_rules.def_safety

def test_points_from_score_pa_0(default_scoring_rules):
    assert points_from_score(0, default_scoring_rules) == default_scoring_rules.pa_0

def test_points_from_score_pa_1_6(default_scoring_rules):
    assert points_from_score(3, default_scoring_rules) == default_scoring_rules.pa_1_6

def test_points_from_score_pa_7_13(default_scoring_rules):
    assert points_from_score(10, default_scoring_rules) == default_scoring_rules.pa_7_13

def test_points_from_score_pa_14_20(default_scoring_rules):
    assert points_from_score(17, default_scoring_rules) == default_scoring_rules.pa_14_20

def test_points_from_score_pa_21_27(default_scoring_rules):
    assert points_from_score(24, default_scoring_rules) == default_scoring_rules.pa_21_27

def test_points_from_score_pa_28_34(default_scoring_rules):
    assert points_from_score(30, default_scoring_rules) == default_scoring_rules.pa_28_34

def test_points_from_score_pa_35_plus(default_scoring_rules):
    assert points_from_score(35, default_scoring_rules) == default_scoring_rules.pa_35_plus
    assert points_from_score(40, default_scoring_rules) == default_scoring_rules.pa_35_plus

