import pandas as pd
from data import loader


# Calculate team statistics that are used to determine tendencies.
def calculate(data, season):
    data = data.loc[(data.play_type.isin(['no_play', 'pass', 'run']))]
    data = data.loc[data.season == season]
    lg_avg_ypc = data.loc[data.rush == 1]["rushing_yards"].mean()
    lg_avg_yac = data["yards_after_catch"].mean()
    lg_avg_air_yards = data["air_yards"].mean()
    lvg_avg_int_rate = data.loc[data.interception == True].shape[0] / data.loc[data.play_type.isin(["pass"])].shape[0]
    lvg_avg_sack_rate = data.loc[data.sack == True].shape[0] / data.loc[data.play_type.isin(["pass"])].shape[0]

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
    total_relevant_snaps_offense = data.groupby("posteam")\
        .size().sort_values().to_frame(name="offense_snaps").reset_index()\
        .rename(columns={'posteam': 'team'})
    dropbacks = data.loc[(data.play_type.isin(['pass']))].groupby("posteam").size().sort_values().to_frame(name="dropbacks")\
         .reset_index().rename(columns={'posteam': 'team'})
    total_relevant_snaps_defense = data.groupby(
        "defteam").size().sort_values().to_frame(name="defense_snaps").reset_index()\
        .rename(columns={'defteam': 'team'})
    dropbacks_def = data.loc[(data.play_type.isin(['pass']))].groupby("defteam").size().sort_values().to_frame(
        name="dropbacks_def") \
        .reset_index().rename(columns={'defteam': 'team'})
    mean_yac = data.groupby(
        "defteam")["yards_after_catch"].mean().sort_values().to_frame(name="defense_yac").reset_index()\
        .rename(columns={'defteam': 'team'})
    yac_est = compute_defense_yac_estimator(data)
    mean_cpoe = data.loc[(data.play_type.isin(['no_play', 'pass', 'run']))].groupby(
        "defteam")["cpoe"].mean().sort_values().to_frame(name="defense_cpoe").reset_index() \
        .rename(columns={'defteam': 'team'})
    cpoe_est = compute_defense_cpoe_estimator(data)
    mean_air_yards = data.groupby(
        "defteam")["air_yards"].mean().sort_values().to_frame(name="defense_air_yards").reset_index() \
        .rename(columns={'defteam': 'team'})
    mean_ypc = data.loc[data.rush == 1].groupby(
        "defteam")["rushing_yards"].mean().sort_values().to_frame(name="defense_ypc").reset_index() \
        .rename(columns={'defteam': 'team'})
    ypc_est = compute_defense_ypc_estimator(data)
    targets = data.groupby(
        "posteam")["receiver_player_id"].count().sort_values().to_frame(name="targets").reset_index()\
        .rename(columns={'posteam': 'team'})
    carries = data.loc[data.rush == 1].groupby(
        "posteam")["rusher_player_id"].count().sort_values().to_frame(name="carries").reset_index() \
        .rename(columns={'posteam': 'team'})
    red_zone_targets = data.loc[data.yardline_100 <= 10].groupby(
        "posteam")["receiver_player_id"].count().sort_values().to_frame(name="red_zone_targets").reset_index() \
        .rename(columns={'posteam': 'team'})
    red_zone_carries = data.loc[data.rush == 1].loc[data.yardline_100 <= 10].groupby(
        "posteam")["rusher_player_id"].count().sort_values().to_frame(name="red_zone_carries").reset_index() \
        .rename(columns={'posteam': 'team'})
    deep_targets = data.loc[data.air_yards >= 30].groupby(
        "posteam")["receiver_player_id"].count().sort_values().to_frame(name="deep_targets").reset_index() \
        .rename(columns={'posteam': 'team'})
    def_sacks = data.groupby(
        "defteam")["sack"].sum().sort_values().to_frame(name="defense_sacks").reset_index()\
        .rename(columns={'defteam': 'team'})
    def_qb_hits = data.groupby(
        "defteam")["qb_hit"].sum().sort_values().to_frame(name="defense_qb_hits").reset_index() \
        .rename(columns={'defteam': 'team'})
    def_int = data.loc[data.play_type.isin(['pass'])].groupby(
        "defteam")["interception"].sum().sort_values().to_frame(name="def_ints").reset_index() \
        .rename(columns={'defteam': 'team'})
    off_sacks = data.groupby(
        "posteam")["sack"].sum().sort_values().to_frame(name="offense_sacks").reset_index() \
        .rename(columns={'posteam': 'team'})
    off_qb_hits = data.groupby(
        "posteam")["qb_hit"].sum().sort_values().to_frame(name="offense_qb_hits").reset_index() \
        .rename(columns={'posteam': 'team'})
    off_scrambles = data.groupby(
        "posteam")["qb_scramble"].sum().sort_values().to_frame(name="offense_scrambles").reset_index() \
        .rename(columns={'posteam': 'team'})
    def_tfl = data.groupby(
        "defteam")["tackled_for_loss"].sum().sort_values().to_frame(name="defense_tfl").reset_index() \
        .rename(columns={'defteam': 'team'})
    off_tfl = data.groupby(
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

    all_teams = pd.DataFrame(pd.concat([data['posteam'], data['defteam']]).dropna().unique(), columns=['team'])

    team_stats = all_teams\
        .merge(pass_happiness_offense, on="team", how="left")\
        .merge(pass_happiness_offense_est, on="team", how="left") \
        .merge(pass_suppression_defense, on="team", how="left") \
        .merge(pass_suppression_defense_est, on="team", how="left") \
        .merge(goal_line_pass_happiness_offense, on="team", how="left")\
        .merge(total_relevant_snaps_offense, on="team", how="left")\
        .merge(total_relevant_snaps_defense, on="team", how="left")\
        .merge(dropbacks, on="team", how="left") \
        .merge(dropbacks_def, on="team", how="left") \
        .merge(mean_yac, on="team", how="left") \
        .merge(yac_est, on="team", how="left") \
        .merge(mean_cpoe, on="team", how="left") \
        .merge(cpoe_est, on="team", how="left") \
        .merge(mean_air_yards, on="team", how="left") \
        .merge(mean_ypc, on="team", how="left")\
        .merge(ypc_est, on="team", how="left")\
        .merge(targets, on="team", how="left")\
        .merge(carries, on="team", how="left")\
        .merge(red_zone_targets, how="left", on="team")\
        .merge(red_zone_carries, how="left", on="team")\
        .merge(deep_targets, how="left", on="team")\
        .merge(def_sacks, how="left", on="team")\
        .merge(def_int, how="left", on="team")\
        .merge(def_qb_hits, how="left", on="team")\
        .merge(off_sacks, how="left", on="team")\
        .merge(off_qb_hits, how="left", on="team")\
        .merge(off_scrambles, how="left", on="team")\
        .merge(def_tfl, how="left", on="team")\
        .merge(off_tfl, how="left", on="team")\
        .merge(def_holds_drawn, how="left", on="team")\
        .merge(off_holds_drawn, how="left", on="team")

    team_stats['offense_pen_rate'] = (team_stats['offense_tfl'] + team_stats['offense_qb_hits']) / team_stats['offense_snaps']
    team_stats['defense_pen_rate'] = (team_stats['defense_tfl'] + team_stats['defense_qb_hits']) / team_stats['defense_snaps']
    team_stats['offense_hold_rate'] = team_stats['offense_holds_drawn'] / team_stats['offense_snaps']
    team_stats['defense_hold_rate'] = team_stats['defense_holds_drawn'] / team_stats['defense_snaps']
    team_stats['offense_sacks_per_dropback'] = team_stats["offense_sacks"] / team_stats["dropbacks"]
    team_stats = team_stats.merge(compute_offense_sack_rate_estimator(data), on="team")
    team_stats["offense_qb_hits_per_dropback"] = team_stats["offense_qb_hits"] / team_stats["dropbacks"]
    team_stats["offense_scrambles_per_dropback"] = team_stats["offense_scrambles"] / team_stats["dropbacks"]
    team_stats["defense_int_rate"] = team_stats["def_ints"] / team_stats["dropbacks_def"]
    team_stats = team_stats.merge(compute_defense_int_rate_estimator(data), on="team")
    team_stats['defense_sacks_per_dropback'] = team_stats["defense_sacks"] / team_stats["dropbacks_def"]
    team_stats = team_stats.merge(compute_defense_sack_rate_estimator(data), on="team")
    team_stats['defense_relative_ypc'] = team_stats["defense_ypc"] / lg_avg_ypc
    team_stats['defense_relative_yac'] = team_stats["defense_yac"] / lg_avg_yac
    team_stats['defense_relative_ypc_est'] = team_stats["defense_ypc_est"] / lg_avg_ypc
    team_stats['defense_relative_yac_est'] = team_stats["defense_yac_est"] / lg_avg_yac
    team_stats['defense_relative_air_yards'] = team_stats["defense_air_yards"] / lg_avg_air_yards
    team_stats['defense_relative_int_rate'] = team_stats['defense_int_rate'] / lvg_avg_int_rate
    team_stats['defense_relative_int_rate_est'] = team_stats['defense_int_rate_est'] / lvg_avg_int_rate
    team_stats['offense_relative_sack_rate'] = team_stats['offense_sacks_per_dropback'] / lvg_avg_sack_rate
    team_stats['defense_relative_sack_rate'] = team_stats['defense_sacks_per_dropback'] / lvg_avg_sack_rate
    team_stats['offense_relative_sack_rate_est'] = team_stats['offense_sack_rate_est'] / lvg_avg_sack_rate
    team_stats['defense_relative_sack_rate_est'] = team_stats['defense_sack_rate_est'] / lvg_avg_sack_rate
    team_stats['lg_sack_rate'] = lvg_avg_sack_rate
    if season <= 2019:
      team_stats['team'] = team_stats["team"].replace("LV", "OAK")


    team_stats.to_csv("team_stats.csv")
    return team_stats

def calculate_weekly(data, season):
    data = data.loc[data.season == season]
    targets_weekly = data.groupby(
        ["posteam", "week"])["receiver_player_id"].count().sort_values().to_frame(name="targets_wk").reset_index()\
        .rename(columns={'posteam': 'team'})
    carries_weekly = data.loc[data.rush == 1].groupby(
        ["posteam", "week"])["rusher_player_id"].count().sort_values().to_frame(name="carries_wk").reset_index()\
        .rename(columns={'posteam': 'team'})
    red_zone_targets_weekly = data.loc[data.yardline_100 <= 10].groupby(
        ["posteam", "week"])["receiver_player_id"].count().sort_values().to_frame(name="redzone_targets_wk").reset_index() \
        .rename(columns={'posteam': 'team'})
    red_zone_carries_weekly = data.loc[data.rush == 1].loc[data.yardline_100 <= 10].groupby(
        ["posteam", "week"])["rusher_player_id"].count().sort_values().to_frame(name="redzone_carries_wk").reset_index() \
        .rename(columns={'posteam': 'team'})

    weekly_data = targets_weekly\
        .merge(carries_weekly, how="outer", on=["team", "week"])\
        .merge(red_zone_targets_weekly, how="outer", on=["team", "week"])\
        .merge(red_zone_carries_weekly, how="outer", on=["team", "week"])
    if season <= 2019:
      weekly_data['team'] = weekly_data["team"].replace("LV", "OAK")
    return weekly_data

def compute_offense_poe_estimator(data):
    poe_prior = 0
    # Use the last 1000 snap window
    poe_span = 500
    biased_poe = data.groupby(["posteam"])["pass_oe"].apply(lambda d: prepend(d, poe_prior)).to_frame()
    poe_est = biased_poe["pass_oe"].groupby(["posteam"]).apply(lambda x: x.ewm(span=poe_span, adjust=False).mean()).to_frame()
    poe_est_now = poe_est.groupby("posteam").tail(1).reset_index(allow_duplicates=True).rename(columns={'posteam': 'team', 'pass_oe': 'offense_pass_oe_est'})[["team", "offense_pass_oe_est"]]
    print(poe_est_now)
    print (poe_est_now.T.drop_duplicates().T)
    return poe_est_now.T.drop_duplicates().T

def compute_defense_poe_estimator(data):
    poe_prior = 0
    # Use the last 1000 snap window
    poe_span = 500
    biased_poe = data.groupby(["defteam"])["pass_oe"].apply(lambda d: prepend(d, poe_prior)).to_frame()
    poe_est = biased_poe.groupby(["defteam"])["pass_oe"].apply(lambda x: x.ewm(span=poe_span, adjust=False).mean()).to_frame()
    poe_est_now = poe_est.groupby(["defteam"]).tail(1).reset_index(allow_duplicates=True).rename(columns={'defteam': 'team', 'pass_oe': 'defense_pass_oe_est'})[["team", "defense_pass_oe_est"]]
    return poe_est_now.T.drop_duplicates().T

def compute_defense_cpoe_estimator(data):
    cpoe_prior = 0
    # Use the last 500 pass window to judge completion.
    cpoe_span = 500
    biased_cpoe = data.groupby(["defteam"])["cpoe"].apply(lambda d: prepend(d, cpoe_prior)).to_frame()
    cpoe_est = biased_cpoe.groupby(["defteam"])["cpoe"].apply(lambda x: x.ewm(span=cpoe_span, adjust=False).mean()).to_frame()
    cpoe_est_now = cpoe_est.groupby(["defteam"]).tail(1).reset_index(allow_duplicates=True).rename(columns={'defteam': 'team', 'cpoe': 'defense_cpoe_est'})[["team", "defense_cpoe_est"]]
    return cpoe_est_now.T.drop_duplicates().T

def compute_defense_yac_estimator(data):
    yac_prior = data["yards_after_catch"].mean()
    yac_span = 500
    biased_yac = data.groupby(["defteam"])["yards_after_catch"].apply(lambda d: prepend(d, yac_prior)).to_frame()
    yac_est = biased_yac.groupby(["defteam"])["yards_after_catch"].apply(lambda x: x.ewm(span=yac_span, adjust=False).mean()).to_frame()
    yac_est_now = yac_est.groupby(["defteam"]).tail(1).reset_index(allow_duplicates=True).rename(columns={'defteam': 'team', 'yards_after_catch': 'defense_yac_est'})[["team", "defense_yac_est"]]
    return yac_est_now.T.drop_duplicates().T

def compute_defense_ypc_estimator(data):
    data = data.loc[data.rush == 1]
    ypc_prior = data["rushing_yards"].mean()
    ypc_span = 500
    biased_ypc = data.groupby(["defteam"])["rushing_yards"].apply(lambda d: prepend(d, ypc_prior)).to_frame()
    ypc_est = biased_ypc.groupby(["defteam"])["rushing_yards"].apply(lambda x: x.ewm(span=ypc_span, adjust=False).mean()).to_frame()
    ypc_est_now = ypc_est.groupby(["defteam"]).tail(1).reset_index(allow_duplicates=True).rename(columns={'defteam': 'team', 'rushing_yards': 'defense_ypc_est'})[["team", "defense_ypc_est"]]
    return ypc_est_now.T.drop_duplicates().T

def compute_defense_int_rate_estimator(data):
    int_prior = data.loc[data.interception == True].shape[0] / data.loc[data.play_type.isin(["pass"])].shape[0]
    int_span=1000
    data = data.loc[data["pass"] == 1]
    biased_int = data.groupby(["defteam"])["interception"].apply(lambda d: prepend(d, int_prior)).to_frame()
    int_est = biased_int.groupby(["defteam"])["interception"].apply(lambda x: x.ewm(span=int_span, adjust=False).mean()).to_frame()
    int_est_now = int_est.groupby(["defteam"]).tail(1).reset_index(allow_duplicates=True).rename(columns={'defteam': 'team', 'interception': 'defense_int_rate_est'})[["team", "defense_int_rate_est"]]
    return int_est_now.T.drop_duplicates().T

def compute_defense_sack_rate_estimator(data):
    sack_prior = data.loc[data.sack == True].shape[0] / data.loc[data["pass"] == 1].shape[0]
    sack_span=1000
    data = data.loc[data["pass"] == 1]
    biased_sack = data.groupby(["defteam"])["sack"].apply(lambda d: prepend(d, sack_prior)).to_frame()
    sack_est = biased_sack.groupby(["defteam"])["sack"].apply(lambda x: x.ewm(span=sack_span, adjust=False).mean()).to_frame()
    sack_est_now = sack_est.groupby(["defteam"]).tail(1).reset_index(allow_duplicates=True).rename(columns={'defteam': 'team', 'sack': 'defense_sack_rate_est'})[["team", "defense_sack_rate_est"]]
    return sack_est_now.T.drop_duplicates().T

def compute_offense_sack_rate_estimator(data):
    sack_prior = data.loc[data.sack == True].shape[0] / data.loc[data["pass"] == 1].shape[0]
    sack_span=1000
    data = data.loc[data["pass"] == 1]
    biased_sack = data.groupby(["posteam"])["sack"].apply(lambda d: prepend(d, sack_prior)).to_frame()
    sack_est = biased_sack.groupby(["posteam"])["sack"].apply(lambda x: x.ewm(span=sack_span, adjust=False).mean()).to_frame()
    sack_est_now = sack_est.groupby(["posteam"]).tail(1).reset_index(allow_duplicates=True).rename(columns={'posteam': 'team', 'sack': 'offense_sack_rate_est'})[["team", "offense_sack_rate_est"]]
    return sack_est_now.T.drop_duplicates().T

def prepend(df, val):
    df.loc[-1] = val
    df.index = df.index + 1
    df = df.sort_index()
    return df
