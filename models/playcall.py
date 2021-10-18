import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

# Produces a model from logistic regression that produces a probability of
# run/pass/kick/punt from the gamestate.
def build_playcall_model():
    # get the baseline data (all relevant snaps 2016-2021)
    # Determine the relevant information:
    # down, clock, quarter, yards to go, score differential
    YEARS = [2016,2017,2018,2019,2020,2021]
    data = pd.DataFrame()
    for i in YEARS:
        i_data = pd.read_csv('data/pbp_' + str(i) + '.csv.gz',
                             compression='gzip', low_memory=False)

        data = data.append(i_data, sort=True)

    # Give data Pass/Run/Punt/Kick Labels
    feature_cols= ['down', 'score_differential', 'quarter_seconds_remaining', 'qtr', 'yardline_100', 'ydstogo']
    X = data[feature_cols]
    Y = data['play_type']
    # Split the data randomly
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=.25)

    # Train a model
    logreg = LogisticRegression()
    logreg.fit(X_train, Y_train)
    Y_pred = logreg.predict_proba(X_train)
