import matplotlib.pyplot as plt
from sklearn.neighbors import KernelDensity
from sklearn.model_selection import GridSearchCV
import pandas as pd
import numpy as np
import joblib
from data import loader

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
    
    # Classify QBs for Split KDEs
    rush_stats = data[data['rush'] == 1].groupby(['season', 'rusher_player_id']).agg({
        'rushing_yards': 'sum',
        'game_id': 'nunique'
    }).reset_index()
    rush_stats['ypg'] = rush_stats['rushing_yards'] / rush_stats['game_id']
    
    # Map (season, id) -> is_mobile
    mobile_map = {}
    for _, row in rush_stats.iterrows():
        mobile_map[(row['season'], row['rusher_player_id'])] = row['ypg'] > 20.0
        
    scrambles = data.loc[data.qb_scramble == 1].copy()
    scrambles['rusher_player_id'] = scrambles['rusher_player_id'].fillna(scrambles['passer_player_id'])
    
    scrambles['is_mobile'] = scrambles.apply(lambda x: mobile_map.get((x['season'], x['rusher_player_id']), False), axis=1)
    
    # Train Models
    all_rush = scrambles['rushing_yards'].dropna()
    kde_default = fit_kde(all_rush, fast=fast)
    
    mobile_data = scrambles[scrambles['is_mobile']]['rushing_yards'].dropna()
    kde_mobile = fit_kde(mobile_data, fast=fast) if len(mobile_data) > 50 else kde_default
    
    pocket_data = scrambles[~scrambles['is_mobile']]['rushing_yards'].dropna()
    kde_pocket = fit_kde(pocket_data, fast=fast) if len(pocket_data) > 50 else kde_default
    
    return {
        'default': kde_default,
        'mobile': kde_mobile,
        'pocket': kde_pocket
    }

def build_or_load_scramble_kde(fast=False):
    try:
        return joblib.load(scramble_model_name)
    except FileNotFoundError:
        model = build_scramble_kde(fast=fast)
        joblib.dump(model, scramble_model_name)
        return model


def rusher_data(fast=False):
    if fast:
        YEARS = [2022, 2023]
    else:
        YEARS = [2019, 2020, 2021, 2022, 2023]
    
    # Use loader instead of direct CSV read
    data = loader.load_data(YEARS)
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
