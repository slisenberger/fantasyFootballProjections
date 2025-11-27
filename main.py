import random
import argparse
import warnings
import os
import datetime
from collections import defaultdict

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.calibration import CalibrationDisplay
from joblib import Parallel, delayed
from dateutil.parser import parse

import nfl_data_py
import score
from engine import game
from stats import players, teams, injuries
from data import loader
from models import int_return, kicking, completion, playcall, receivers, rushers
from evaluation import calibration
from settings import AppConfig


def calculate_fantasy_leaders(pbp_data, season, week, config):
    data = pbp_data.loc[pbp_data.week == week]
    data = data.loc[data.season == season]
    data = data.loc[~(data.play_type.isin(["no_play"]))]
    scores = defaultdict(float)
    for i in range(data.shape[0]):
        play_score = score.score_from_play(data.iloc[i], config.scoring)
        if play_score is not None:
            for key in play_score.keys():
                scores[key] += play_score[key]

    games = data.groupby("game_id").tail(1)[
        ["game_id", "away_team", "home_team", "total_away_score", "total_home_score"]
    ]
    for i in range(games.shape[0]):
        row = games.iloc[i]
        scores[row.home_team] += score.points_from_score(row.total_away_score, config.scoring)
        scores[row.away_team] += score.points_from_score(row.total_home_score, config.scoring)

    base_data = scores.items()
    all_scores = pd.DataFrame(base_data, columns=["player_id", "score"])
    all_scores_sorted = all_scores.sort_values(by=["score"], ascending=False).dropna()
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


def project_week(data, models, season, week, config):
    n = config.runtime.n_simulations
    season_data = data.loc[
        (data.season == season - 1) | ((data.season == season) & (data.week < week))
    ]
    team_stats = teams.calculate(season_data, season)
    player_stats = players.calculate(season_data, team_stats, season, week)
    schedules = nfl_data_py.import_schedules([season])
    schedules = schedules.loc[schedules.week == week]

    inj_data = injuries.get_injury_data(season, week)
    all_projections = []
    if inj_data is not None:
        player_stats = player_stats.merge(
            inj_data[["player_id", "status", "exp_return"]], on="player_id", how="left"
        )
    else:
        player_stats["status"] = "Active"
        player_stats["exp_return"] = None

    player_stats = player_stats[
        [
            "player_id", "player_name", "position", "team", "status", "exp_return",
            "relative_air_yards_est", "target_share_est", "redzone_target_share_est",
            "target_percentage", "targets", "relative_yac", "relative_yac_est",
            "receiver_cpoe_est", "carry_share_est", "redzone_carry_share_est",
            "carry_percentage", "carries", "relative_ypc", "relative_ypc_est",
            "cpoe_est", "pass_attempts", "scramble_rate_est", "yards_per_scramble_est",
            "starting_qb", "kick_attempts", "starting_k",
        ]
    ]
    team_stats = team_stats[
        [
            "team", "defense_relative_ypc_est", "defense_relative_yac_est",
            "defense_relative_air_yards", "defense_cpoe_est", "defense_int_rate_est",
            "offense_sacks_per_dropback", "defense_sacks_per_dropback",
            "offense_sack_rate_est", "defense_sack_rate_est", "lg_sack_rate",
            "offense_pass_oe_est", "defense_pass_oe_est",
        ]
    ]
    player_stats["relative_yac_est"].fillna(1, inplace=True)
    player_stats["relative_air_yards_est"].fillna(1, inplace=True)
    for i, row in schedules.iterrows():
        gameday_time = datetime.datetime.fromordinal(
            parse(row.gameday).date().toordinal()
        )
        print("Projecting %s at %s" % (row.away_team, row.home_team))

        game_stats = player_stats.loc[
            player_stats.team.isin([row.home_team, row.away_team])
        ]
        game_stats.loc[game_stats.exp_return > gameday_time]
        game_stats = game_stats.loc[~(game_stats.exp_return > gameday_time)]
        game_stats.loc[game_stats.status == "Questionable"]
        
        if config.runtime.use_parallel:
            projections = Parallel(n_jobs=-1)(
                delayed(project_game)(
                    models, game_stats, team_stats, row.home_team, row.away_team, week, config
                )
                for i in range(n)
            )
        else:
            projections = [
                project_game(models, game_stats, team_stats, row.home_team, row.away_team, week, config)
                for i in range(n)
            ]

        df = pd.DataFrame(projections).transpose()
        all_projections.append(df)
    proj_df = pd.concat(all_projections)

    return proj_df


def project_game(models, player_stats, team_stats, home, away, week, config):
    # Apply Probabilistic Injury Logic
    # Logic: Q players have 25% chance of being scratch (removed), 
    # and if active, 20% volume reduction (limited/decoy risk).
    
    # We must work on a copy to avoid modifying the master DF for other sims
    player_stats = player_stats.copy()
    
    q_players = player_stats[player_stats['status'] == 'Questionable']
    drop_indices = []
    
    for idx, row in q_players.iterrows():
        if random.random() < 0.25:
            # Simulating Inactive
            drop_indices.append(idx)
        else:
            # Simulating Active but Limited
            # Reduce volume share by 20%
            player_stats.at[idx, 'target_share_est'] *= 0.8
            player_stats.at[idx, 'carry_share_est'] *= 0.8
            
    if drop_indices:
        player_stats = player_stats.drop(drop_indices)

    home_player_stats = player_stats[player_stats["team"].isin([home])]
    away_player_stats = player_stats[player_stats["team"].isin([away])]
    home_team_stats = team_stats[team_stats["team"].isin([home])]
    away_team_stats = team_stats[team_stats["team"].isin([away])]
    game_machine = game.GameState(
        models,
        home,
        away,
        home_player_stats,
        away_player_stats,
        home_team_stats,
        away_team_stats,
        rules=config.scoring
    )
    return game_machine.play_game()


def score_predictions(predictions):
    plot_predictions(predictions)
    actual = predictions["score"].fillna(0)
    predicted = predictions["mean"].fillna(0)
    r2_all = r2_score(actual, predicted)
    rmse_all = mean_squared_error(actual, predicted, squared=False)
    all_data = []
    all_data.append(pd.Series(dict(position="all", r2=r2_all, rmse=rmse_all)))
    for position in ["QB", "TE", "WR", "RB", "K", "DEF"]:
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
    axs.flat[0].scatter(predicted, actual, c="crimson")
    positions = ["QB", "TE", "WR", "RB", "DEF"]
    for i in range(1, 6):
        sub = axs.flat[i]
        position = positions[i - 1]
        predicted = predictions.loc[predictions.position == position]["mean"]
        actual = predictions.loc[predictions.position == position]["score"]
        sub.scatter(predicted, actual)
        sub.set_title(position)

    predictions["p6"] = predictions.quantile(0.0625, axis=1) > predictions["score"]
    predictions["p12"] = predictions.quantile(0.125, axis=1) > predictions["score"]
    predictions["p25"] = predictions.quantile(0.25, axis=1) > predictions["score"]
    predictions["p50"] = predictions.quantile(0.5, axis=1) > predictions["score"]
    predictions["p75"] = predictions.quantile(0.75, axis=1) > predictions["score"]
    predictions["p88"] = predictions.quantile(0.875, axis=1) > predictions["score"]
    predictions["p94"] = predictions.quantile(0.9375, axis=1) > predictions["score"]

    probs = (
        [0.0625] * predictions.shape[0]
        + [0.125] * predictions.shape[0]
        + [0.25] * predictions.shape[0]
        + [0.5] * predictions.shape[0]
        + [0.75] * predictions.shape[0]
        + [0.875] * predictions.shape[0]
        + [0.9375] * predictions.shape[0]
    )
    CalibrationDisplay.from_predictions(
        pd.concat(
            [
                predictions["p6"],
                predictions["p12"],
                predictions["p25"],
                predictions["p50"],
                predictions["p75"],
                predictions["p88"],
                predictions["p94"],
            ]
        ),
        probs,
    )
    plt.show()


def compute_stats_and_export(projection_data, season, week, version):
    median = projection_data.median(axis=1)
    percentile_12 = projection_data.quantile(0.125, axis=1)
    percentile_25 = projection_data.quantile(0.25, axis=1)
    percentile_75 = projection_data.quantile(0.75, axis=1)
    percentile_88 = projection_data.quantile(0.875, axis=1)
    projection_data = projection_data.assign(median=median)
    projection_data = projection_data.assign(percentile_12=percentile_12)
    projection_data = projection_data.assign(percentile_25=percentile_25)
    projection_data = projection_data.assign(percentile_75=percentile_75)
    projection_data = projection_data.assign(percentile_88=percentile_88)
    roster_data = nfl_data_py.import_seasonal_rosters(
        [season], columns=["player_id", "position", "player_name", "team"]
    )
    projection_data = projection_data.merge(roster_data, on="player_id", how="left")
    projection_data = projection_data.sort_values(by="median", ascending=False)[
        [
            "player_id",
            "player_name",
            "team",
            "position",
            "percentile_12",
            "percentile_25",
            "median",
            "percentile_75",
            "percentile_88",
        ]
    ]

    # New Structured Output
    base_dir = os.path.join("projections", f"v{version}", f"week_{week}")
    os.makedirs(base_dir, exist_ok=True)

    # Save Summary (was projections_week_X_vY.csv)
    projection_data.to_csv(os.path.join(base_dir, "summary.csv"))
    
    # Save Splits
    projection_data.to_csv(os.path.join(base_dir, "all.csv"))
    projection_data.loc[projection_data.position == "QB"].to_csv(os.path.join(base_dir, "qb.csv"))
    projection_data.loc[projection_data.position == "RB"].to_csv(os.path.join(base_dir, "rb.csv"))
    projection_data.loc[projection_data.position == "WR"].to_csv(os.path.join(base_dir, "wr.csv"))
    projection_data.loc[projection_data.position == "TE"].to_csv(os.path.join(base_dir, "te.csv"))
    projection_data.loc[projection_data.position.isin(["RB", "WR", "TE"])].to_csv(
        os.path.join(base_dir, "flex.csv")
    )
    projection_data.loc[projection_data.position == "K"].to_csv(os.path.join(base_dir, "k.csv"))


def project_ros(pbp_data, models, config):
    all_weeks = []
    
    season = config.runtime.season
    cur_week = config.runtime.week
    version = config.runtime.version
    
    for week in range(cur_week, cur_week + 1):
        print("Running projections on %s Week %s" % (season, week))
        projection_data = project_week(
            pbp_data, models, season, week, config
        ).reset_index()
        mean = projection_data.mean(axis=1)
        percentile_90 = projection_data.quantile(0.9, axis=1)
        projection_data = projection_data.assign(mean=mean)
        projection_data = projection_data.assign(percentile_90=percentile_90)
        projection_data = projection_data.assign(week=week)
        projection_data = projection_data.rename(columns={"index": "player_id"}).fillna(
            0
        )
        all_weeks.append(projection_data)
        compute_stats_and_export(projection_data, season, week, version)

    all_ros = pd.concat(all_weeks)
    roster_data = nfl_data_py.import_seasonal_rosters(
        [season], columns=["player_id", "position", "player_name", "team"]
    )
    all_ros = all_ros.merge(roster_data, on="player_id", how="left")
    ros_sum = (
        all_ros.groupby("player_id")["mean"]
        .sum()
        .to_frame("ros_total")
        .sort_values(by="ros_total", ascending=False)
        .reset_index()
    )
    ros_mean = (
        all_ros.groupby("player_id")["mean"]
        .mean()
        .to_frame("ros_mean")
        .sort_values(by="ros_mean", ascending=False)
        .reset_index()
    )
    playoffs_mean = (
        all_ros.loc[all_ros.week >= 15]
        .groupby("player_id")["mean"]
        .mean()
        .to_frame("playoffs_mean")
        .sort_values(by="playoffs_mean", ascending=False)
        .reset_index()
    )

    # New Structured Output for ROS
    base_dir = os.path.join("projections", f"v{version}", "ros")
    os.makedirs(base_dir, exist_ok=True)

    ros_sum.merge(roster_data, on="player_id", how="outer")[
        ["player_id", "player_name", "team", "position", "ros_total"]
    ].to_csv(os.path.join(base_dir, "total.csv"))
    
    ros_mean.merge(roster_data, on="player_id", how="outer")[
        ["player_id", "player_name", "team", "position", "ros_mean"]
    ].to_csv(os.path.join(base_dir, "mean.csv"))
    
    playoffs_mean.merge(roster_data, on="player_id", how="outer")[
        ["player_id", "player_name", "team", "position", "playoffs_mean"]
    ].to_csv(os.path.join(base_dir, "playoffs.csv"))


def get_models():
    models = {
        "playcall_model": playcall.build_or_load_playcall_model(),
        "rush_model": rushers.build_or_load_rush_kde(),
        "scramble_model": rushers.build_or_load_scramble_kde(),
        "completion_model": completion.build_or_load_completion_model(),
        "field_goal_model": kicking.build_or_load_kicking_model(),
        "int_return_model": int_return.build_or_load_int_return_kde(),
    }
    
    # Load Clock Model
    try:
        clock_df = pd.read_csv("stats/clock_runoff.csv")
        models["clock_model"] = clock_df.set_index(
            ['qtr_bucket', 'time_bucket', 'score_bucket', 'play_type_detail']
        )['mean'].to_dict()
    except FileNotFoundError:
        print("Warning: Clock model not found.")
        models["clock_model"] = {}

    models.update(receivers.build_or_load_all_air_yards_kdes())
    models.update(receivers.build_or_load_all_yac_kdes())

    # Optimization: Pre-sample KDEs to avoid expensive sampling during simulation loops
    # This moves the cost from O(simulations * plays) to O(1) per execution
    SAMPLE_SIZE = 100000
    
    # Core Movement Models
    models["rush_samples"] = models["rush_model"].sample(SAMPLE_SIZE).flatten()
    models["scramble_samples"] = models["scramble_model"].sample(SAMPLE_SIZE).flatten()
    models["int_return_samples"] = models["int_return_model"].sample(SAMPLE_SIZE).flatten()
    
    # Receiver Models (Air Yards & YAC)
    for pos in ["RB", "WR", "TE", "ALL"]:
        # Air Yards
        key_ay = f"air_yards_{pos}"
        if key_ay in models:
            models[f"{key_ay}_samples"] = models[key_ay].sample(SAMPLE_SIZE).flatten()
        
        # YAC
        key_yac = f"yac_{pos}"
        if key_yac in models:
            models[f"{key_yac}_samples"] = models[key_yac].sample(SAMPLE_SIZE).flatten()

    return models


def run_projections(pbp_data, config):
    models = get_models()
    print(f"--- Generating Projections for Season {config.runtime.season} Week {config.runtime.week}+ ---")
    project_ros(pbp_data, models, config)


def run_backtest(pbp_data, config):
    models = get_models()
    print("\n--- Starting Backtesting & Calibration ---")
    calibration_results = []

    # Configurable backtest range (hardcoded for smoke test)
    # In a real run, this would loop over [2018, 2019...] and weeks [1..17]
    backtest_config = [(2018, 8)] 

    for season, week in backtest_config:
        try:
            print(f"Backtesting {season} Week {week}...")
            
            # A. Run Simulations -> Get Raw Distribution
            sims_df = project_week(pbp_data, models, season, week, config)
            
            # B. Get Actual Outcomes
            actuals_df = calculate_fantasy_leaders(pbp_data, season, week, config)
            
            # C. Merge
            sims_df['simulations'] = sims_df.values.tolist()
            sims_df = sims_df.reset_index().rename(columns={'index': 'player_id'})
            merged = sims_df[['player_id', 'simulations']].merge(actuals_df, on='player_id')
            merged['season'] = season
            merged['week'] = week
            merged = merged.rename(columns={'score': 'actual'})
            
            calibration_results.append(merged)
            
        except Exception as e:
            print(f"Backtesting failed for {season} W{week}: {e}")
            print("Skipping this week. (Likely missing historical data)")

    # 3. Evaluate
    if calibration_results:
        full_calib_df = pd.concat(calibration_results)
        print(f"\nEvaluating Calibration on {len(full_calib_df)} player-games...")
        evaluated_df = calibration.evaluate_calibration(full_calib_df)
        
        try:
            calibration.plot_pit_histogram(evaluated_df, title=f"Calibration (v{config.runtime.version})")
            print("Calibration plot displayed (or saved).")
        except Exception as e:
            print(f"Could not generate plot: {e}")
        
        # New Structured Output for Calibration
        base_dir = os.path.join("projections", f"v{config.runtime.version}", "calibration")
        os.makedirs(base_dir, exist_ok=True)
        
        output_path = os.path.join(base_dir, "metrics.csv")
        
        evaluated_df[['player_id', 'season', 'week', 'actual', 'pit']].to_csv(
            output_path, index=False
        )
        print(f"Calibration metrics saved to {output_path}")
    else:
        print("\nNo backtesting results generated. Calibration skipped.")


def parse_args():
    parser = argparse.ArgumentParser(description="Run NFL Fantasy Projections")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Common arguments
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("--season", type=int, default=2024, help="Season")
    common_parser.add_argument("--week", type=int, default=2, help="Week")
    common_parser.add_argument("--simulations", type=int, default=5, help="Number of simulations")
    common_parser.add_argument("--version", type=str, default="402", help="Version tag")

    # Subcommands
    subparsers.add_parser("project", parents=[common_parser], help="Run future projections")
    subparsers.add_parser("backtest", parents=[common_parser], help="Run backtesting")
    subparsers.add_parser("all", parents=[common_parser], help="Run both (default)")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    # Initialize Config
    config = AppConfig.load() # Load from scoring.yaml by default
    if args.season: config.runtime.season = args.season
    if args.week: config.runtime.week = args.week
    if args.simulations: config.runtime.n_simulations = args.simulations
    if args.version: config.runtime.version = args.version
    
    command = args.command or "all"

    warnings.filterwarnings("ignore", category=FutureWarning)
    pd.set_option("display.max_rows", 100)
    pd.set_option("display.max_columns", 400)
    
    years_to_load = set()
    
    if command in ["project", "all"]:
        years_to_load.add(config.runtime.season)
        years_to_load.add(config.runtime.season - 1)
        
    if command in ["backtest", "all"]:
        # Hardcoded backtest year for now
        years_to_load.add(2018) 
        years_to_load.add(2017)

    print(f"Loading data for years: {sorted(list(years_to_load))}")
    loader.clean_and_save_data(list(years_to_load))
    injuries.clean_and_save_data(list(years_to_load))
    pbp_data = loader.load_data(list(years_to_load))
    
    if command == "all":
        run_projections(pbp_data, config)
        run_backtest(pbp_data, config)
    elif command == "project":
        run_projections(pbp_data, config)
    elif command == "backtest":
        run_backtest(pbp_data, config)
