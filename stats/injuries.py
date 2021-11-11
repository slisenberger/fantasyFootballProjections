import requests
import json
import pandas as pd
import nfl_data_py

INJURY_API_URL = "https://api.myfantasyleague.com/%s/export?TYPE=injuries&W=%s&JSON=1"

def get_injury_data(season, week):
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
9
def get_season_injury_data(season):
    all_weeks = []
    id_map = nfl_data_py.import_ids(columns=["gsis_id", "mfl_id"], ids=["gsis", "mfl"])
    for week in range(1,11):
        try:
          full_url = INJURY_API_URL % (season, week)
          response = requests.get(full_url)
          data = json.loads(response.content.decode(response.encoding))
          basic_injuries = pd.DataFrame(data["injuries"]["injury"])
          basic_injuries['week'] = data["injuries"]["week"]
          all_weeks.append(basic_injuries)
        except KeyError:
            continue

    df = pd.concat(all_weeks).rename(columns={'id': 'mfl_id'})
    df["mfl_id"] = pd.to_numeric(df["mfl_id"])
    df = df.merge(id_map, how="outer", on="mfl_id")
    df["exp_return"] = pd.to_datetime(df["exp_return"])
    df = df.rename(columns={'gsis_id': 'player_id'})
    df["week"] = pd.to_numeric(df["week"])
    return df

