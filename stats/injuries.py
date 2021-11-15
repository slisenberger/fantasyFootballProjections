import requests
import json
import pandas as pd
import nfl_data_py

INJURY_API_URL = "https://api.myfantasyleague.com/%s/export?TYPE=injuries&W=%s&JSON=1"

# Returns live injury data from the MFL Fantasy API. Updated regularly, best for future
# projections.
def get_injury_data(season, week):
    # Iterate backwards
    while week > 0:
        try:
            full_url = INJURY_API_URL % (season, week)
            id_map = nfl_data_py.import_ids(columns=["gsis_id", "mfl_id"], ids=["gsis", "mfl"])
            response = requests.get(full_url)
            data = json.loads(response.content.decode(response.encoding))
            df = pd.DataFrame(data["injuries"]["injury"]).rename(columns={'id': 'mfl_id'})
            df["mfl_id"] = pd.to_numeric(df["mfl_id"])
            df = df.merge(id_map, how="outer", on="mfl_id")
            df["exp_return"] = pd.to_datetime(df["exp_return"])
            df = df.rename(columns={'gsis_id': 'player_id'})
            return df
        # Keep trying weeks until one has an error report with usable dates.
        except KeyError:
            week -= 1
            continue
9
def get_season_injury_data(season):
    if season < 2016:
        print("Injury data not available before 2016")
        return None

    all_weeks = []
    id_map = nfl_data_py.import_ids(columns=["gsis_id", "mfl_id"], ids=["gsis", "mfl"])
    for week in range(1, 11):
        try:
            full_url = INJURY_API_URL % (season, week)
            response = requests.get(full_url)
            data = json.loads(response.content.decode(response.encoding))
            basic_injuries = pd.DataFrame(data["injuries"]["injury"])
            basic_injuries['week'] = data["injuries"]["week"]
            all_weeks.append(basic_injuries)
        except KeyError:
            break
    df = pd.concat(all_weeks).rename(columns={'id': 'mfl_id'})
    df["mfl_id"] = pd.to_numeric(df["mfl_id"])
    df = df.merge(id_map, how="outer", on="mfl_id")
    df["exp_return"] = pd.to_datetime(df["exp_return"])
    df = df.rename(columns={'gsis_id': 'player_id'})
    df["week"] = pd.to_numeric(df["week"])
    return df


def clean_and_save_data(years=[]):
    # Default to the most recent year.
    if not years:
        years = [2019, 2020, 2021]

    for year in years:
        inj_data = get_season_injury_data(year)
        inj_data.to_csv('data/inj_' + str(year) + '.csv.gz', index=False, compression='gzip')

def load_historical_data(years):
    data = pd.DataFrame()
    for i in years:
        i_data = pd.read_csv('data/inj_' + str(i) + '.csv.gz',
                             compression='gzip', low_memory=False)

        data = data.append(i_data, sort=True)

    data.reset_index(drop=True, inplace=True)
    return data



