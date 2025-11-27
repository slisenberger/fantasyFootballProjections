import matplotlib.pyplot as plt
import nfl_data_py
from sklearn.neighbors import KernelDensity
from sklearn.model_selection import GridSearchCV
import pandas as pd
import numpy as np
import joblib

# Global Model Paths
air_yards_model_name = "models/trained_models/air_yards_kde"
rb_air_yards_model_name = "models/trained_models/air_yards_kde_rb"
wr_air_yards_model_name = "models/trained_models/air_yards_kde_wr"
te_air_yards_model_name = "models/trained_models/air_yards_kde_te"

def fit_kde(data):
    array_like = data.values.reshape(-1, 1)
    params = {"bandwidth": np.logspace(-1, 1, 20)}
    grid = GridSearchCV(KernelDensity(), params)
    kde = grid.fit(array_like).best_estimator_
    return kde

def receiver_data():
    YEARS = [2019, 2020, 2021, 2022, 2023]
    data = pd.DataFrame()
    for i in YEARS:
        i_data = pd.read_csv(
            "data/pbp_" + str(i) + ".csv.gz", compression="gzip", low_memory=False
        )
        # Include yardline_100 for zone splitting
        i_data = i_data.loc[~i_data.receiver_player_id.isnull()][
            ["receiver_player_id", "air_yards", "yards_after_catch", "yardline_100"]
        ]
        data = pd.concat([data, i_data], sort=True)
    data = data.rename(columns={"receiver_player_id": "player_id"})
    roster_data = nfl_data_py.import_seasonal_rosters(
        YEARS, columns=["player_id", "position", "player_name"]
    ).drop_duplicates()
    data = data.merge(roster_data, on="player_id", how="left")
    return data

# --- Air Yards (Global) ---
def build_or_load_all_air_yards_kdes():
    data = receiver_data()
    return {
        "air_yards_RB": build_or_load_pos_kde(data, "air_yards", "RB", rb_air_yards_model_name),
        "air_yards_WR": build_or_load_pos_kde(data, "air_yards", "WR", wr_air_yards_model_name),
        "air_yards_TE": build_or_load_pos_kde(data, "air_yards", "TE", te_air_yards_model_name),
        "air_yards_ALL": build_or_load_pos_kde(data, "air_yards", "ALL", air_yards_model_name),
    }

def build_or_load_pos_kde(data, col, pos, path):
    try:
        return joblib.load(path)
    except FileNotFoundError:
        if pos != "ALL":
            values = data.loc[data.position == pos][col].dropna()
        else:
            values = data[col].dropna()
        
        if len(values) < 20:
             values = data[col].dropna() # Fallback to ALL
             
        model = fit_kde(values)
        joblib.dump(model, path)
        return model

# --- YAC (Split Open/RZ) ---
def build_or_load_all_yac_kdes():
    data = receiver_data()
    models = {}
    for pos in ["RB", "WR", "TE", "ALL"]:
        for zone in ["open", "rz"]:
            name_pos = "" if pos == "ALL" else f"_{pos.lower()}"
            path = f"models/trained_models/yards_after_catch_kde{name_pos}_{zone}"
            key = f"yac_{pos}_{zone}"
            models[key] = _build_zone_kde(path, data, "yards_after_catch", pos, zone)
    return models

def _build_zone_kde(model_path, data, col, pos, zone):
    try:
        return joblib.load(model_path)
    except FileNotFoundError:
        # Filter Position
        if pos and pos != "ALL":
            subset = data.loc[data.position == pos]
        else:
            subset = data
            
        # Filter Zone
        if zone == "open":
            subset = subset.loc[subset.yardline_100 > 20]
        elif zone == "rz":
            subset = subset.loc[subset.yardline_100 <= 20]
            
        values = subset[col].dropna()
        
        if len(values) < 20:
            print(f"Warning: Low sample size for {model_path}: {len(values)}. Using Global.")
            values = data[col].dropna() 
             
        model = fit_kde(values)
        joblib.dump(model, model_path)
        return model

# Legacy functions if called directly (Maintains API compatibility)
def build_or_load_air_yards_kde(data=None):
    if data is None: data = receiver_data()
    return build_or_load_pos_kde(data, "air_yards", "ALL", air_yards_model_name)