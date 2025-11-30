import pandas as pd
from data import loader
from settings import BENCHMARK_SUITE

def diagnose():
    print("Loading Benchmark Results...")
    df = pd.read_csv("benchmarks/details_v444_gfi.csv")
    qbs = df[df['position'] == 'QB'].copy()
    
    # Calculate Error/Bias
    qbs['error'] = qbs['mean_projection'] - qbs['actual']
    
    # Identify Fail High (Error < -10)
    fail_high = qbs[qbs['error'] < -10].copy()
    
    print(f"Total QB Samples: {len(qbs)}")
    print(f"Fail High QBs (Error < -10): {len(fail_high)}")
    
    # Load PBP for Breakdown
    print("Loading PBP Data...")
    years = list(set([s for s, w in BENCHMARK_SUITE]))
    pbp = loader.load_data(years)
    
    print("Loading Roster...")
    roster = loader.nfl_data_py.import_seasonal_rosters(years)
    id_map = roster.set_index('player_id')['player_name'].to_dict()
    
    results = []
    
    for idx, row in fail_high.iterrows():
        pid = row['player_id']
        season = row['season']
        week = row['week']
        
        # Filter PBP
        game_pbp = pbp[(pbp['season'] == season) & (pbp['week'] == week)]
        
        # Stats
        pass_yds = game_pbp[game_pbp['passer_player_id'] == pid]['passing_yards'].sum()
        pass_tds = game_pbp[(game_pbp['passer_player_id'] == pid) & (game_pbp['pass_touchdown'] == 1)].shape[0]
        rush_yds = game_pbp[game_pbp['rusher_player_id'] == pid]['rushing_yards'].sum()
        rush_tds = game_pbp[(game_pbp['rusher_player_id'] == pid) & (game_pbp['rush_touchdown'] == 1)].shape[0]
        
        max_pass = game_pbp[game_pbp['passer_player_id'] == pid]['passing_yards'].max()
        max_rush = game_pbp[game_pbp['rusher_player_id'] == pid]['rushing_yards'].max()
        
        results.append({
            'player_name': id_map.get(pid, pid),
            'season': season,
            'week': week,
            'actual': row['actual'],
            'proj': row['mean_projection'],
            'error': row['error'],
            'pass_yds': pass_yds,
            'pass_tds': pass_tds,
            'rush_yds': rush_yds,
            'rush_tds': rush_tds,
            'total_tds': pass_tds + rush_tds,
            'max_pass': max_pass,
            'max_rush': max_rush
        })
        
    results_df = pd.DataFrame(results)
    if not results_df.empty:
        print("\n--- Top 20 Fail High QBs Analysis ---")
        print(results_df.sort_values('error').head(20).to_string(index=False))
        
        print("\n--- Correlation Analysis (Negative Corr = Higher Stat contributes to Negative Error) ---")
        print(results_df[['error', 'pass_yds', 'pass_tds', 'rush_yds', 'rush_tds', 'max_pass', 'max_rush']].corr()['error'])
        
        print("\n--- Average Stats of Fail High QBs ---")
        print(results_df.mean(numeric_only=True))
    else:
        print("No Fail High QBs found.")

if __name__ == "__main__":
    diagnose()
