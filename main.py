# This is a sample Python script.
import pandas as pd
import matplotlib.pyplot as plt
import score
from collections import defaultdict

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

# The Hello World will be correctly plotting the leaders in fantasy points for week 4. This ensures two goals:
# Testability, we can compare with unit tests.
# Our point calculation is correct.
def basic_plot():
    YEARS = [2021]
    data = pd.DataFrame()

    for i in YEARS:
        i_data = pd.read_csv('data/pbp_' + str(i) + '.csv.gz',
                             compression='gzip', low_memory=False)

        data = data.append(i_data, sort=True)

    week_four = data.loc[data.week <= 4]
    all_players = build_player_id_map(week_four)
    scores = defaultdict(float)

    for i in range(len(week_four)):
        play_score = score.score_from_play(week_four.iloc[i])
        if play_score != None:
            for key in play_score.keys():
                scores[key] += play_score[key]

    base_data = scores.items()
    new_base_data = []
    for row in base_data:
        if row[0] in all_players:
          new_base_data.append([row[0], all_players[row[0]], row[1]])
    w4_scores = pd.DataFrame(new_base_data, columns=["player_id", "Player Name", "Score"])
    w4_scores_sorted = w4_scores.sort_values(by=["Score"], ascending=False)


    print(w4_scores_sorted)


def load_and_clean_data():
    import pandas as pd

    pd.options.mode.chained_assignment = None

    # Enter desired years of data
    YEARS = [1999, 2000, 2001, 2002, 2003,
             2004, 2005, 2006, 2007, 2008,
             2009, 2010, 2011, 2012, 2013,
             2014, 2015, 2016, 2017, 2018,
             2019, 2020, 2021]

    for i in YEARS:
        # Link to data repo
        link = 'https://github.com/guga31bb/nflfastR-data/blob/master/data/play_by_play_' + str(i) + '.csv.gz?raw=true'
        # Read in CSV
        data = pd.read_csv(link, compression='gzip', low_memory=False)
        # Filter to regular season data only
        data = data.loc[data.season_type == 'REG']
        # Output cleaned, compressed CSV to current directory
        data.to_csv('data/pbp_' + str(i) + '.csv.gz', index=False, compression='gzip')

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





# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # This doesn't always need to be done. would like to run this on a cron schedule.
    ## load_and_clean_data()

    # Create an easier way to identify players in fantasy
    basic_plot()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
