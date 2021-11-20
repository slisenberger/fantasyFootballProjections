import pandas as pd
import numpy as np
import nfl_data_py
from statsmodels.formula.api import mixedlm
from collections import defaultdict
from stats import injuries, teams
from data import loader

# Calculate statistics about players
from stats.util import prepend


def calculate(data, team_stats, season):
    data = data.loc[(data.play_type.isin(['no_play', 'pass', 'run', 'field_goal']))]
    roster_data = nfl_data_py.import_rosters(
        [season], columns=["player_id", "position", "player_name", "team"])


    receiver_data = data.loc[data.pass_attempt == 1]
    rel_air_yards = {
        "RB": receiver_data.loc[receiver_data.position_receiver == "RB"]["air_yards"].mean(),
        "WR": receiver_data.loc[receiver_data.position_receiver == "WR"]["air_yards"].mean(),
        "TE": receiver_data.loc[receiver_data.position_receiver == "TE"]["air_yards"].mean(),
        "ALL": receiver_data["air_yards"].mean()
    }
    rel_yac = {
        "RB": receiver_data.loc[receiver_data.position_receiver == "RB"]["yards_after_catch"].mean(),
        "WR": receiver_data.loc[receiver_data.position_receiver == "WR"]["yards_after_catch"].mean(),
        "TE": receiver_data.loc[receiver_data.position_receiver == "TE"]["yards_after_catch"].mean(),
        "ALL": receiver_data["yards_after_catch"].mean()
    }

    def get_pos_rel_air_yards(pos):
        if pos in rel_air_yards:
            return rel_air_yards[pos]
        else:
            return rel_air_yards["ALL"]

    def get_pos_rel_yac(pos):
        if pos in rel_yac:
            return rel_yac[pos]
        else:
            return rel_yac["ALL"]

    lg_avg_ypc = data.loc[data.rush == 1]["rushing_yards"].mean()
    lg_avg_ypc_middle = data.loc[data.rush == 1 & data.run_gap.isin(["guard","tackle"])]["rushing_yards"].mean()
    lg_avg_yac = data["yards_after_catch"].mean()
    lg_avg_air_yards = data["air_yards"].mean()
    lg_avg_scramble_yards = data.loc[data.qb_scramble == 1]["rushing_yards"].mean()

    weekly_team_stats = teams.calculate_weekly(data, season)
    weekly_player_stats = calculate_weekly(data, weekly_team_stats, season)

    receiver_targets = data.groupby("receiver_player_id")\
        .size().sort_values().to_frame(name='targets').reset_index()\
        .rename(columns={'receiver_player_id': 'player_id'})
    receiver_deep_targets = data.loc[data.air_yards >= 30].groupby("receiver_player_id")\
        .size().sort_values().to_frame(name='deep_targets').reset_index()\
        .rename(columns={'receiver_player_id': 'player_id'})
    receiver_red_zone_targets = data.loc[data.yardline_100 <= 10].groupby("receiver_player_id").size()\
        .sort_values().to_frame(name='red_zone_targets').reset_index()\
        .rename(columns={'receiver_player_id': 'player_id'})
    receiver_checkdown_targets = data.loc[data.air_yards < 0].groupby("receiver_player_id").size()\
        .sort_values().to_frame(name="checkdown_targets").reset_index()\
        .rename(columns={'receiver_player_id': 'player_id'})
    receiver_air_yards = data.groupby("receiver_player_id")["air_yards"].sum()\
        .sort_values().to_frame(name='air_yards').reset_index()\
        .rename(columns={'receiver_player_id': 'player_id'})
    receiver_air_yards_per_target = data.groupby("receiver_player_id")["air_yards"].mean() \
        .sort_values().to_frame(name='air_yards_per_target').reset_index() \
        .rename(columns={'receiver_player_id': 'player_id'})
    air_yards_est = compute_air_yards_estimator(receiver_data)
    receiver_yac = data.groupby("receiver_player_id")["yards_after_catch"].mean().sort_values()\
        .to_frame(name='yac').reset_index()\
        .rename(columns={'receiver_player_id': 'player_id'})
    yac_est = compute_yac_estimator(receiver_data)
    receiver_cpoe_est = compute_receiver_cpoe_estimator(data)
    deep_target_rate_est = compute_deep_target_rate_estimator(data)
    rushing_carries = data.loc[data.rush == 1].groupby("rusher_player_id").size().sort_values()\
        .to_frame(name="carries").reset_index().rename(columns={'rusher_player_id': 'player_id'})
    yards_per_carry = data.loc[data.rush == 1].groupby("rusher_player_id")["rushing_yards"].mean()\
        .to_frame(name="yards_per_carry").reset_index()\
        .rename(columns={'rusher_player_id': 'player_id'})
    ypc_est = compute_ypc_estimator(data)
    yards_per_carry_middle = data.loc[data.rush == 1 & data.run_gap.isin(["guard", "tackle"])].groupby(
        "rusher_player_id")["rushing_yards"].mean() \
        .to_frame(name="yards_per_carry_middle").reset_index() \
        .rename(columns={'rusher_player_id': 'player_id'})
    ypc_middle_est = compute_ypc_middle_estimator(data)
    red_zone_carries = data.loc[data.rush==1].loc[data.yardline_100 <= 10].groupby("rusher_player_id").size()\
        .sort_values().to_frame(name="red_zone_carries").reset_index()\
        .rename(columns={'rusher_player_id': 'player_id'})
    big_carries = data.loc[data.rush == 1].loc[data.rushing_yards >= 10].groupby("rusher_player_id").size() \
        .sort_values().to_frame(name="big_carries").reset_index() \
        .rename(columns={'rusher_player_id': 'player_id'})
    big_carry_rate_est = compute_big_carry_rate_estimator(data)
    cpoe = data.groupby("passer_player_id")["cpoe"].mean() \
        .to_frame(name="cpoe").reset_index() \
        .rename(columns={'passer_player_id': 'player_id'})
    cpoe_est = compute_cpoe_estimator(data)
    int = data.groupby("passer_player_id").size() \
        .to_frame(name="interceptions").reset_index() \
        .rename(columns={'passer_player_id': 'player_id'})
    pass_attempts = data.groupby("passer_player_id").size() \
        .to_frame(name="pass_attempts").reset_index() \
        .rename(columns={'passer_player_id': 'player_id'})
    scramble_rate_estimator = compute_scramble_rate_estimator(data)
    yards_per_scramble_estimator = compute_yards_per_scramble_estimator(data)
    kick_attempts = data.loc[data.field_goal_attempt == True].groupby("kicker_player_id").size() \
        .to_frame(name="kick_attempts").reset_index() \
        .rename(columns={'kicker_player_id': 'player_id'})
    all_players = build_player_id_map(data)
    all_teams = build_player_team_map(data)
    offense_stats = receiver_targets\
        .merge(receiver_deep_targets,how="outer",on="player_id")\
        .merge(receiver_red_zone_targets,how="outer", on="player_id")\
        .merge(receiver_checkdown_targets,how="outer", on="player_id")\
        .merge(receiver_air_yards,how="outer", on="player_id") \
        .merge(receiver_air_yards_per_target, how="outer", on="player_id") \
        .merge(air_yards_est, how="outer", on="player_id") \
        .merge(deep_target_rate_est, how="outer", on="player_id") \
        .merge(receiver_yac, how="outer", on="player_id") \
        .merge(yac_est, how="outer", on="player_id") \
        .merge(receiver_cpoe_est, how="outer", on="player_id") \
        .merge(rushing_carries, how="outer", on="player_id") \
        .merge(yards_per_carry, how="outer", on="player_id") \
        .merge(ypc_est, how="outer", on="player_id") \
        .merge(yards_per_carry_middle, how="outer", on="player_id") \
        .merge(ypc_middle_est, how="outer", on="player_id") \
        .merge(red_zone_carries, how="outer", on="player_id") \
        .merge(big_carries, how="outer", on="player_id")\
        .merge(big_carry_rate_est, how="outer", on="player_id") \
        .merge(cpoe, how="outer", on="player_id") \
        .merge(cpoe_est, how="outer", on="player_id") \
        .merge(pass_attempts, how="outer", on="player_id")\
        .merge(scramble_rate_estimator, how="outer", on="player_id") \
        .merge(yards_per_scramble_estimator, how="outer", on="player_id") \
        .merge(kick_attempts, how="outer", on="player_id")
    offense_stats['checkdown_percentage'] = offense_stats["checkdown_targets"] / offense_stats["targets"]


    # Set metadata
    offense_stats = offense_stats.merge(roster_data, on="player_id", how="left")
    team_targets = team_stats[["team", "targets", "carries", "red_zone_targets", "red_zone_carries"]]
    offense_stats = offense_stats.merge(team_targets, how="outer", on="team", suffixes=[None,"_team"])
    offense_stats['target_percentage'] = offense_stats.apply(lambda row: row["targets"] / row["targets_team"], axis=1)
    offense_stats['carry_percentage'] = offense_stats.apply(lambda row: row["carries"] / row["carries_team"], axis=1)
    targets_est = weekly_target_share_estimator(weekly_player_stats)
    carries_est = weekly_carry_share_estimator(weekly_player_stats)
    offense_stats = offense_stats.merge(targets_est, how="outer", on="player_id")
    offense_stats = offense_stats.merge(carries_est, how="outer", on="player_id")
    offense_stats["target_share_est"].fillna(0, inplace=True)
    offense_stats["carry_share_est"].fillna(0, inplace=True)
    offense_stats['red_zone_target_percentage'] = offense_stats.apply(lambda row: row["red_zone_targets"] / row["red_zone_targets_team"], axis=1)
    offense_stats['red_zone_carry_percentage'] = offense_stats.apply(lambda row: row["red_zone_carries"] / row["red_zone_carries_team"], axis=1)
    offense_stats['relative_ypc'] = offense_stats["yards_per_carry"] / lg_avg_ypc
    offense_stats['relative_ypc_est'] = offense_stats["ypc_est"] / lg_avg_ypc
    offense_stats['relative_ypc_middle'] = offense_stats["yards_per_carry_middle"] / lg_avg_ypc_middle
    offense_stats['relative_ypc_middle_est'] = offense_stats["ypc_middle_est"] / lg_avg_ypc_middle
    offense_stats['relative_yac'] = offense_stats.apply(
        lambda row: row["yac"] / get_pos_rel_yac(row["position"]), axis=1)
    offense_stats['relative_yac_est'] = offense_stats.apply(
        lambda row: row["yac_est"] / get_pos_rel_yac(row["position"]), axis=1).fillna(1)

    offense_stats['relative_air_yards'] = offense_stats.apply(
        lambda row: row["air_yards_per_target"] / get_pos_rel_air_yards(row["position"]), axis=1)
    offense_stats['relative_air_yards_est'] = offense_stats.apply(
        lambda row: row["air_yards_est"] / get_pos_rel_air_yards(row["position"]), axis=1).fillna(1)
    offense_stats['relative_yards_per_scramble_est'] = offense_stats["yards_per_scramble_est"] / lg_avg_scramble_yards

    # Experimental modeling to use MLM. Will take some work to get right.
    # estimate_cpoe_attribution(data)

    # Filter only to players that are playing this season.
    all_player_ids = roster_data["player_id"].to_list()
    offense_stats = offense_stats.loc[offense_stats.player_id.isin(all_player_ids)]
    offense_stats.to_csv('offense_stats.csv')
    return offense_stats

def estimate_cpoe_attribution(data):
    data["group"] = 1
    data = data.loc[~data.cpoe.isnull()]
    vcf = {"passer_player_id": "0 + C(passer_player_id)", "receiver_player_id": "0 + C(receiver_player_id)"}
    model = mixedlm("cpoe ~ qb_hit", groups=data["group"], vc_formula=vcf, data=data)
    mdf = model.fit()
    print(mdf.summary())
    print(mdf.random_effects)

def compute_cpoe_estimator(data):
    cpoe_prior = 0
    # Essentially, use the last 500 pass window to judge completion.
    cpoe_span = 500
    biased_cpoe = data.groupby(["passer_player_id"])["cpoe"].apply(lambda d: prepend(d, cpoe_prior)).to_frame()
    cpoe_est = biased_cpoe.groupby(["passer_player_id"])["cpoe"].apply(lambda x: x.ewm(span=cpoe_span, adjust=False).mean()).to_frame()
    cpoe_est_now = cpoe_est.groupby(["passer_player_id"]).tail(1).reset_index().rename(columns={'passer_player_id': 'player_id', 'cpoe': 'cpoe_est'})[["player_id", "cpoe_est"]]
    return cpoe_est_now

def compute_scramble_rate_estimator(data):
    data = data.loc[data["pass"] == 1]
    scramble_prior = data.loc[data.qb_scramble == True].shape[0] / data.shape[0]
    # Essentially, use the last 500 pass window to judge completion.
    scramble_span = 500
    biased_scramble = data.groupby(["passer_id"])["qb_scramble"].apply(lambda d: prepend(d, scramble_prior)).to_frame()
    scramble_est = biased_scramble.groupby(["passer_id"])["qb_scramble"].apply(lambda x: x.ewm(span=scramble_span, adjust=False).mean()).to_frame()
    return scramble_est.groupby(["passer_id"]).tail(1).reset_index().rename(
        columns={'passer_id': 'player_id', 'qb_scramble': 'scramble_rate_est'})[["player_id", "scramble_rate_est"]]

def compute_big_carry_rate_estimator(data):
    # Only use rushes, avoid QB scrambles.
    data = data.loc[data["rush"] == 1]
    data.loc[data.rushing_yards >=10, "big_carry"] = 1
    data["big_carry"].fillna(0, inplace=True)
    big_carry_prior = data.loc[data.big_carry == 1].shape[0] / data.shape[0]
    big_carry_span = 160
    biased = data.groupby(["rusher_player_id"])["big_carry"].apply(lambda d: prepend(d, big_carry_prior)).to_frame()
    big_carry_est = biased.groupby(["rusher_player_id"])["big_carry"].apply(lambda x: x.ewm(span=big_carry_span, adjust=False).mean()).to_frame()
    return big_carry_est.groupby(["rusher_player_id"]).tail(1).reset_index().rename(
        columns={'rusher_player_id': 'player_id', 'big_carry': 'big_carry_rate_est'})[["player_id", "big_carry_rate_est"]]

def compute_deep_target_rate_estimator(data):
    data.loc[data.air_yards >= 30, "deep_target"] = 1
    data["deep_target"].fillna(0, inplace=True)
    deep_target_prior = 0
    deep_target_span = 500
    biased = data.groupby(["receiver_player_id"])["deep_target"].apply(lambda d: prepend(d, deep_target_prior)).to_frame()
    deep_target_est = biased.groupby(["receiver_player_id"])["deep_target"].apply(lambda x: x.ewm(span=deep_target_span, adjust=False).mean()).to_frame()
    return deep_target_est.groupby(["receiver_player_id"]).tail(1).reset_index().rename(
        columns={'receiver_player_id': 'player_id', 'deep_target': 'deep_target_rate_est'})[["player_id", "deep_target_rate_est"]]

def compute_yards_per_scramble_estimator(data):
    data = data.loc[data["qb_scramble"] == 1]
    # Essentially, use the last 100 scramble window to judge talent.
    scramble_prior = data["rushing_yards"].mean()
    scramble_span = 160
    biased_scramble = data.groupby(["passer_id"])["rushing_yards"].apply(lambda d: prepend(d, scramble_prior)).to_frame()
    scramble_est = biased_scramble.groupby(["passer_id"])["rushing_yards"].apply(lambda x: x.ewm(span=scramble_span, adjust=False).mean()).to_frame()
    return scramble_est.groupby(["passer_id"]).tail(1).reset_index().rename(
        columns={'passer_id': 'player_id', 'rushing_yards': 'yards_per_scramble_est'})[["player_id", "yards_per_scramble_est"]]

def compute_receiver_cpoe_estimator(data):
    cpoe_prior = 0
    # Essentially, use the last 200 target window to judge completion.
    cpoe_span = 200
    biased_cpoe = data.groupby(["receiver_player_id"])["cpoe"].apply(lambda d: prepend(d, cpoe_prior)).to_frame()
    cpoe_est = biased_cpoe.groupby(["receiver_player_id"])["cpoe"].apply(lambda x: x.ewm(span=cpoe_span, adjust=False).mean()).to_frame()
    cpoe_est_now = cpoe_est.groupby(["receiver_player_id"]).tail(1).reset_index().rename(columns={'receiver_player_id': 'player_id', 'cpoe': 'receiver_cpoe_est'})[["player_id", "receiver_cpoe_est"]]
    return cpoe_est_now

def compute_air_yards_estimator(data):
    air_yards_priors = {
        "RB": data.loc[data.position_receiver == "RB"]["air_yards"].mean(),
        "WR": data.loc[data.position_receiver == "WR"]["air_yards"].mean(),
        "TE": data.loc[data.position_receiver == "TE"]["air_yards"].mean(),
        "ALL": data["air_yards"].mean()
    }

    def get_prior(pos):
        if pos in air_yards_priors:
            return air_yards_priors[pos]
        else:
            return air_yards_priors["ALL"]

    # Essentially, use the last 200 target window to judge completion.
    air_yards_span = 200
    all_biased_data = []
    # For each position, get that position's data, break down by receiver ID, and apply a special prior
    for pos in ["RB", "WR", "TE", "FB"]:
      all_biased_data.append(
          data.loc[data.position_receiver == pos].groupby(["receiver_player_id"])["air_yards"]
              .apply(lambda d: prepend(d, get_prior(pos))).to_frame())
    biased_ay = pd.concat(all_biased_data)
    ay_est = biased_ay.groupby(["receiver_player_id"])["air_yards"].apply(lambda x: x.ewm(span=air_yards_span, adjust=False).mean()).to_frame()
    ay_est_now = ay_est.groupby(["receiver_player_id"]).tail(1).reset_index().rename(columns={'receiver_player_id': 'player_id', 'air_yards': 'air_yards_est'})[["player_id", "air_yards_est"]]
    return ay_est_now

def compute_ypc_estimator(data):
    data = data.loc[data.rush == 1]
    ypc_prior = data["rushing_yards"].mean()
    ypc_span = 160
    biased_ypc = data.groupby(["rusher_player_id"])["rushing_yards"].apply(lambda d: prepend(d, ypc_prior)).to_frame()
    ypc_est = biased_ypc.groupby(["rusher_player_id"])["rushing_yards"].apply(lambda x: x.ewm(span=ypc_span, adjust=False).mean()).to_frame()
    ypc_est_now = ypc_est.groupby(["rusher_player_id"]).tail(1).reset_index().rename(columns={'rusher_player_id': 'player_id', 'rushing_yards': 'ypc_est'})[[
        "player_id", "ypc_est"
    ]]
    return ypc_est_now

def compute_ypc_middle_estimator(data):
    data = data.loc[data.rush == 1 & data.run_gap.isin(["guard", "tackle"])]
    ypc_prior = data["rushing_yards"].mean()
    ypc_span = 160
    biased_ypc = data.groupby(["rusher_player_id"])["rushing_yards"].apply(lambda d: prepend(d, ypc_prior)).to_frame()
    ypc_est = biased_ypc.groupby(["rusher_player_id"])["rushing_yards"].apply(lambda x: x.ewm(span=ypc_span, adjust=False).mean()).to_frame()
    ypc_est_now = ypc_est.groupby(["rusher_player_id"]).tail(1).reset_index().rename(columns={'rusher_player_id': 'player_id', 'rushing_yards': 'ypc_middle_est'})[[
        "player_id", "ypc_middle_est"
    ]]
    return ypc_est_now

# Use an ewma with a bias to estimate a player's chance of receiving checkdowns.
def checkdown_estimator(data):
    pass

def compute_big_carry_estimator(data):
    pass

def compute_yac_estimator(data):
    yac_priors = {
        "RB": data.loc[data.position_receiver == "RB"]["yards_after_catch"].mean(),
        "WR": data.loc[data.position_receiver == "WR"]["yards_after_catch"].mean(),
        "TE": data.loc[data.position_receiver == "TE"]["yards_after_catch"].mean(),
        "ALL": data["yards_after_catch"].mean()
    }
    def get_prior(pos):
        if pos in yac_priors:
            return yac_priors[pos]
        else:
            return yac_priors["ALL"]
    yac_span = 140
    all_biased_data = []
    # For each position, get that position's data, break down by receiver ID, and apply a special prior
    for pos in ["RB", "WR", "TE", "FB"]:
        all_biased_data.append(
            data.loc[data.position_receiver == pos].groupby(["receiver_player_id"])["yards_after_catch"]
                .apply(lambda d: prepend(d, get_prior(pos))).to_frame())
    biased_yac = pd.concat(all_biased_data)
    yac_est = biased_yac.groupby(["receiver_player_id"])["yards_after_catch"].apply(lambda x: x.ewm(span=yac_span, adjust=False).mean()).to_frame()
    yac_est_now = yac_est.groupby(["receiver_player_id"]).tail(1).reset_index().rename(columns={'receiver_player_id': 'player_id', 'yards_after_catch': 'yac_est'})[
        ["player_id", "yac_est"]
    ]
    return yac_est_now

def calculate_weekly(data, weekly_team_stats, season):
    data = data.loc[(data.play_type.isin(['no_play', 'pass', 'run', 'field_goal']))]
    data = data.loc[data.season == season]
    all_players = build_player_id_map(data)
    all_teams = build_player_team_map(data)
    weekly_receiver_data = data.groupby(["receiver_player_id", "week"])
    weekly_rusher_data = data.loc[data.rush == 1].groupby(["rusher_player_id", "week"])
    weekly_targets = weekly_receiver_data.size().sort_values().to_frame(name='targets_wk').reset_index().rename(columns={'receiver_player_id': 'player_id'})
    weekly_red_zone_targets = data.loc[data.yardline_100 <= 10].groupby(["receiver_player_id", "week"]).size().sort_values().to_frame(name='red_zone_targets_wk').reset_index().rename(columns={'receiver_player_id': 'player_id'})
    weekly_deep_targets = data.loc[data.air_yards >= 30].groupby(["receiver_player_id", "week"]).size().sort_values().to_frame(name='deep_targets_wk').reset_index().rename(columns={'receiver_player_id': 'player_id'})
    weekly_air_yards_target = weekly_receiver_data["air_yards"].mean().sort_values().to_frame(name='air_yards_per_target_wk').reset_index().rename(columns={'receiver_player_id': 'player_id'})
    weekly_carries = weekly_rusher_data.size().sort_values().to_frame(name="carries_wk").reset_index().rename(columns={'rusher_player_id': 'player_id'})
    weekly_red_zone_carries = data.loc[data.rush == 1].loc[data.yardline_100 <= 10].groupby(["rusher_player_id", "week"]).size().sort_values().to_frame(name="red_zone_carries_wk").reset_index().rename(columns={'rusher_player_id': 'player_id'})
    weekly_yards_per_carry = weekly_rusher_data["rushing_yards"].mean().sort_values().to_frame(name='yards_per_carry_wk').reset_index().rename(columns={'rusher_player_id':'player_id'})

    weekly_stats = weekly_targets\
        .merge(weekly_red_zone_targets, how="outer", on=["player_id", "week"])\
        .merge(weekly_deep_targets, how="outer", on=["player_id", "week"])\
        .merge(weekly_air_yards_target, how="outer", on=["player_id", "week"])\
        .merge(weekly_carries, how="outer", on=["player_id", "week"])\
        .merge(weekly_red_zone_carries, how="outer", on=["player_id", "week"])\
        .merge(weekly_yards_per_carry, how="outer", on=["player_id", "week"])\
        .merge(get_weekly_injuries(season), how="outer", on=["player_id", "week"])

    weekly_stats["available"] = weekly_stats["available"].fillna(True)
    roster_data = nfl_data_py.import_rosters([season], columns=["player_id", "position", "team"])
    weekly_stats = weekly_stats.merge(roster_data, on="player_id", how="left")
    weekly_team_targets = weekly_team_stats[["team", "week", "targets_wk", "carries_wk"]]
    weekly_stats = weekly_stats.merge(weekly_team_targets, how="outer", on=["team", "week"], suffixes=[None, "_team"])

    weekly_stats['target_percentage_wk'] = weekly_stats.apply(lambda row: compute_target_percentage(row), axis=1)
    weekly_stats['carry_percentage_wk'] = weekly_stats.apply(lambda row: compute_carry_percentage(row), axis=1)
    weekly_stats['player_name'] = weekly_stats.apply(lambda row: all_players[row['player_id']], axis=1)

    weekly_stats.to_csv("weekly_stats.csv")
    return weekly_stats

def compute_target_percentage(row):
    if row["available"]:
        return row["targets_wk"] / row["targets_wk_team"]
    else:
        return np.nan

def compute_carry_percentage(row):
    if row["available"]:
        return row["carries_wk"] / row["carries_wk_team"]
    else:
        return np.nan


def get_weekly_injuries(season):
    injured = ["IR", "IR-R", "IR-PUP", "IR-NFI", "Suspended", "COVID-IR", "Out"]
    all_injuries = injuries.load_historical_data([season])
    all_injuries = all_injuries.loc[all_injuries["status"].isin(injured)]
    all_injuries = all_injuries.assign(available=False)
    return all_injuries[["week", "player_id", "available"]]


def weekly_target_share_estimator(weekly_data):
    target_prior = 0
    # One season's worth of games. This may want to be larger (to incorporate past seasons of targets).
    target_span = 17
    biased_targets = weekly_data.groupby(["player_id"])["target_percentage_wk"].apply(
        lambda d: prepend(d, target_prior)).to_frame()
    targets_est = biased_targets.groupby(["player_id"])["target_percentage_wk"].apply(
        lambda x: x.ewm(span=target_span, adjust=True, ignore_na=True).mean()).to_frame()
    targets_est_now = targets_est.groupby(["player_id"]).tail(1).reset_index().rename(
        columns={'target_percentage_wk': 'target_share_est'})[
        ["player_id", "target_share_est"]
    ]
    return targets_est_now

def weekly_carry_share_estimator(weekly_data):
    carry_prior = 0
    carry_span = 17
    biased_carries = weekly_data.groupby(["player_id"])["carry_percentage_wk"].apply(
        lambda d: prepend(d, carry_prior)).to_frame()
    carries_est = biased_carries.groupby(["player_id"])["carry_percentage_wk"].apply(
        lambda x: x.ewm(span=carry_span, adjust=True, ignore_na=True).mean()).to_frame()
    carries_est_now = carries_est.groupby(["player_id"]).tail(1).reset_index().rename(
        columns={'carry_percentage_wk': 'carry_share_est'})[
        ["player_id", "carry_share_est"]
    ]
    return carries_est_now

def build_player_id_map(data):
    all_players = defaultdict(lambda: "Unknown")
    for i in range(len(data)):
        row = data.iloc[i]
        if row.passer_player_id not in all_players:
            all_players[row.passer_player_id] = row.passer_player_name
        if row.receiver_player_id not in all_players:
            all_players[row.receiver_player_id] = row.receiver_player_name
        if row.rusher_player_id not in all_players:
            all_players[row.rusher_player_id] = row.rusher_player_name
        if row.kicker_player_id not in all_players:
            all_players[row.kicker_player_id] = row.kicker_player_name

    return all_players

def build_player_team_map(data):
    player_teams = defaultdict(lambda: "Unknown")
    for i in range(len(data)):
        row = data.iloc[i]
        if row.passer_player_id not in player_teams:
            player_teams[row.passer_player_id] = row.posteam
        if row.receiver_player_id not in player_teams:
            player_teams[row.receiver_player_id] = row.posteam
        if row.rusher_player_id not in player_teams:
            player_teams[row.rusher_player_id] = row.posteam
        if row.kicker_player_id not in player_teams:
            player_teams[row.kicker_player_id] = row.posteam

    return player_teams

