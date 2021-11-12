import pandas as pd

# Load a year range of pbp data.
def load_data(years):
    data = pd.DataFrame()
    for i in years:
        i_data = pd.read_csv('data/pbp_' + str(i) + '.csv.gz',
                             compression='gzip', low_memory=False)

        data = data.append(i_data, sort=True)

    data.reset_index(drop=True, inplace=True)
    return data

# Downloads the pbp data to a local file. Updates
def clean_and_save_data(years=[]):
    # Default to the most recent year.
    if not years:
        years = [2021]

    for i in years:
        # Link to data repo
        link = 'https://github.com/guga31bb/nflfastR-data/blob/master/data/play_by_play_' + str(i) + '.csv.gz?raw=true'
        # Read in CSV
        data = pd.read_csv(link, compression='gzip', low_memory=False)
        # Filter to regular season data only
        data = data.loc[data.season_type == 'REG']
        # Output cleaned, compressed CSV to current directory
        data.to_csv('data/pbp_' + str(i) + '.csv.gz', index=False, compression='gzip')