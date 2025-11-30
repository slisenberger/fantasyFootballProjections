from data import nfl_client as nfl_data_py
from stats import teams
from data import loader

# Load data
data = loader.load_data([2024])
team_stats = teams.calculate(data, 2024)

# Load schedule
schedules = nfl_data_py.import_schedules([2024])

# Check intersection
stats_teams = set(team_stats["team"].unique())
schedule_home = set(schedules["home_team"].unique())
schedule_away = set(schedules["away_team"].unique())
schedule_teams = schedule_home.union(schedule_away)

print("Teams in Stats:", sorted(stats_teams))
print("Teams in Schedule:", sorted(schedule_teams))

missing = schedule_teams - stats_teams
print("Missing from Stats:", missing)
