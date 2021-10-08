import pandas as pd
# Calculate 2021 team statistics that are used to determine tendencies.
def calculate_player_statistics():
    YEARS = [2021]
    data = pd.DataFrame()
    for i in YEARS:
        i_data = pd.read_csv('data/pbp_' + str(i) + '.csv.gz',
                             compression='gzip', low_memory=False)

        data = data.append(i_data, sort=True)

    data = data.loc[(data.play_type.isin(['no_play', 'pass', 'run']))]
    data["yac_oe"] = data["yards_after_catch"] - data["xyac_mean_yardage"]

    receiver_targets = data.groupby("receiver_player_id")\
        .size().sort_values().to_frame(name='targets').reset_index()\
        .rename(columns={'receiver_player_id': 'player_id'})
    receiver_deep_targets = data.loc[data.air_yards >= 30].groupby("receiver_player_id")\
        .size().sort_values().to_frame(name='deep_targets').reset_index()\
        .rename(columns={'receiver_player_id': 'player_id'})
    receiver_red_zone_targets = data.loc[data.ydstogo < 10].groupby("receiver_player_id").size()\
        .sort_values().to_frame(name='red_zone_targets').reset_index()\
        .rename(columns={'receiver_player_id': 'player_id'})
    receiver_air_yards = data.groupby("receiver_player_id")["air_yards"].sum()\
        .sort_values().to_frame(name='air_yards').reset_index()\
        .rename(columns={'receiver_player_id': 'player_id'})
    receiver_yac_oe = data.groupby("receiver_player_id")["yards_after_catch"].sum().sort_values()\
        .to_frame(name='yac').reset_index()\
        .rename(columns={'receiver_player_id': 'player_id'})
    receiver_yac = data.groupby("receiver_player_id")["yac_oe"].sum().sort_values()\
        .to_frame(name='yac_oe').reset_index()\
        .rename(columns={'receiver_player_id': 'player_id'})
    rushing_carries = data.groupby("rusher_player_id").size().sort_values()\
        .to_frame(name="carries").reset_index().rename(columns={'rusher_player_id': 'player_id'})
    yards_per_carry = data.groupby("rusher_player_id")["rushing_yards"].mean()\
        .to_frame(name="yards_per_carry").reset_index()\
        .rename(columns={'rusher_player_id': 'player_id'})
    goal_line_carries = data.loc[data.ydstogo < 10].groupby("rusher_player_id").size()\
        .sort_values().to_frame(name="goal_line_carries").reset_index()\
        .rename(columns={'rusher_player_id': 'player_id'})
    big_carries = data.loc[data.rushing_yards > 10].groupby("rusher_player_id").size() \
        .sort_values().to_frame(name="big_carries").reset_index() \
        .rename(columns={'rusher_player_id': 'player_id'})
    all_players = build_player_id_map(data)
    offense_stats = receiver_targets\
        .merge(receiver_deep_targets,how="outer",on="player_id")\
        .merge(receiver_red_zone_targets,how="outer", on="player_id")\
        .merge(receiver_air_yards,how="outer", on="player_id")\
        .merge(receiver_yac, how="outer", on="player_id") \
        .merge(receiver_yac_oe, how="outer", on="player_id") \
        .merge(rushing_carries, how="outer", on="player_id") \
        .merge(yards_per_carry, how="outer", on="player_id") \
        .merge(goal_line_carries, how="outer", on="player_id") \
        .merge(big_carries, how="outer", on="player_id")
    offense_stats['big_carry_percentage'] = offense_stats["big_carries"] / offense_stats["carries"]
    offense_stats['player_name'] = offense_stats['player_id'].map(lambda x: all_players[x])

    offense_stats.to_csv('offense_stats.csv')
    print(offense_stats)

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
