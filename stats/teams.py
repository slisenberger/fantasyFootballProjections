import pandas as pd
from stats.util import _compute_estimator_vectorized


# Helper functions to compute EWMA estimators for team stats.
# These must be defined before `calculate` calls them.

def compute_offense_poe_estimator(data: pd.DataFrame) -> pd.DataFrame:
    """Computes an EWMA estimator for offensive Pass Over Expectation (POE).

    Args:
        data (pd.DataFrame): Play-by-play data including 'posteam' and 'pass_oe'.

    Returns:
        pd.DataFrame: DataFrame with 'team' and 'offense_pass_oe_est' columns.
    """
    poe_prior = 0
    poe_span = 500
    priors_df = data[['posteam']].drop_duplicates().copy()
    priors_df['pass_oe'] = poe_prior
    return _compute_estimator_vectorized(data, 'posteam', 'pass_oe', poe_span, priors_df, 'offense_pass_oe_est', time_col='week').rename(columns={'posteam': 'team'})

def compute_defense_poe_estimator(data: pd.DataFrame) -> pd.DataFrame:
    """Computes an EWMA estimator for defensive Pass Over Expectation (POE).

    Args:
        data (pd.DataFrame): Play-by-play data including 'defteam' and 'pass_oe'.

    Returns:
        pd.DataFrame: DataFrame with 'team' and 'defense_pass_oe_est' columns.
    """
    poe_prior = 0
    poe_span = 500
    priors_df = data[['defteam']].drop_duplicates().copy()
    priors_df['pass_oe'] = poe_prior
    return _compute_estimator_vectorized(data, 'defteam', 'pass_oe', poe_span, priors_df, 'defense_pass_oe_est', time_col='week').rename(columns={'defteam': 'team'})

def compute_defense_cpoe_estimator(data: pd.DataFrame) -> pd.DataFrame:
    """Computes an EWMA estimator for defensive Completion Percentage Over Expectation (CPOE).

    Args:
        data (pd.DataFrame): Play-by-play data including 'defteam' and 'cpoe'.

    Returns:
        pd.DataFrame: DataFrame with 'team' and 'defense_cpoe_est' columns.
    """
    cpoe_prior = 0
    cpoe_span = 500
    priors_df = data[['defteam']].drop_duplicates().copy()
    priors_df['cpoe'] = cpoe_prior
    return _compute_estimator_vectorized(data, 'defteam', 'cpoe', cpoe_span, priors_df, 'defense_cpoe_est', time_col='week').rename(columns={'defteam': 'team'})

def compute_defense_yac_estimator(data: pd.DataFrame) -> pd.DataFrame:
    """Computes an EWMA estimator for defensive Yards After Catch (YAC) allowed.

    Args:
        data (pd.DataFrame): Play-by-play data including 'defteam' and 'yards_after_catch'.

    Returns:
        pd.DataFrame: DataFrame with 'team' and 'defense_yac_est' columns.
    """
    yac_prior = data["yards_after_catch"].mean()
    yac_span = 500
    priors_df = data[['defteam']].drop_duplicates().copy()
    priors_df['yards_after_catch'] = yac_prior
    return _compute_estimator_vectorized(data, 'defteam', 'yards_after_catch', yac_span, priors_df, 'defense_yac_est', time_col='week').rename(columns={'defteam': 'team'})

def compute_defense_ypc_estimator(data: pd.DataFrame) -> pd.DataFrame:
    """Computes an EWMA estimator for defensive Yards Per Carry (YPC) allowed.

    Args:
        data (pd.DataFrame): Play-by-play data including 'defteam' and 'rushing_yards'.

    Returns:
        pd.DataFrame: DataFrame with 'team' and 'defense_ypc_est' columns.
    """
    data_filtered = data.loc[data.rush == 1].copy()
    ypc_prior = data_filtered["rushing_yards"].mean()
    ypc_span = 500
    priors_df = data_filtered[['defteam']].drop_duplicates().copy()
    priors_df['rushing_yards'] = ypc_prior
    return _compute_estimator_vectorized(data_filtered, 'defteam', 'rushing_yards', ypc_span, priors_df, 'defense_ypc_est', time_col='week').rename(columns={'defteam': 'team'})

def compute_defense_int_rate_estimator(data: pd.DataFrame) -> pd.DataFrame:
    """Computes an EWMA estimator for defensive Interception Rate.

    Args:
        data (pd.DataFrame): Play-by-play data including 'defteam', 'pass', and 'interception'.

    Returns:
        pd.DataFrame: DataFrame with 'team' and 'defense_int_rate_est' columns.
    """
    pass_plays = data.loc[data["pass"] == 1].copy()
    int_prior = (pass_plays.loc[pass_plays.interception == 1].shape[0] / pass_plays.shape[0]) if pass_plays.shape[0] > 0 else 0
    int_span = 1000
    priors_df = pass_plays[['defteam']].drop_duplicates().copy()
    priors_df['interception'] = int_prior
    return _compute_estimator_vectorized(pass_plays, 'defteam', 'interception', int_span, priors_df, 'defense_int_rate_est', time_col='week').rename(columns={'defteam': 'team'})

def compute_defense_sack_rate_estimator(data: pd.DataFrame) -> pd.DataFrame:
    """Computes an EWMA estimator for defensive Sack Rate.

    Args:
        data (pd.DataFrame): Play-by-play data including 'defteam', 'pass', and 'sack'.

    Returns:
        pd.DataFrame: DataFrame with 'team' and 'defense_sack_rate_est' columns.
    """
    pass_plays = data.loc[data["pass"] == 1].copy()
    sack_prior = (pass_plays.loc[pass_plays.sack == 1].shape[0] / pass_plays.shape[0]) if pass_plays.shape[0] > 0 else 0
    sack_span = 1000
    priors_df = pass_plays[['defteam']].drop_duplicates().copy()
    priors_df['sack'] = sack_prior
    return _compute_estimator_vectorized(pass_plays, 'defteam', 'sack', sack_span, priors_df, 'defense_sack_rate_est', time_col='week').rename(columns={'defteam': 'team'})

def compute_offense_sack_rate_estimator(data: pd.DataFrame) -> pd.DataFrame:
    """Computes an EWMA estimator for offensive Sack Rate.

    Args:
        data (pd.DataFrame): Play-by-play data including 'posteam', 'pass', and 'sack'.

    Returns:
        pd.DataFrame: DataFrame with 'team' and 'offense_sack_rate_est' columns.
    """
    pass_plays = data.loc[data["pass"] == 1].copy()
    sack_prior = (pass_plays.loc[pass_plays.sack == 1].shape[0] / pass_plays.shape[0]) if pass_plays.shape[0] > 0 else 0
    sack_span = 1000
    priors_df = pass_plays[['posteam']].drop_duplicates().copy()
    priors_df['sack'] = sack_prior
    return _compute_estimator_vectorized(pass_plays, 'posteam', 'sack', sack_span, priors_df, 'offense_sack_rate_est', time_col='week').rename(columns={'posteam': 'team'})


# Calculate team statistics that are used to determine tendencies.
def calculate(data: pd.DataFrame, season: int) -> pd.DataFrame:
    """Calculates various team-level statistics and EWMA-smoothed estimators.

    Args:
        data (pd.DataFrame): Raw play-by-play data (PBP).
            Expected columns include: 'play_type', 'rush', 'yards_after_catch',
            'air_yards', 'interception', 'sack', 'posteam', 'defteam', 'pass_oe',
            'cpoe', 'yardline_100', 'receiver_player_id', 'rusher_player_id',
            'qb_hit', 'tackled_for_loss', 'penalty_type', 'penalty', 'week'.
        season (int): The current season for which to calculate team stats.

    Returns:
        pd.DataFrame: A DataFrame containing calculated team statistics and estimators,
                      including offensive/defensive efficiency, pressure rates, and
                      relative metrics compared to league averages.
    """
    data = data.loc[(data.play_type.isin(["no_play", "pass", "run"]))]
    data = data.sort_values('week') # Ensure data is sorted by week for EWMA calculations

    lg_avg_ypc = data.loc[data.rush == 1]["rushing_yards"].mean()
    lg_avg_yac = data["yards_after_catch"].mean()
    lg_avg_air_yards = data["air_yards"].mean()
    n_pass_plays = data.loc[data.play_type.isin(["pass"])].shape[0]
    if n_pass_plays > 0:
        lvg_avg_int_rate = data.loc[data.interception == 1].shape[0] / n_pass_plays
        lvg_avg_sack_rate = data.loc[data.sack == 1].shape[0] / n_pass_plays
    else:
        lvg_avg_int_rate = 0.0
        lvg_avg_sack_rate = 0.0

    pass_happiness_offense = (
        data.groupby("posteam")["pass_oe"]
        .mean()
        .sort_values()
        .to_frame(name="offense_pass_oe")
        .reset_index()
        .rename(columns={"posteam": "team"})
    )
    pass_happiness_offense_est = compute_offense_poe_estimator(data)
    pass_suppression_defense = (
        data.groupby("defteam")["pass_oe"]
        .mean()
        .sort_values()
        .to_frame(name="defense_pass_oe")
        .reset_index()
        .rename(columns={"defteam": "team"})
    )
    pass_suppression_defense_est = compute_defense_poe_estimator(data)
    goal_line_pass_happiness_offense = (
        data.loc[data.yardline_100 <= 10]
        .groupby("posteam")["pass_oe"]
        .mean()
        .sort_values()
        .to_frame(name="goal_offense_pass_oe")
        .reset_index()
        .rename(columns={"posteam": "team"})
    )
    total_relevant_snaps_offense = (
        data.groupby("posteam")
        .size()
        .sort_values()
        .to_frame(name="offense_snaps")
        .reset_index()
        .rename(columns={"posteam": "team"})
    )
    dropbacks = (
        data.loc[(data.play_type.isin(["pass"]))]
        .groupby("posteam")
        .size()
        .sort_values()
        .to_frame(name="dropbacks")
        .reset_index()
        .rename(columns={"posteam": "team"})
    )
    total_relevant_snaps_defense = (
        data.groupby("defteam")
        .size()
        .sort_values()
        .to_frame(name="defense_snaps")
        .reset_index()
        .rename(columns={"defteam": "team"})
    )
    dropbacks_def = (
        data.loc[(data.play_type.isin(["pass"]))]
        .groupby("defteam")
        .size()
        .sort_values()
        .to_frame(name="dropbacks_def")
        .reset_index()
        .rename(columns={"defteam": "team"})
    )
    mean_yac = (
        data.groupby("defteam")["yards_after_catch"]
        .mean()
        .sort_values()
        .to_frame(name="defense_yac")
        .reset_index()
        .rename(columns={"defteam": "team"})
    )
    yac_est = compute_defense_yac_estimator(data)
    mean_cpoe = (
        data.loc[(data.play_type.isin(["no_play", "pass", "run"]))]
        .groupby("defteam")["cpoe"]
        .mean()
        .sort_values()
        .to_frame(name="defense_cpoe")
        .reset_index()
        .rename(columns={"defteam": "team"})
    )
    cpoe_est = compute_defense_cpoe_estimator(data)
    mean_air_yards = (
        data.groupby("defteam")["air_yards"]
        .mean()
        .sort_values()
        .to_frame(name="defense_air_yards")
        .reset_index()
        .rename(columns={"defteam": "team"})
    )
    mean_ypc = (
        data.loc[data.rush == 1]
        .groupby("defteam")["rushing_yards"]
        .mean()
        .sort_values()
        .to_frame(name="defense_ypc")
        .reset_index()
        .rename(columns={"defteam": "team"})
    )
    ypc_est = compute_defense_ypc_estimator(data)
    targets = (
        data.groupby("posteam")["receiver_player_id"]
        .count()
        .sort_values()
        .to_frame(name="targets")
        .reset_index()
        .rename(columns={"posteam": "team"})
    )
    carries = (
        data.loc[data.rush == 1]
        .groupby("posteam")["rusher_player_id"]
        .count()
        .sort_values()
        .to_frame(name="carries")
        .reset_index()
        .rename(columns={"posteam": "team"})
    )
    red_zone_targets = (
        data.loc[data.yardline_100 <= 10]
        .groupby("posteam")["receiver_player_id"]
        .count()
        .sort_values()
        .to_frame(name="red_zone_targets")
        .reset_index()
        .rename(columns={"posteam": "team"})
    )
    red_zone_carries = (
        data.loc[data.rush == 1]
        .loc[data.yardline_100 <= 10]
        .groupby(["posteam", "week"])["rusher_player_id"]
        .count()
        .sort_values()
        .to_frame(name="red_zone_carries")
        .reset_index()
        .rename(columns={"posteam": "team"})
    )
    deep_targets = (
        data.loc[data.air_yards >= 30]
        .groupby("posteam")["receiver_player_id"]
        .count()
        .sort_values()
        .to_frame(name="deep_targets")
        .reset_index()
        .rename(columns={"posteam": "team"})
    )
    def_sacks = (
        data.groupby("defteam")["sack"]
        .sum()
        .sort_values()
        .to_frame(name="defense_sacks")
        .reset_index()
        .rename(columns={"defteam": "team"})
    )
    def_qb_hits = (
        data.groupby("defteam")["qb_hit"]
        .sum()
        .sort_values()
        .to_frame(name="defense_qb_hits")
        .reset_index()
        .rename(columns={"defteam": "team"})
    )
    def_int = (
        data.loc[data.play_type.isin(["pass"])]
        .groupby("defteam")["interception"]
        .sum()
        .sort_values()
        .to_frame(name="def_ints")
        .reset_index()
        .rename(columns={"defteam": "team"})
    )
    off_sacks = (
        data.groupby("posteam")["sack"]
        .sum()
        .sort_values()
        .to_frame(name="offense_sacks")
        .reset_index()
        .rename(columns={"posteam": "team"})
    )
    off_qb_hits = (
        data.groupby("posteam")["qb_hit"]
        .sum()
        .sort_values()
        .to_frame(name="offense_qb_hits")
        .reset_index()
        .rename(columns={"posteam": "team"})
    )
    off_scrambles = (
        data.groupby("posteam")["qb_scramble"]
        .sum()
        .sort_values()
        .to_frame(name="offense_scrambles")
        .reset_index()
        .rename(columns={"posteam": "team"})
    )
    def_tfl = (
        data.groupby("defteam")["tackled_for_loss"]
        .sum()
        .sort_values()
        .to_frame(name="defense_tfl")
        .reset_index()
        .rename(columns={"defteam": "team"})
    )
    off_tfl = (
        data.groupby("posteam")["tackled_for_loss"]
        .sum()
        .sort_values()
        .to_frame(name="offense_tfl")
        .reset_index()
        .rename(columns={"posteam": "team"})
    )
    def_holds_drawn = (
        data.loc[data["penalty_type"].str.contains("Offensive Holding", na=False)]
        .groupby("defteam")["penalty"]
        .sum()
        .sort_values()
        .to_frame(name="defense_holds_drawn")
        .reset_index()
        .rename(columns={"defteam": "team"})
    )
    off_holds_drawn = (
        data.loc[data["penalty_type"].str.contains("Offensive Holding", na=False)]
        .groupby("posteam")["penalty"]
        .sum()
        .sort_values()
        .to_frame(name="offense_holds_drawn")
        .reset_index()
        .rename(columns={"posteam": "team"})
    )

    all_teams = pd.DataFrame(
        pd.concat([data["posteam"], data["defteam"]]).dropna().unique(),
        columns=["team"],
    )

    team_stats = (
        all_teams.merge(pass_happiness_offense, on="team", how="left")
        .merge(pass_happiness_offense_est, on="team", how="left")
        .merge(pass_suppression_defense, on="team", how="left")
        .merge(pass_suppression_defense_est, on="team", how="left")
        .merge(goal_line_pass_happiness_offense, on="team", how="left")
        .merge(total_relevant_snaps_offense, on="team", how="left")
        .merge(total_relevant_snaps_defense, on="team", how="left")
        .merge(dropbacks, on="team", how="left")
        .merge(dropbacks_def, on="team", how="left")
        .merge(mean_yac, on="team", how="left")
        .merge(yac_est, on="team", how="left")
        .merge(mean_cpoe, on="team", how="left")
        .merge(cpoe_est, on="team", how="left")
        .merge(mean_air_yards, on="team", how="left")
        .merge(mean_ypc, on="team", how="left")
        .merge(ypc_est, on="team", how="left")
        .merge(targets, on="team", how="left")
        .merge(carries, on="team", how="left")
        .merge(red_zone_targets, how="left", on="team")
        .merge(red_zone_carries, how="left", on="team")
        .merge(deep_targets, how="left", on="team")
        .merge(def_sacks, how="left", on="team")
        .merge(def_int, how="left", on="team")
        .merge(def_qb_hits, how="left", on="team")
        .merge(off_sacks, how="left", on="team")
        .merge(off_qb_hits, how="left", on="team")
        .merge(off_scrambles, how="left", on="team")
        .merge(def_tfl, how="left", on="team")
        .merge(off_tfl, how="left", on="team")
        .merge(def_holds_drawn, how="left", on="team")
        .merge(off_holds_drawn, how="left", on="team")
    )

    team_stats["offense_pen_rate"] = (
        team_stats["offense_tfl"] + team_stats["offense_qb_hits"]
    ) / team_stats["offense_snaps"]
    team_stats["defense_pen_rate"] = (
        team_stats["defense_tfl"] + team_stats["defense_qb_hits"]
    ) / team_stats["defense_snaps"]
    team_stats["offense_hold_rate"] = (
        team_stats["offense_holds_drawn"] / team_stats["offense_snaps"]
    )
    team_stats["defense_hold_rate"] = (
        team_stats["defense_holds_drawn"] / team_stats["defense_snaps"]
    )
    team_stats["offense_sacks_per_dropback"] = (
        team_stats["offense_sacks"] / team_stats["dropbacks"]
    )
    team_stats = team_stats.merge(compute_offense_sack_rate_estimator(data), on="team")
    team_stats["offense_qb_hits_per_dropback"] = (
        team_stats["offense_qb_hits"] / team_stats["dropbacks"]
    )
    team_stats["offense_scrambles_per_dropback"] = (
        team_stats["offense_scrambles"] / team_stats["dropbacks"]
    )
    team_stats["defense_int_rate"] = (
        team_stats["def_ints"] / team_stats["dropbacks_def"]
    )
    team_stats = team_stats.merge(compute_defense_int_rate_estimator(data), on="team")
    team_stats["defense_sacks_per_dropback"] = (
        team_stats["defense_sacks"] / team_stats["dropbacks_def"]
    )
    team_stats = team_stats.merge(compute_defense_sack_rate_estimator(data), on="team")
    team_stats["defense_relative_ypc"] = team_stats["defense_ypc"] / lg_avg_ypc
    team_stats["defense_relative_yac"] = team_stats["defense_yac"] / lg_avg_yac
    team_stats["defense_relative_ypc_est"] = team_stats["defense_ypc_est"] / lg_avg_ypc
    team_stats["defense_relative_yac_est"] = team_stats["defense_yac_est"] / lg_avg_yac
    team_stats["defense_relative_air_yards"] = (
        team_stats["defense_air_yards"] / lg_avg_air_yards
    )
    team_stats["defense_relative_int_rate"] = (
        team_stats["defense_int_rate"] / lvg_avg_int_rate
    )
    team_stats["defense_relative_int_rate_est"] = (
        team_stats["defense_int_rate_est"] / lvg_avg_int_rate
    )
    team_stats["offense_relative_sack_rate"] = (
        team_stats["offense_sacks_per_dropback"] / lvg_avg_sack_rate
    )
    team_stats["defense_relative_sack_rate"] = (
        team_stats["defense_sacks_per_dropback"] / lvg_avg_sack_rate
    )
    team_stats["offense_relative_sack_rate_est"] = (
        team_stats["offense_sack_rate_est"] / lvg_avg_sack_rate
    )
    team_stats["defense_relative_sack_rate_est"] = (
        team_stats["defense_sack_rate_est"] / lvg_avg_sack_rate
    )
    team_stats["lg_sack_rate"] = lvg_avg_sack_rate
    if season <= 2019:
        team_stats["team"] = team_stats["team"].replace("LV", "OAK")

    team_stats.to_csv("team_stats.csv")
    return team_stats


def calculate_weekly(data: pd.DataFrame, season: int) -> pd.DataFrame:
    """Calculates weekly team-level statistics for targets, carries, and redzone attempts.

    Aggregates play-by-play data on a weekly basis to provide team-level volume metrics.

    Args:
        data (pd.DataFrame): Raw play-by-play data (PBP).
            Expected columns include: 'play_type', 'rush', 'receiver_player_id',
            'rusher_player_id', 'yardline_100', 'season', 'posteam', 'week'.
        season (int): The current season for which to calculate weekly team stats.

    Returns:
        pd.DataFrame: A DataFrame containing weekly team statistics.
    """
    data = data.loc[(data.play_type.isin(["no_play", "pass", "run", "field_goal"]))]
    data = data.sort_values(['season', 'week'])
    targets_weekly = (
        data.groupby(["season", "posteam", "week"])["receiver_player_id"]
        .count()
        .sort_values()
        .to_frame(name="targets_wk")
        .reset_index()
        .rename(columns={"posteam": "team"})
    )
    carries_weekly = (
        data.loc[data.rush == 1]
        .groupby(["season", "posteam", "week"])["rusher_player_id"]
        .count()
        .sort_values()
        .to_frame(name="carries_wk")
        .reset_index()
        .rename(columns={"posteam": "team"})
    )
    red_zone_targets_weekly = (
        data.loc[data.yardline_100 <= 10]
        .groupby(["season", "posteam", "week"])["receiver_player_id"]
        .count()
        .sort_values()
        .to_frame(name="redzone_targets_wk")
        .reset_index()
        .rename(columns={"posteam": "team"})
    )
    red_zone_carries_weekly = (
        data.loc[data.rush == 1]
        .loc[data.yardline_100 <= 10]
        .groupby(["season", "posteam", "week"])["rusher_player_id"]
        .count()
        .sort_values()
        .to_frame(name="redzone_carries_wk")
        .reset_index()
        .rename(columns={"posteam": "team"})
    )

    weekly_data = (
        targets_weekly.merge(carries_weekly, how="outer", on=["season", "team", "week"])
        .merge(red_zone_targets_weekly, how="outer", on=["season", "team", "week"])
        .merge(red_zone_carries_weekly, how="outer", on=["season", "team", "week"])
    )
    if season <= 2019:
        weekly_data["team"] = weekly_data["team"].replace("LV", "OAK")
    return weekly_data