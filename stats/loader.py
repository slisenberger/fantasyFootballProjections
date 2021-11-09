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