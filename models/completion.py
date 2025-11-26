import pandas as pd
import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

model_name = "models/trained_models/completion_regression_model"

def build_or_load_completion_model():
    try:
        return joblib.load(model_name)
    except FileNotFoundError:
        model = build_completion_model()
        joblib.dump(model, model_name)
        return model

# Produces a model from logistic regression that produces the probability of a completion.
def build_completion_model():
    # get the baseline data
    YEARS = [2016, 2017, 2018, 2019, 2020, 2021]
    data = pd.DataFrame()
    for i in YEARS:
        i_data = pd.read_csv('data/pbp_' + str(i) + '.csv.gz',
                             compression='gzip', low_memory=False)

        data = pd.concat([data,i_data], sort=True)
    data.reset_index(drop=True, inplace=True)
    meaningful_plays = data.loc[(data.play_type.isin(['pass']))].loc[data.pass_attempt == True].loc[data.two_point_attempt == False].loc[data.sack == False].loc[data.fumble == False]
    feature_cols = ['down', 'ydstogo', 'yardline_100', 'air_yards']
    label_col = ['complete_pass']
    cleaned_plays = meaningful_plays[feature_cols+label_col].dropna()
    X = cleaned_plays[feature_cols]
    X_nan = X[X.isna().any(axis=1)]
    Y = cleaned_plays[label_col]
    print(X_nan)
    # Split the data randomly
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=.25)

    # Train a model
    logreg = LogisticRegression(max_iter=10000)
    logreg.fit(X_train.values, Y_train.values)
    print(logreg.score(X_test, Y_test))
    return logreg
