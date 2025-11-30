import matplotlib.pyplot as plt
from sklearn.neighbors import KernelDensity
from sklearn.model_selection import GridSearchCV
import pandas as pd
import numpy as np
import joblib

rush_open_model_name = "models/trained_models/rushing_yards_open_kde"
rush_rz_model_name = "models/trained_models/rushing_yards_rz_kde"
scramble_model_name = "models/trained_models/scramble_yards_kde"


def build_rush_open_kde(fast=False):
    data = rusher_data(fast=fast)
    data = data.loc[data.rush == 1]
    # Open Field: > 20 yards to go
    data = data.loc[data.yardline_100 > 20]
    all_rush = data["rushing_yards"].dropna()
    model = fit_kde(all_rush, fast=fast)
    return model

def build_or_load_rush_open_kde(fast=False):
    try:
        return joblib.load(rush_open_model_name)
    except FileNotFoundError:
        model = build_rush_open_kde(fast=fast)
        joblib.dump(model, rush_open_model_name)
        return model

def build_rush_rz_kde(fast=False):
    data = rusher_data(fast=fast)
    data = data.loc[data.rush == 1]
    # Red Zone: <= 20 yards to go
    data = data.loc[data.yardline_100 <= 20]
    all_rush = data["rushing_yards"].dropna()
    model = fit_kde(all_rush, fast=fast)
    return model

def build_or_load_rush_rz_kde(fast=False):
    try:
        return joblib.load(rush_rz_model_name)
    except FileNotFoundError:
        model = build_rush_rz_kde(fast=fast)
        joblib.dump(model, rush_rz_model_name)
        return model


def build_scramble_kde(fast=False):
    data = rusher_data(fast=fast)
    data = data.loc[data.qb_scramble == 1]
    all_rush = data["rushing_yards"].dropna()
    model = fit_kde(all_rush, fast=fast)
    return model

def build_or_load_scramble_kde(fast=False):
    try:
        return joblib.load(scramble_model_name)
    except FileNotFoundError:
        model = build_scramble_kde(fast=fast)
        joblib.dump(model, scramble_model_name)
        return model


def rusher_data(fast=False):
    if fast:
        # Use 2 years for fast mode to cover recent trends without full history overhead
        YEARS = [2022, 2023]
    else:
        YEARS = [2019, 2020, 2021, 2022, 2023]
    data = pd.DataFrame()
    for i in YEARS:
        i_data = pd.read_csv(
            "data/pbp_" + str(i) + ".csv.gz", compression="gzip", low_memory=False
        )

        data = pd.concat([data, i_data], sort=True)
    data.reset_index(drop=True, inplace=True)
    return data


def fit_kde(data, fast=False):
    array_like = data.values.reshape(-1, 1)
    if fast:
        # Reduced search space for speed, but not fixed.
        params = {"bandwidth": [0.5, 1.0, 2.0]} 
    else:
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
