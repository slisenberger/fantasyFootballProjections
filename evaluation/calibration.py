import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def calculate_pit(simulated_scores: np.array, actual_score: float) -> float:
    """
    Calculates the Probability Integral Transform (PIT) value.
    PIT = F(y), where F is the CDF of the predicted distribution.
    Empirically: (Count of sims < actual) / Total sims.
    """
    if len(simulated_scores) == 0:
        return np.nan
    
    # We add random noise to breaks ties (if actual == simulated)
    # This "randomized PIT" is standard for discrete distributions (like fantasy points).
    # But simplest version:
    return np.mean(simulated_scores <= actual_score)

def evaluate_calibration(results_df: pd.DataFrame):
    """
    Expects a DataFrame where:
    - Each row is a player-game.
    - 'actual' column is the real score.
    - 'simulations' column contains a list/array of simulated scores.
    """
    
    results_df['pit'] = results_df.apply(
        lambda row: calculate_pit(np.array(row['simulations']), row['actual']), 
        axis=1
    )
    
    return results_df

def plot_pit_histogram(results_df, title="PIT Histogram (Calibration Check)"):
    """
    Plots the histogram of PIT values.
    - Flat (Uniform) = Well Calibrated.
    - U-Shape = Under-confident (Actuals are outliers).
    - Hill-Shape = Over-confident (Actuals are too close to mean).
    """
    plt.figure(figsize=(10, 6))
    sns.histplot(results_df['pit'], bins=20, stat='density', kde=False)
    plt.axhline(1.0, color='red', linestyle='--', label="Perfect Calibration")
    plt.title(title)
    plt.xlabel("Probability Integral Transform (PIT)")
    plt.ylabel("Density")
    plt.legend()
    plt.show()
    plt.close()

def calculate_bias(results_df):
    """
    Calculates the Mean Error (Bias).
    Positive = Model Over-predicts.
    Negative = Model Under-predicts.
    """
    mean_preds = results_df['simulations'].apply(np.mean)
    return (mean_preds - results_df['actual']).mean()
