import pandas as pd

def _compute_estimator_vectorized(data, group_col, target_col, span, priors_df, result_col_name, time_col='week'):
    """
    Vectorized calculation of EWMA with prior seeding.
    Ensures data is sorted by time before calculation.
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
