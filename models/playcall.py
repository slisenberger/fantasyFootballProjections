import pandas as pd
import joblib
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from data import loader # Import loader

model_name = "models/trained_models/playcall_regression_model"

class XGBPlayCaller:
    def __init__(self, model, encoder):
        self.model = model
        self.encoder = encoder
    
    @property
    def classes_(self):
        return self.encoder.classes_
        
    def predict_proba(self, X):
        return self.model.predict_proba(X)
        
    def score(self, X, y):
        # X is values, y is strings
        y_enc = self.encoder.transform(y)
        return self.model.score(X, y_enc)

def build_or_load_playcall_model(fast=False):
    try:
        return joblib.load(model_name)
    except FileNotFoundError:
        model = build_playcall_model(fast=fast)
        joblib.dump(model, model_name)
        return model


def test_playcall_model(model):
    test_data = [
        # 1st and short near endzone
        [1, 2, 0, 120, 3, 1, 45.0, 0.0, 1], # Added Vegas and drive_play_count
        # 3rd and short near endzone
        [3, 2, 0, 120, 3, 1, 45.0, 0.0, 3], # Added Vegas and drive_play_count
        # 4th and short near endzone
        [4, 2, 0, 120, 3, 1, 45.0, 0.0, 5], # Added Vegas and drive_play_count
        # 4th and long early game, your opponent territory
        [4, 15, 20, 20, 2, 30, 50.0, -7.0, 7], # Added Vegas and drive_play_count
        # 4th and long early game, your territory
        [4, 15, 0, 20, 1, 75, 40.0, 3.0, 2], # Added Vegas and drive_play_count
        # 4th and long late game, your territory
        [4, 15, -6, 20, 4, 75, 40.0, 3.0, 10], # Added Vegas and drive_play_count
    ]

    print(model.classes_)
    # Make sure there are reasonable probabilities here.
    print(model.predict_proba(test_data))


# Produces a model from XGBoost that produces a probability of
# run/pass/kick/punt from the gamestate.
def build_playcall_model(fast=False):
    # get the baseline data
    YEARS = [2018, 2019, 2020, 2021, 2022, 2023]
    data = loader.load_data(YEARS) # Use loader.load_data
    
    # Fill NaNs for new features before filtering
    data['total_line'] = data['total_line'].fillna(data['total_line'].mean())
    data['spread_line'] = data['spread_line'].fillna(0.0) # Spread can be 0.0
    data['drive_play_count'] = data['drive_play_count'].fillna(1) # Default to 1 for first play of drive
    data['drive_play_count'] = data['drive_play_count'].astype(int)

    data.reset_index(drop=True, inplace=True)
    meaningful_plays = data.loc[
        (data.play_type.isin(["punt", "field_goal", "pass", "run"]))
    ].loc[data.two_point_attempt == 0]
    # Give data Pass/Run/Punt/Kick Labels
    feature_cols = [
        "down",
        "ydstogo",
        "score_differential",
        "quarter_seconds_remaining",
        "qtr",
        "yardline_100",
        "total_line",
        "spread_line",
        "drive_play_count",
    ]
    meaningful_plays.dropna(inplace=True, subset=feature_cols)
    X = meaningful_plays[feature_cols]
    Y = meaningful_plays["play_type"]
    
    # Encode targets
    le = LabelEncoder()
    Y_enc = le.fit_transform(Y)
    
    # Split the data randomly
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y_enc, test_size=0.25)

    # Train a model
    # Use XGBClassifier for speed and better non-linear fit
    n_estimators = 50 if fast else 100
    xgb_model = XGBClassifier(
        n_estimators=n_estimators, 
        max_depth=4, 
        learning_rate=0.1,
        objective='multi:softprob',
        eval_metric='mlogloss'
    )
    xgb_model.fit(X_train.values, Y_train)
    
    wrapper = XGBPlayCaller(xgb_model, le)
    # Pass original string Y labels to wrapper.score for verification (it handles encoding)
    print(wrapper.score(X_test.values, le.inverse_transform(Y_test)))
    
    return wrapper
