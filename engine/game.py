import random
import models


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

      # The logistic regression that assigns playcall probabilities. These are
      # adjusted up or down with team tendencies.
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

  def play_game(self):
      self.opening_kickoff()
      while not self.game_over:
          self.advance_snap()

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
    if playcall == "run":
        player = self.choose_carrier()
        yards = self.compute_carry_yards()
    if playcall == "pass":
        player = self.choose_target()
        air_yards = self.compute_air_yards()
        is_complete = self.is_complete(air_yards)

        if is_complete:
            yac = self.compute_yac()
            yards = air_yards + yac
        else:
            print("pass of %s yards intended for %s incomplete" % (air_yards, player))


    if playcall == "punt":
        self.punt()
        return

    if playcall == "field_goal":
        self.field_goal()
        return


    if yards > self.yard_line:
      yards = self.yard_line
      print("Touchdown %s!" % player)
      self.touchdown()
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

    self.advance_clock()


  def touchdown(self):
      if self.posteam == self.home_team:
          self.home_score += 6
      else:
          self.away_score += 6

      self.kickoff()


  def advance_clock(self):
      self.sec_remaining -= 20
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
    playcall = random.choices(self.playcall_model.classes_, weights=base_probs, k=1)[0]
    return playcall

  def choose_target(self):
      pos_player_stats = self.get_pos_stats()
      eligible_targets = pos_player_stats.loc[pos_player_stats["target_percentage"] > 0][["player_name", "target_percentage"]]
      target = random.choices(eligible_targets["player_name"].tolist(), weights=eligible_targets["target_percentage"].tolist(), k=1)[0]
      return target

  def choose_carrier(self):
      pos_player_stats = self.get_pos_stats()
      eligible_carriers = pos_player_stats.loc[pos_player_stats["carry_percentage"] > 0][["player_name", "carry_percentage"]]
      carrier = random.choices(eligible_carriers["player_name"].tolist(), weights=eligible_carriers["carry_percentage"].tolist(), k=1)[0]
      return carrier

  def compute_air_yards(self):
      return self.air_yards_model.sample(n_samples=1)[0]

  def compute_yac(self):
      return self.yac_model.sample(n_samples=1)[0]

  def compute_carry_yards(self):
      return self.rush_model.sample(n_samples=1)[0]

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
       model_input = [self.home_score - self.away_score, self.sec_remaining, self.quarter, self.yard_line+17]
       base_probs = self.field_goal_model.predict_proba([model_input])[0]
       good = random.choices(self.field_goal_model.classes_, weights=base_probs, k=1)[0]
       if good:
           if self.posteam == self.home_team:
              self.home_score += 3
           else:
              self.away_score += 3
           print("Field Goal is Good!")
           self.kickoff()
       else:
           self.turnover_on_downs()



  def get_pos_stats(self):
      if self.posteam == self.home_team:
          return self.home_player_stats
      else:
          return self.away_player_stats

  def is_complete(self, air_yards):
      # Baseline -- Use a logistic regression model to choose a playtype.
      model_input = [
          self.down,
          self.yds_to_go,
          self.yard_line,
          air_yards]

      base_probs = self.completion_model.predict_proba([model_input])[0]
      # Adjust probabilities for team trends
      complete = random.choices(self.completion_model.classes_, weights=base_probs, k=1)[0]

      return complete


