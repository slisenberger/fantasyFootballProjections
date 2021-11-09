
import nfl_data_py
import pandas as pd
import matplotlib.pyplot as plt
import score
import warnings
import numpy as np
from engine import game
from stats import players, teams
from models import kicking, completion, playcall, receivers, rushers
from collections import defaultdict

# The Hello World will be correctly plotting the leaders in fantasy points for week 4. This ensures two goals:
# Testability, we can compare with unit tests.
# Our point calculation is correct.
def calculate_fantasy_leaders():
    YEARS = [2021]
    data = pd.DataFrame()

    for i in YEARS:
        i_data = pd.read_csv('data/pbp_' + str(i) + '.csv.gz',
                             compression='gzip', low_memory=False)

        data = data.append(i_data, sort=True)

    week_four = data.loc[data.week == 9]
    all_players = build_player_id_map(week_four)
    scores = defaultdict(float)

    for i in range(len(week_four)):
        play_score = score.score_from_play(week_four.iloc[i])
        if play_score != None:
            for key in play_score.keys():
                scores[key] += play_score[key]

    base_data = scores.items()
    new_base_data = []
    for row in base_data:
        if row[0] in all_players:
          new_base_data.append([row[0], all_players[row[0]], row[1]])
    w4_scores = pd.DataFrame(new_base_data, columns=["player_id", "Player Name", "Score"])
    w4_scores_sorted = w4_scores.sort_values(by=["Score"], ascending=False)
    print(w4_scores_sorted)



def load_and_clean_data():
    import pandas as pd

    pd.options.mode.chained_assignment = None

    # Enter desired years of data. Data goes back to '99, but we don't need
    # to update it.
    YEARS = [2021]

    for i in YEARS:
        # Link to data repo
        link = 'https://github.com/guga31bb/nflfastR-data/blob/master/data/play_by_play_' + str(i) + '.csv.gz?raw=true'
        # Read in CSV
        data = pd.read_csv(link, compression='gzip', low_memory=False)
        # Filter to regular season data only
        data = data.loc[data.season_type == 'REG']
        # Output cleaned, compressed CSV to current directory
        data.to_csv('data/pbp_' + str(i) + '.csv.gz', index=False, compression='gzip')

def build_player_id_map(data):
    all_players = {}
    for i in range(len(data)):
        row = data.iloc[i]
        if row.passer_player_id not in all_players:
            all_players[row.passer_player_id] = row.passer_player_name
        if row.receiver_player_id not in all_players:
            all_players[row.receiver_player_id] = row.receiver_player_name
        if row.rusher_player_id not in all_players:
            all_players[row.rusher_player_id] = row.rusher_player_name

    return all_players

# Projects the next week's estimated fantasy points.

# To produce anything, I have this set only to 2021. However, this will be refactored.
def project_week(player_stats, team_stats, week):
    schedules = nfl_data_py.import_schedules([2021])
    schedules = schedules.loc[schedules.week == week]
    all_projections = []
    for i, row in schedules.iterrows():
        print("Projecting %s at %s" % (row.away_team, row.home_team))
        projections = []
        for i in range(50):
            projections.append(project_game(player_stats, team_stats, row.home_team, row.away_team, week))

        df = pd.DataFrame(projections).transpose()
        all_projections.append(df)
    proj_df = pd.concat(all_projections)
    proj_df.to_csv("projections_week_10_player_aware.csv")
    return proj_df


def project_game(player_stats, team_stats, home, away, week):
    # load rosters and injury information.
    # depth_charts = nfl_data_py.import_depth_charts([2021])
    # injuries = nfl_data_py.import_injuries([2021])
    # rosters = nfl_data_py.import_rosters([2021], ["team", "player_name", "position", "player_id"])


    # Get all the injuries for a team
    # injuries = injuries.loc[injuries.week == week]
    # injuries = injuries[injuries["team"].isin([home,away])]
    # injuries = injuries[injuries["report_status"].isin(["Out"])]
    # print("players ruled out: \n\n%s" % injuries[["full_name","gsis_id"]])

    # print("fantasy relevant players in this game:")
    # rosters = rosters[rosters["team"].isin([home,away])]
    # rosters = rosters[rosters["position"].isin(["RB", "WR", "TE", "QB"])]
    #print(rosters)

    # Here's all data about the players:
    home_player_stats = player_stats[player_stats["team"].isin([home])]
    away_player_stats = player_stats[player_stats["team"].isin([away])]
    home_team_stats = team_stats[team_stats["team"].isin([home])]
    away_team_stats = team_stats[team_stats["team"].isin([home])]

    # print("Home team stats:\n %s" % home_player_stats[["player_name", "cpoe", "pass_attempts"]])
    # print("Away team stats:\n %s" % away_player_stats[["player_name", "cpoe", "pass_attempts"]])
    game_machine = game.GameState(home, away, home_player_stats, away_player_stats, home_team_stats, away_team_stats)
    return game_machine.play_game()




# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # Quiet the deprecation warnings in the command line a little.
    warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)

    # This doesn't always need to be done. would like to run this on a cron schedule.
    # load_and_clean_data()
    #calculate_fantasy_leaders(9)


    # Create an easier way to identify players in fantasy
    team_stats = teams.calculate()
    # weekly_team_stats = teams.calculate_weekly()
    player_stats = players.calculate(team_stats)
    # weekly_stats = players.calculate_weekly(weekly_team_stats)

    # Generate all week 10 Projection Data
    projection_data = project_week(player_stats, team_stats, 10).reset_index()
    projection_data = projection_data.rename(columns={"index": "player_name"})

    # Plot projections, sorted by median
    meds = projection_data.median(axis=1)
    meds.sort_values(ascending=False, inplace=True)
    median = projection_data.median(axis=1)
    percentile_10 = projection_data.quantile(.1, axis=1)
    percentile_25 = projection_data.quantile(.25, axis=1)
    percentile_75 = projection_data.quantile(.75, axis=1)
    percentile_90 = projection_data.quantile(.9, axis=1)
    projection_data = projection_data.assign(median=median)
    projection_data = projection_data.assign(percentile_10=percentile_10)
    projection_data = projection_data.assign(percentile_25=percentile_25)
    projection_data = projection_data.assign(percentile_75=percentile_75)
    projection_data = projection_data.assign(percentile_90=percentile_90)
    projection_data = projection_data.sort_values(by="median",ascending=False)[["player_name", "percentile_10", "percentile_25", "median", "percentile_75", "percentile_90"]]
    projection_data.to_csv("projections_week_10_v3.csv")
    plt.boxplot(projection_data.head(30), vert=False)
    plt.show()

