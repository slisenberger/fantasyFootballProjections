import pandas as pd
import joblib
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from data import loader

model_name = "models/trained_models/kicking_regression_model"

class XGBKicker:
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

def build_or_load_kicking_model():
    try:
        return joblib.load(model_name)
    except FileNotFoundError:
        model = build_kicking_model()
        joblib.dump(model, model_name)
        return model


# Produces a model from XGBoost that predicts kick accuracy.
def build_kicking_model():
    # get the baseline data
    YEARS = [2019, 2020, 2021, 2022, 2023]
    data = loader.load_data(YEARS)
    
    # Enrich with weather features
    if 'roof' in data.columns:
        data['is_outdoors'] = data['roof'].apply(lambda x: 1 if x in ['outdoors', 'open'] else 0)
    else:
        data['is_outdoors'] = 1 # Default to outdoors if missing
        
    if 'wind' in data.columns:
        data['wind'] = data['wind'].fillna(0).astype(float)
    else:
        data['wind'] = 0.0

    data.reset_index(drop=True, inplace=True)
    meaningful_plays = data.loc[data.play_type.isin(["field_goal"])]
    feature_cols = [
        "score_differential",
        "quarter_seconds_remaining",
        "qtr",
        "kick_distance",
        "wind",
        "is_outdoors"
    ]
    # Fill NaNs in features
    meaningful_plays = meaningful_plays.copy() # Avoid SettingWithCopy
    for col in feature_cols:
        meaningful_plays[col] = meaningful_plays[col].fillna(0)

    X = meaningful_plays[feature_cols]
    Y = meaningful_plays["field_goal_result"]
    
    # Encode targets
    le = LabelEncoder()
    Y_enc = le.fit_transform(Y)
    
    # Split the data randomly
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y_enc, test_size=0.25)

    # Train a model
    xgb_model = XGBClassifier(
        n_estimators=100, 
        max_depth=4, 
        learning_rate=0.1, 
        eval_metric='logloss'
    )
    xgb_model.fit(X_train.values, Y_train)
    
    wrapper = XGBKicker(xgb_model, le)
    print(wrapper.score(X_test.values, le.inverse_transform(Y_test)))
    return wrapper
