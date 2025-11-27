import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

def calculate_pit(simulated_scores: np.array, actual_score: float) -> float:
    """
    Calculates the Probability Integral Transform (PIT) value.
    PIT = F(y), where F is the CDF of the predicted distribution.
    """
    # Filter out NaNs
    simulated_scores = simulated_scores[~np.isnan(simulated_scores)]
    
    if len(simulated_scores) == 0:
        return np.nan
    
    # Randomized PIT for discrete distributions
    # P(Y < y) + u * P(Y = y), where u ~ Uniform(0, 1)
    less_than = np.mean(simulated_scores < actual_score)
    equal_to = np.mean(simulated_scores == actual_score)
    
    # If we just do less_than + equal_to, we get standard CDF
    # Randomized PIT smooths this out for discrete data (fantasy points are semi-discrete)
    # But given we have float scores, standard PIT is usually fine. 
    # Let's use the randomized version to be safe and rigorous.
    u = np.random.uniform(0, 1)
    return less_than + (u * equal_to)

def calculate_metrics(results_df: pd.DataFrame) -> dict:
    """
    Calculates key calibration metrics from a DataFrame containing 'pit' and 'actual'/'simulations'.
    """
    if 'pit' not in results_df.columns:
        raise ValueError("DataFrame must contain 'pit' column. Run evaluate_calibration first.")

    pit_values = results_df['pit'].dropna()
    
    # 1. KS Test (Uniformity)
    # Compares sample distribution to theoretical uniform distribution
    # Statistic D: Max distance between CDFs. Closer to 0 is better.
    # p-value: Probability that samples are drawn from uniform dist.
    ks_stat, p_value = stats.kstest(pit_values, 'uniform')
    
    # 2. Bias (Mean PIT - 0.5)
    # Positive = Under-prediction (Actuals > Sims) -> Mean PIT > 0.5
    # Negative = Over-prediction (Actuals < Sims) -> Mean PIT < 0.5
    # Ideally 0.0
    bias = np.mean(pit_values) - 0.5
    
    # 3. Interval Coverage
    # Do the X% Confidence Intervals capture X% of actuals?
    def get_coverage(df, percentile):
        lower = (1 - percentile) / 2
        upper = 1 - lower
        
        in_interval = df.apply(
            lambda row: np.nanquantile(row['simulations'], lower) <= row['actual'] <= np.nanquantile(row['simulations'], upper),
            axis=1
        )
        return in_interval.mean()

    coverage_50 = get_coverage(results_df, 0.50)
    coverage_90 = get_coverage(results_df, 0.90)
    
    # Failure Directionality (for 90% interval)
    # Fail Low: Actual < 5th percentile (Model Over-predicted)
    # Fail High: Actual > 95th percentile (Model Under-predicted / Missed Boom)
    fail_low_pct = results_df.apply(
        lambda row: row['actual'] < np.nanquantile(row['simulations'], 0.05), axis=1
    ).mean()
    
    fail_high_pct = results_df.apply(
        lambda row: row['actual'] > np.nanquantile(row['simulations'], 0.95), axis=1
    ).mean()

    # 4. RMSE (Point Estimate Accuracy)
    rmse = np.sqrt(np.mean((results_df['actual'] - results_df['mean_projection'])**2))
    
    return {
        "ks_stat": ks_stat,
        "ks_p_value": p_value,
        "bias": bias,
        "coverage_50": coverage_50,
        "coverage_90": coverage_90,
        "fail_low_pct": fail_low_pct,   # Actual < Lower Bound (Model too high)
        "fail_high_pct": fail_high_pct, # Actual > Upper Bound (Model too low)
        "rmse": rmse,
        "n_samples": len(results_df),
        "pit_histogram": get_ascii_histogram(pit_values)
    }

def get_ascii_histogram(data, bins=10, width=50):
    """Generates a simple ASCII histogram for CLI visualization."""
    counts, bin_edges = np.histogram(data, bins=bins, range=(0, 1))
    max_count = counts.max()
    
    hist_str = "\n  PIT Distribution (0.0 = Over-predicted, 1.0 = Under-predicted):\n"
    for i, count in enumerate(counts):
        bar_len = int((count / max_count) * width) if max_count > 0 else 0
        bar = "#" * bar_len
        label = f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}"
        hist_str += f"  {label} | {bar} ({count})\n"
    return hist_str

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
    
    results_df['mean_projection'] = results_df['simulations'].apply(np.mean)
    
    return results_df

def plot_pit_histogram(results_df, title="PIT Histogram"):
    """
    Plots the histogram of PIT values.
    """
    plt.figure(figsize=(10, 6))
    sns.histplot(results_df['pit'], bins=20, stat='density', kde=False)
    plt.axhline(1.0, color='red', linestyle='--', label="Perfect Calibration")
    plt.title(title)
    plt.xlabel("Probability Integral Transform (PIT)")
    plt.ylabel("Density")
    plt.legend()
    plt.savefig("pit_histogram.png") # Save instead of show for CLI
    plt.close()