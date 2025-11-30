import pandas as pd

def _compute_estimator_vectorized(
    data: pd.DataFrame, 
    group_col: str, 
    target_col: str, 
    span: int, 
    priors_df: pd.DataFrame, 
    result_col_name: str, 
    time_col: str = 'week'
) -> pd.DataFrame:
    """Vectorized calculation of Exponentially Weighted Moving Average (EWMA) with prior seeding.

    This function is used to calculate smoothed, regressed estimates for player and team
    statistics. It ensures data is sorted by time before calculation and seeds the EWMA
    with a prior value to handle small sample sizes (Bayesian approach).

    Args:
        data (pd.DataFrame): The input DataFrame containing historical data.
            Must contain `group_col`, `target_col`, and `time_col` (default 'week').
            Optionally contains 'season'.
        group_col (str): The column to group by (e.g., 'player_id', 'posteam').
        target_col (str): The column representing the target variable for estimation.
        span (int): The span parameter for the EWMA calculation (controls weighting).
        priors_df (pd.DataFrame): A DataFrame containing prior values for each group.
            Must contain `group_col` and `target_col`.
        result_col_name (str): The name for the resulting estimator column.
        time_col (str, optional): The column representing the time unit for sorting (default 'week').

    Returns:
        pd.DataFrame: A DataFrame with `group_col` and the calculated `result_col_name`
                      representing the EWMA-smoothed estimator.
    """
    # Determine sort keys
    sort_cols = [group_col]
    has_season = 'season' in data.columns
    if has_season:
        sort_cols.append('season')
    sort_cols.append(time_col)

    # 1. Prepare Priors
    # Priors need to match the columns for concat
    priors_df = priors_df[[group_col, target_col]].copy()
    priors_df[time_col] = -1 # Ensure priors come before week 1
    if has_season:
        priors_df['season'] = data['season'].min() - 1 if not data.empty else 0
    
    # 2. Prepare Main Data
    # Select only necessary columns
    cols_needed = list(set([group_col, target_col] + sort_cols))
    main_df = data[cols_needed].copy()
    
    # 3. Concat
    combined = pd.concat([priors_df, main_df], ignore_index=True)
    
    # Filter out NaN groups (groupby drops them, causing length mismatch otherwise)
    combined = combined.dropna(subset=[group_col])
    
    # 4. Sort (Stable) to ensure Prior comes first, then time order preserved
    combined = combined.sort_values(by=sort_cols, ascending=True, kind='mergesort')
    
    # 5. EWM
    # Note: groupby().ewm() returns a MultiIndex series (group, index)
    est = combined.groupby(group_col)[target_col].ewm(span=span, adjust=False).mean()
    
    # 6. Align results
    # We assign values back. Since 'est' preserves order of 'combined', we can just assign .values
    combined[result_col_name] = est.values
    
    # 7. Extract latest estimate (tail 1)
    result = combined.groupby(group_col).tail(1)[[group_col, result_col_name]]
    return result
