# 3. XGBoost for Core Decision Models

Date: 2025-11-30

## Status

Accepted

## Context

The engine's decision-making (Play Call: Run/Pass/Kick, and eventually Target Share) relies on predictive models.
*   **Previous State:** We used `sklearn.linear_model.LogisticRegression` with `max_iter=10000`.
*   **Problem:**
    *   **Speed:** Training was prohibitively slow (~500s for playcall model) due to convergence issues with large datasets.
    *   **Linearity:** Logistic Regression assumes linear relationships between features (Down, Distance, Score Diff) and log-odds. Game scripts are often non-linear (e.g., behavior at 2 min remaining vs 5 min remaining is not a linear decay).

## Decision

We will use **XGBoost (`xgboost.XGBClassifier`)** for all core classification and regression tasks within the engine.

*   **Configuration:**
    *   Standard Tree Booster (`gbtree`).
    *   `objective='multi:softprob'` for multiclass (Play Call).
    *   Early stopping or fixed `n_estimators` (~100) for speed during dev/fast mode.

## Consequences

### Positive
*   **Speed:** Training time reduced by ~40x (12s vs 500s).
*   **Performance:** Gradient Boosted Trees naturally handle non-linearities and interactions (e.g., "4th down AND trailing by 3").
*   **Feature Handling:** Handles missing values (NaNs) natively, simplifying the feature engineering pipeline.

### Negative
*   **Dependency:** Adds `xgboost` dependency (compiled C++ binary), which can be heavier to install in some environments (solved by `uv` management).
*   **Interpretability:** Less interpretable than coefficients in Logistic Regression (requires SHAP values for deep analysis).
*   **Calibration:** XGBoost probabilities can sometimes be poorly calibrated (overconfident). We may need `CalibratedClassifierCV` if "Fail High/Low" metrics degrade.

## Compliance
All new models introduced (e.g., Target Share, Completion Probability) should default to XGBoost unless a strong reason exists for a simpler linear model.
