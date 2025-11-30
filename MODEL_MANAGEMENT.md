# Model Management & Hygiene

This project relies on pre-trained machine learning models (Regressions, KDEs) to drive the physics engine. Rebuilding these models is computationally expensive and should not be done lightly.

## 🛑 Golden Rules

1.  **Never Rebuild on a Whim:** Only rebuild models if you have changed the underlying data structure, feature engineering logic, or are upgrading `scikit-learn` versions.
2.  **Always Backup:** Before rebuilding, ensure the current working models are backed up.
3.  **Version Control:** Model artifacts (`.joblib` files) are generally *not* committed to Git (due to size), but their performance metrics *are* (via `BENCHMARKS.md`).

## 🛠️ Utilities

### `rebuild_models.py`
The master script for retraining all models.

**Usage:**
```bash
# Dry run (Safe - default behavior)
python rebuild_models.py

# Actual Rebuild (Dangerous)
python rebuild_models.py --force

# With Backup (Recommended)
python rebuild_models.py --force --backup
```

### `diagnose_estimator_diff.py`
Use this to compare the *outputs* of the player stats estimators before and after code changes, to ensure logic changes didn't silently break the inputs to the models.

## 📦 Model Inventory

| Model | Type | Source File | Description |
| :--- | :--- | :--- | :--- |
| `playcall_regression_model` | Logistic Regression | `models/playcall.py` | Predicts Run/Pass/Punt/FG based on down, distance, score, time. |
| `completion_regression_model` | Logistic Regression | `models/completion.py` | Predicts completion probability based on air yards, down, distance. |
| `rushing_yards_open_kde` | KDE | `models/rushers.py` | Distribution of run yards in open field. |
| `rushing_yards_rz_kde` | KDE | `models/rushers.py` | Distribution of run yards in red zone. |
| `air_yards_kde_*` | KDE | `models/receivers.py` | Distributions of air yards by position (WR, RB, TE). |

## 🧪 Testing Changes
If you modify model logic:
1.  Run `python benchmark.py --simulations 50` to see if calibration drifts.
2.  Do **not** rebuild the full model suite until you are satisfied with the code logic.
