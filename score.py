from collections import defaultdict
import pandas as pd

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
    _YARDS_RUSHING: 0.1,
    _YARDS_RECEIVING: 0.1,
    _YARDS_PASSING: 0.04,
    _YARDS_RETURN: 0.04,
    _RECEPTION: 0.5,
    _INTERCEPTION_THROW: -1.5,
    _TWO_POINT_CONVERSION: 2,
    _FUMBLE_LOST: -2,
    _TOUCHDOWN_FUMBLE_RECOVERY: 6,
    _FIELD_GOAL_0_39_YDS: 3,
    _FIELD_GOAL_40_49_YDS: 4,
    _FIELD_GOAL_50_OR_MORE_YDS: 5,
    _MADE_PAT: 1,
    _SACK: 1,
    _SAFETY: 2,
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
    if (
        play.kickoff_attempt or play.punt_attempt
    ) and play.return_touchdown:
        return_id = (
            play.kickoff_returner_player_id
            if play.kickoff_returner_player_id
            else play.punt_returner_player_id
        )
        scores_on_play[return_id] += _SCORING_VALUES[_TOUCHDOWN_RETURN]
    if play.receiving_yards > 0:
        scores_on_play[play.receiver_player_id] += (
            _SCORING_VALUES[_YARDS_RECEIVING] * play.receiving_yards
        )
        scores_on_play[play.receiver_player_id] += _SCORING_VALUES[_RECEPTION]
    if play.passing_yards > 0:
        scores_on_play[play.passer_player_id] += (
            _SCORING_VALUES[_YARDS_PASSING] * play.passing_yards
        )
    if play.rushing_yards > 0 or play.rushing_yards < 0:
        scores_on_play[play.rusher_player_id] += (
            _SCORING_VALUES[_YARDS_RUSHING] * play.rushing_yards
        )
    if play.kickoff_returner_player_id or play.punt_returner_id:
        return_id = (
            play.kickoff_returner_player_id
            if play.kickoff_returner_player_id
            else play.punt_returner_player_id
        )
        scores_on_play[return_id] += _SCORING_VALUES[_YARDS_RETURN] * play.return_yards
    if play.interception:
        scores_on_play[play.passer_player_id] += _SCORING_VALUES[_INTERCEPTION_THROW]
        scores_on_play[play.defteam] += _SCORING_VALUES[_INTERCEPTION]
        if play.return_touchdown:
            scores_on_play[play.defteam] += _SCORING_VALUES[_TOUCHDOWN_DEFENSE]
    if play.fumble_lost:
        scores_on_play[play.fumbled_1_player_id] += _SCORING_VALUES[_FUMBLE_LOST]
    if play.two_point_conv_result == "success":
        if not pd.isnull(play.rusher_player_id):
            scores_on_play[play.rusher_player_id] += _SCORING_VALUES[
                _TWO_POINT_CONVERSION
            ]
        if not pd.isnull(play.receiver_player_id):
            scores_on_play[play.receiver_player_id] += _SCORING_VALUES[
                _TWO_POINT_CONVERSION
            ]
            scores_on_play[play.passer_player_id] += _SCORING_VALUES[
                _TWO_POINT_CONVERSION
            ]

    if play.sack:
        scores_on_play[play.defteam] += _SCORING_VALUES[_SACK]

    if play.field_goal_attempt and play.field_goal_result == "blocked":
        scores_on_play[play.defteam] += _SCORING_VALUES[_BLOCK_KICK]

    if play.field_goal_attempt and play.field_goal_result == "made":
        if play.kick_distance <= 39:
            scores_on_play[play.kicker_player_id] += _SCORING_VALUES[
                _FIELD_GOAL_0_39_YDS
            ]
        elif play.kick_distance <= 49:
            scores_on_play[play.kicker_player_id] += _SCORING_VALUES[
                _FIELD_GOAL_40_49_YDS
            ]
        else:
            scores_on_play[play.kicker_player_id] += _SCORING_VALUES[
                _FIELD_GOAL_50_OR_MORE_YDS
            ]

    if play.extra_point_attempt and play.extra_point_result == "made":
        scores_on_play[play.kicker_player_id] += _SCORING_VALUES[_MADE_PAT]

    if play.safety:
        scores_on_play[play.defteam] += _SCORING_VALUES[_SAFETY]

    return scores_on_play


def points_from_score(score):
    score = int(score)
    if score == 0:
        return _SCORING_VALUES[_POINTS_ALLOWED_0]
    elif score < 7:
        return _SCORING_VALUES[_POINTS_ALLOWED_1_6]
    elif score < 14:
        return _SCORING_VALUES[_POINTS_ALLOWED_7_13]
    elif score < 21:
        return _SCORING_VALUES[_POINTS_ALLOWED_14_20]
    elif score < 28:
        return _SCORING_VALUES[_POINTS_ALLOWED_21_27]
    elif score < 35:
        return _SCORING_VALUES[_POINTS_ALLOWED_28_34]
    else:
        return _SCORING_VALUES[_POINTS_ALLOWED_35_OR_MORE]
