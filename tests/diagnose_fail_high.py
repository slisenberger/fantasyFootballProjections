import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from main import project_week, calculate_fantasy_leaders, get_models
from data import loader
from stats import injuries
from settings import AppConfig

# Configuration
SEASON = 2023
WEEKS = range(1, 18)
SIMS = 50 # Speed vs Precision trade-off

def run_diagnosis():
    print(f"--- Starting Diagnostic Run ({SEASON}) ---")
    config = AppConfig.load()
    config.runtime.n_simulations = SIMS
    
    # Load Data
    print("Loading Data...")
    loader.clean_and_save_data([SEASON, SEASON-1])
    injuries.clean_and_save_data([SEASON, SEASON-1])
    pbp_data = loader.load_data([SEASON, SEASON-1])
    models = get_models()
    
    results = []
    
    for week in WEEKS:
        print(f"Processing Week {week}...")
        try:
            # 1. Projections (Distribution)
            proj = project_week(pbp_data, models, SEASON, week, config) 
            
            # 2. Actuals
            actuals = calculate_fantasy_leaders(pbp_data, SEASON, week, config)
            
            # 3. Merge
            # proj is rows of simulations. Transpose?
            # project_week returns DataFrame where index is player_id, columns are 0..N-1 (sim scores)
            # Actually project_week returns a DataFrame where rows are players?
            # Let's check main.py return format.
            # "df = pd.DataFrame(projections).transpose()" -> Rows are players, Cols are sims.
            # "proj_df = pd.concat(all_projections)"
            
            # Calculate metrics per player
            metrics = []
            for player_id, row in proj.iterrows():
                sim_scores = row.values
                metrics.append({
                    'player_id': player_id,
                    'week': week,
                    'proj_mean': np.mean(sim_scores),
                    'proj_median': np.median(sim_scores),
                    'proj_p10': np.percentile(sim_scores, 10),
                    'proj_p90': np.percentile(sim_scores, 90),
                    'proj_max': np.max(sim_scores),
                    'proj_std': np.std(sim_scores),
                    'proj_zero_prob': np.mean(sim_scores == 0)
                })
            
            metrics_df = pd.DataFrame(metrics)
            merged = metrics_df.merge(actuals, on='player_id', how='inner')
            
            # Add Metadata (Position, Team) - Need roster
            # We can get it from proj index? No.
            # Load roster
            # roster = nfl_data_py.import_seasonal_rosters([SEASON]) ...
            # merged = merged.merge(roster...)
            
            results.append(merged)
            
        except Exception as e:
            print(f"Error week {week}: {e}")

    full_df = pd.concat(results)
    
    # Add Metadata
    import nfl_data_py
    roster = nfl_data_py.import_seasonal_rosters([SEASON], columns=['player_id', 'position', 'player_name'])
    full_df = full_df.merge(roster, on='player_id', how='left')
    
    # --- Analysis ---
    analyze_results(full_df)

def analyze_results(df):
    print("\n--- DIAGNOSTIC REPORT ---")
    df['error'] = df['score'] - df['proj_median']
    df['fail_high'] = df['score'] > df['proj_p90']
    df['fail_low'] = df['score'] < df['proj_p10'] # Need p10? Approximating
    
    # 1. By Position
    print("\n1. Fail High Rate by Position:")
    pos_grp = df.groupby('position')['fail_high'].mean()
    print(pos_grp)
    
    # 2. By Projected Tier
    # Bin median into buckets
    bins = [-1, 5, 10, 15, 20, 50]
    labels = ['Scrubs (<5)', 'Bench (5-10)', 'Flex (10-15)', 'Starters (15-20)', 'Stars (20+)']
    df['tier'] = pd.cut(df['proj_median'], bins=bins, labels=labels)
    
    print("\n2. Fail High Rate by Tier:")
    tier_grp = df.groupby('tier')['fail_high'].mean()
    print(tier_grp)
    
    # 3. The "Boom" Gap
    # For players who Failed High, how much did they beat p90 by?
    booms = df[df['fail_high']].copy()
    booms['boom_magnitude'] = booms['score'] - booms['proj_p90']
    print("\n3. Boom Magnitude (Avg points above p90 when booming):")
    print(f"Mean: {booms['boom_magnitude'].mean():.2f}")
    print(booms.groupby('position')['boom_magnitude'].mean())
    
    # 4. Zero Analysis
    # Players projected > 5 pts who scored 0
    busts = df[(df['proj_median'] > 5) & (df['score'] == 0)]
    print(f"\n4. True Zero Busts (Proj > 5, Actual 0): {len(busts)}")
    print(busts.groupby('position').size())

    # Save for plotting
    df.to_csv("tests/diagnostic_results.csv", index=False)
    print("\nSaved results to tests/diagnostic_results.csv")

if __name__ == "__main__":
    run_diagnosis()
