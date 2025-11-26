import argparse
import pandas as pd
import json
import os
from main import run_backtest, AppConfig, get_models
from evaluation import calibration
from data import loader
from stats import injuries

# Define the Benchmark Suite
# A mix of weeks from different seasons to get a representative sample
BENCHMARK_SUITE = [
    (2023, 1),
    (2023, 8),
    (2023, 17),
    (2022, 1),
    (2022, 8),
    (2022, 17),
]

def run_benchmark(simulations=50, version="benchmark"):
    print(f"--- Starting Benchmark Run (v{version}) ---")
    print(f"Simulations per game: {simulations}")
    print(f"Weeks: {BENCHMARK_SUITE}")
    
    config = AppConfig()
    config.runtime.n_simulations = simulations
    config.runtime.version = version
    
    # Ensure data is loaded
    years_needed = set([y for y, w in BENCHMARK_SUITE] + [y-1 for y, w in BENCHMARK_SUITE])
    print(f"Loading data for years: {sorted(list(years_needed))}")
    loader.clean_and_save_data(list(years_needed))
    injuries.clean_and_save_data(list(years_needed))
    pbp_data = loader.load_data(list(years_needed))
    
    all_results = []
    models = get_models()
    
    # Run Backtests
    # We essentially replicate run_backtest but with our specific suite and without the hardcoded loop
    from main import project_week, calculate_fantasy_leaders
    
    for season, week in BENCHMARK_SUITE:
        try:
            print(f"Benchmarking {season} Week {week}...")
            config.runtime.season = season
            config.runtime.week = week
            
            sims_df = project_week(pbp_data, models, season, week, config)
            actuals_df = calculate_fantasy_leaders(pbp_data, season, week, config)
            
            sims_df['simulations'] = sims_df.values.tolist()
            sims_df = sims_df.reset_index().rename(columns={'index': 'player_id'})
            
            merged = sims_df[['player_id', 'simulations']].merge(actuals_df, on='player_id')
            merged['season'] = season
            merged['week'] = week
            merged = merged.rename(columns={'score': 'actual'})
            
            all_results.append(merged)
            
        except Exception as e:
            print(f"Failed {season} W{week}: {e}")
            import traceback
            traceback.print_exc()

    if not all_results:
        print("No results generated.")
        return

    full_df = pd.concat(all_results)
    
    # Calculate Metrics
    print("Evaluating Calibration...")
    evaluated_df = calibration.evaluate_calibration(full_df)
    metrics = calibration.calculate_metrics(evaluated_df)
    
    print("\n--- BENCHMARK RESULTS ---")
    print(json.dumps(metrics, indent=4))
    
    # Save Results
    os.makedirs("benchmarks", exist_ok=True)
    output_file = f"benchmarks/results_{version}.json"
    with open(output_file, "w") as f:
        json.dump(metrics, f, indent=4)
    
    print(f"Results saved to {output_file}")
    
    # Save detailed CSV for debugging
    evaluated_df.to_csv(f"benchmarks/details_{version}.csv", index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulations", type=int, default=50)
    parser.add_argument("--version", type=str, default="baseline")
    args = parser.parse_args()
    
    run_benchmark(simulations=args.simulations, version=args.version)
