import time
import nfl_data_py
import pandas as pd
import random
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.calibration import CalibrationDisplay
import score
import warnings
import numpy as np
import os
from dateutil.parser import parse
import datetime
from engine import game
from stats import players, teams, injuries
from data import loader
from models import int_return, kicking, completion, playcall, receivers, rushers
from collections import defaultdict

# Calculates the fantasy leaders on a given dataframe.
def calculate_fantasy_leaders(pbp_data, season, week):
    data = pbp_data.loc[pbp_data.week == week]
    data = data.loc[data.season == season]
    data = data.loc[~(data.play_type.isin(['no_play']))]
    scores = defaultdict(float)
    for i in range(data.shape[0]):
        play_score = score.score_from_play(data.iloc[i])
        if play_score != None:
            for key in play_score.keys():
                scores[key] += play_score[key]

    # Add defensive points
    games = data.groupby("game_id").tail(1)[["game_id", "away_team", "home_team", "total_away_score", "total_home_score"]]
    for i in range(games.shape[0]):
        row = games.iloc[i]
        scores[row.home_team] += score.points_from_score(row.total_away_score)
        scores[row.away_team] += score.points_from_score(row.total_home_score)


    base_data = scores.items()
    all_scores = pd.DataFrame(base_data, columns=["player_id", "score"])
    all_scores_sorted = all_scores.sort_values(by=["score"], ascending=False).dropna()
    print(all_scores_sorted)
    return all_scores_sorted


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
def project_week(data, models, season, week, n):
    # Load the relevant dataset, which includes one week for look-behind calculation of
    # talent estimators.

    # EXPERIMENT: one season of lookbehind data.
    # Get this and last season.
    season_data = data.loc[data.season.isin([season, season - 1])]
    # From the smaller dataset, it's either last season, or this season, in which case we want
    # a more recent week.
    season_data = season_data.loc[(season_data.season == season-1) | (data.week < week)]
    team_stats = teams.calculate(season_data, season)
    player_stats = players.calculate(season_data, team_stats, season)
    schedules = nfl_data_py.import_schedules([season])
    schedules = schedules.loc[schedules.week == week]
    # The models used to inform probabilities and choices.

    inj_data = injuries.get_injury_data(season, week)
    all_projections = []
    player_stats = player_stats.merge(inj_data[["player_id", "status", "exp_return"]], on="player_id", how="left")
    # Trim the size of the player_stats object to only necessary fields to save space:
    player_stats = player_stats[[
        # General Info
        "player_id", "player_name", "position","team", "status", "exp_return",
        # Receiving data
        "relative_air_yards_est", "target_share_est", "target_percentage", "targets", "relative_yac", "relative_yac_est",
        "receiver_cpoe_est",
        # Rushing data
        "carry_share_est", "carry_percentage", "big_carry_percentage","carries", "relative_ypc", "relative_ypc_est",
        # Passing data
        "cpoe_est", "pass_attempts", "scramble_rate_est", "yards_per_scramble_est",
        # Kicking data
        "kick_attempts"]]
    team_stats = team_stats[[
        # Basic
        "team",
        # Defensive outcome adjustments
        "defense_relative_ypc_est", "defense_relative_yac_est", "defense_relative_air_yards", "defense_cpoe_est",
        "defense_int_rate_est",
        # Offensive outcome adjustments
        "offense_sacks_per_dropback",
        # Playcall tendencies
        "offense_pass_oe_est", "defense_pass_oe_est"
    ]]
    player_stats["relative_yac_est"].fillna(1, inplace=True)
    player_stats["relative_air_yards_est"].fillna(1, inplace=True)
    for i, row in schedules.iterrows():
        gameday_time = datetime.datetime.fromordinal(parse(row.gameday).date().toordinal())
        print("Projecting %s at %s" % (row.away_team, row.home_team))

        # TODO: give questionable players a fractional chance to miss
        game_stats = player_stats.loc[player_stats.team.isin([row.home_team, row.away_team])]
        out_players = game_stats.loc[game_stats.exp_return > gameday_time]
        questionable_players = game_stats.loc[game_stats.exp_return <= gameday_time]
        game_stats = game_stats.loc[~(game_stats.exp_return > gameday_time)]
        projections = []
        for i in range(n):
            projections.append(project_game(models, game_stats, team_stats, row.home_team, row.away_team, week))

        df = pd.DataFrame(projections).transpose()
        all_projections.append(df)
    proj_df = pd.concat(all_projections)

    return proj_df



def project_game(models, player_stats, team_stats, home, away, week):

    # Here's all data about the players:
    home_player_stats = player_stats[player_stats["team"].isin([home])]
    away_player_stats = player_stats[player_stats["team"].isin([away])]
    home_team_stats = team_stats[team_stats["team"].isin([home])]
    away_team_stats = team_stats[team_stats["team"].isin([away])]
    game_machine = game.GameState(models, home, away, home_player_stats, away_player_stats, home_team_stats, away_team_stats)
    return game_machine.play_game()

def score_predictions(predictions):
    plot_predictions(predictions)
    actual = predictions["score"].fillna(0)
    predicted = predictions["mean"].fillna(0)
    r2_all = r2_score(actual, predicted)
    rmse_all = mean_squared_error(actual, predicted, squared=False)
    all_data = []
    all_data.append(pd.Series(dict(position="all", r2=r2_all, rmse=rmse_all)))
    for position in ["QB", "TE", "WR", "RB", "K"]:
        predicted = predictions.loc[predictions.position == position]["mean"].fillna(0)
        actual = predictions.loc[predictions.position == position]["score"].fillna(0)
        r2_pos = r2_score(actual, predicted)
        rmse_pos = mean_squared_error(actual, predicted, squared=False)
        all_data.append(pd.Series(dict(position=position, r2=r2_pos, rmse=rmse_pos)))

    return pd.concat(all_data)

def plot_predictions(predictions):
    actual = predictions["score"].fillna(0)
    predicted = predictions["mean"].fillna(0)
    fig, axs = plt.subplots(3, 2)
    axs.flat[0].scatter(predicted, actual, c='crimson')
    positions = ["QB", "TE", "WR", "RB", "K"]
    for i in range(1, 6):
        sub = axs.flat[i]
        position = positions[i-1]
        predicted = predictions.loc[predictions.position == position]["mean"]
        actual = predictions.loc[predictions.position == position]["score"]
        sub.scatter(predicted, actual)
        sub.set_title(position)

    # Values ranging from 1 in 16, 1 in 8, 1 in 4, 1 in 2. This can be interpreted as
    # once per season, twice per season, etc..
    predictions["p6"]  = predictions.quantile(.0625, axis=1) > predictions["score"]
    predictions["p12"] = predictions.quantile(.125, axis=1) > predictions["score"]
    predictions["p25"] = predictions.quantile(.25, axis=1) > predictions["score"]
    predictions["p50"] = predictions.quantile(.5, axis=1) > predictions["score"]
    predictions["p75"] = predictions.quantile(.75, axis=1) > predictions["score"]
    predictions["p88"] = predictions.quantile(.875, axis=1) > predictions["score"]
    predictions["p94"] = predictions.quantile(.9375, axis=1) > predictions["score"]

    probs = [.0625] * predictions.shape[0] +\
            [.125] * predictions.shape[0] +\
            [.25] * predictions.shape[0] +\
            [.5] * predictions.shape[0] + \
            [.75] * predictions.shape[0] + \
            [.875] * predictions.shape[0] + \
            [.9375] * predictions.shape[0]
    disp = CalibrationDisplay.from_predictions(
        pd.concat([predictions["p6"], predictions["p12"], predictions["p25"], predictions["p50"],
                   predictions["p75"], predictions["p88"], predictions["p94"]]),
        probs)
    plt.show()


def compute_stats_and_export(projection_data, season, week):
    median = projection_data.median(axis=1)
    percentile_12 = projection_data.quantile(.125, axis=1)
    percentile_25 = projection_data.quantile(.25, axis=1)
    percentile_75 = projection_data.quantile(.75, axis=1)
    percentile_88 = projection_data.quantile(.875, axis=1)
    projection_data = projection_data.assign(median=median)
    projection_data = projection_data.assign(percentile_12=percentile_12)
    projection_data = projection_data.assign(percentile_25=percentile_25)
    projection_data = projection_data.assign(percentile_75=percentile_75)
    projection_data = projection_data.assign(percentile_88=percentile_88)
    roster_data = nfl_data_py.import_rosters([season], columns=["player_id", "position", "player_name", "team"])
    projection_data = projection_data.merge(roster_data, on="player_id", how="left")
    projection_data = projection_data.sort_values(by="median", ascending=False)[
        ["player_id", "player_name", "team", "position", "percentile_12", "percentile_25", "median", "percentile_75",
         "percentile_88"]]

    projection_data.to_csv("projections_week_%s_v%s.csv" % (week, version))
    base_path = os.path.join("projections/", "w%s_v%s_" % (week, version))
    projection_data.to_csv(base_path + "all.csv")
    projection_data.loc[projection_data.position == "QB"].to_csv(base_path + "qb.csv")
    projection_data.loc[projection_data.position == "RB"].to_csv(base_path + "rb.csv")
    projection_data.loc[projection_data.position == "WR"].to_csv(base_path + "wr.csv")
    projection_data.loc[projection_data.position == "TE"].to_csv(base_path + "te.csv")
    projection_data.loc[projection_data.position.isin(["RB", "WR", "TE"])].to_csv(base_path + "flex.csv")
    projection_data.loc[projection_data.position == "K"].to_csv(base_path + "k.csv")

def project_ros(pbp_data, models, season,  cur_week, n_projections, version):
    # Generate all remaining weeks projection data
    all_weeks = []
    for week in range(cur_week, 19):
        print("Running projections on %s Week %s" % (season, week))
        projection_data = project_week(pbp_data, models, 2021, week, n_projections).reset_index()
        mean = projection_data.mean(axis=1)
        percentile_90 = projection_data.quantile(.9, axis=1)
        projection_data = projection_data.assign(mean=mean)
        projection_data = projection_data.assign(percentile_90=percentile_90)
        projection_data = projection_data.assign(week=week)
        projection_data = projection_data.rename(columns={"index": "player_id"}).fillna(0)
        all_weeks.append(projection_data)
        compute_stats_and_export(projection_data, 2021, week)


    all_ros = pd.concat(all_weeks)
    roster_data = nfl_data_py.import_rosters([season], columns=["player_id", "position", "player_name", "team"])
    all_ros = all_ros.merge(roster_data, on="player_id", how="left")
    ros_sum = all_ros.groupby("player_id")["mean"].sum().to_frame("ros_total").sort_values(
        by="ros_total", ascending=False).reset_index()
    ros_mean = all_ros.groupby("player_id")["mean"].mean().to_frame("ros_mean").sort_values(
        by="ros_mean", ascending=False).reset_index()
    playoffs_mean = all_ros.loc[all_ros.week >= 15].groupby("player_id")["mean"].mean().to_frame("playoffs_mean").sort_values(
        by="playoffs_mean", ascending=False).reset_index()

    base_path = os.path.join("projections/", "v%s_" % version)
    ros_sum.merge(roster_data, on="player_id", how="outer")[
        ["player_id", "player_name", "team", "position", "ros_total"]].to_csv(base_path + "ros_total.csv")
    ros_mean.merge(roster_data, on="player_id", how="outer")[
        ["player_id", "player_name", "team", "position", "ros_mean"]].to_csv(base_path + "ros_mean.csv")
    playoffs_mean.merge(roster_data, on="player_id", how="outer")[
        ["player_id", "player_name", "team", "position", "playoffs_mean"]].to_csv(base_path + "playoffs_mean.csv")



# The primary entry point for the program. Initializes the majority of necessary data.
if __name__ == '__main__':
    # Quiet the deprecation warnings in the command line a little.
    warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)

    # Modify print settings
    pd.set_option('display.max_rows', 100)
    pd.set_option('display.max_columns', 400)
    # loader.clean_and_save_data()
    # injuries.clean_and_save_data()
    # Get full datasets for pbp and injuries and rosters for future joining.
    pbp_data = loader.load_data([2017,2018,2019,2020,2021])
    version = 300
    current_week = 11
    season = 2021
    # If possible, lean into values divisible by 16, for calculating percentiles.
    # 16, 32, 48, 96, 256, 512, 1024 are examples close to known round numbers
    n_projections = 256
    models = {
        'playcall_model': playcall.build_or_load_playcall_model(),
        'rush_model': rushers.build_or_load_rush_kde(),
        'scramble_model': rushers.build_or_load_scramble_kde(),
        'completion_model': completion.build_or_load_completion_model(),
        'field_goal_model': kicking.build_or_load_kicking_model(),
        'int_return_model': int_return.build_or_load_int_return_kde(),
    }
    models.update(receivers.build_or_load_all_air_yards_kdes())
    models.update(receivers.build_or_load_all_yac_kdes())

    # Run backtesting against previous years to assess model predictive ability.
    all_scores = []
    all_prediction_data = []
    for season in range(2021, 2022):
        for week in range(8, 18):
            print("Running projections on %s Week %s" % (season, week))
            prediction_data = project_week(pbp_data, models, season, week, 48).reset_index()
            prediction_data = prediction_data.assign(mean=prediction_data.mean(axis=1))
            prediction_data = prediction_data.rename(columns={"index": "player_id"})

            prediction_data = prediction_data.merge(
                calculate_fantasy_leaders(pbp_data, season, week), on="player_id", how="outer")
            roster_data = nfl_data_py.import_rosters([season], columns=["player_id", "position", "player_name", "team"])
            prediction_data = prediction_data.merge(roster_data, on="player_id", how="left")
            prediction_data["position"] = prediction_data["position"].fillna("DEF")
            prediction_data = prediction_data.assign(week=week)
            prediction_data = prediction_data.assign(season=season)
            all_prediction_data.append(prediction_data)

    full_data = pd.concat(all_prediction_data)
    scores = score_predictions(full_data)
    scores.to_csv("projection_test_scores_v%s.csv" % version)
    full_data[["player_id", "player_name", "position", "team","week", "mean", "score"]].to_csv("projection_raw_values_v%s.csv" % version)

    # Generate projections for all remaining weeks and ROS metadata.
    project_ros(pbp_data, models, season, current_week, n_projections, version)









