import pandas as pd
# Calculate 2021 team statistics that are used to determine tendencies.
def calculate_team_statistics():
    YEARS = [2021]
    data = pd.DataFrame()
    for i in YEARS:
        i_data = pd.read_csv('data/pbp_' + str(i) + '.csv.gz',
                             compression='gzip', low_memory=False)

        data = data.append(i_data, sort=True)
    data["yac_oe"] = data["yards_after_catch"] - data["xyac_mean_yardage"]


    pass_happiness_offense = data.groupby("posteam")["pass_oe"].mean().sort_values().to_frame(name="offense_pass_oe")
    pass_suppression_defense = data.groupby("defteam")["pass_oe"].mean().sort_values().to_frame(name="defense_pass_oe")
    goal_line_pass_happiness_offense = data.loc[data.ydstogo < 10].groupby("posteam")["pass_oe"].mean().sort_values().to_frame(name="goal_offense_pass_oe")
    total_relevant_snaps_offense = data.loc[(data.play_type.isin(['no_play', 'pass', 'run']))].groupby("posteam").size().sort_values().to_frame(name="offense_snaps")
    total_relevant_snaps_defense = data.loc[(data.play_type.isin(['no_play', 'pass', 'run']))].groupby(
        "defteam").size().sort_values()
    yac_over_expected = data.loc[(data.play_type.isin(['no_play', 'pass', 'run']))].groupby(
        "defteam")["yac_oe"].mean().sort_values()
    mean_yac = data.loc[(data.play_type.isin(['no_play', 'pass', 'run']))].groupby(
        "defteam")["yards_after_catch"].mean().sort_values()

    team_stats = pass_happiness_offense.merge(pass_suppression_defense, left_on="posteam",right_on="defteam")

    print(team_stats)

    # Secondary YAC over expected -- given the yards after catch of a play, and the median expected yards after catch,
    # how much does the defense give up?
    print(pass_suppression_defense)
    print(pass_happiness_offense)
    print(goal_line_pass_happiness_offense)
    print(total_relevant_snaps_offense)
    print(total_relevant_snaps_defense)
    print(yac_over_expected)
    print(mean_yac)
