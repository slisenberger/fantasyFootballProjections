import pandas as pd
import numpy as np
from typing import Dict, Any
from data import nfl_client as nfl_data_py
from statsmodels.formula.api import mixedlm
from collections import defaultdict
from stats import injuries, teams
from stats.util import _compute_estimator_vectorized

# Use previous 1000 passes to judge passers
passer_span = 1000
# Use previous 150 targets to judge receivers
receiver_span = 150
# Use previous 150 rushes to judge rushers
rusher_span = 150


def calculate(data: pd.DataFrame, snap_counts: pd.DataFrame, team_stats: pd.DataFrame, season: int, week: int) -> pd.DataFrame:
    """Calculates comprehensive player statistics and estimators for a given season and week.

    This function processes raw play-by-play data, merges roster and depth chart information,
    and computes various advanced metrics and EWMA-smoothed estimators for each player.

    Args:
        data (pd.DataFrame): Raw play-by-play data (PBP).
            Expected columns include: 'play_type', 'pass_attempt', 'rush', 'qb_scramble',
            'air_yards', 'yards_after_catch', 'receiver_player_id', 'rusher_player_id',
            'run_gap', 'passer_player_id', 'cpoe', 'field_goal_attempt', 'kicker_player_id',
            'yardline_100', 'season', 'week', 'posteam', 'defteam', 'position_receiver'.
        snap_counts (pd.DataFrame): Snap count data from nflreadpy.
        team_stats (pd.DataFrame): Pre-calculated team statistics and estimators.
            Expected columns include: 'team', various 'offense_oe_est', 'defense_oe_est',
            'offense_sack_rate_est', 'defense_sack_rate_est', etc.
        season (int): The current season for which to calculate player stats.
        week (int): The current week within the season.

    Returns:
        pd.DataFrame: A DataFrame containing calculated player statistics and estimators,
                      including share metrics, relative efficiency, and fantasy-relevant
                      indicators, merged with player metadata (name, position, team).
    """
    data = data.copy() # Ensure data is a copy to prevent SettingWithCopyWarning
    data = data.loc[(data.play_type.isin(["no_play", "pass", "run", "field_goal"]))]
    data = data.sort_values('week') # Ensure data is sorted by week for EWMA calculations

    # Load roster data for current season (only needed for player metadata)
    roster_data = nfl_data_py.import_seasonal_rosters(
        [season], columns=["player_id", "position", "player_name", "team"]
    ).drop_duplicates(subset="player_id")

    depth_charts = nfl_data_py.import_depth_charts([season])
    
    if "week" in depth_charts.columns:
        depth_charts = depth_charts.loc[depth_charts.week == week]
    else:
        # Handle Live Data Format (Missing week, different column names)
        depth_charts = depth_charts.rename(columns={
            "pos_rank": "depth_team",
            "pos_abb": "position" 
        })

    # Ensure depth_team is numeric
    depth_charts["depth_team"] = pd.to_numeric(depth_charts["depth_team"], errors="coerce")

    qb1s = depth_charts.loc[
        (depth_charts.position == "QB") & (depth_charts.depth_team == 1)
    ].rename(columns={"gsis_id": "player_id", "depth_team": "starting_qb"})[
        ["player_id", "starting_qb"]
    ]
    k1s = depth_charts.loc[
        (depth_charts.position == "K") & (depth_charts.depth_team == 1)
    ].rename(columns={"gsis_id": "player_id", "depth_team": "starting_k"})[
        ["player_id", "starting_k"]
    ]

    receiver_data = data.loc[data.pass_attempt == 1]
    rel_air_yards = {
        "RB": receiver_data.loc[receiver_data.position_receiver == "RB"][
            "air_yards"
        ].mean(),
        "WR": receiver_data.loc[receiver_data.position_receiver == "WR"][
            "air_yards"
        ].mean(),
        "TE": receiver_data.loc[receiver_data.position_receiver == "TE"][
            "air_yards"
        ].mean(),
        "ALL": receiver_data["air_yards"].mean(),
    }
    rel_yac = {
        "RB": receiver_data.loc[receiver_data.position_receiver == "RB"][
            "yards_after_catch"
        ].mean(),
        "WR": receiver_data.loc[receiver_data.position_receiver == "WR"][
            "yards_after_catch"
        ].mean(),
        "TE": receiver_data.loc[receiver_data.position_receiver == "TE"][
            "yards_after_catch"
        ].mean(),
        "ALL": receiver_data["yards_after_catch"].mean(),
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
    lg_avg_ypc_middle = data.loc[
        data.rush == 1 & data.run_gap.isin(["guard", "tackle"])
    ]["rushing_yards"].mean()
    data["yards_after_catch"].mean()
    data["air_yards"].mean()
    lg_avg_scramble_yards = data.loc[data.qb_scramble == 1]["rushing_yards"].mean()

    weekly_team_stats = teams.calculate_weekly(data, season)
    weekly_player_stats = calculate_weekly(data, snap_counts, weekly_team_stats, season)

    receiver_targets = (
        data.groupby("receiver_player_id")["receiver_player_id"]
        .count()
        .to_frame(name="targets")
        .reset_index()
        .rename(columns={"receiver_player_id": "player_id"})
    )
    receiver_deep_targets = (
        data.loc[data.air_yards >= 30]
        .groupby("receiver_player_id")["receiver_player_id"]
        .count()
        .to_frame(name="deep_targets")
        .reset_index()
        .rename(columns={"receiver_player_id": "player_id"})
    )
    receiver_red_zone_targets = (
        data.loc[data.yardline_100 <= 10]
        .groupby("receiver_player_id")["receiver_player_id"]
        .count()
        .to_frame(name="red_zone_targets")
        .reset_index()
        .rename(columns={"receiver_player_id": "player_id"})
    )
    receiver_checkdown_targets = (
        data.loc[data.air_yards < 0]
        .groupby("receiver_player_id")["receiver_player_id"]
        .count()
        .to_frame(name="checkdown_targets")
        .reset_index()
        .rename(columns={"receiver_player_id": "player_id"})
    )
    receiver_air_yards = (
        data.groupby("receiver_player_id")["air_yards"]
        .sum()
        .sort_values()
        .to_frame(name="air_yards")
        .reset_index()
        .rename(columns={"receiver_player_id": "player_id"})
    )
    receiver_air_yards_per_target = (
        data.groupby("receiver_player_id")["air_yards"]
        .mean()
        .sort_values()
        .to_frame(name="air_yards_per_target")
        .reset_index()
        .rename(columns={"receiver_player_id": "player_id"})
    )
    air_yards_est = compute_air_yards_estimator(receiver_data)
    receiver_yac = (
        data.groupby("receiver_player_id")["yards_after_catch"]
        .mean()
        .sort_values()
        .to_frame(name="yac")
        .reset_index()
        .rename(columns={"receiver_player_id": "player_id"})
    )
    yac_est = compute_yac_estimator(receiver_data)
    receiver_cpoe_est = compute_receiver_cpoe_estimator(data)
    deep_target_rate_est = compute_deep_target_rate_estimator(data)
    rushing_carries = (
        data.loc[data.rush == 1]
        .groupby("rusher_player_id")["rusher_player_id"]
        .count()
        .to_frame(name="carries")
        .reset_index()
        .rename(columns={"rusher_player_id": "player_id"})
    )
    yards_per_carry = (
        data.loc[data.rush == 1]
        .groupby("rusher_player_id")["rushing_yards"]
        .mean()
        .to_frame(name="yards_per_carry")
        .reset_index()
        .rename(columns={"rusher_player_id": "player_id"})
    )
    ypc_est = compute_ypc_estimator(data)
    yards_per_carry_middle = (
        data.loc[data.rush == 1 & data.run_gap.isin(["guard", "tackle"])]
        .groupby("rusher_player_id")["rushing_yards"]
        .mean()
        .to_frame(name="yards_per_carry_middle")
        .reset_index()
        .rename(columns={"rusher_player_id": "player_id"})
    )
    ypc_middle_est = compute_ypc_middle_estimator(data)
    red_zone_carries = (
        data.loc[data.rush == 1]
        .loc[data.yardline_100 <= 10]
        .groupby("rusher_player_id")["rusher_player_id"]
        .count()
        .sort_values()
        .to_frame(name="red_zone_carries")
        .reset_index()
        .rename(columns={"rusher_player_id": "player_id"})
    )
    big_carries = (
        data.loc[data.rush == 1]
        .loc[data.rushing_yards >= 10]
        .groupby("rusher_player_id")["rusher_player_id"]
        .count()
        .sort_values()
        .to_frame(name="big_carries")
        .reset_index()
        .rename(columns={"rusher_player_id": "player_id"})
    )
    big_carry_rate_est = compute_big_carry_rate_estimator(data)
    cpoe = (
        data.groupby("passer_player_id")["cpoe"]
        .mean()
        .to_frame(name="cpoe")
        .reset_index()
        .rename(columns={"passer_player_id": "player_id"})
    )
    cpoe_est = compute_cpoe_estimator(data)
    (
        data.groupby("passer_player_id")
        .size()
        .to_frame(name="interceptions")
        .reset_index()
        .rename(columns={"passer_player_id": "player_id"})
    )
    pass_attempts = (
        data.groupby("passer_player_id")
        .size()
        .to_frame(name="pass_attempts")
        .reset_index()
        .rename(columns={"passer_player_id": "player_id"})
    )
    scramble_rate_estimator = compute_scramble_rate_estimator(data)
    yards_per_scramble_estimator = compute_yards_per_scramble_estimator(data)
    kick_attempts = (
        data.loc[data.field_goal_attempt == 1]
        .groupby("kicker_player_id")
        .size()
        .to_frame(name="kick_attempts")
        .reset_index()
        .rename(columns={"kicker_player_id": "player_id"})
    )
    
    # Mobile QB Classification (>20 rushing yards per game)
    qb_ids_list = roster_data.loc[roster_data.position == 'QB', 'player_id']
    rush_stats_qb = data[data['rush'] == 1].groupby('rusher_player_id').agg({
        'rushing_yards': 'sum',
        'game_id': 'nunique'
    })
    rush_stats_qb['ypg'] = rush_stats_qb['rushing_yards'] / rush_stats_qb['game_id']
    mobile_qb_ids = rush_stats_qb[(rush_stats_qb.index.isin(qb_ids_list)) & (rush_stats_qb['ypg'] > 20.0)].index.to_list()
    mobile_df = pd.DataFrame({'player_id': mobile_qb_ids, 'is_mobile': 1})

    # Useless calls removed from here
    offense_stats = (
        receiver_targets.merge(receiver_deep_targets, how="outer", on="player_id")
        .merge(receiver_red_zone_targets, how="outer", on="player_id")
        .merge(receiver_checkdown_targets, how="outer", on="player_id")
        .merge(receiver_air_yards, how="outer", on="player_id")
        .merge(receiver_air_yards_per_target, how="outer", on="player_id")
        .merge(air_yards_est, how="outer", on="player_id")
        .merge(deep_target_rate_est, how="outer", on="player_id")
        .merge(receiver_yac, how="outer", on="player_id")
        .merge(yac_est, how="outer", on="player_id")
        .merge(receiver_cpoe_est, how="outer", on="player_id")
        .merge(rushing_carries, how="outer", on="player_id")
        .merge(yards_per_carry, how="outer", on="player_id")
        .merge(ypc_est, how="outer", on="player_id")
        .merge(yards_per_carry_middle, how="outer", on="player_id")
        .merge(ypc_middle_est, how="outer", on="player_id")
        .merge(red_zone_carries, how="outer", on="player_id")
        .merge(big_carries, how="outer", on="player_id")
        .merge(big_carry_rate_est, how="outer", on="player_id")
        .merge(cpoe, how="outer", on="player_id")
        .merge(cpoe_est, how="outer", on="player_id")
        .merge(pass_attempts, how="outer", on="player_id")
        .merge(scramble_rate_estimator, how="outer", on="player_id")
        .merge(yards_per_scramble_estimator, how="outer", on="player_id")
        .merge(kick_attempts, how="outer", on="player_id")
        .merge(qb1s, how="left", on="player_id")
        .merge(k1s, how="left", on="player_id")
        .merge(mobile_df, how="left", on="player_id") # Added
    )
    offense_stats["is_mobile"] = offense_stats["is_mobile"].fillna(0).astype(int)
    
    offense_stats["checkdown_percentage"] = (
        offense_stats["checkdown_targets"] / offense_stats["targets"]
    )

    # Set metadata
    offense_stats = offense_stats.merge(roster_data, on="player_id", how="left")
    team_targets = team_stats[
        ["team", "targets", "carries", "red_zone_targets", "red_zone_carries"]
    ]
    offense_stats = offense_stats.merge(
        team_targets, how="outer", on="team", suffixes=[None, "_team"]
    )
    offense_stats["target_percentage"] = offense_stats.apply(
        lambda row: row["targets"] / row["targets_team"], axis=1
    )
    offense_stats["carry_percentage"] = offense_stats.apply(
        lambda row: row["carries"] / row["carries_team"], axis=1
    )
    targets_est = weekly_target_share_estimator(weekly_player_stats)
    carries_est = weekly_carry_share_estimator(weekly_player_stats)
    snaps_est = weekly_snap_share_estimator(weekly_player_stats)
    fgoe_est = weekly_fgoe_estimator(weekly_player_stats)
    offense_stats = offense_stats.merge(targets_est, how="outer", on="player_id")
    offense_stats = offense_stats.merge(carries_est, how="outer", on="player_id")
    offense_stats = offense_stats.merge(snaps_est, how="outer", on="player_id")
    offense_stats = offense_stats.merge(fgoe_est, how="outer", on="player_id")
    offense_stats["target_share_est"].fillna(0, inplace=True)
    offense_stats["carry_share_est"].fillna(0, inplace=True)
    offense_stats["snap_share_est"].fillna(0, inplace=True)
    offense_stats["fgoe_est"].fillna(0, inplace=True)
    rz_targets_est = weekly_redzone_target_share_estimator(weekly_player_stats)
    rz_carries_est = weekly_redzone_carry_share_estimator(weekly_player_stats)
    offense_stats = offense_stats.merge(rz_targets_est, how="outer", on="player_id")
    offense_stats = offense_stats.merge(rz_carries_est, how="outer", on="player_id")
    offense_stats["redzone_target_share_est"].fillna(0, inplace=True)
    offense_stats["redzone_carry_share_est"].fillna(0, inplace=True)

    offense_stats["red_zone_target_percentage"] = offense_stats.apply(
        lambda row: 0
        if row["red_zone_targets_team"] == 0
        else row["red_zone_targets"] / row["red_zone_targets_team"],
        axis=1,
    )
    offense_stats["red_zone_carry_percentage"] = offense_stats.apply(
        lambda row: 0
        if row["red_zone_carries_team"] == 0
        else row["red_zone_carries"] / row["red_zone_carries_team"],
        axis=1,
    )
    offense_stats["relative_ypc"] = offense_stats["yards_per_carry"] / lg_avg_ypc
    offense_stats["relative_ypc_est"] = offense_stats["ypc_est"] / lg_avg_ypc
    offense_stats["relative_ypc_middle"] = (
        offense_stats["yards_per_carry_middle"] / lg_avg_ypc_middle
    )
    offense_stats["relative_ypc_middle_est"] = (
        offense_stats["ypc_middle_est"] / lg_avg_ypc_middle
    )
    offense_stats["relative_yac"] = offense_stats.apply(
        lambda row: row["yac"] / get_pos_rel_yac(row["position"]), axis=1
    )
    offense_stats["relative_yac_est"] = offense_stats.apply(
        lambda row: row["yac_est"] / get_pos_rel_yac(row["position"]), axis=1
    ).fillna(1)

    offense_stats["relative_air_yards"] = offense_stats.apply(
        lambda row: row["air_yards_per_target"]
        / get_pos_rel_air_yards(row["position"]),
        axis=1,
    )
    AIR_YARDS_SHIFT = 15.0
    offense_stats["relative_air_yards_est"] = offense_stats.apply(
        lambda row: (row["air_yards_est"] + AIR_YARDS_SHIFT) / (get_pos_rel_air_yards(row["position"]) + AIR_YARDS_SHIFT),
        axis=1,
    ).fillna(1.0)
    offense_stats["relative_yards_per_scramble_est"] = (
        offense_stats["yards_per_scramble_est"] / lg_avg_scramble_yards
    )

    # Experimental modeling to use MLM. Will take some work to get right.
    # estimate_cpoe_attribution(data)

    # Filter only to players that are playing this season.
    all_player_ids = roster_data["player_id"].to_list()
    offense_stats = offense_stats.loc[offense_stats.player_id.isin(all_player_ids)]
    offense_stats = offense_stats.drop_duplicates(subset="player_id")
    offense_stats.to_csv("offense_stats.csv")
    return offense_stats


def estimate_cpoe_attribution(data: pd.DataFrame) -> None:
    data["group"] = 1
    data = data.loc[~data.cpoe.isnull()]
    vcf = {
        "passer_player_id": "0 + C(passer_player_id)",
        "receiver_player_id": "0 + C(receiver_player_id)",
    }
    model = mixedlm("cpoe ~ qb_hit", groups=data["group"], vc_formula=vcf, data=data)
    mdf = model.fit()
    print(mdf.summary())
    print(mdf.random_effects)


def compute_cpoe_estimator(data: pd.DataFrame) -> pd.DataFrame:
    cpoe_prior = 0
    priors_df = data[['passer_player_id']].drop_duplicates()
    priors_df['cpoe'] = cpoe_prior

    return _compute_estimator_vectorized(
        data,
        'passer_player_id',
        'cpoe',
        passer_span,
        priors_df,
        'cpoe_est'
    ).rename(columns={'passer_player_id': 'player_id'})


def compute_scramble_rate_estimator(data: pd.DataFrame) -> pd.DataFrame:
    data = data.loc[data["pass"] == 1]
    scramble_prior = data.loc[data.qb_scramble == 1].shape[0] / data.shape[0] if not data.empty else 0

    priors_df = data[['passer_id']].drop_duplicates()
    priors_df['qb_scramble'] = scramble_prior

    return _compute_estimator_vectorized(
        data,
        'passer_id',
        'qb_scramble',
        passer_span,
        priors_df,
        'scramble_rate_est'
    ).rename(columns={'passer_id': 'player_id'})


def compute_big_carry_rate_estimator(data: pd.DataFrame) -> pd.DataFrame:
    # Only use rushes, avoid QB scrambles.
    data = data.loc[data["rush"] == 1].copy()
    data.loc[data.rushing_yards >= 10, "big_carry"] = 1
    data["big_carry"].fillna(0, inplace=True)
    
    big_carry_prior = data.loc[data.big_carry == 1].shape[0] / data.shape[0] if not data.empty else 0
    
    priors_df = data[['rusher_player_id']].drop_duplicates()
    priors_df['big_carry'] = big_carry_prior
    
    return _compute_estimator_vectorized(
        data, 
        'rusher_player_id', 
        'big_carry', 
        rusher_span, 
        priors_df, 
        'big_carry_rate_est'
    ).rename(columns={'rusher_player_id': 'player_id'})


def compute_deep_target_rate_estimator(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    data.loc[data.air_yards >= 30, "deep_target"] = 1
    data["deep_target"].fillna(0, inplace=True)
    deep_target_prior = 0
    
    priors_df = data[['receiver_player_id']].drop_duplicates()
    priors_df['deep_target'] = deep_target_prior
    
    return _compute_estimator_vectorized(
        data, 
        'receiver_player_id', 
        'deep_target', 
        receiver_span, 
        priors_df, 
        'deep_target_rate_est'
    ).rename(columns={'receiver_player_id': 'player_id'})


def compute_yards_per_scramble_estimator(data: pd.DataFrame) -> pd.DataFrame:
    data = data.loc[data["qb_scramble"] == 1]
    scramble_prior = data["rushing_yards"].mean()
    
    priors_df = data[['passer_id']].drop_duplicates()
    priors_df['rushing_yards'] = scramble_prior
    
    return _compute_estimator_vectorized(
        data, 
        'passer_id', 
        'rushing_yards', 
        rusher_span, 
        priors_df, 
        'yards_per_scramble_est'
    ).rename(columns={'passer_id': 'player_id'})


def compute_receiver_cpoe_estimator(data: pd.DataFrame) -> pd.DataFrame:
    cpoe_prior = 0
    priors_df = data[['receiver_player_id']].drop_duplicates()
    priors_df['cpoe'] = cpoe_prior
    
    return _compute_estimator_vectorized(
        data, 
        'receiver_player_id', 
        'cpoe', 
        receiver_span, 
        priors_df, 
        'receiver_cpoe_est'
    ).rename(columns={'receiver_player_id': 'player_id'})


def compute_air_yards_estimator(data: pd.DataFrame) -> pd.DataFrame:
    air_yards_priors = {
        "RB": data.loc[data.position_receiver == "RB"]["air_yards"].mean(),
        "WR": data.loc[data.position_receiver == "WR"]["air_yards"].mean(),
        "TE": data.loc[data.position_receiver == "TE"]["air_yards"].mean(),
        "ALL": data["air_yards"].mean(),
    }

    def get_prior(pos):
        return air_yards_priors.get(pos, air_yards_priors["ALL"])

    # Generate Priors DataFrame
    priors_df = data[['receiver_player_id', 'position_receiver']].drop_duplicates('receiver_player_id')
    priors_df['air_yards'] = priors_df['position_receiver'].map(get_prior)
    
    # DEBUG
    neg_air = data[data['air_yards'] < -10]
    if not neg_air.empty:
        print(f"DEBUG: Found {len(neg_air)} plays with air_yards < -10")
        print(neg_air[['receiver_player_name', 'air_yards', 'season', 'week']].head())

    res = _compute_estimator_vectorized(
        data, 
        'receiver_player_id', 
        'air_yards', 
        receiver_span, 
        priors_df, 
        'air_yards_est'
    )
    
    # DEBUG Result
    neg_est = res[res['air_yards_est'] < -5]
    if not neg_est.empty:
        print(f"DEBUG: Found {len(neg_est)} players with air_yards_est < -5")
        print(neg_est.head())

    return res.rename(columns={'receiver_player_id': 'player_id'})


def compute_ypc_estimator(data: pd.DataFrame) -> pd.DataFrame:
    data = data.loc[data.rush == 1]
    ypc_prior = data["rushing_yards"].mean()
    
    priors_df = data[['rusher_player_id']].drop_duplicates()
    priors_df['rushing_yards'] = ypc_prior
    
    return _compute_estimator_vectorized(
        data, 
        'rusher_player_id', 
        'rushing_yards', 
        rusher_span, 
        priors_df, 
        'ypc_est'
    ).rename(columns={'rusher_player_id': 'player_id'})


def compute_ypc_middle_estimator(data: pd.DataFrame) -> pd.DataFrame:
    data = data.loc[data.rush == 1 & data.run_gap.isin(["guard", "tackle"])]
    ypc_prior = data["rushing_yards"].mean()
    
    priors_df = data[['rusher_player_id']].drop_duplicates()
    priors_df['rushing_yards'] = ypc_prior
    
    return _compute_estimator_vectorized(
        data, 
        'rusher_player_id', 
        'rushing_yards', 
        rusher_span, 
        priors_df, 
        'ypc_middle_est'
    ).rename(columns={'rusher_player_id': 'player_id'})


# Use an ewma with a bias to estimate a player's chance of receiving checkdowns.
def checkdown_estimator(data: pd.DataFrame) -> None:
    pass


def compute_big_carry_estimator(data: pd.DataFrame) -> None:
    pass


def compute_yac_estimator(data: pd.DataFrame) -> pd.DataFrame:
    yac_priors = {
        "RB": data.loc[data.position_receiver == "RB"]["yards_after_catch"].mean(),
        "WR": data.loc[data.position_receiver == "WR"]["yards_after_catch"].mean(),
        "TE": data.loc[data.position_receiver == "TE"]["yards_after_catch"].mean(),
        "ALL": data["yards_after_catch"].mean(),
    }

    def get_prior(pos: str) -> float:
        return yac_priors.get(pos, yac_priors["ALL"])

    priors_df = data[['receiver_player_id', 'position_receiver']].drop_duplicates('receiver_player_id')
    priors_df['yards_after_catch'] = priors_df['position_receiver'].map(get_prior)
    
    return _compute_estimator_vectorized(
        data, 
        'receiver_player_id', 
        'yards_after_catch', 
        receiver_span, 
        priors_df, 
        'yac_est'
    ).rename(columns={'receiver_player_id': 'player_id'})


def calculate_weekly(data: pd.DataFrame, snap_counts: pd.DataFrame, weekly_team_stats: pd.DataFrame, season: int) -> pd.DataFrame:
    """Calculates weekly player statistics for target and carry shares.

    This function aggregates play-by-play data on a weekly basis, computes player
    and team weekly totals, and derives weekly percentage shares (e.g., target share)
    adjusted for player availability (injuries).

    Args:
        data (pd.DataFrame): Raw play-by-play data (PBP).
            Expected columns include: 'play_type', 'rush', 'receiver_player_id',
            'rusher_player_id', 'yardline_100', 'season', 'week', 'posteam'.
        snap_counts (pd.DataFrame): Snap count data.
        weekly_team_stats (pd.DataFrame): Weekly team totals for targets, carries, etc.
            Expected columns include: 'team', 'season', 'week', 'targets_wk',
            'carries_wk', 'redzone_targets_wk', 'redzone_carries_wk'.
        season (int): The current season for which to calculate weekly stats.

    Returns:
        pd.DataFrame: A DataFrame containing weekly player statistics, including
                      target/carry percentages, and merged roster information.
    """
    data = data.loc[(data.play_type.isin(["no_play", "pass", "run", "field_goal"]))]
    data = data.sort_values(['season', 'week']) # Ensure data is sorted for multi-year EWMA calculation
    all_players = build_player_id_map(data)
    build_player_team_map(data)
    
    # Update groupby to include season
    weekly_receiver_data = data.groupby(["season", "receiver_player_id", "week"])
    weekly_rusher_data = data.loc[data.rush == 1].groupby(["season", "rusher_player_id", "week"])
    
    weekly_targets = (
        weekly_receiver_data.size()
        .sort_values()
        .to_frame(name="targets_wk")
        .reset_index()
        .rename(columns={"receiver_player_id": "player_id"})
    )
    weekly_red_zone_targets = (
        data.loc[data.yardline_100 <= 10]
        .groupby(["season", "receiver_player_id", "week"])
        .size()
        .sort_values()
        .to_frame(name="redzone_targets_wk")
        .reset_index()
        .rename(columns={"receiver_player_id": "player_id"})
    )
    weekly_deep_targets = (
        data.loc[data.air_yards >= 30]
        .groupby(["season", "receiver_player_id", "week"])
        .size()
        .sort_values()
        .to_frame(name="deep_targets_wk")
        .reset_index()
        .rename(columns={"receiver_player_id": "player_id"})
    )
    weekly_air_yards_target = (
        weekly_receiver_data["air_yards"]
        .mean()
        .sort_values()
        .to_frame(name="air_yards_per_target_wk")
        .reset_index()
        .rename(columns={"receiver_player_id": "player_id"})
    )
    weekly_carries = (
        weekly_rusher_data.size()
        .sort_values()
        .to_frame(name="carries_wk")
        .reset_index()
        .rename(columns={"rusher_player_id": "player_id"})
    )
    weekly_red_zone_carries = (
        data.loc[data.rush == 1]
        .loc[data.yardline_100 <= 10]
        .groupby(["season", "rusher_player_id", "week"])
        .size()
        .sort_values()
        .to_frame(name="redzone_carries_wk")
        .reset_index()
        .rename(columns={"rusher_player_id": "player_id"})
    )
    weekly_yards_per_carry = (
        weekly_rusher_data["rushing_yards"]
        .mean()
        .sort_values()
        .to_frame(name="yards_per_carry_wk")
        .reset_index()
        .rename(columns={"rusher_player_id": "player_id"})
    )
    
    # FGOE Calculation
    fg_data = data.loc[data.play_type == 'field_goal'].copy()
    fg_data['made'] = fg_data['field_goal_result'].apply(lambda x: 1 if x == 'made' else 0)
    if 'fg_prob' in fg_data.columns:
        fg_data['fg_prob'] = fg_data['fg_prob'].fillna(0.75) # Default to 75% if missing?
    else:
        fg_data['fg_prob'] = 0.75
        
    fg_data['fgoe'] = fg_data['made'] - fg_data['fg_prob']
    
    fgoe_weekly = (
        fg_data.groupby(["season", "kicker_player_id", "week"])['fgoe']
        .mean()
        .reset_index()
        .rename(columns={"kicker_player_id": "player_id", "fgoe": "fgoe_wk"})
    )

    # Merge on season, player_id, week
    weekly_stats = (
        weekly_targets.merge(
            weekly_red_zone_targets, how="outer", on=["season", "player_id", "week"]
        )
        .merge(weekly_deep_targets, how="outer", on=["season", "player_id", "week"])
        .merge(weekly_air_yards_target, how="outer", on=["season", "player_id", "week"])
        .merge(weekly_carries, how="outer", on=["season", "player_id", "week"])
        .merge(weekly_red_zone_carries, how="outer", on=["season", "player_id", "week"])
        .merge(weekly_yards_per_carry, how="outer", on=["season", "player_id", "week"])
        .merge(fgoe_weekly, how="outer", on=["season", "player_id", "week"]) # Merge FGOE
        # Note: Injuries merge is tricky with multi-season. Assuming we want current season injuries or ignoring for backtest EWMA history?
        # For EWMA, we don't strictly need injury status history unless we filter by it?
        # get_weekly_injuries returns for [season].
        # If we omit it here, calculate_weekly works for history.
        # But available flag is used for percentages.
        # Let's keep it but be aware it might be partial.
        .merge(get_weekly_injuries(season), how="left", on=["player_id", "week"]) 
    )

    # --- Snap Count Integration ---
    # 1. Load ID Map to link PFR ID to GSIS ID
    id_map = nfl_data_py.import_ids(columns=["gsis_id", "pfr_id"])
    id_map = id_map.dropna(subset=["pfr_id", "gsis_id"]).rename(columns={"pfr_id": "pfr_player_id", "gsis_id": "player_id"})
    
    # 2. Merge IDs into Snap Counts
    snap_counts = snap_counts.merge(id_map, on="pfr_player_id", how="inner")
    
    # 3. Prepare Snap Data for Merge
    # We need: season, week, player_id, offense_pct
    snap_metrics = snap_counts[["season", "week", "player_id", "offense_pct", "offense_snaps"]].copy()
    snap_metrics["offense_pct"] = snap_metrics["offense_pct"].astype(float)
    
    # 4. Merge into Weekly Stats
    weekly_stats = weekly_stats.merge(snap_metrics, on=["season", "week", "player_id"], how="left")
    weekly_stats["offense_pct"] = weekly_stats["offense_pct"].fillna(0.0)
    weekly_stats["offense_snaps"] = weekly_stats["offense_snaps"].fillna(0.0)

    weekly_stats["available"] = weekly_stats["available"].fillna(True)
    
    # Roster merge for name/position/team
    roster_data = nfl_data_py.import_seasonal_rosters(
        [season], columns=["player_id", "position", "team"]
    )
    weekly_stats = weekly_stats.merge(roster_data, on="player_id", how="left")
    
    weekly_team_targets = weekly_team_stats[
        [
            "team",
            "season", # Add season
            "week",
            "targets_wk",
            "carries_wk",
            "redzone_targets_wk",
            "redzone_carries_wk",
        ]
    ]
    weekly_stats = weekly_stats.merge(
        weekly_team_targets, how="outer", on=["season", "team", "week"], suffixes=[None, "_team"]
    )

    # Fill NaNs from outer merge with 0 before percentages.
    weekly_stats["targets_wk_team"] = weekly_stats["targets_wk_team"].fillna(0)
    weekly_stats["carries_wk_team"] = weekly_stats["carries_wk_team"].fillna(0)
    weekly_stats["redzone_targets_wk_team"] = weekly_stats["redzone_targets_wk_team"].fillna(0)
    weekly_stats["redzone_carries_wk_team"] = weekly_stats["redzone_carries_wk_team"].fillna(0)

    weekly_stats["target_percentage_wk"] = weekly_stats.apply(
        lambda row: compute_target_percentage(row), axis=1
    )
    weekly_stats["carry_percentage_wk"] = weekly_stats.apply(
        lambda row: compute_carry_percentage(row), axis=1
    )
    weekly_stats["redzone_target_percentage_wk"] = weekly_stats.apply(
        lambda row: compute_target_percentage(row, True), axis=1
    )
    weekly_stats["redzone_carry_percentage_wk"] = weekly_stats.apply(
        lambda row: compute_carry_percentage(row, True), axis=1
    )
    weekly_stats["player_name"] = weekly_stats.apply(
        lambda row: all_players[row["player_id"]], axis=1
    )

    weekly_stats.to_csv("weekly_stats.csv")
    return weekly_stats


def compute_target_percentage(row: pd.Series, redzone: bool = False) -> float:
    player_metric = "redzone_targets_wk" if redzone else "targets_wk"
    team_metric = "redzone_targets_wk_team" if redzone else "targets_wk_team"
    if row["available"]:
        if row[team_metric] == 0:
            return 0.0
        return row[player_metric] / row[team_metric]
    else:
        return np.nan


def compute_carry_percentage(row: pd.Series, redzone: bool = False) -> float:
    player_metric = "redzone_carries_wk" if redzone else "carries_wk"
    team_metric = "redzone_carries_wk_team" if redzone else "carries_wk_team"
    if row["available"]:
        if row[team_metric] == 0:
            return 0.0
        return row[player_metric] / row[team_metric]
    else:
        return np.nan


def get_weekly_injuries(season: int) -> pd.DataFrame:
    not_injured = ["Questionable"]
    all_injuries = injuries.load_historical_data([season])
    
    if all_injuries.empty:
        return pd.DataFrame(columns=["week", "player_id", "available"])

    all_injuries = all_injuries.dropna()
    all_injuries = all_injuries.loc[~all_injuries["report_status"].isin(not_injured)]
    all_injuries = all_injuries.assign(available=False).rename(
        columns={"gsis_id": "player_id"}
    )
    return all_injuries[["week", "player_id", "available"]]


def weekly_target_share_estimator(weekly_data: pd.DataFrame) -> pd.DataFrame:
    # assume shared 1/8th
    target_prior = 0
    # Temporarily shorten span for early season.
    target_span = 17
    
    priors_df = weekly_data[['player_id']].drop_duplicates()
    priors_df['target_percentage_wk'] = target_prior
    
    return _compute_estimator_vectorized(
        weekly_data, 
        'player_id', 
        'target_percentage_wk', 
        target_span, 
        priors_df, 
        'target_share_est'
    )


def weekly_snap_share_estimator(weekly_data: pd.DataFrame) -> pd.DataFrame:
    """Computes an EWMA estimator for player snap share.

    Args:
        weekly_data (pd.DataFrame): Weekly player stats including 'offense_pct'.

    Returns:
        pd.DataFrame: DataFrame with 'player_id' and 'snap_share_est'.
    """
    # Assume 10% snap share for new players
    snap_prior = 0.1
    # Short span to adapt quickly to role changes
    snap_span = 4
    
    priors_df = weekly_data[['player_id']].drop_duplicates()
    priors_df['offense_pct'] = snap_prior
    
    return _compute_estimator_vectorized(
        weekly_data, 
        'player_id', 
        'offense_pct', 
        snap_span, 
        priors_df, 
        'snap_share_est'
    )


def weekly_redzone_target_share_estimator(weekly_data: pd.DataFrame) -> pd.DataFrame:
    # assume shared 1/8th
    target_prior = 0
    # Temporarily shorten span for early season.
    target_span = 17
    
    priors_df = weekly_data[['player_id']].drop_duplicates()
    priors_df['redzone_target_percentage_wk'] = target_prior
    
    return _compute_estimator_vectorized(
        weekly_data, 
        'player_id', 
        'redzone_target_percentage_wk', 
        target_span, 
        priors_df, 
        'redzone_target_share_est'
    )


def weekly_carry_share_estimator(weekly_data: pd.DataFrame) -> pd.DataFrame:
    # Assume rookies part of a committee of 4 backs
    carry_prior = 0
    # Temporarily shorten span for early season.
    carry_span = 17
    
    priors_df = weekly_data[['player_id']].drop_duplicates()
    priors_df['carry_percentage_wk'] = carry_prior
    
    return _compute_estimator_vectorized(
        weekly_data, 
        'player_id', 
        'carry_percentage_wk', 
        carry_span, 
        priors_df, 
        'carry_share_est'
    )


def weekly_redzone_carry_share_estimator(weekly_data: pd.DataFrame) -> pd.DataFrame:
    # Assume part of a committee of 4 backs
    carry_prior = 0
    # Temporarily shorten span for early season.
    carry_span = 17
    
    priors_df = weekly_data[['player_id']].drop_duplicates()
    priors_df['redzone_carry_percentage_wk'] = carry_prior
    
    return _compute_estimator_vectorized(
        weekly_data, 
        'player_id', 
        'redzone_carry_percentage_wk', 
        carry_span, 
        priors_df, 
        'redzone_carry_share_est'
    )


def weekly_fgoe_estimator(weekly_data: pd.DataFrame) -> pd.DataFrame:
    """Computes an EWMA estimator for Field Goal Over Expected (FGOE).

    Args:
        weekly_data (pd.DataFrame): Weekly player stats including 'fgoe_wk'.

    Returns:
        pd.DataFrame: DataFrame with 'player_id' and 'fgoe_est'.
    """
    # Assume average kicker (0.0)
    fgoe_prior = 0.0
    # Span of 16 weeks (one season)
    fgoe_span = 16
    
    priors_df = weekly_data[['player_id']].drop_duplicates()
    priors_df['fgoe_wk'] = fgoe_prior
    
    return _compute_estimator_vectorized(
        weekly_data, 
        'player_id', 
        'fgoe_wk', 
        fgoe_span, 
        priors_df, 
        'fgoe_est'
    )


def build_player_id_map(data: pd.DataFrame) -> Dict[str, str]:
    # Vectorized approach
    passers = data[["passer_player_id", "passer_player_name"]].rename(
        columns={"passer_player_id": "player_id", "passer_player_name": "player_name"}
    )
    receivers = data[["receiver_player_id", "receiver_player_name"]].rename(
        columns={"receiver_player_id": "player_id", "receiver_player_name": "player_name"}
    )
    rushers = data[["rusher_player_id", "rusher_player_name"]].rename(
        columns={"rusher_player_id": "player_id", "rusher_player_name": "player_name"}
    )
    kickers = data[["kicker_player_id", "kicker_player_name"]].rename(
        columns={"kicker_player_id": "player_id", "kicker_player_name": "player_name"}
    )
    
    all_players_df = pd.concat([passers, receivers, rushers, kickers])
    all_players_df = all_players_df.dropna().drop_duplicates(subset="player_id")
    
    # Convert to dict
    return defaultdict(lambda: "Unknown", zip(all_players_df.player_id, all_players_df.player_name))


def build_player_team_map(data: pd.DataFrame) -> Dict[str, str]:
    # Vectorized approach
    cols = ["posteam"]
    passers = data[["passer_player_id"] + cols].rename(columns={"passer_player_id": "player_id"})
    receivers = data[["receiver_player_id"] + cols].rename(columns={"receiver_player_id": "player_id"})
    rushers = data[["rusher_player_id"] + cols].rename(columns={"rusher_player_id": "player_id"})
    kickers = data[["kicker_player_id"] + cols].rename(columns={"kicker_player_id": "player_id"})
    
    all_teams_df = pd.concat([passers, receivers, rushers, kickers])
    # Keep last to get most recent team
    all_teams_df = all_teams_df.dropna().drop_duplicates(subset="player_id", keep="last")
    
    return defaultdict(lambda: "Unknown", zip(all_teams_df.player_id, all_teams_df.posteam))