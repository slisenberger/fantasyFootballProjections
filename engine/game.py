import random


# I think the API I want is something like: result = advance_snap(game_state)
# The gamestate would itself be update, a synthetic play would be generated, and this can be used in
# any sort of projection model we want.
class GameState:
  """Representation of the Game Details of a football game, like down, quarter, and clock."""
  def __init__(self, home_team, away_team):
      # Names of the participating teams
      self.home_team = home_team
      self.away_team = away_team
      # Current team possessing the ball
      self.posteam = None
      # Current quarter
      self.quarter = 0
      # Current down
      self.down = 1
      # Time remaining in quarter, in seconds
      self.sec_remaining = 15*60
      self.home_score = 0
      self.away_score = 0
      # A representation of the yard line, where 0 is the home endzone and 100 is the away endzone
      self.yard_line = 50


  def add_points(self, team, points):
      if team == self.home_team:
        self.home_score += points
      if team == self.away_team:
        self.away_score += points



def advance_snap(gamestate):
    play_type = choose_play_type(gamestate)
    if play_type == RUN:
        choose_carrier()
    if play_type = PASS:
        choose_target()

    compute_yards()
    update_game_state()

"""Chooses a play type between running and passing

Currently, this ignores the game state and randomly chooses
and outcome. When implemented correctly, this will be a model
that takes into account team tendencies and league-wide
game-state tendencies.
"""
def choose_play_type(gamestate):
   return "RUN"

"""Chooses an intended receiver for a given gamestate and team/player stats"""
def choose_target():
    return None

def choose_carrier():
    return None

"""Determines if an intended pass was complete."""
def is_complete()