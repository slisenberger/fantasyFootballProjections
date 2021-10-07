from collections import defaultdict

# Offensive Scoring Categories
_TOUCHDOWN_RUSHING = "TOUCHDOWN_RUSHING"
_TOUCHDOWN_RECEIVING = "TOUCHDOWN_RECEIVING"
_TOUCHDOWN_PASSING = "TOUCHDOWN_PASSING"
_TOUCHDOWN_RETURN = "TOUCHDOWN_RETURN"
_YARDS_RUSHING = "YARDS_RUSHING"
_YARDS_RECEIVING = "YARDS_RECEIVING"
_YARDS_PASSING = "YARDS_PASSING"
_YARDS_RETURN = "YARDS_RETURN"
_RECEPTION = "RECEPTION"
_INTERCEPTION_THROW = "INTERCEPTION_THROW"
_TWO_POINT_CONVERSION = "TWO_POINT_CONVERSION"
_FUMBLE_LOST = "FUMBLE_LOST"
_TOUCHDOWN_FUMBLE_RECOVERY = "TOUCHDOWN_FUMBLE_RECOVERY"
# Kicking Scoring Categories
_FIELD_GOAL_0_39_YDS = "_FIELD_GOAL_0_39_YDS"
_FIELD_GOAL_40_49_YDS = "_FIELD_GOAL_40_49_YDS"
_FIELD_GOAL_50_OR_MORE_YDS = "_FIELD_GOAL_50_OR_MORE_YDS"
_MADE_PAT = "_MADE_PAT"
# Defense Scoring Categories
_SACK = "SACK"
_INTERCEPTION = "INTERCEPTION"
_FUMBLE_RECOVERY = "FUMBLE_RECOVERY"
_TOUCHDOWN_DEFENSE = "TOUCHDOWN_DEFENSE"
_SAFETY = "SAFETY"
_BLOCK_KICK = "BLOCK_KICK"
_EXTRA_POINT_RETURN = "EXTRA_POINT_RETURN"
_POINTS_ALLOWED_0 = "POINTS_ALLOWED_0"
_POINTS_ALLOWED_1_6 = "POINTS_ALLOWED_1_6"
_POINTS_ALLOWED_7_13 = "POINTS_ALLOWED_7_13"
_POINTS_ALLOWED_14_20 = "POINTS_ALLOWED_14_20"
_POINTS_ALLOWED_21_27 = "POINTS_ALLOWED_21_28"
_POINTS_ALLOWED_28_34 = "POINTS_ALLOWED_28_34"
_POINTS_ALLOWED_35_OR_MORE = "POINTS_ALLOWED_35_OR_MORE"

# The scoring values for each category.
_SCORING_VALUES = {
    _TOUCHDOWN_RUSHING: 6,
    _TOUCHDOWN_RECEIVING: 6,
    _TOUCHDOWN_PASSING: 4,
    _TOUCHDOWN_RETURN: 6,
    _YARDS_RUSHING: .1,
    _YARDS_RECEIVING: .1,
    _YARDS_PASSING: .04,
    _YARDS_RETURN: .04,
    _RECEPTION: .5,
    _INTERCEPTION_THROW: -1.5,
    _TWO_POINT_CONVERSION: 2,
    _FUMBLE_LOST: -2,
    _TOUCHDOWN_FUMBLE_RECOVERY: 6,
    _FIELD_GOAL_0_39_YDS: 3,
    _FIELD_GOAL_40_49_YDS: 4,
    _FIELD_GOAL_50_OR_MORE_YDS: 5,
    _MADE_PAT: 1,
    _SACK: 1,
    _INTERCEPTION: 2,
    _FUMBLE_RECOVERY: 2,
    _TOUCHDOWN_DEFENSE: 6,
    _BLOCK_KICK: 2,
    _EXTRA_POINT_RETURN: 2,
    _POINTS_ALLOWED_0: 10,
    _POINTS_ALLOWED_1_6: 7,
    _POINTS_ALLOWED_7_13: 4,
    _POINTS_ALLOWED_14_20: 1,
    _POINTS_ALLOWED_21_27: 0,
    _POINTS_ALLOWED_28_34: -1,
    _POINTS_ALLOWED_35_OR_MORE: -4,
}

def score_from_play(play):
    # A map of player ID to the score they receive on this play.
    scores_on_play = defaultdict(float)
    if play.pass_touchdown:
        scores_on_play[play.passer_player_id] += _SCORING_VALUES[_TOUCHDOWN_PASSING]
        scores_on_play[play.receiver_player_id] += _SCORING_VALUES[_TOUCHDOWN_RECEIVING]
    if play.rush_touchdown:
        scores_on_play[play.rusher_player_id] += _SCORING_VALUES[_TOUCHDOWN_RUSHING]
    if play.return_touchdown:
        return_id = play.kickoff_returner_player_id if play.kickoff_returner_player_id else play.punt_returner_player_id
        scores_on_play[return_id] += _SCORING_VALUES[_TOUCHDOWN_RETURN]
    if play.receiving_yards > 0:
       scores_on_play[play.receiver_player_id] += _SCORING_VALUES[_YARDS_RECEIVING] * play.receiving_yards
       scores_on_play[play.receiver_player_id] += _SCORING_VALUES[_RECEPTION]
    if play.passing_yards > 0:
       scores_on_play[play.passer_player_id] += _SCORING_VALUES[_YARDS_PASSING] * play.passing_yards
    if play.rusher_player_id:
       scores_on_play[play.rusher_player_id] += _SCORING_VALUES[_YARDS_RUSHING] * play.rushing_yards
    if play.return_yards:
        return_id = play.kickoff_returner_player_id if play.kickoff_returner_player_id else play.punt_returner_player_id
        scores_on_play[return_id] += _SCORING_VALUES[_YARDS_RETURN] * play.return_yards
    if play.interception:
        scores_on_play[play.passer_player_id] += _SCORING_VALUES[_INTERCEPTION_THROW]




    return scores_on_play

