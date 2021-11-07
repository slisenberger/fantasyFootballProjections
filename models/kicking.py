import pandas as pd
import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

model_name = "kicking_regression_model"

def build_or_load_kicking_model():
    try:
        return joblib.load(model_name)
    except FileNotFoundError:
        model = build_kicking_model()
        joblib.dump(model, model_name)
        return model


# Produces a model from logistic regression that predicts kick accuracy.
def build_kicking_model():
    # get the baseline data
    YEARS = [2016, 2017, 2018, 2020, 2021]
    data = pd.DataFrame()
    for i in YEARS:
        i_data = pd.read_csv('data/pbp_' + str(i) + '.csv.gz',
                             compression='gzip', low_memory=False)

        data = data.append(i_data, sort=True)
    data.reset_index(drop=True, inplace=True)
    meaningful_plays = data.loc[data.play_type.isin(['field_goal'])]
    # Give data Pass/Run/Punt/Kick Labels
    feature_cols = ['score_differential', 'quarter_seconds_remaining', 'qtr', 'kick_distance']
    X = meaningful_plays[feature_cols]
    X_nan = X[X.isna().any(axis=1)]
    Y = meaningful_plays['field_goal_result']
    print(X_nan)
    # Split the data randomly
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=.25)

    # Train a model
    logreg = LogisticRegression(max_iter=10000)
    logreg.fit(X_train, Y_train)
    print(logreg.score(X_test, Y_test))
    return logreg