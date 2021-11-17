import random
from collections import defaultdict


# I think the API I want is something like: result = advance_snap(game_state)
# The gamestate would itself be update, a synthetic play would be generated, and this can be used in
# any sort of projection model we want.
class GameState:
  """Representation of the Game Details of a football game, like down, quarter, and clock."""
  def __init__(self, models, home_team, away_team, home_player_stats, away_player_stats, home_team_stats, away_team_stats):
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

      self.completion_model = models["completion_model"]
      self.field_goal_model = models["field_goal_model"]
      self.playcall_model = models["playcall_model"]
      self.yac_model = models["yac_model"]
      self.air_yards_models = {
          'RB': models["RB"],
          'TE': models["TE"],
          "WR": models["WR"],
          "ALL": models["ALL"],
      }
      self.rush_model = models["rush_model"]
      self.int_return_model = models["int_return_model"]


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
      # Give end-of-game point adjustments for defenses.
      self.fantasy_points[self.home_team] += self.get_defense_score_points(self.away_score)
      self.fantasy_points[self.away_team] += self.get_defense_score_points(self.home_score)
      return self.fantasy_points

  def get_defense_score_points(self, score):
      if score == 0:
          return 10
      elif score < 7:
          return 7
      elif score < 14:
          return 4
      elif score < 21:
          return 1
      elif score < 28:
          return 0
      elif score < 35:
          return -1
      else:
          return -4



      return points


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
    is_complete = False
    yards = 0
    td = False
    sack = False
    interception = False
    if playcall == "run":
        carrier = self.choose_carrier()
        carrier_id = carrier["player_id"].values[0]
        yards = self.compute_carry_yards(carrier)
    if playcall == "pass":
        qb = self.choose_quarterback()
        try:
            qb_id = qb["player_id"].values[0]
        except IndexError:
            qb_id = "QB_%s" % self.posteam
        offense_sack_rate = self.get_pos_team_stats()["offense_sacks_per_dropback"].values[0]
        defense_int_rate = self.get_def_team_stats()["defense_int_rate_est"].values[0]
        if random.random() < offense_sack_rate:
            sack = True
            yards = -7


        if not sack:
            if random.random() < defense_int_rate:
                interception = True

            target = self.choose_target()
            target_id = target["player_id"].values[0]

            air_yards = self.compute_air_yards(target)

            if random.random() < defense_int_rate:
                interception = True

            is_complete = not interception and self.is_complete(air_yards)

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
    try:
      k_id = k["player_id"].values[0]
    except IndexError:
      k_id = "Kicker_%s" % self.posteam

    # TODO: Handle return yards. currenly assumes no return.
    if interception:
        # Advance the ball the point of the air yards.
        self.yard_line -= yards
        # Change possession and return
        self.change_possession()
        return_yards = self.int_return_model.sample(n_samples=1)[0][0]
        self.yard_line -= return_yards

        # Handle touchback
        if self.yard_line >= 100:
            self.yard_line = 75

        if self.yard_line <= 0:
            self.touchdown()
            self.fantasy_points[self.posteam] += 6
            td = True

        else:
            self.first_down()

    # If more yards were gained than remaining yards, touchdown.
    elif yards > self.yard_line:
      yards = self.yard_line
      self.touchdown()
      td = True

    # Tackled for loss into endzone should result in safety.
    elif self.yard_line - yards > 100:
        self.fantasy_points[self.defteam()] += 2
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
          self.down = self.down+1
          self.yds_to_go -= yards

    # Count the fantasy points for this play.
    if playcall == "run":
        self.fantasy_points[carrier_id] += .1 * yards
        if td:
            self.fantasy_points[carrier_id] += 6
            if self.extra_point():
            # TODO: model this
              self.fantasy_points[k_id] += 1
    if playcall == "pass" and not sack and is_complete:
        self.fantasy_points[qb_id] += .04 * yards
        self.fantasy_points[target_id] += .1 * yards
        self.fantasy_points[target_id] += .5
        if td:
            self.fantasy_points[qb_id] += 4
            self.fantasy_points[target_id] += 6
            if self.extra_point():
            # TODO: model this
              self.fantasy_points[k_id] += 1
    if interception:
        self.fantasy_points[qb_id] -= 1.5
        self.fantasy_points[self.defteam()] += 2

    if sack:
        self.fantasy_points[self.defteam()] += 1


    self.advance_clock(playcall, sack, is_complete)

  def extra_point(self):
      # Arbitrary value chosen from google. In future, compute this from lg avg or model.
      chance = .93
      good = False
      if random.random() < chance:
          if self.posteam == self.home_team:
              self.home_score += 1
          else:
              self.away_score += 1
          good = True

      self.kickoff()
      return good

  def touchdown(self):
      if self.posteam == self.home_team:
          self.home_score += 6
      else:
          self.away_score += 6



  def safety(self):
      # Give 2 points to the team that does not have the ball.
      if self.posteam == self.home_team:
          self.away_score += 2
      else:
          self.home_score += 2

      self.kickoff()



  # Manage the clock after a play. This is very unsophisticated.
  # Areas of improvement:
  # - Modeling getting out of bounds in 4th quarter situations
  # - Modeling timeouts and hurry-up situations
  # - Modeling spikes and kneels
  # - Modeling clock loss due to penalities
  def advance_clock(self, playcall, sack, is_complete):
      original_sec_remaining = self.sec_remaining
      if playcall == "pass" and not is_complete and not sack:
          self.sec_remaining -= 5
      elif playcall == "field_goal":
          self.sec_remaining -= 5
      elif playcall == "punt":
          self.sec_remaining -= 5
      else:
          self.sec_remaining -= 35

      # Check for the 2 minute warning.
      if self.quarter in [2,4] and (self.sec_remaining < 120 and original_sec_remaining > 120):
          self.sec_remaining = 120
      # Check for the end of quarters.
      if self.sec_remaining <= 0:
          if self.quarter == 2:
              self.half_time()
          if self.quarter == 4:
              self.game_end()
          self.quarter += 1
          self.sec_remaining = 15*60

  def game_end(self):
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
    defense_pass_oe = self.get_def_team_stats()["defense_pass_oe_est"].values[0] / 100.0
    offense_pass_oe = self.get_pos_team_stats()["offense_pass_oe_est"].values[0] / 100.0
    base_probs[PASS_INDEX] += defense_pass_oe
    base_probs[PASS_INDEX] += offense_pass_oe
    base_probs[RUN_INDEX] -= defense_pass_oe
    base_probs[RUN_INDEX] -= offense_pass_oe

    playcall = random.choices(self.playcall_model.classes_, weights=base_probs, k=1)[0]
    return playcall

  def choose_target(self):
      pos_player_stats = self.get_pos_player_stats()
      eligible_targets = pos_player_stats.loc[pos_player_stats["target_percentage"] > 0][
          ["player_id", "player_name", "position", "relative_air_yards_est", "target_share_est",
           "targets", "relative_yac", "relative_yac_est", "receiver_cpoe_est"]]
      target = random.choices(eligible_targets["player_id"].tolist(), weights=eligible_targets["target_share_est"].tolist(), k=1)[0]
      return eligible_targets.loc[eligible_targets["player_id"] == target]

  def choose_carrier(self):
      pos_player_stats = self.get_pos_player_stats()
      eligible_carriers = pos_player_stats.loc[pos_player_stats["carry_percentage"] > 0][[
          "player_id", "player_name", "carry_share_est", "big_carry_percentage",
          "carries", "relative_ypc", "relative_ypc_est"]]
      carrier = random.choices(eligible_carriers["player_id"].tolist(), weights=eligible_carriers["carry_share_est"].tolist(), k=1)[0]
      return eligible_carriers.loc[eligible_carriers["player_id"] == carrier]

  def choose_quarterback(self):
      pos_player_stats = self.get_pos_player_stats()
      eligible_qbs = pos_player_stats.loc[pos_player_stats["position"] == "QB"][["player_id", "player_name", "cpoe_est", "pass_attempts"]]
      qb = eligible_qbs.sort_values(by="pass_attempts", ascending=False).head(1)
      return qb

  def choose_kicker(self):
      pos_player_stats = self.get_pos_player_stats()
      eligible_ks = pos_player_stats.loc[pos_player_stats["position"] == "K"][
          ["player_id", "player_name", "kick_attempts"]]
      k = eligible_ks.sort_values(by="kick_attempts", ascending=False).head(1)
      return k

  def compute_air_yards(self, target):
      pos = target["position"].values[0]
      # Use special position trained models at first, before adjusting.

      if pos in ["WR", "RB", "TE"]:
        base = self.air_yards_models[pos].sample(n_samples=1)[0][0]
      else:
        base = self.air_yards_models["ALL"].sample(n_samples=1)[0][0]


      defense_relative_air_yards = self.get_def_team_stats()["defense_relative_air_yards"].values[0]
      # For routes that are clearly in positive territory, apply multiplies.
      if pos in ["WR", "TE"] and base >= 0:
          # For WR and TE, apply a multiplier to increase their ADOT.
          base *= target["relative_air_yards_est"].values[0]
          # In red zone offense, stop applying team air yards multipliers.
          if self.yard_line <= 20:
              base *= defense_relative_air_yards

      # If the total is too high to be realistic for the back of the end zone, try again.
      if self.yard_line - base <= -10:
          return self.compute_air_yards(target)
      return base

  def compute_yac(self, target):
      yac = self.yac_model.sample(n_samples=1)[0]
      # Come up with a way to handle small sample high yac players
      targets = target["targets"].values[0]
      relative_yac_est = target["relative_yac_est"].values[0]
      defense_relative_yac = self.get_def_team_stats()["defense_relative_yac_est"].values[0]
      if yac > 0:
        yac *= defense_relative_yac
        yac *= relative_yac_est

      return yac[0]




  def compute_carry_yards(self, carrier):

      carries = carrier["carries"].values[0]
      # TODO: Sample more and keep the largest to simulate big carries for backs who get them.
      yards = self.rush_model.sample(n_samples=1)[0]
      # Come up with a way to handle small sample high yac players

      relative_ypc_est = carrier["relative_ypc_est"].values[0]
      defense_relative_ypc = self.get_def_team_stats()["defense_relative_ypc_est"].values[0]
      yards *= defense_relative_ypc
      yards *= relative_ypc_est

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
          try:
            k_id = k["player_id"].values[0]
          except IndexError:
            k_id = "Kicker_%s" % self.posteam
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

  def is_complete(self, air_yards, target):
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
      defense_cpoe = self.get_def_team_stats()["defense_cpoe_est"].values[0] / 100.0
      base_probs[COMPLETE_INDEX] += defense_cpoe
      base_probs[INCOMPLETE_INDEX] -= defense_cpoe

      # Adjust the completion probability for the active quarterback.
      qb = self.choose_quarterback()
      try:
          qb_cpoe = qb["cpoe_est"].values[0] / 100.0

      # Certain situations currently lead to no QBs being rostered
      except IndexError:
          qb_cpoe = 0

      target_cpoe = target["receiver_cpoe_est"].values[0] / 100.0
      # TODO: Find a less arbitrary way of assigning credit to qb and receiver
      offense_cpoe = .75 * qb_cpoe + .25 * receiver_cpoe
      base_probs[COMPLETE_INDEX] += offense_cpoe
      base_probs[INCOMPLETE_INDEX] -= offense_cpoe

      complete = random.choices(self.completion_model.classes_, weights=base_probs, k=1)[0]

      return complete

  def defteam(self):
      if self.posteam == self.home_team:
          return self.home_team
      else:
          return self.away_team

