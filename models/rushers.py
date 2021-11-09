import matplotlib.pyplot as plt
from scipy.stats import gumbel_r
from sklearn.neighbors import KernelDensity
from sklearn.model_selection import GridSearchCV
import pandas as pd
import numpy as np
import joblib

rush_model_name = "models/trained_models/rushing_yards_kde"

def build_or_load_rush_kde():
    try:
        return joblib.load(rush_model_name)
    except FileNotFoundError:
        data = rusher_data()
        all_rush = data["rushing_yards"].dropna()
        model = fit_kde(all_rush)
        joblib.dump(model, rush_model_name)
        return model


def rusher_data():
    YEARS = [2016, 2017, 2018, 2019, 2020, 2021]
    data = pd.DataFrame()
    for i in YEARS:
        i_data = pd.read_csv('data/pbp_' + str(i) + '.csv.gz',
                             compression='gzip', low_memory=False)

        data = data.append(i_data, sort=True)
    data.reset_index(drop=True, inplace=True)
    return data


def fit_kde(data):
    array_like = data.values.reshape(-1,1)
    params = {'bandwidth': np.logspace(-1, 1, 20)}
    grid = GridSearchCV(KernelDensity(), params)
    kde = grid.fit(array_like).best_estimator_
    x = np.linspace(data.min(),
                    data.max(), 100)
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