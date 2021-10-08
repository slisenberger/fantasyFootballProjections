# Adjust To Opponent is a simple projection strategy that takes the recent
# fantasy performances for players, looks at their opponents tendencies, and produces
# new expected averages. This strategy is going to be stronger later in the year,
# as more games have taken place to determine opponent strength.

# Basic sequence:
# Take player or team or game
# Compute opponent adjustment
# Apply to baseline (perhaps adding variance -- strategies can be extensible)
# Return output (score for each player).

def compute_team_tendencies():