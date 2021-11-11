import pandas as pd
from stats import loader
# Calculate 2021 team statistics that are used to determine tendencies.
def calculate():
    YEARS = [2021]
    data = loader.load_data(YEARS)
    data["yac_oe"] = data["yards_after_catch"] - data["xyac_mean_yardage"]
    lg_avg_ypc = data["rushing_yards"].mean()
    lg_avg_yac = data["yards_after_catch"].mean()
    lg_avg_air_yards = data["yards_after_catch"].mean()

    pass_happiness_offense = data.groupby("posteam")["pass_oe"].mean().sort_values()\
        .to_frame(name="offense_pass_oe").reset_index()\
        .rename(columns={'posteam': 'team'})
    pass_happiness_offense_est = compute_offense_poe_estimator(data)
    pass_suppression_defense = data.groupby("defteam")["pass_oe"].mean().sort_values()\
        .to_frame(name="defense_pass_oe").reset_index()\
        .rename(columns={'defteam': 'team'})
    pass_suppression_defense_est = compute_defense_poe_estimator(data)
    goal_line_pass_happiness_offense = data.loc[data.yardline_100 <= 10].groupby("posteam")["pass_oe"].mean().sort_values()\
        .to_frame(name="goal_offense_pass_oe").reset_index()\
        .rename(columns={'posteam': 'team'})
    total_relevant_snaps_offense = data.loc[(data.play_type.isin(['no_play', 'pass', 'run']))].groupby("posteam")\
        .size().sort_values().to_frame(name="offense_snaps").reset_index()\
        .rename(columns={'posteam': 'team'})
    dropbacks = data.loc[(data.play_type.isin(['pass']))].groupby("posteam").size().sort_values().to_frame(name="dropbacks")\
         .reset_index().rename(columns={'posteam': 'team'})
    total_relevant_snaps_defense = data.loc[(data.play_type.isin(['no_play', 'pass', 'run']))].groupby(
        "defteam").size().sort_values().to_frame(name="defense_snaps").reset_index()\
        .rename(columns={'defteam': 'team'})
    yac_over_expected = data.loc[(data.play_type.isin(['no_play', 'pass', 'run']))].groupby(
        "defteam")["yac_oe"].mean().sort_values().to_frame(name="defense_yac_oe").reset_index()\
        .rename(columns={'defteam': 'team'})
    mean_yac = data.loc[(data.play_type.isin(['no_play', 'pass', 'run']))].groupby(
        "defteam")["yards_after_catch"].mean().sort_values().to_frame(name="defense_yac").reset_index()\
        .rename(columns={'defteam': 'team'})
    mean_cpoe = data.loc[(data.play_type.isin(['no_play', 'pass', 'run']))].groupby(
        "defteam")["cpoe"].mean().sort_values().to_frame(name="defense_cpoe").reset_index() \
        .rename(columns={'defteam': 'team'})
    cpoe_est = compute_defense_cpoe_estimator(data)
    mean_air_yards = data.loc[(data.play_type.isin(['no_play', 'pass', 'run']))].groupby(
        "defteam")["air_yards"].mean().sort_values().to_frame(name="defense_air_yards").reset_index() \
        .rename(columns={'defteam': 'team'})
    mean_ypc = data.loc[(data.play_type.isin(['no_play', 'pass', 'run']))].groupby(
        "defteam")["rushing_yards"].mean().sort_values().to_frame(name="defense_ypc").reset_index() \
        .rename(columns={'defteam': 'team'})
    targets = data.loc[(data.play_type.isin(['no_play', 'pass', 'run']))].groupby(
        "posteam")["receiver_player_id"].count().sort_values().to_frame(name="targets").reset_index()\
        .rename(columns={'posteam': 'team'})
    carries = data.loc[(data.play_type.isin(['no_play', 'pass', 'run']))].groupby(
        "posteam")["rusher_player_id"].count().sort_values().to_frame(name="carries").reset_index() \
        .rename(columns={'posteam': 'team'})
    red_zone_targets = data.loc[(data.play_type.isin(['no_play', 'pass', 'run']))].loc[data.yardline_100 <= 10].groupby(
        "posteam")["receiver_player_id"].count().sort_values().to_frame(name="red_zone_targets").reset_index() \
        .rename(columns={'posteam': 'team'})
    red_zone_carries = data.loc[(data.play_type.isin(['no_play', 'pass', 'run']))].loc[data.yardline_100 <= 10].groupby(
        "posteam")["rusher_player_id"].count().sort_values().to_frame(name="red_zone_carries").reset_index() \
        .rename(columns={'posteam': 'team'})
    deep_targets = data.loc[(data.play_type.isin(['no_play', 'pass', 'run']))].loc[data.air_yards >= 30].groupby(
        "posteam")["receiver_player_id"].count().sort_values().to_frame(name="deep_targets").reset_index() \
        .rename(columns={'posteam': 'team'})
    def_sacks = data.loc[(data.play_type.isin(['no_play', 'pass', 'run']))].groupby(
        "defteam")["sack"].sum().sort_values().to_frame(name="defense_sacks").reset_index()\
        .rename(columns={'defteam': 'team'})
    off_sacks = data.loc[(data.play_type.isin(['no_play', 'pass', 'run']))].groupby(
        "posteam")["sack"].sum().sort_values().to_frame(name="offense_sacks").reset_index() \
        .rename(columns={'posteam': 'team'})
    def_tfl = data.loc[(data.play_type.isin(['no_play', 'pass', 'run']))].groupby(
        "defteam")["tackled_for_loss"].sum().sort_values().to_frame(name="defense_tfl").reset_index() \
        .rename(columns={'defteam': 'team'})
    off_tfl = data.loc[(data.play_type.isin(['no_play', 'pass', 'run']))].groupby(
        "posteam")["tackled_for_loss"].sum().sort_values().to_frame(name="offense_tfl").reset_index() \
        .rename(columns={'posteam': 'team'})
    def_holds_drawn = data.loc[data['penalty_type'].str.contains("Offensive Holding", na=False)].groupby("defteam")["penalty"]\
        .sum()\
        .sort_values().to_frame(name="defense_holds_drawn").reset_index() \
        .rename(columns={'defteam': 'team'})
    off_holds_drawn = data.loc[data['penalty_type'].str.contains("Offensive Holding", na=False)].groupby("posteam")[
        "penalty"] \
        .sum() \
        .sort_values().to_frame(name="offense_holds_drawn").reset_index() \
        .rename(columns={'posteam': 'team'})

    team_stats = pass_happiness_offense\
        .merge(pass_happiness_offense_est, on="team") \
        .merge(pass_suppression_defense, on="team") \
        .merge(pass_suppression_defense_est, on="team") \
        .merge(goal_line_pass_happiness_offense, on="team")\
        .merge(total_relevant_snaps_offense, on="team")\
        .merge(total_relevant_snaps_defense, on="team")\
        .merge(dropbacks, on="team")\
        .merge(yac_over_expected, on="team")\
        .merge(mean_yac, on="team") \
        .merge(mean_cpoe, on="team") \
        .merge(cpoe_est, on="team") \
        .merge(mean_air_yards, on="team") \
        .merge(mean_ypc, on="team")\
        .merge(targets, on="team")\
        .merge(carries, on="team")\
        .merge(red_zone_targets, on="team")\
        .merge(red_zone_carries, on="team")\
        .merge(deep_targets, on="team")\
        .merge(def_sacks, on="team")\
        .merge(off_sacks, on="team")\
        .merge(def_tfl, on="team")\
        .merge(off_tfl, on="team")\
        .merge(def_holds_drawn, on="team")\
        .merge(off_holds_drawn, on="team")

    team_stats['offense_pen_rate'] = (team_stats['offense_tfl'] + team_stats['offense_sacks']) / team_stats['offense_snaps']
    team_stats['defense_pen_rate'] = (team_stats['defense_tfl'] + team_stats['defense_sacks']) / team_stats['defense_snaps']
    team_stats['offense_hold_rate'] = team_stats['offense_holds_drawn'] / team_stats['offense_snaps']
    team_stats['defense_hold_rate'] = team_stats['defense_holds_drawn'] / team_stats['defense_snaps']
    team_stats['offense_sacks_per_dropback'] = team_stats["offense_sacks"] / team_stats["dropbacks"]
    team_stats['defense_relative_ypc'] = team_stats["defense_ypc"] / lg_avg_ypc
    team_stats['defense_relative_yac'] = team_stats["defense_yac"] / lg_avg_yac
    team_stats['defense_relative_air_yards'] = team_stats["defense_air_yards"] / lg_avg_air_yards

    team_stats.to_csv("team_stats.csv")
    return team_stats

def calculate_weekly():
    YEARS = [2021]
    data = loader.load_data(YEARS)
    targets_weekly = data.loc[(data.play_type.isin(['no_play', 'pass', 'run']))].groupby(
        ["posteam", "week"])["receiver_player_id"].count().sort_values().to_frame(name="targets_wk").reset_index()\
        .rename(columns={'posteam': 'team'})
    carries_weekly = data.loc[(data.play_type.isin(['no_play', 'pass', 'run']))].groupby(
        ["posteam", "week"])["rusher_player_id"].count().sort_values().to_frame(name="carries_wk").reset_index()\
        .rename(columns={'posteam': 'team'})

    weekly_data = targets_weekly.merge(carries_weekly, on=["team", "week"])
    return weekly_data

def compute_offense_poe_estimator(data):
    poe_prior = 0
    # Use the last 1000 snap window
    poe_span = 500
    biased_poe = data.groupby(["posteam"])["pass_oe"].apply(lambda d: prepend(d, poe_prior)).to_frame()
    poe_est = biased_poe.groupby(["posteam"])["pass_oe"].apply(lambda x: x.ewm(span=poe_span, adjust=False).mean()).to_frame()
    poe_est_now = poe_est.groupby(["posteam"]).tail(1).reset_index().rename(columns={'posteam': 'team', 'pass_oe': 'offense_pass_oe_est'})[["team", "offense_pass_oe_est"]]
    return poe_est_now

def compute_defense_poe_estimator(data):
    poe_prior = 0
    # Use the last 1000 snap window
    poe_span = 500
    biased_poe = data.groupby(["defteam"])["pass_oe"].apply(lambda d: prepend(d, poe_prior)).to_frame()
    poe_est = biased_poe.groupby(["defteam"])["pass_oe"].apply(lambda x: x.ewm(span=poe_span, adjust=False).mean()).to_frame()
    poe_est_now = poe_est.groupby(["defteam"]).tail(1).reset_index().rename(columns={'defteam': 'team', 'pass_oe': 'defense_pass_oe_est'})[["team", "defense_pass_oe_est"]]
    return poe_est_now

def compute_defense_cpoe_estimator(data):
    cpoe_prior = 0
    # Use the last 500 pass window to judge completion.
    cpoe_span = 500
    biased_cpoe = data.groupby(["defteam"])["cpoe"].apply(lambda d: prepend(d, cpoe_prior)).to_frame()
    cpoe_est = biased_cpoe.groupby(["defteam"])["cpoe"].apply(lambda x: x.ewm(span=cpoe_span, adjust=False).mean()).to_frame()
    cpoe_est_now = cpoe_est.groupby(["defteam"]).tail(1).reset_index().rename(columns={'defteam': 'team', 'cpoe': 'defense_cpoe_est'})[["team", "defense_cpoe_est"]]
    return cpoe_est_now

def prepend(df, val):
    df.loc[-1] = val
    df.index = df.index + 1
    df = df.sort_index()
    return df