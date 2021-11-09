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
    return df