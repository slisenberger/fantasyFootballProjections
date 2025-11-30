import requests
import json
import pandas as pd
from typing import List, Dict, Optional, Tuple
from data import nfl_client as nfl_data_py

INJURY_API_URL = "https://api.myfantasyleague.com/%s/export?TYPE=injuries&W=%s&JSON=1"

cached_data: Dict[int, pd.DataFrame] = {}
cached_inj_data: Dict[Tuple[int, int], pd.DataFrame] = {}


# Returns live injury data from the MFL Fantasy API. Updated regularly, best for future
# projections.
def get_injury_data(season: int, week: int) -> Optional[pd.DataFrame]:
    if week <= 0:
        return None
    if tuple([season, week]) in cached_inj_data:
        return cached_inj_data[(season, week)]
    # Iterate backwards
    try:
        if (season, week) in cached_inj_data:
            return cached_inj_data[(season, week)]
        full_url = INJURY_API_URL % (season, week)
        id_map = nfl_data_py.import_ids(
            columns=["gsis_id", "mfl_id"], ids=["gsis", "mfl"]
        )
        response = requests.get(full_url)
        data = json.loads(response.content.decode(response.encoding))
        df = pd.DataFrame(data["injuries"]["injury"]).rename(columns={"id": "mfl_id"})
        df["mfl_id"] = pd.to_numeric(df["mfl_id"])
        df = df.merge(id_map, on="mfl_id")
        df["exp_return"] = pd.to_datetime(df["exp_return"])
        df = df.rename(columns={"gsis_id": "player_id"})
        cached_inj_data[(season, week)] = df
        return df
    # Recursively try previous weeks.
    except KeyError:
        return get_injury_data(season, week - 1)


def get_season_injury_data(season: int) -> Optional[pd.DataFrame]:
    if season < 2016:
        print("Injury data not available before 2016")
        return None

    try:
        df = nfl_data_py.import_injuries([season])
        return df
    except Exception as e:
        print(f"Warning: Could not import injuries for {season}: {e}")
        return pd.DataFrame()


def clean_and_save_data(years: List[int] = []) -> None:
    # Default to the most recent year.
    if not years:
        years = [2024]
    for year in years:
        inj_data = get_season_injury_data(year)
        if inj_data is not None and not inj_data.empty:
            inj_data.to_csv(
                "data/inj_" + str(year) + ".csv.gz", index=False, compression="gzip"
            )


def load_historical_data(years: List[int]) -> pd.DataFrame:
    data = pd.DataFrame()
    for i in years:
        if i in cached_data:
            i_data = cached_data[i]
        else:
            try:
                i_data = pd.read_csv(
                    "data/inj_" + str(i) + ".csv.gz", compression="gzip", low_memory=False
                )
                # Prevent future reads of this data from going to disk.
                cached_data[i] = i_data
            except FileNotFoundError:
                print(f"Warning: Injury file for {i} not found. Assuming no injuries.")
                i_data = pd.DataFrame()

        data = pd.concat([data, i_data], sort=True)

    data.reset_index(drop=True, inplace=True)
    return data
