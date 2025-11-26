from collections import defaultdict
import pandas as pd
from settings import ScoringSettings

def score_from_play(play, rules: ScoringSettings):
    """
    Calculates fantasy points for a single play based on the provided ScoringSettings.
    Returns a dictionary mapping player_id -> points earned on this play.
    """
    # A map of player ID to the score they receive on this play.
    scores_on_play = defaultdict(float)
    
    # --- Touchdowns ---
    if play.pass_touchdown:
        scores_on_play[play.passer_player_id] += rules.pass_td
        scores_on_play[play.receiver_player_id] += rules.rec_td
    if play.rush_touchdown:
        scores_on_play[play.rusher_player_id] += rules.rush_td
    
    # Return Touchdowns (Kickoff/Punt)
    if (play.kickoff_attempt or play.punt_attempt) and play.return_touchdown:
        return_id = (
            play.kickoff_returner_player_id
            if play.kickoff_returner_player_id
            else play.punt_returner_player_id
        )
        if return_id:
            scores_on_play[return_id] += rules.ret_td

    # --- Yardage ---
    if play.receiving_yards:
        scores_on_play[play.receiver_player_id] += rules.rec_yard * play.receiving_yards
        scores_on_play[play.receiver_player_id] += rules.reception # PPR
        
    if play.passing_yards:
        scores_on_play[play.passer_player_id] += rules.pass_yard * play.passing_yards
        
    if play.rushing_yards:
        scores_on_play[play.rusher_player_id] += rules.rush_yard * play.rushing_yards
        
    if play.kickoff_returner_player_id or play.punt_returner_id:
        # Note: Return yardage scoring isn't in the config yet, defaulting to 0.04 if not specified
        # But for now, let's assume it maps to a field or use hardcoded if missing.
        # The previous code used 0.04. 
        # Let's assume standard leagues don't score return yards, but we should add it to config later.
        # For parity with previous code:
        return_id = (
            play.kickoff_returner_player_id
            if play.kickoff_returner_player_id
            else play.punt_returner_player_id
        )
        # scores_on_play[return_id] += 0.04 * play.return_yards # TODO: Add to settings
        pass 

    # --- Turnovers ---
    if play.interception:
        scores_on_play[play.passer_player_id] += rules.intercept
        scores_on_play[play.defteam] += rules.def_int
        if play.return_touchdown:
            scores_on_play[play.defteam] += rules.def_td
            
    if play.fumble_lost:
        scores_on_play[play.fumbled_1_player_id] += rules.fumble_lost
        # Note: DST fumble recovery points?
        # Previous code: _FUMBLE_RECOVERY: 2
        scores_on_play[play.defteam] += rules.def_fumble_rec

    # --- 2 Point Conversions ---
    if play.two_point_conv_result == "success":
        if not pd.isnull(play.rusher_player_id):
            scores_on_play[play.rusher_player_id] += rules.two_pt_conv
        if not pd.isnull(play.receiver_player_id):
            scores_on_play[play.receiver_player_id] += rules.two_pt_conv
            scores_on_play[play.passer_player_id] += rules.two_pt_conv

    # --- Defense / Special Teams ---
    if play.sack:
        scores_on_play[play.defteam] += rules.def_sack
        scores_on_play[play.passer_player_id] += rules.sack # QB negative points for sack

    if play.field_goal_attempt and play.field_goal_result == "blocked":
        scores_on_play[play.defteam] += rules.def_block

    if play.field_goal_attempt and play.field_goal_result == "made":
        if play.kick_distance <= 39:
            scores_on_play[play.kicker_player_id] += rules.fg_0_39
        elif play.kick_distance <= 49:
            scores_on_play[play.kicker_player_id] += rules.fg_40_49
        else:
            scores_on_play[play.kicker_player_id] += rules.fg_50_plus

    if play.extra_point_attempt and play.extra_point_result == "made":
        scores_on_play[play.kicker_player_id] += rules.pat_made

    if play.safety:
        scores_on_play[play.defteam] += rules.def_safety

    return scores_on_play


def points_from_score(score, rules: ScoringSettings):
    score = int(score)
    if score == 0:
        return rules.pa_0
    elif score < 7:
        return rules.pa_1_6
    elif score < 14:
        return rules.pa_7_13
    elif score < 21:
        return rules.pa_14_20
    elif score < 28:
        return rules.pa_21_27
    elif score < 35:
        return rules.pa_28_34
    else:
        return rules.pa_35_plus