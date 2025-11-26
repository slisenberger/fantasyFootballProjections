import matplotlib.pyplot as plt
import nfl_data_py
from sklearn.neighbors import KernelDensity
from sklearn.model_selection import GridSearchCV
import pandas as pd
import numpy as np
import joblib

yac_model_name = "models/trained_models/yards_after_catch_kde"
air_yards_model_name = "models/trained_models/air_yards_kde"
rb_air_yards_model_name = "models/trained_models/air_yards_kde_rb"
wr_air_yards_model_name = "models/trained_models/air_yards_kde_wr"
te_air_yards_model_name = "models/trained_models/air_yards_kde_te"
rb_yac_model_name = "models/trained_models/yards_after_catch_kde_rb"
wr_yac_model_name = "models/trained_models/yards_after_catch_kde_wr"
te_yac_model_name = "models/trained_models/yards_after_catch_kde_te"


def build_or_load_yac_kde(data=None):
    try:
        return joblib.load(yac_model_name)
    except FileNotFoundError:
        if data is None:
            data = receiver_data()
        all_yac = data["yards_after_catch"].dropna()
        model = fit_kde(all_yac)
        joblib.dump(model, yac_model_name)
        return model


def build_or_load_all_air_yards_kdes():
    data = receiver_data()
    return {
        "air_yards_RB": build_or_load_rb_air_yards_kde(data),
        "air_yards_WR": build_or_load_wr_air_yards_kde(data),
        "air_yards_TE": build_or_load_te_air_yards_kde(data),
        "air_yards_ALL": build_or_load_air_yards_kde(data),
    }


def build_or_load_all_yac_kdes():
    data = receiver_data()
    return {
        "yac_RB": build_or_load_rb_yac_kde(data),
        "yac_WR": build_or_load_wr_yac_kde(data),
        "yac_TE": build_or_load_te_yac_kde(data),
        "yac_ALL": build_or_load_yac_kde(data),
    }


def build_or_load_air_yards_kde(data=None):
    try:
        return joblib.load(air_yards_model_name)
    except FileNotFoundError:
        if data is None:
            data = receiver_data()
        all_air_yards = data["air_yards"].dropna()
        model = fit_kde(all_air_yards)
        joblib.dump(model, air_yards_model_name)
        return model


def build_or_load_rb_air_yards_kde(data):
    try:
        return joblib.load(rb_air_yards_model_name)
    except FileNotFoundError:
        all_air_yards = data.loc[data.position == "RB"]["air_yards"].dropna()
        model = fit_kde(all_air_yards)
        joblib.dump(model, rb_air_yards_model_name)
        return model


def build_or_load_wr_air_yards_kde(data):
    try:
        return joblib.load(wr_air_yards_model_name)
    except FileNotFoundError:
        all_air_yards = data.loc[data.position == "WR"]["air_yards"].dropna()
        model = fit_kde(all_air_yards)
        joblib.dump(model, wr_air_yards_model_name)
        return model


def build_or_load_te_air_yards_kde(data):
    try:
        return joblib.load(te_air_yards_model_name)
    except FileNotFoundError:
        all_air_yards = data.loc[data.position == "TE"]["air_yards"].dropna()
        model = fit_kde(all_air_yards)
        joblib.dump(model, te_air_yards_model_name)
        return model


def build_or_load_rb_yac_kde(data):
    try:
        return joblib.load(rb_yac_model_name)
    except FileNotFoundError:
        all_yac = data.loc[data.position == "RB"]["yards_after_catch"].dropna()
        model = fit_kde(all_yac)
        joblib.dump(model, rb_yac_model_name)
        return model


def build_or_load_wr_yac_kde(data):
    try:
        return joblib.load(wr_yac_model_name)
    except FileNotFoundError:
        all_yac = data.loc[data.position == "WR"]["yards_after_catch"].dropna()
        model = fit_kde(all_yac)
        joblib.dump(model, wr_yac_model_name)
        return model


def build_or_load_te_yac_kde(data):
    try:
        return joblib.load(te_yac_model_name)
    except FileNotFoundError:
        all_yac = data.loc[data.position == "TE"]["yards_after_catch"].dropna()
        model = fit_kde(all_yac)
        joblib.dump(model, te_yac_model_name)
        return model


def receiver_data():
    YEARS = [2019, 2020, 2021, 2022, 2023]
    data = pd.DataFrame()
    for i in YEARS:
        i_data = pd.read_csv(
            "data/pbp_" + str(i) + ".csv.gz", compression="gzip", low_memory=False
        )

        # Reduce the size of the datasets to make the join easier.
        i_data = i_data.loc[~i_data.receiver_player_id.isnull()][
            ["receiver_player_id", "air_yards", "yards_after_catch"]
        ]
        data = pd.concat([data, i_data], sort=True)
    data = data.rename(columns={"receiver_player_id": "player_id"})
    roster_data = nfl_data_py.import_seasonal_rosters(
        [2017, 2018, 2019, 2020, 2021], columns=["player_id", "position", "player_name"]
    ).drop_duplicates()
    data = data.merge(roster_data, on="player_id", how="left")
    return data


def fit_kde(data):
    array_like = data.values.reshape(-1, 1)
    params = {"bandwidth": np.logspace(-1, 1, 20)}
    grid = GridSearchCV(KernelDensity(), params)
    kde = grid.fit(array_like).best_estimator_
    x = np.linspace(data.min(), data.max(), 100)
    log_dens = kde.score_samples(x.reshape(-1, 1))

    # Plot it all
    fig, ax = plt.subplots(1, 1)

    ax.plot(x, np.exp(log_dens))
    ax2 = ax.twinx()
    ax2.hist(array_like, color="yellow", bins=50)

    synthetic = kde.sample(n_samples=1000)
    ax3 = ax2.twinx()
    ax3.hist(synthetic, color="blue", bins=50)
    plt.show()
    return kde


def plot_kde_samples(kde):
    # Plot it all
    fig, ax = plt.subplots(1, 1)
    synthetic = kde.sample(n_samples=1000)
    ax.hist(synthetic, color="blue", bins=50)
    plt.show()
