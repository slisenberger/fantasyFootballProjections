import pandas as pd
import joblib
from xgboost import XGBClassifier
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
        i_data = pd.read_csv(
            "data/pbp_" + str(i) + ".csv.gz", compression="gzip", low_memory=False
        )

        data = pd.concat([data, i_data], sort=True)
    data.reset_index(drop=True, inplace=True)
    meaningful_plays = (
        data.loc[(data.play_type.isin(["pass"]))]
        .loc[data.pass_attempt == 1]
        .loc[data.two_point_attempt == 0]
        .loc[data.sack == 0]
        .loc[data.fumble == 0]
    )
    feature_cols = ["down", "ydstogo", "yardline_100", "air_yards"]
    label_col = ["complete_pass"]
    cleaned_plays = meaningful_plays[feature_cols + label_col].dropna()
    X = cleaned_plays[feature_cols]
    X_nan = X[X.isna().any(axis=1)]
    Y = cleaned_plays[label_col]
    print(X_nan)
    # Split the data randomly
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.25)

    # Train a model
    # Swapped LogisticRegression for XGBClassifier for speed and non-linearity
    xgb_model = XGBClassifier(
        n_estimators=100, 
        max_depth=4, 
        learning_rate=0.1, 
        eval_metric='logloss'
    )
    xgb_model.fit(X_train.values, Y_train.values.ravel())
    print(xgb_model.score(X_test.values, Y_test.values.ravel()))
    return xgb_model
