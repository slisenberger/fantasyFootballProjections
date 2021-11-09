import random
import models
from collections import defaultdict


# I think the API I want is something like: result = advance_snap(game_state)
# The gamestate would itself be update, a synthetic play would be generated, and this can be used in
# any sort of projection model we want.
class GameState:
  """Representation of the Game Details of a football game, like down, quarter, and clock."""
  def __init__(self, home_team, away_team, home_player_stats, away_player_stats, home_team_stats, away_team_stats):
      # Names of the participating teams
      self.home_team = home_team
      self.away_team = away_team
      # Current team possessing the ball
      self.posteam = None
      # Current quarter
      self.quarter = 0
      # Current down
      self.down = 1
      self.yds_to_go = 10
      # Time remaining in quarter, in seconds
      self.sec_remaining = 15*60
      self.home_score = 0
      self.away_score = 0
      # A representation of the yard line, where 0 is the home endzone and 100 is the away endzone
      self.yard_line = 50

      # The models used to inform probabilities and choices.
      self.playcall_model = models.playcall.build_or_load_playcall_model()
      self.yac_model = models.receivers.build_or_load_yac_kde()
      self.air_yards_model = models.receivers.build_or_load_air_yards_kde()
      self.rush_model = models.rushers.build_or_load_rush_kde()
      self.completion_model = models.completion.build_or_load_completion_model()
      self.field_goal_model = models.kicking.build_or_load_kicking_model()

      self.game_over = False

      # Set basic data
      self.home_player_stats = home_player_stats
      self.away_player_stats = away_player_stats
      self.home_team_stats = home_team_stats
      self.away_team_stats = away_team_stats
      self.fantasy_points = defaultdict(float)

  def play_game(self):
      self.opening_kickoff()
      while not self.game_over:
          self.advance_snap()

      return self.fantasy_points

  def change_possession(self):
      if self.posteam == self.home_team:
          self.posteam = self.away_team
      else:
          self.posteam = self.home_team

  def opening_kickoff(self):
      self.down = 1
      self.quarter = 1
      self.posteam = random.choice([self.home_team, self.away_team])
      self.second_half_posteam = self.home_team if self.posteam == self.away_team else self.away_team
      self.yard_line = 75


  def kickoff(self):
      self.change_possession()
      self.yard_line = 75
      self.first_down()


  def advance_snap(self):
    playcall = self.choose_playcall()
    player = None
    yards = 0
    td = False
    if playcall == "run":
        carrier = self.choose_carrier()
        player = carrier
        carrier_id = carrier["player_name"].values[0]
        yards = self.compute_carry_yards(carrier)
    if playcall == "pass":
        qb = self.choose_quarterback()
        qb_id = qb["player_name"].values[0]
        # TODO: Estimate sacks and make sure to change outcome for them.
        target = self.choose_target()
        target_id = target["player_name"].values[0]
        player = target
        air_yards = self.compute_air_yards()
        is_complete = self.is_complete(air_yards)

        if is_complete:
            yac = self.compute_yac(target)
            yards = air_yards + yac


    if playcall == "punt":
        self.punt()
        return

    if playcall == "field_goal":
        self.field_goal()
        k = self.choose_kicker()
        return

    k = self.choose_kicker()
    k_id = k["player_name"].values[0]

    if yards > self.yard_line:
      yards = self.yard_line
      self.touchdown()
      td = True

    elif self.yds_to_go < yards:
        self.yard_line -= yards
        self.first_down()
    else:
        self.yard_line -= yards
        if self.down == 4:
            self.turnover_on_downs()
        else:
          self.down = self.down+1
          self.yds_to_go -= yards

    # Count the fantasy points for this play.
    if playcall == "run":
        self.fantasy_points[carrier_id] += .1 * yards
        if td:
            self.fantasy_points[carrier_id] += 6
            # TODO: model this
            self.fantasy_points[k_id] += 1
    if playcall == "pass" and is_complete:
        self.fantasy_points[qb_id] += .04 * yards
        self.fantasy_points[target_id] += .1 * yards
        self.fantasy_points[target_id] += .5
        if td:
            self.fantasy_points[qb_id] += 4
            self.fantasy_points[target_id] += 6
            # TODO: model this
            self.fantasy_points[k_id] += 1

    self.advance_clock()



  def touchdown(self):
      if self.posteam == self.home_team:
          self.home_score += 7
      else:
          self.away_score += 7

      self.kickoff()


  def advance_clock(self):
      self.sec_remaining -= 30
      if self.sec_remaining <= 0:
          if self.quarter == 2:
              self.half_time()
          if self.quarter == 4:
              self.game_end()
          self.quarter += 1
          self.sec_remaining = 15*60

  def game_end(self):
      print("Game is over")
      self.game_over = True
      print("%s %s - %s %s" %(self.home_team, self.home_score, self.away_team, self.away_score))

  def turnover_on_downs(self):
      self.change_possession()
      self.yard_line = 100 - self.yard_line
      self.first_down()


  def first_down(self):
      self.down = 1
      self.yds_to_go = 10 if self.yard_line >= 10 else self.yard_line

  def half_time(self):
      self.posteam = self.second_half_posteam
      self.yard_line = 75
      self.first_down()



  # Choose a play type for this snap
  def choose_playcall(self):
    PASS_INDEX = 1
    RUN_INDEX = 3
    # Baseline -- Use a logistic regression model to choose a playtype.
    model_input = [
        self.down,
        self.yds_to_go,
        self.home_score - self.away_score,
        self.sec_remaining,
        self.quarter,
        self.yard_line]

    base_probs = self.playcall_model.predict_proba([model_input])[0]
    # Adjust probabilities for team trends
    defense_pass_oe = self.get_def_team_stats()["defense_pass_oe"].values[0] / 100.0
    offense_pass_oe = self.get_pos_team_stats()["offense_pass_oe"].values[0] / 100.0
    base_probs[PASS_INDEX] += defense_pass_oe
    base_probs[PASS_INDEX] += offense_pass_oe
    base_probs[RUN_INDEX] -= defense_pass_oe
    base_probs[RUN_INDEX] -= offense_pass_oe

    playcall = random.choices(self.playcall_model.classes_, weights=base_probs, k=1)[0]
    return playcall

  def choose_target(self):
      pos_player_stats = self.get_pos_player_stats()
      eligible_targets = pos_player_stats.loc[pos_player_stats["target_percentage"] > 0][["player_id", "player_name", "target_percentage", "targets", "relative_yac"]]
      target = random.choices(eligible_targets["player_id"].tolist(), weights=eligible_targets["target_percentage"].tolist(), k=1)[0]
      return eligible_targets.loc[eligible_targets["player_id"] == target]

  def choose_carrier(self):
      pos_player_stats = self.get_pos_player_stats()
      eligible_carriers = pos_player_stats.loc[pos_player_stats["carry_percentage"] > 0][[
          "player_id", "player_name", "carry_percentage", "big_carry_percentage",
          "carries", "relative_ypc"]]
      carrier = random.choices(eligible_carriers["player_id"].tolist(), weights=eligible_carriers["carry_percentage"].tolist(), k=1)[0]
      return eligible_carriers.loc[eligible_carriers["player_id"] == carrier]

  def choose_quarterback(self):
      pos_player_stats = self.get_pos_player_stats()
      eligible_qbs = pos_player_stats.loc[pos_player_stats["pass_attempts"] > 0][["player_id", "player_name", "cpoe", "pass_attempts"]]
      qb = eligible_qbs.sort_values(by="pass_attempts", ascending=False).head(1)
      return qb

  def choose_kicker(self):
      pos_player_stats = self.get_pos_player_stats()
      eligible_ks = pos_player_stats.loc[pos_player_stats["kick_attempts"] > 0][
          ["player_id", "player_name", "kick_attempts"]]
      k = eligible_ks.sort_values(by="kick_attempts", ascending=False).head(1)
      return k

  def compute_air_yards(self):
      return self.air_yards_model.sample(n_samples=1)[0][0]

  def compute_yac(self, target):
      yac = self.yac_model.sample(n_samples=1)[0]
      # Come up with a way to handle small sample high yac players
      targets = target["targets"].values[0]
      relative_yac = target["relative_yac"].values[0]
      defense_relative_yac = self.get_def_team_stats()["defense_relative_yac"].values[0]
      yac *= defense_relative_yac
      if targets > 20:
          yac *= relative_yac

      return yac[0]




  def compute_carry_yards(self, carrier):

      carries = carrier["carries"].values[0]
      # TODO: Sample more and keep the largest to simulate big carries for backs who get them.
      yards = self.rush_model.sample(n_samples=1)[0]
      # Come up with a way to handle small sample high yac players

      relative_ypc = carrier["relative_ypc"].values[0]
      defense_relative_ypc = self.get_def_team_stats()["defense_relative_ypc"].values[0]
      yards *= defense_relative_ypc
      if carries > 80:
          yards *= relative_ypc

      return yards[0]


  def punt(self):
      punt_distance = 45
      new_yardline = self.yard_line - punt_distance
      if new_yardline < 0:
          self.yard_line = 75
      else:
          self.yard_line = 100 - new_yardline
      self.change_possession()
      self.down = 1
      self.yds_to_go = 10

  def field_goal(self):
      kicking_yards = self.yard_line + 17
      model_input = [self.home_score - self.away_score, self.sec_remaining, self.quarter, kicking_yards]
      base_probs = self.field_goal_model.predict_proba([model_input])[0]
      good = random.choices(self.field_goal_model.classes_, weights=base_probs, k=1)[0]
      if good:
          k = self.choose_kicker()
          k_id = k["player_name"].values[0]
          if kicking_yards <= 39:
              self.fantasy_points[k_id] += 3
          elif kicking_yards <= 49:
              self.fantasy_points[k_id] += 4
          else:
              self.fantasy_points[k_id] += 5

          if self.posteam == self.home_team:
              self.home_score += 3
          else:
              self.away_score += 3
          self.kickoff()
      else:
          self.turnover_on_downs()



  def get_pos_player_stats(self):
      if self.posteam == self.home_team:
          return self.home_player_stats
      else:
          return self.away_player_stats

  def get_pos_team_stats(self):
      if self.posteam == self.home_team:
          return self.home_team_stats
      else:
          return self.away_team_stats

  def get_def_team_stats(self):
      if self.posteam == self.home_team:
          return self.away_team_stats
      else:
          return self.home_team_stats

  def is_complete(self, air_yards):
      COMPLETE_INDEX = 1
      INCOMPLETE_INDEX = 0
      # Baseline -- Use a logistic regression model to choose a playtype.
      model_input = [
          self.down,
          self.yds_to_go,
          self.yard_line,
          air_yards]

      base_probs = self.completion_model.predict_proba([model_input])[0]

      # Adjust probabilities for team trends
      defense_cpoe = self.get_def_team_stats()["defense_cpoe"].values[0] / 100.0
      base_probs[COMPLETE_INDEX] += defense_cpoe
      base_probs[INCOMPLETE_INDEX] -= defense_cpoe

      # Adjust the completion probability for the active quarterback.
      qb = self.choose_quarterback()
      qb_cpoe = qb["cpoe"].values[0] / 100.0
      base_probs[COMPLETE_INDEX] += qb_cpoe
      base_probs[INCOMPLETE_INDEX] -= qb_cpoe

      complete = random.choices(self.completion_model.classes_, weights=base_probs, k=1)[0]

      return complete


