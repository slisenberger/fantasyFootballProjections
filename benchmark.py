import argparse
import pandas as pd
import json
import os
import time
from main import get_models
from data import loader
from stats import injuries
from evaluation import calibration

# Define the Benchmark Suite
BENCHMARK_SUITE = [
    (2023, 1),
    (2023, 8),
    (2023, 17),
    (2022, 1),
    (2022, 8),
    (2022, 17),
]

# Define Season Segments
SEGMENTS = {
    "Early": range(1, 5),   # Weeks 1-4
    "Mid": range(5, 13),    # Weeks 5-12
    "Late": range(13, 19),  # Weeks 13-18
}

def get_segment(week):
    for seg, weeks in SEGMENTS.items():
        if week in weeks:
            return seg
    return "Unknown"

def run_benchmark(simulations=50, version="benchmark"):
    print(f"--- Starting Benchmark Run (v{version}) ---")
    print(f"Simulations per game: {simulations}")
    print(f"Weeks: {BENCHMARK_SUITE}")
    
    from settings import AppConfig # Import here to avoid circular deps if any
    config = AppConfig.load() # Load from scoring.yaml by default
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
    
    from main import project_week, calculate_fantasy_leaders
    
    start_time = time.time()
    
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
            merged['segment'] = get_segment(week)
            merged = merged.rename(columns={'score': 'actual'})
            
            all_results.append(merged)
            
        except Exception as e:
            print(f"Failed {season} W{week}: {e}")
            import traceback
            traceback.print_exc()

    end_time = time.time()
    total_time = end_time - start_time
    time_per_week = total_time / len(BENCHMARK_SUITE) if BENCHMARK_SUITE else 0

    if not all_results:
        print("No results generated.")
        return

    full_df = pd.concat(all_results)
    
    # Overall Metrics
    print("\n--- OVERALL RESULTS ---")
    evaluated_df = calibration.evaluate_calibration(full_df)
    overall_metrics = calibration.calculate_metrics(evaluated_df)
    
    overall_metrics['time_total'] = total_time
    overall_metrics['time_per_week'] = time_per_week
    
    print(f"RMSE: {overall_metrics['rmse']:.2f}")
    print(f"Bias: {overall_metrics['bias']:.3f}")
    print(f"Coverage 90%: {overall_metrics['coverage_90']:.1%} (Target: 90%)")
    print(f"  - Fail Low (Over-predicted): {overall_metrics['fail_low_pct']:.1%}")
    print(f"  - Fail High (Missed Boom):   {overall_metrics['fail_high_pct']:.1%}")
    print(f"Speed: {time_per_week:.2f}s per week (Total: {total_time:.2f}s)")
    
    print(overall_metrics.pop('pit_histogram')) # Print and remove from dict
    
    print(json.dumps(overall_metrics, indent=4))
    
    # Segmented Metrics
    segment_metrics = {}
    print("\n--- SEGMENTED RESULTS ---")
    for segment in SEGMENTS.keys():
        seg_df = evaluated_df[evaluated_df['segment'] == segment]
        if not seg_df.empty:
            print(f"\n{segment} Season (n={len(seg_df)}):")
            metrics = calibration.calculate_metrics(seg_df)
            segment_metrics[segment] = metrics
            print(json.dumps(metrics, indent=4))
    
    # Save Results
    os.makedirs("benchmarks", exist_ok=True)
    results = {
        "overall": overall_metrics,
        "segments": segment_metrics
    }
    
    output_file = f"benchmarks/results_{version}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=4)
    
    print(f"\nResults saved to {output_file}")
    
    # Save detailed CSV
    evaluated_df.to_csv(f"benchmarks/details_{version}.csv", index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulations", type=int, default=50)
    parser.add_argument("--version", type=str, default="baseline")
    args = parser.parse_args()
    
    run_benchmark(simulations=args.simulations, version=args.version)
