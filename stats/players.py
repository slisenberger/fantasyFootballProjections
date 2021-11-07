import pandas as pd
# Calculate 2021 team statistics that are used to determine tendencies.
def calculate(team_stats):
    YEARS = [2021]
    data = pd.DataFrame()
    for i in YEARS:
        i_data = pd.read_csv('data/pbp_' + str(i) + '.csv.gz',
                             compression='gzip', low_memory=False)

        data = data.append(i_data, sort=True)

    data.reset_index(drop=True, inplace=True)
    data = data.loc[(data.play_type.isin(['no_play', 'pass', 'run']))]
    data["yac_oe"] = data["yards_after_catch"] - data["xyac_mean_yardage"]

    receiver_targets = data.groupby("receiver_player_id")\
        .size().sort_values().to_frame(name='targets').reset_index()\
        .rename(columns={'receiver_player_id': 'player_id'})
    receiver_deep_targets = data.loc[data.air_yards >= 30].groupby("receiver_player_id")\
        .size().sort_values().to_frame(name='deep_targets').reset_index()\
        .rename(columns={'receiver_player_id': 'player_id'})
    receiver_red_zone_targets = data.loc[data.yardline_100 <= 10].groupby("receiver_player_id").size()\
        .sort_values().to_frame(name='red_zone_targets').reset_index()\
        .rename(columns={'receiver_player_id': 'player_id'})
    receiver_air_yards = data.groupby("receiver_player_id")["air_yards"].sum()\
        .sort_values().to_frame(name='air_yards').reset_index()\
        .rename(columns={'receiver_player_id': 'player_id'})
    receiver_air_yards_per_target = data.groupby("receiver_player_id")["air_yards"].mean() \
        .sort_values().to_frame(name='air_yards_per_target').reset_index() \
        .rename(columns={'receiver_player_id': 'player_id'})
    receiver_yac = data.groupby("receiver_player_id")["yards_after_catch"].sum().sort_values()\
        .to_frame(name='yac').reset_index()\
        .rename(columns={'receiver_player_id': 'player_id'})
    receiver_yac_oe = data.groupby("receiver_player_id")["yac_oe"].sum().sort_values()\
        .to_frame(name='yac_oe').reset_index()\
        .rename(columns={'receiver_player_id': 'player_id'})
    rushing_carries = data.groupby("rusher_player_id").size().sort_values()\
        .to_frame(name="carries").reset_index().rename(columns={'rusher_player_id': 'player_id'})
    yards_per_carry = data.groupby("rusher_player_id")["rushing_yards"].mean()\
        .to_frame(name="yards_per_carry").reset_index()\
        .rename(columns={'rusher_player_id': 'player_id'})
    red_zone_carries = data.loc[data.yardline_100 <= 10].groupby("rusher_player_id").size()\
        .sort_values().to_frame(name="red_zone_carries").reset_index()\
        .rename(columns={'rusher_player_id': 'player_id'})
    big_carries = data.loc[data.rushing_yards >= 10].groupby("rusher_player_id").size() \
        .sort_values().to_frame(name="big_carries").reset_index() \
        .rename(columns={'rusher_player_id': 'player_id'})
    cpoe = data.groupby("passer_player_id")["cpoe"].mean() \
        .to_frame(name="cpoe").reset_index() \
        .rename(columns={'passer_player_id': 'player_id'})
    all_players = build_player_id_map(data)
    all_teams = build_player_team_map(data)
    offense_stats = receiver_targets\
        .merge(receiver_deep_targets,how="outer",on="player_id")\
        .merge(receiver_red_zone_targets,how="outer", on="player_id")\
        .merge(receiver_air_yards,how="outer", on="player_id") \
        .merge(receiver_air_yards_per_target, how="outer", on="player_id") \
        .merge(receiver_yac, how="outer", on="player_id") \
        .merge(receiver_yac_oe, how="outer", on="player_id") \
        .merge(rushing_carries, how="outer", on="player_id") \
        .merge(yards_per_carry, how="outer", on="player_id") \
        .merge(red_zone_carries, how="outer", on="player_id") \
        .merge(big_carries, how="outer", on="player_id")\
        .merge(cpoe, how="outer", on="player_id")
    offense_stats['big_carry_percentage'] = offense_stats["big_carries"] / offense_stats["carries"]


    # Set metadata
    offense_stats['player_name'] = offense_stats.apply(lambda row: all_players[row['player_id']], axis=1)
    offense_stats['team'] = offense_stats.apply(lambda row: all_teams[row['player_id']], axis=1)
    team_targets = team_stats[["team", "targets", "carries", "red_zone_targets", "red_zone_carries"]]
    offense_stats = offense_stats.merge(team_targets, how="outer", on="team", suffixes=[None,"_team"])
    offense_stats['target_percentage'] = offense_stats.apply(lambda row: row["targets"] / row["targets_team"], axis=1)
    offense_stats['carry_percentage'] = offense_stats.apply(lambda row: row["carries"] / row["carries_team"], axis=1)
    offense_stats['red_zone_target_percentage'] = offense_stats.apply(lambda row: row["red_zone_targets"] / row["red_zone_targets_team"], axis=1)
    offense_stats['red_zone_carry_percentage'] = offense_stats.apply(lambda row: row["red_zone_carries"] / row["red_zone_carries_team"], axis=1)

    # Compute team relative stats like target % and carry %
    #offense_stats['target_percentage'] = offense_stats.apply(lambda row: row["targets"] / team_stats.loc[team_stats["team"] == row["team_name"]])


    offense_stats.to_csv('offense_stats.csv')
    return offense_stats

def calculate_weekly_stats():
    pass

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

def build_player_team_map(data):
    player_teams = {}
    for i in range(len(data)):
        row = data.iloc[i]
        if row.passer_player_id not in player_teams:
            player_teams[row.passer_player_id] = row.posteam
        if row.receiver_player_id not in player_teams:
            player_teams[row.receiver_player_id] = row.posteam
        if row.rusher_player_id not in player_teams:
            player_teams[row.rusher_player_id] = row.posteam

    return player_teams
