
import nfl_data_py
import pandas as pd
import random
import matplotlib.pyplot as plt
import score
import warnings
import numpy as np
import os
from dateutil.parser import parse
from engine import game
from stats import players, teams, injuries, loader
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

# Projects the a given week's estimated fantasy points.
def project_week(player_stats, team_stats, week, n):
    schedules = nfl_data_py.import_schedules([2021])
    schedules = schedules.loc[schedules.week == week]
    inj_data = injuries.get_injury_data(2021, week)
    all_projections = []
    for i, row in schedules.iterrows():
        gameday = row.gameday
        valid_injuries = inj_data.loc[inj_data.exp_return > parse(gameday)]

        print("Projecting %s at %s" % (row.away_team, row.home_team))

        projections = []
        for i in range(n):
            # Automatically make questionable players start.
            # TODO: give questionable players a fractional chance to miss
            q_adjusted_injuries = valid_injuries.loc[~valid_injuries.status.isin(["Questionable"])]
            injured_ids = q_adjusted_injuries["player_id"].to_list()
            player_stats = player_stats.loc[~player_stats.player_id.isin(injured_ids)]
            projections.append(project_game(player_stats, team_stats, row.home_team, row.away_team, week))

        df = pd.DataFrame(projections).transpose()
        all_projections.append(df)
    proj_df = pd.concat(all_projections)
    return proj_df



def project_game(player_stats, team_stats, home, away, week):
    # load rosters and injury information.
    # depth_charts = nfl_data_py.import_depth_charts([2021])
    # rosters = nfl_data_py.import_rosters([2021], ["team", "player_name", "position", "player_id"])

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


# Returns the projection results for a single week and year.
def project(data, week, year, n_projections):
    team_stats = teams.calculate(data, week, year)
    player_stats = players.calculate(data, week, year, team_stats)
    projection_data = project_week(player_stats, team_stats, year, week, n_projections).reset_index()
    projection_data = projection_data.rename(columns={"index": "player_id"})

    projection_data = projection_data.fillna(0)
    median = projection_data.median(axis=1)
    percentile_10 = projection_data.quantile(.1, axis=1)
    percentile_25 = projection_data.quantile(.25, axis=1)
    percentile_75 = projection_data.quantile(.75, axis=1)
    percentile_90 = projection_data.quantile(.9, axis=1)
    projection_data = projection_data.assign(median=median)
    roster_data = nfl_data_py.import_rosters([2021], columns=["player_id", "position", "player_name", "team"])
    projection_data = projection_data.merge(roster_data, on="player_id", how="left")
    projection_data = projection_data.sort_values(by="median", ascending=False)[
        ["player_id", "player_name", "team", "position", "percentile_10", "percentile_25", "median", "percentile_75",
         "percentile_90"]]


# The primary entry point for the program. Initializes the majority of necessary data.
if __name__ == '__main__':
    # Quiet the deprecation warnings in the command line a little.
    warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)
    # injuries.clean_and_save_data()
    # Get full datasets for pbp and injuries and rosters for future joining.
    # pbp_data = loader.load_data([2016, 2017, 2018, 2019, 2020, 2021])


    # This doesn't always need to be done. would like to run this on a cron schedule.
    # load_and_clean_data()
    #calculate_fantasy_leaders(9)
    week = 10
    version = 13
    n_projections = 1000

    # Create an easier way to identify players in fantasy
    team_stats = teams.calculate()
    player_stats = players.calculate(team_stats)

    # Generate all week 10 Projection Data
    projection_data = project_week(player_stats, team_stats, week, n_projections).reset_index()
    projection_data = projection_data.rename(columns={"index": "player_id"})

    projection_data = projection_data.fillna(0)
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
    roster_data = nfl_data_py.import_rosters([2021], columns=["player_id", "position", "player_name", "team"])
    projection_data = projection_data.merge(roster_data, on="player_id", how="left")
    projection_data = projection_data.sort_values(by="median",ascending=False)[
        ["player_id", "player_name", "team", "position", "percentile_10", "percentile_25", "median", "percentile_75",
         "percentile_90"]]


    projection_data.to_csv("projections_week_%s_v%s.csv" % (week, version))
    base_path = os.path.join("projections/", "w%s_v%s_" % (week, version))
    projection_data.to_csv(base_path + "all.csv")
    projection_data.loc[projection_data.position == "QB"].to_csv(base_path +"qb.csv")
    projection_data.loc[projection_data.position == "RB"].to_csv(base_path + "rb.csv")
    projection_data.loc[projection_data.position == "WR"].to_csv(base_path + "wr.csv")
    projection_data.loc[projection_data.position == "TE"].to_csv(base_path + "te.csv")
    projection_data.loc[projection_data.position.isin(["RB", "WR", "TE"])].to_csv(base_path + "flex.csv")
    projection_data.loc[projection_data.position == "K"].to_csv(base_path + "k.csv")
