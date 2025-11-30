import pandas as pd
import random
from collections import defaultdict
from typing import Dict, List, Optional, Any, Tuple
from enums import PlayType, Position
from settings import ScoringSettings
import pandas as pd
import numpy as np # Added

# I think the API I want is something like: result = advance_snap(game_state)
# The gamestate would itself be update, a synthetic play would be generated, and this can be used in
# any sort of projection model we want.
class GameState:
    """Representation of the Game Details of a football game, like down, quarter, and clock.
    
    This class acts as the central engine for the Monte Carlo simulation. It maintains the
    state of the game (score, possession, field position) and orchestrates the transition
    between states by invoking strategies and models.

    Attributes:
        home_team (str): Abbreviation of the home team (e.g., "KC").
        away_team (str): Abbreviation of the away team (e.g., "DET").
        posteam (str): Team currently in possession.
        quarter (int): Current quarter (1-4, 5+ for OT).
        down (int): Current down (1-4).
        yds_to_go (int): Yards required for a first down.
        sec_remaining (int): Seconds remaining in the current quarter.
        home_score (int): Current score for home team.
        away_score (int): Current score for away team.
        yard_line (int): Distance from the home team's endzone (0-100). 
                         0 = Home Endzone, 100 = Away Endzone.
        rules (ScoringSettings): Configuration for fantasy point scoring.
        fantasy_points (DefaultDict[str, float]): Accumulator for fantasy points by player ID.
        play_log (List[Dict]): History of executed plays for auditing/debugging.
    """

    def __init__(
        self,
        models: Dict[str, Any],
        home_team: str,
        away_team: str,
        home_player_stats: pd.DataFrame,
        away_player_stats: pd.DataFrame,
        home_team_stats: pd.DataFrame,
        away_team_stats: pd.DataFrame,
        rules: ScoringSettings,
        game_info: Dict[str, Any] = {},
        trace: bool = False
    ):
        """Initializes the GameState with teams, stats, and models.

        Args:
            models: Dictionary of loaded ML models and KDEs.
            home_team: Home team abbreviation.
            away_team: Away team abbreviation.
            home_player_stats: DataFrame of home player stats/estimators.
            away_player_stats: DataFrame of away player stats/estimators.
            home_team_stats: DataFrame of home team stats (defensive/offensive profiles).
            away_team_stats: DataFrame of away team stats.
            rules: ScoringSettings object defining fantasy point values.
            game_info: Dictionary containing game-specific context (wind, roof, etc).
            trace: If True, records a log of every play.
        """
        # Names of the participating teams
        self.home_team = home_team
        self.away_team = away_team
        # Game Info
        self.wind = game_info.get("wind", 0.0)
        self.is_outdoors = game_info.get("is_outdoors", 1)
        self.vegas_total = game_info.get("total_line", 45.0) # Default for generic game if missing
        self.vegas_spread = game_info.get("spread_line", 0.0) # Default to pick'em if missing
        
        # Drive-specific stats
        self.drive_play_count = 1
        
        # Current team possessing the ball
        self.posteam = None
        # Current quarter
        self.quarter = 0
        # Current down
        self.down = 1
        self.yds_to_go = 10
        # Time remaining in quarter, in seconds
        self.sec_remaining = 15 * 60
        self.home_score = 0
        self.away_score = 0
        # A representation of the yard line, where 0 is the home endzone and 100 is the away endzone
        self.yard_line = 50
        self.rules = rules

        self.completion_model = models["completion_model"]
        self.field_goal_model = models["field_goal_model"]
        self.playcall_model = models["playcall_model"]
        self.clock_model = models.get("clock_model", {})
        
        # Retrieve pre-sampled buffers from models dict (Optimization)
        self.air_yards_samples = {
            Position.RB: models["air_yards_RB_samples"],
            Position.TE: models["air_yards_TE_samples"],
            Position.WR: models["air_yards_WR_samples"],
            "ALL": models["air_yards_ALL_samples"],
        }
        
        self.yac_samples = {}
        for pos in [Position.RB, Position.TE, Position.WR, "ALL"]:
            p_key = pos 
            str_key = pos if pos == "ALL" else pos.name
            self.yac_samples[p_key] = {
                "open": models[f"yac_{str_key}_open_samples"],
                "rz": models[f"yac_{str_key}_rz_samples"]
            }
        
        self.rush_open_samples = models["rush_open_samples"]
        self.rush_rz_samples = models["rush_rz_samples"]
        
        self.scramble_samples = {
            "default": models.get("scramble_samples", []),
            "mobile": models.get("scramble_samples_mobile", []),
            "pocket": models.get("scramble_samples_pocket", [])
        }
        self.int_return_samples = models["int_return_samples"]

        self.game_over = False
        
        # Overtime State
        self.in_overtime = False
        self.ot_possession_count = 0
        self.ot_first_drive_score = 0 # 0=None/Punt, 3=FG
        
        # Diagnostics
        self.trace = trace
        self.play_log = []

        # --- OPTIMIZATION: Pre-cache stats to avoid Pandas overhead in loop ---
        
        # Convert Team Stats DF to Dict for O(1) lookup
        # Expected format: { 'offense_pass_oe_est': val, ... }
        # We assume home_team_stats and away_team_stats are single-row DFs
        
        def df_to_dict(df):
            if df.empty: return {}
            return df.iloc[0].to_dict()

        self.home_team_stats_dict = df_to_dict(home_team_stats)
        self.away_team_stats_dict = df_to_dict(away_team_stats)

        # Pre-filter players by team and position
        
        def get_qbs(df):
            qbs = df.loc[df["position"] == Position.QB]
            # Sort logic from choose_quarterback
            starting = qbs.loc[qbs.starting_qb == 1]
            if len(starting) == 1:
                return starting.to_dict('records')
            return qbs.sort_values(by="pass_attempts", ascending=False).head(1).to_dict('records')

        def get_kickers(df):
            ks = df.loc[df["position"] == Position.K]
            starting = ks.loc[ks.starting_k == 1]
            if len(starting) == 1:
                return starting.to_dict('records')
            return ks.sort_values(by="kick_attempts", ascending=False).head(1).to_dict('records')

        def get_carriers(df, zone="standard"):
            if zone == "goal_line":
                est_col = "goal_line_carry_share_est"
            elif zone == "redzone":
                est_col = "redzone_carry_share_est"
            else:
                est_col = "carry_share_est"
                
            eligible = df.loc[df[est_col] > 0]
            if eligible.empty: return [], []
            # Return list of dicts and list of weights
            records = eligible.to_dict('records')
            weights = [p[est_col] for p in records]
            return records, weights

        def get_targets(df):
            eligible = df.loc[df["target_percentage"] > 0]
            if eligible.empty: return [], []
            records = eligible.to_dict('records')
            weights = [p["target_share_est"] for p in records]
            
            total = sum(weights)
            if total == 0:
                # Fallback if all estimates are 0
                weights = [1.0 for _ in weights]
                total = len(weights)
                
            weights = [w / total for w in weights]
            return records, weights

        self.home_qbs = get_qbs(home_player_stats)
        self.away_qbs = get_qbs(away_player_stats)
        
        self.home_kickers = get_kickers(home_player_stats)
        self.away_kickers = get_kickers(away_player_stats)
        
        self.home_carriers, self.home_carry_weights = get_carriers(home_player_stats, "standard")
        self.away_carriers, self.away_carry_weights = get_carriers(away_player_stats, "standard")
        
        self.home_rz_carriers, self.home_rz_carry_weights = get_carriers(home_player_stats, "redzone")
        self.away_rz_carriers, self.away_rz_carry_weights = get_carriers(away_player_stats, "redzone")
        
        self.home_gl_carriers, self.home_gl_carry_weights = get_carriers(home_player_stats, "goal_line")
        self.away_gl_carriers, self.away_gl_carry_weights = get_carriers(away_player_stats, "goal_line")
        
        self.home_targets, self.home_target_weights = get_targets(home_player_stats)
        self.away_targets, self.away_target_weights = get_targets(away_player_stats)

        self.fantasy_points = defaultdict(float)

    def _get_sample(self, samples: Any) -> float:
        """Fast random access from pre-calculated buffer."""
        # random.choice on numpy array is fast enough for our needs compared to KDE tree traversal
        return random.choice(samples)

    def play_game(self) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
        """Simulates an entire game from kickoff to end.

        Transitions the state through all quarters and overtime until game_over is True.
        Applies end-of-game defensive scoring logic.

        Returns:
            Tuple containing:
                - fantasy_points (Dict[str, float]): Map of player_id to total fantasy points.
                - play_log (List[Dict]): Detailed log of plays (if trace=True).
        """
        self.opening_kickoff()
        while not self.game_over:
            self.advance_snap()
        # Give end-of-game point adjustments for defenses.
        self.fantasy_points[self.home_team] += self.get_defense_score_points(
            self.away_score
        )
        self.fantasy_points[self.away_team] += self.get_defense_score_points(
            self.home_score
        )
        return self.fantasy_points, self.play_log

    def get_defense_score_points(self, score: int) -> float:
        """Calculates fantasy points for a defense based on opponent's final score.
        
        Args:
            score (int): The opponent's final score.

        Returns:
            float: Fantasy points awarded to the defense.
        """
        if score == 0:
            return self.rules.pa_0
        elif score < 7:
            return self.rules.pa_1_6
        elif score < 14:
            return self.rules.pa_7_13
        elif score < 21:
            return self.rules.pa_14_20
        elif score < 28:
            return self.rules.pa_21_27
        elif score < 35:
            return self.rules.pa_28_34
        else:
            return self.rules.pa_35_plus

    def change_possession(self) -> None:
        """Switches possession of the ball to the other team."""
        if self.in_overtime:
            self.ot_possession_count += 1
            
        if self.posteam == self.home_team:
            self.posteam = self.away_team
        else:
            self.posteam = self.home_team

    def opening_kickoff(self) -> None:
        """Initializes the game state for the opening kickoff."""
        self.down = 1
        self.quarter = 1
        self.posteam = random.choice([self.home_team, self.away_team])
        self.second_half_posteam = (
            self.home_team if self.posteam == self.away_team else self.away_team
        )
        self.yard_line = 75

    def start_overtime(self) -> None:
        """Initializes the game state for the start of overtime."""
        self.in_overtime = True
        # self.quarter will be incremented to 5 in advance_clock immediately after this returns
        self.posteam = random.choice([self.home_team, self.away_team])
        self.yard_line = 75
        self.first_down()

    def kickoff(self) -> None:
        """Resets the game state for a kickoff (after a score or start of half/OT)."""
        self.change_possession()
        self.yard_line = 75
        self.first_down()
        self.drive_play_count = 1

    def advance_snap(self) -> None:
        """Executes a single play (snap) and updates the game state.

        Determines the play type (Run/Pass/Kick), selects players involved,
        simulates the outcome (yards, turnover, score), updates field position/clock,
        and accumulates fantasy points.
        """
        playcall = self.choose_playcall()
        is_complete = 0
        yards = 0.0
        air_yards = 0.0
        td = False
        sack = False
        interception = False
        scramble = False
        fumble = False
        carrier_id = None
        target_id = None
        
        # Get team stats dicts for current possession
        pos_stats = self.get_pos_team_stats()
        def_stats = self.get_def_team_stats()

        if playcall == PlayType.RUN:
            carrier = self.choose_carrier()
            if carrier:
                carrier_id = carrier["player_id"]
                yards = self.compute_carry_yards(carrier)
            else:
                yards = 0 # Should not happen if carriers exist
                carrier_id = "Team" # Fallback
            
            # Fumble Logic (Run) - ~0.8% chance
            if random.random() < 0.008:
                fumble = True

        if playcall == PlayType.PASS:
            qb = self.choose_quarterback()
            if qb:
                qb_id = qb["player_id"]
            else:
                qb_id = "QB_%s" % self.posteam
            
            # Average the offensive and defensive sack rates.
            offense_sack_rate = pos_stats.get("offense_sack_rate_est", 0.06)
            defense_sack_rate = def_stats.get("defense_sack_rate_est", 0.06)
            lg_sack_rate = pos_stats.get("lg_sack_rate", 0.06)
            
            sack_rate = compute_odds_ratio(
                offense_sack_rate, defense_sack_rate, lg_sack_rate
            )

            defense_int_rate = def_stats.get("defense_int_rate_est", 0.02)
            
            if random.random() < sack_rate:
                sack = True
                yards = -7
                # Fumble Logic (Sack) - ~0.8% chance
                if random.random() < 0.008:
                    fumble = True

            scramble = not sack and self.is_scramble(qb)
            if scramble:
                yards = self.compute_scramble_yards(qb)

            if not sack and not scramble:
                if random.random() < defense_int_rate:
                    interception = True

                target = self.choose_target()
                if target:
                    target_id = target["player_id"]
                    air_yards = self.compute_air_yards(target)
                    is_complete = int(not interception and self.is_complete(air_yards, target))

                    if is_complete:
                        yac = self.compute_yac(target)
                        yards = air_yards + yac
                else:
                    is_complete = 0

        if playcall == PlayType.PUNT:
            self.punt()
            return

        if playcall == PlayType.FIELD_GOAL:
            self.field_goal()
            return

        k = self.choose_kicker()
        if k:
            k_id = k["player_id"]
        else:
            k_id = "Kicker_%s" % self.posteam

        if interception:
            # Advance the ball the point of the air yards.
            self.yard_line -= air_yards
            # Change possession and return
            self.change_possession()
            
            if self.in_overtime and self.ot_possession_count == 2 and self.ot_first_drive_score == 3:
                self.game_over = True

            return_yards = self._get_sample(self.int_return_samples)
            self.yard_line -= return_yards

            # Handle touchback
            if self.yard_line >= 100:
                self.yard_line = 75

            if self.yard_line <= 0:
                self.touchdown()
                self.fantasy_points[self.posteam] += self.rules.def_td
                td = True
                # Have to do this here because elsewise the kickoff doesn't happen.
                if self.extra_point():
                    self.fantasy_points[k_id] += self.rules.pat_made

            else:
                self.first_down()
        
        # Handle Fumble (Turnover)
        elif fumble:
            self.yard_line -= yards
            self.change_possession()
            
            if self.in_overtime and self.ot_possession_count == 2 and self.ot_first_drive_score == 3:
                self.game_over = True

            self.yard_line = 100 - self.yard_line
            self.first_down()

        # If more yards were gained than remaining yards, touchdown.
        elif yards > self.yard_line:
            yards = self.yard_line
            self.touchdown()
            td = True

        # Tackled for loss into endzone should result in safety.
        elif self.yard_line - yards > 100:
            self.fantasy_points[self.defteam()] += self.rules.def_safety
            self.safety()

        # If more yards were gained than remaining yards
        elif self.yds_to_go <= yards:
            self.yard_line -= yards
            self.first_down()
        else:
            self.yard_line -= yards
            if self.down == 4:
                self.turnover_on_downs()
            else:
                self.down = self.down + 1
                self.yds_to_go -= yards

        # Count the fantasy points for this play.
        if playcall == PlayType.RUN and carrier:
            self.fantasy_points[carrier_id] += self.rules.rush_yard * yards
            
            if td:
                self.fantasy_points[carrier_id] += self.rules.rush_td
                if self.extra_point():
                    self.fantasy_points[k_id] += self.rules.pat_made
        if (playcall == PlayType.PASS) and (not sack) and (not scramble) and (is_complete) and target:
            self.fantasy_points[qb_id] += self.rules.pass_yard * yards
            target_fpts = self.rules.reception
            target_fpts += self.rules.rec_yard * yards
            
            if td:
                self.fantasy_points[qb_id] += self.rules.pass_td
                target_fpts += self.rules.rec_td
                if self.extra_point():
                    self.fantasy_points[k_id] += self.rules.pat_made

            self.fantasy_points[target_id] += target_fpts

        if scramble:
            self.fantasy_points[qb_id] += self.rules.rush_yard * yards
            if td:
                self.fantasy_points[qb_id] += self.rules.rush_td
                if self.extra_point():
                    self.fantasy_points[k_id] += self.rules.pat_made

        if interception:
            self.fantasy_points[qb_id] += self.rules.intercept # usually negative
            self.fantasy_points[self.defteam()] += self.rules.def_int

        if sack:
            self.fantasy_points[self.defteam()] += self.rules.def_sack
            self.fantasy_points[qb_id] += self.rules.sack

        if fumble:
            # Identify fumbler
            if playcall == PlayType.RUN and carrier_id:
                fumbler_id = carrier_id
            elif playcall == PlayType.PASS:
                fumbler_id = qb_id
            else:
                fumbler_id = None # Should be handled if needed, but generic flow covers run/pass

            if fumbler_id:
                self.fantasy_points[fumbler_id] += self.rules.fumble_lost
            
            # Award defense points (defteam here refers to the team ON DEFENSE when fumble occurred? 
            # NO. change_possession was called.
            # self.posteam is now the RECOVERING team (Old Defense).
            # self.defteam() is now the FUMBLING team (Old Offense).
            # So we want to award points to self.posteam.
            self.fantasy_points[self.posteam] += self.rules.def_fumble_rec

        if self.trace:
            pid = None
            if playcall == PlayType.PASS and target_id: pid = target_id
            if playcall == PlayType.RUN and carrier_id: pid = carrier_id
            
            self.play_log.append({
                'qtr': self.quarter,
                'time': self.sec_remaining,
                'down': self.down,
                'dist': self.yds_to_go,
                'score_diff': self.score_differential(),
                'play_type': playcall.name,
                'yards': yards,
                'is_complete': is_complete,
                'player_id': pid,
                'drive_play_count': self.drive_play_count # Add to log
            })

        self.advance_clock(playcall, sack, is_complete, scramble)
        self.drive_play_count += 1 # Increment after play

    def extra_point(self) -> bool:
        """Simulates an extra point attempt.

        Returns:
            bool: True if the extra point is good, False otherwise.
        """
        # Arbitrary value chosen from google. In future, compute this from lg avg or model.
        chance = 0.93
        good = False
        if random.random() < chance:
            if self.posteam == self.home_team:
                self.home_score += 1
            else:
                self.away_score += 1
            good = True

        self.kickoff()
        return good

    def extra_point(self) -> bool:
        """Simulates an extra point attempt.

        Returns:
            bool: True if the extra point is good, False otherwise.
        """
        # Arbitrary value chosen from google. In future, compute this from lg avg or model.
        chance = 0.93
        good = False
        if random.random() < chance:
            if self.posteam == self.home_team:
                self.home_score += 1
            else:
                self.away_score += 1
            good = True

        self.kickoff()
        return good

    def touchdown(self) -> None:
        """Updates game state and score for a touchdown."""
        if self.posteam == self.home_team:
            self.home_score += 6
        else:
            self.away_score += 6
            
        if self.in_overtime:
            self.game_over = True

    def safety(self) -> None:
        """Updates game state and score for a safety."""
        # Give 2 points to the team that does not have the ball.
        if self.posteam == self.home_team:
            self.away_score += 2
        else:
            self.home_score += 2
            
        if self.in_overtime:
            self.game_over = True

        self.kickoff()

    # Manage the clock using empirical runoff data
    def advance_clock(self, playcall: PlayType, sack: bool, is_complete: int, scramble: bool) -> None:
        """Advances the game clock based on play outcome and game situation.

        Uses a clock model to determine empirical runoff for plays, with fallback logic.
        Handles quarter transitions, half time, and game end conditions.

        Args:
            playcall (PlayType): The type of play that just occurred.
            sack (bool): True if the play was a sack.
            is_complete (int): 1 if pass was complete, 0 otherwise.
            scramble (bool): True if the play was a QB scramble.
        """
        original_sec_remaining = self.sec_remaining
        
        # Determine Buckets
        qtr_bucket = 'OT' if self.quarter >= 5 else ('Q4' if self.quarter == 4 else 'regulation')
        
        if self.sec_remaining > 300: time_bucket = 'high'
        elif self.sec_remaining > 120: time_bucket = 'mid'
        else: time_bucket = 'low'
        
        diff = self.score_differential()
        if diff >= 9: score_bucket = 'leading_big'
        elif diff > 0: score_bucket = 'leading_close'
        elif diff == 0: score_bucket = 'tied'
        elif diff > -9: score_bucket = 'trailing_close'
        else: score_bucket = 'trailing_big'
        
        # Determine Play Type Detail
        if playcall == PlayType.PASS:
            if sack: play_type_detail = 'pass_complete' # Sack keeps clock running like complete
            elif is_complete: play_type_detail = 'pass_complete'
            else: play_type_detail = 'pass_incomplete'
        elif playcall == PlayType.RUN:
            play_type_detail = 'run'
        elif playcall == PlayType.PUNT:
            play_type_detail = 'punt'
        elif playcall == PlayType.FIELD_GOAL:
            play_type_detail = 'field_goal'
        else:
            play_type_detail = 'run'

        # Lookup
        runoff = self.clock_model.get((qtr_bucket, time_bucket, score_bucket, play_type_detail))
        
        if runoff is not None:
            self.sec_remaining -= runoff
        else:
            # Fallback (Original Logic)
            if playcall == PlayType.PASS and not is_complete and not sack and not scramble:
                self.sec_remaining -= 5
            elif playcall == PlayType.FIELD_GOAL:
                self.sec_remaining -= 5
            elif playcall == PlayType.PUNT:
                self.sec_remaining -= 5
            else:
                clock_burn = 0
                if self.quarter == 4:
                    if self.is_winning(self.posteam):
                        clock_burn = 45
                    else:
                        if self.sec_remaining < 5 * 60:
                            clock_burn = 10
                        else:
                            clock_burn = 30
                else:
                    clock_burn = 35
                self.sec_remaining -= clock_burn

        # Check for the 2 minute warning.
        if self.quarter in [2, 4] and (
            self.sec_remaining < 120 and original_sec_remaining > 120
        ):
            self.sec_remaining = 120
        # Check for the end of quarters.
        if self.sec_remaining <= 0:
            if self.quarter == 2:
                self.half_time()
            elif self.quarter == 4:
                if self.home_score != self.away_score:
                    self.game_end()
                else:
                    self.start_overtime()
            elif self.quarter >= 5:
                self.game_end()
            
            if not self.game_over:
                self.quarter += 1
                if self.quarter <= 4:
                    self.sec_remaining = 15 * 60
                else:
                    self.sec_remaining = 10 * 60 # 10 min OT

    def is_winning(self, team: str) -> bool:
        """Determines if the specified team is currently winning.

        Args:
            team (str): The team abbreviation to check.

        Returns:
            bool: True if the team is winning, False otherwise.
        """
        if self.home_team == team:
            return self.home_score > self.away_score
        else:
            return self.away_score > self.home_score

    def game_end(self) -> None:
        """Sets the game_over flag to True, ending the simulation."""
        self.game_over = True

    def turnover_on_downs(self) -> None:
        """Handles a turnover on downs, changing possession and field position."""
        self.change_possession()
        
        if self.in_overtime and self.ot_possession_count == 2 and self.ot_first_drive_score == 3:
            self.game_over = True

        self.yard_line = 100 - self.yard_line
        self.first_down()
        self.drive_play_count = 1

    def first_down(self):
        """Resets down and distance for a first down."""
        self.down = 1
        self.yds_to_go = 10 if self.yard_line >= 10 else self.yard_line
        self.drive_play_count = 1

    def half_time(self) -> None:
        """Handles half-time procedures, including possession change and field position reset."""
        self.posteam = self.second_half_posteam
        self.yard_line = 75
        self.first_down()

    def score_differential(self):
        """Calculates the score differential from the perspective of the team with possession."""
        pos_score = (
            self.home_score if self.posteam == self.home_team else self.away_score
        )
        def_score = (
            self.home_score if self.posteam == self.away_team else self.away_score
        )
        return pos_score - def_score

    # Choose a play type for this snap
    def choose_playcall(self) -> PlayType:
        """Predicts the next play type (Run, Pass, Punt, FG) using the playcall model.

        Combines the ML model's base probability with contextual adjustments (team tendencies).

        Returns:
            PlayType: The selected play type enum.
        """
        PASS_INDEX = 1
        RUN_INDEX = 3
        # Baseline -- Use a logistic regression model to choose a playtype.
        
        model_input = [
            self.down,
            self.yds_to_go,
            self.score_differential(),
            self.sec_remaining,
            self.quarter,
            self.yard_line,
            self.vegas_total,
            self.vegas_spread,
            self.drive_play_count,
        ]
        try:
            base_probs = self.playcall_model.predict_proba([model_input])[0]
        except ValueError:
            print("posteam: %s\ninput: %s" % (self.posteam, model_input))
        # Adjust probabilities for team trends
        
        pos_stats = self.get_pos_team_stats()
        def_stats = self.get_def_team_stats()
        
        defense_pass_oe = def_stats.get("defense_pass_oe_est", 0.0) / 100.0
        offense_pass_oe = pos_stats.get("offense_pass_oe_est", 0.0) / 100.0

        base_probs[PASS_INDEX] += defense_pass_oe
        base_probs[PASS_INDEX] += offense_pass_oe
        base_probs[RUN_INDEX] -= defense_pass_oe
        base_probs[RUN_INDEX] -= offense_pass_oe

        # NEW: 4th Down Aggressiveness Adjustment
        if self.down == 4:
            go_for_it_oe = pos_stats.get("offense_go_for_it_rate_est", 0.0)
            
            # Map classes to indices dynamically
            classes = list(self.playcall_model.classes_)
            fg_idx = classes.index('field_goal')
            pass_idx = classes.index('pass')
            punt_idx = classes.index('punt')
            run_idx = classes.index('run')

            p_run_pass_combined = base_probs[run_idx] + base_probs[pass_idx]
            p_fg_punt_combined = base_probs[fg_idx] + base_probs[punt_idx]
            
            # Ensure no division by zero if all probabilities for a group are zero
            run_pass_ratio = base_probs[run_idx] / p_run_pass_combined if p_run_pass_combined > 0 else 0.5
            pass_run_ratio = base_probs[pass_idx] / p_run_pass_combined if p_run_pass_combined > 0 else 0.5
            fg_punt_ratio_fg = base_probs[fg_idx] / p_fg_punt_combined if p_fg_punt_combined > 0 else 0.5
            fg_punt_ratio_punt = base_probs[punt_idx] / p_fg_punt_combined if p_fg_punt_combined > 0 else 0.5


            # Shift amount is proportional to the OE value. Max shift could be 1.0 (100%)
            # We scale it down to prevent over-adjustment, e.g., max 20% shift
            scaled_shift_amount = go_for_it_oe * 0.2 # Tune this scaling factor (e.g., 0.2)
            
            # Always operate on probabilities directly and ensure they stay within [0, 1]
            if scaled_shift_amount > 0: # More aggressive: shift from FG/Punt to Run/Pass
                
                # Max amount we can take from FG/Punt side
                max_take = p_fg_punt_combined
                
                # Actual amount to shift, limited by max_take
                actual_shift = min(scaled_shift_amount, max_take)
                
                # Apply the shift
                base_probs[run_idx] += actual_shift * run_pass_ratio
                base_probs[pass_idx] += actual_shift * pass_run_ratio
                base_probs[fg_idx] -= actual_shift * fg_punt_ratio_fg
                base_probs[punt_idx] -= actual_shift * fg_punt_ratio_punt
                
            elif scaled_shift_amount < 0: # More conservative: shift from Run/Pass to FG/Punt
                
                # Max amount we can take from Run/Pass side
                max_take = p_run_pass_combined
                
                # Actual amount to shift, limited by max_take
                actual_shift = min(abs(scaled_shift_amount), max_take)
                
                # Apply the shift
                base_probs[run_idx] -= actual_shift * run_pass_ratio
                base_probs[pass_idx] -= actual_shift * pass_run_ratio
                base_probs[fg_idx] += actual_shift * fg_punt_ratio_fg
                base_probs[punt_idx] += actual_shift * fg_punt_ratio_punt
            
            # Ensure probabilities sum to 1 and are not negative after adjustments
            base_probs = np.clip(base_probs, 0, None) # Ensure no negative probabilities
            base_probs = base_probs / np.sum(base_probs) # Re-normalize
            
        playcall_str = random.choices(
            self.playcall_model.classes_,
            weights=base_probs,
            k=1
        )[0]
        
        if playcall_str == "pass": return PlayType.PASS
        if playcall_str == "run": return PlayType.RUN
        if playcall_str == "punt": return PlayType.PUNT
        if playcall_str == "field_goal": return PlayType.FIELD_GOAL
        
        return PlayType.RUN

    def choose_target(self) -> Optional[Dict[str, Any]]:
        """Selects a receiver to target based on their target share.

        Returns:
            Optional[Dict[str, Any]]: Dictionary of the chosen target's stats, or None if no candidates.
        """
        if self.posteam == self.home_team:
            candidates = self.home_targets
            weights = self.home_target_weights
        else:
            candidates = self.away_targets
            weights = self.away_target_weights
            
        if not candidates:
            return None

        target = random.choices(candidates, weights=weights, k=1)[0]
        return target

    def is_scramble(self, qb: Optional[Dict[str, Any]]) -> bool:
        """Determines if the quarterback scrambles on a pass play.

        Args:
            qb (Optional[Dict[str, Any]]): Dictionary of the quarterback's stats.

        Returns:
            bool: True if the QB scrambles, False otherwise.
        """
        if not qb: return False
        scramble_rate = qb.get("scramble_rate_est", 0)
        return random.random() < scramble_rate

    def choose_carrier(self):
        """Selects a ball carrier based on their carry share.

        Returns:
            Optional[Dict[str, Any]]: Dictionary of the chosen carrier's stats, or None if no candidates.
        """
        # Determine dist to goal to check Red Zone / Goal Line
        if self.posteam == self.home_team:
            dist_to_goal = 100 - self.yard_line
        else:
            dist_to_goal = self.yard_line
            
        if self.posteam == self.home_team:
            if dist_to_goal <= 3:
                candidates = self.home_gl_carriers
                weights = self.home_gl_carry_weights
            elif dist_to_goal <= 20:
                candidates = self.home_rz_carriers
                weights = self.home_rz_carry_weights
            else:
                candidates = self.home_carriers
                weights = self.home_carry_weights
        else:
            if dist_to_goal <= 3:
                candidates = self.away_gl_carriers
                weights = self.away_gl_carry_weights
            elif dist_to_goal <= 20:
                candidates = self.away_rz_carriers
                weights = self.away_rz_carry_weights
            else:
                candidates = self.away_carriers
                weights = self.away_carry_weights
            
        if not candidates:
            return None

        # If all weights are zero, use equal weights to prevent ValueError
        # Replace NaN weights with 0 before summing
        weights = [0.0 if pd.isna(w) else w for w in weights]

        if sum(weights) == 0:
            weights = [1.0 for _ in weights]
            
        carrier = random.choices(candidates, weights=weights, k=1)[0]
        return carrier

    def choose_quarterback(self) -> Optional[Dict[str, Any]]:
        """Selects the starting quarterback for the current possession.

        Returns:
            Optional[Dict[str, Any]]: Dictionary of the chosen quarterback's stats, or None if no QBs.
        """
        if self.posteam == self.home_team:
            qbs = self.home_qbs
        else:
            qbs = self.away_qbs
            
        if not qbs:
            return None
        return qbs[0] # Assuming we pre-filtered to 1 QB

    def choose_kicker(self) -> Optional[Dict[str, Any]]:
        """Selects the starting kicker for the current possession.

        Returns:
            Optional[Dict[str, Any]]: Dictionary of the chosen kicker's stats, or None if no kickers.
        """
        if self.posteam == self.home_team:
            ks = self.home_kickers
        else:
            ks = self.away_kickers
            
        if not ks:
            return None
        return ks[0]

    def compute_air_yards(self, target: Dict[str, Any]) -> float:
        """Simulates air yards for a pass play.

        Adjusts the sampled air yards based on player skill (relative air yards estimator)
        and defensive scheme (relative air yards allowed).

        Args:
            target (Dict[str, Any]): Dictionary of the target player's stats.

        Returns:
            float: Simulated air yards for the play.
        """
        pos = target["position"]
        # Use special position trained models at first, before adjusting.

        if pos in [Position.WR, Position.RB, Position.TE]:
            base = self._get_sample(self.air_yards_samples[pos])
        else:
            base = self._get_sample(self.air_yards_samples["ALL"])

        orig_base = base
        defense_relative_air_yards = self.get_def_team_stats().get(
            "defense_relative_air_yards", 1.0
        )
        
        AIR_YARDS_SHIFT = 15.0
        # Shifted Multiplicative Scaling
        # Allows RBs with negative avg air yards to be scaled correctly relative to a negative baseline,
        # without flipping positive samples into massive negatives.
        
        if (base + AIR_YARDS_SHIFT) > 0:
            player_multiplier = target.get("relative_air_yards_est", 1.0)
            base = ((base + AIR_YARDS_SHIFT) * player_multiplier) - AIR_YARDS_SHIFT
            
            # In red zone offense, stop applying team air yards multipliers.
            if self.yard_line >= 20:
                base *= defense_relative_air_yards

        # If the total is too high to be realistic for the back of the end zone, cap it at max end zone.
        if self.yard_line - base <= -10:
            return self.yard_line + 10

        return base

    def compute_yac(self, target: Dict[str, Any]) -> float:
        """Simulates yards after catch (YAC) for a pass completion.

        Adjusts the sampled YAC based on player skill (relative YAC estimator)
        and defensive scheme (relative YAC allowed).

        Args:
            target (Dict[str, Any]): Dictionary of the chosen target's stats.

        Returns:
            float: Simulated yards after catch.
        """
        pos = target["position"]
        if pos not in [Position.WR, Position.RB, Position.TE]:
            pos = "ALL"
            
        # Experiment: Use Open Field YAC for ALL situations to un-censor potential.
        # We rely on the engine's mechanical cap (yard_line) to handle the Red Zone constraint.
        yac = self._get_sample(self.yac_samples[pos]["open"])
        
        # Come up with a way to handle small sample high yac players
        relative_yac_est = target.get("relative_yac_est", 1.0)
        defense_relative_yac = self.get_def_team_stats().get(
            "defense_relative_yac_est", 1.0
        )
        if yac > 0:
            yac *= defense_relative_yac
            yac *= relative_yac_est
        return yac

    def compute_carry_yards(self, carrier: Dict[str, Any]) -> float:
        """Simulates rushing yards for a run play.

        Adjusts the sampled rushing yards based on player skill (relative YPC estimator)
        and defensive strength (relative YPC allowed). Distinguishes between open field
        and red zone carries.

        Args:
            carrier (Dict[str, Any]): Dictionary of the ball carrier's stats.

        Returns:
            float: Simulated rushing yards.
        """
        # Determine dist to goal to check Red Zone
        if self.posteam == self.home_team:
            dist_to_goal = 100 - self.yard_line
        else:
            dist_to_goal = self.yard_line
            
        # Red Zone is <= 20 yards. Sample from appropriate KDE.
        if dist_to_goal <= 20:
            yards = self._get_sample(self.rush_rz_samples)
        else:
            yards = self._get_sample(self.rush_open_samples)
        
        relative_ypc_est = carrier.get("relative_ypc_est", 1.0)
        defense_relative_ypc = self.get_def_team_stats().get(
            "defense_relative_ypc_est", 1.0
        )
        yards *= defense_relative_ypc
        
        return yards

    def compute_scramble_yards(self, qb: Dict[str, Any]) -> float:
        """Simulates rushing yards for a quarterback scramble.

        Adjusts the sampled scramble yards based on the QB's relative scramble efficiency.
        Uses split KDEs (mobile vs pocket) if available.

        Args:
            qb (Dict[str, Any]): Dictionary of the quarterback's stats.

        Returns:
            float: Simulated scramble yards.
        """
        is_mobile = qb.get("is_mobile", 0) == 1
        key = "mobile" if is_mobile else "pocket"
        samples = self.scramble_samples.get(key)
        
        # Fallback to default if specific samples are missing or empty
        if samples is None or len(samples) == 0:
             samples = self.scramble_samples.get("default")

        yards = self._get_sample(samples)
        multiplier = qb.get("relative_yards_per_scramble_est", 1.0)
        yards *= multiplier
        return yards

    def punt(self) -> None:
        """Simulates a punt play, updating field position and possession."""
        punt_distance = 45
        new_yardline = self.yard_line - punt_distance
        if new_yardline < 0:
            self.yard_line = 75
        else:
            self.yard_line = 100 - new_yardline
        self.change_possession()
        self.down = 1
        self.yds_to_go = 10

    def field_goal(self) -> None:
        """Simulates a field goal attempt.

        Determines outcome (good/no good) using a field goal model and updates score/possession.
        """
        kicking_yards = self.yard_line + 17
        
        model_input = [
            self.home_score - self.away_score,
            self.sec_remaining,
            self.quarter,
            kicking_yards,
            self.wind,
            self.is_outdoors
        ]
        base_probs = self.field_goal_model.predict_proba([model_input])[0]
        
        # FGOE Adjustment
        k = self.choose_kicker()
        try:
            classes = list(self.field_goal_model.classes_)
            made_idx = classes.index('made')
            
            if k:
                fgoe = k.get("fgoe_est", 0.0)
                # Add fgoe to 'made' probability
                p_made = base_probs[made_idx]
                new_p_made = max(0.0, min(1.0, p_made + fgoe))
                
                # Redistribute difference to other classes
                if p_made < 1.0:
                    factor = (1 - new_p_made) / (1 - p_made)
                    base_probs = base_probs * factor
                    base_probs[made_idx] = new_p_made
        except ValueError:
            pass # 'made' not found in classes

        good = random.choices(self.field_goal_model.classes_, weights=base_probs, k=1)[
            0
        ]
        if good == 'made':
            if k:
                try:
                    k_id = k["player_id"]
                except (IndexError, TypeError):
                    k_id = "Kicker_%s" % self.posteam
                
                if kicking_yards <= 39:
                    self.fantasy_points[k_id] += self.rules.fg_0_39
                elif kicking_yards <= 49:
                    self.fantasy_points[k_id] += self.rules.fg_40_49
                else:
                    self.fantasy_points[k_id] += self.rules.fg_50_plus

            if self.posteam == self.home_team:
                self.home_score += 3
            else:
                self.away_score += 3
            
            if self.in_overtime:
                if self.ot_possession_count == 0:
                    self.ot_first_drive_score = 3
                    self.kickoff()
                elif self.ot_possession_count == 1:
                    if self.ot_first_drive_score == 3:
                        self.kickoff() # Tied again (sudden death next)
                    else:
                        self.game_over = True # We scored, they didn't
                else:
                    self.game_over = True # Sudden death
            else:
                self.kickoff()
        else:
            if self.in_overtime and self.ot_possession_count == 1 and self.ot_first_drive_score == 3:
                 self.game_over = True # Chasing team missed
            self.turnover_on_downs()

    def get_pos_player_stats(self):
        """Retrieves the player statistics DataFrame for the team currently in possession.

        This method might be deprecated if we use cached lists directly within the class
        to avoid Pandas overhead in hot loops.

        Returns:
            pd.DataFrame: DataFrame of player stats for the possessing team.
        """
        # This method might be deprecated if we use cached lists directly
        # But keeping for safety if other methods use it.
        # Ideally, we shouldn't call this in hot loops.
        if self.posteam == self.home_team:
            return self.home_player_stats
        else:
            return self.away_player_stats

    def get_pos_team_stats(self):
        """Retrieves the team statistics dictionary for the team currently in possession.

        Returns:
            Dict[str, Any]: Dictionary of team statistics.
        """
        if self.posteam == self.home_team:
            return self.home_team_stats_dict
        else:
            return self.away_team_stats_dict

    def get_def_team_stats(self):
        """Retrieves the team statistics dictionary for the team currently on defense.

        Returns:
            Dict[str, Any]: Dictionary of team statistics.
        """
        if self.posteam == self.home_team:
            return self.away_team_stats_dict
        else:
            return self.home_team_stats_dict

    def is_complete(self, air_yards: float, target: Dict[str, Any]) -> int:
        """Determines if a pass is complete or incomplete.

        Uses a completion model, adjusted by quarterback and receiver CPOE estimators,
        and defensive CPOE suppression.

        Args:
            air_yards (float): The air yards simulated for the pass.
            target (Dict[str, Any]): Dictionary of the target player's stats.

        Returns:
            int: 1 if the pass is complete, 0 if incomplete.
        """
        COMPLETE_INDEX = 1
        INCOMPLETE_INDEX = 0
        # Baseline -- Use a logistic regression model to choose a playtype.
        model_input = [self.down, self.yds_to_go, self.yard_line, air_yards, self.wind, self.is_outdoors]

        base_probs = self.completion_model.predict_proba([model_input])[0]

        # Adjust probabilities for team trends
        defense_cpoe = self.get_def_team_stats().get("defense_cpoe_est", 0.0) / 100.0
        # base_probs[COMPLETE_INDEX] += defense_cpoe
        # base_probs[INCOMPLETE_INDEX] -= defense_cpoe

        # Adjust the completion probability for the active quarterback.
        qb = self.choose_quarterback()
        if qb:
            qb_cpoe = qb.get("cpoe_est", 0.0) / 100.0
        else:
            qb_cpoe = 0

        target_cpoe = target.get("receiver_cpoe_est", 0.0) / 100.0
        # TODO: Find a less arbitrary way of assigning credit to qb and receiver
        offense_cpoe = 0.75 * qb_cpoe + 0.25 * target_cpoe
        offense_comp = base_probs[COMPLETE_INDEX] + offense_cpoe
        defense_comp = base_probs[COMPLETE_INDEX] + defense_cpoe
        est_comp = compute_odds_ratio(
            offense_comp, defense_comp, base_probs[COMPLETE_INDEX]
        )
        base_probs[COMPLETE_INDEX] = est_comp
        base_probs[INCOMPLETE_INDEX] = 1 - est_comp

        complete = random.choices(
            self.completion_model.classes_,
            weights=base_probs,
            k=1
        )[0]

        return complete

    def defteam(self) -> str:
        """Returns the abbreviation of the team currently on defense.

        Returns:
            str: Team abbreviation (e.g., "KC").
        """
        if self.posteam == self.home_team:
            return self.home_team
        else:
            return self.away_team


def compute_odds_ratio(p1: float, p2: float, lg: float) -> float:
    """Computes an adjusted probability using an odds ratio blending method.

    Blends a player/team specific probability (p1) with a defensive probability (p2)
    relative to a league average (lg). This smooths out extreme values and prevents
    double-counting.

    Args:
        p1 (float): Player/team specific probability.
        p2 (float): Opponent specific probability.
        lg (float): League average probability.

    Returns:
        float: The blended probability.
    """
    epsilon = 1e-4
    p1 = max(epsilon, min(1 - epsilon, p1))
    p2 = max(epsilon, min(1 - epsilon, p2))
    lg = max(epsilon, min(1 - epsilon, lg))

    odds_ratio_p1 = p1 / (1 - p1)
    odds_ratio_p2 = p2 / (1 - p2)
    odds_ratio_lg = lg / (1 - lg)
    or_factor = odds_ratio_p1 * odds_ratio_p2 / odds_ratio_lg
    return or_factor / (1 + or_factor)
