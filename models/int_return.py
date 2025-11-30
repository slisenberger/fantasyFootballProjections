import matplotlib.pyplot as plt
from sklearn.neighbors import KernelDensity
from sklearn.model_selection import GridSearchCV
import pandas as pd
import numpy as np
import joblib

int_return_model_name = "models/trained_models/int_return_yards_kde"


def build_int_return_kde(fast=False):
    data = int_return_data(fast=fast)
    all_returns = data.loc[data.interception == 1]["return_yards"].dropna()
    model = fit_kde(all_returns, fast=fast)
    return model

def build_or_load_int_return_kde(fast=False):
    try:
        return joblib.load(int_return_model_name)
    except FileNotFoundError:
        model = build_int_return_kde(fast=fast)
        joblib.dump(model, int_return_model_name)
        return model


def int_return_data(fast=False):
    if fast:
        YEARS = [2022, 2023]
    else:
        # Always use full history
        YEARS = [2018, 2019, 2020, 2021, 2022, 2023]
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
