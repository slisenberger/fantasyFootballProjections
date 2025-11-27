import pandas as pd
import numpy as np
import nfl_data_py
from data import loader
from settings import AppConfig

def diagnose_qb_error():
    print("--- QB Error Diagnosis ---")
    
    # 1. Load Benchmark Details
    try:
        df = pd.read_csv("benchmarks/details_v419_final_audit_fixed.csv")
        qbs = df[df['position'] == 'QB'].copy()
        print(f"Loaded {len(qbs)} QB samples.")
    except FileNotFoundError:
        print("Benchmark CSV not found. Run benchmark first.")
        return

    # 2. Load Context Data (PBP for Rushing Stats)
    print("Loading Context Data...")
    years = qbs['season'].unique().tolist()
    pbp = loader.load_data(years)
    
    # Load Roster for Team info
    print("Loading Roster for Team info...")
    roster = nfl_data_py.import_seasonal_rosters(years, columns=['player_id', 'team', 'season'])
    # Drop dupes if any
    roster = roster.drop_duplicates(subset=['player_id', 'season'])
    
    qbs = qbs.merge(roster, on=['player_id', 'season'], how='left')
    
    # Calculate QB Rushing Stats per Season (to classify them)
    print("Classifying QB Archetypes...")
    
    # Group by Passer/Rusher ID to get averages
    # We need a map of Player ID -> Rushing Yards Per Game
    qb_stats = []
    
    for season in years:
        season_pbp = pbp[pbp['season'] == season]
        
        # Rushing Yards by QB
        # Filter for QB runs: play_type='run' & rusher_player_id is a QB
        # Note: We don't strictly know who is a QB in PBP, but we have `qbs` dataframe with IDs.
        season_qbs = qbs[qbs['season'] == season]['player_id'].unique()
        
        # Calculate Avg Rushing Yards per Game for these QBs
        for qb_id in season_qbs:
            # Get games played
            games = season_pbp[
                (season_pbp['passer_player_id'] == qb_id) | 
                (season_pbp['rusher_player_id'] == qb_id)
            ]['game_id'].nunique()
            
            if games == 0: continue
            
            # Total Rushing Yards
            rush_yards = season_pbp[
                (season_pbp['rusher_player_id'] == qb_id) &
                (season_pbp['play_type'] == 'run')
            ]['rushing_yards'].sum()
            
            rush_tds = season_pbp[
                (season_pbp['rusher_player_id'] == qb_id) &
                (season_pbp['rush_touchdown'] == 1)
            ]['rush_touchdown'].sum()
            
            qb_stats.append({
                'player_id': qb_id,
                'season': season,
                'rushing_ypg': rush_yards / games,
                'rushing_td_pg': rush_tds / games,
                'games_played': games
            })
            
    stats_df = pd.DataFrame(qb_stats)
    
    # Merge back to QBs
    qbs = qbs.merge(stats_df, on=['player_id', 'season'], how='left')
    
    # Define "Konami" (Mobile) vs "Pocket"
    # Threshold: > 25 yards/game or > 0.4 TD/game = Mobile
    qbs['archetype'] = np.where(
        (qbs['rushing_ypg'] > 25) | (qbs['rushing_td_pg'] > 0.4), 
        'Mobile', 
        'Pocket'
    )
    
    # 3. Analyze Fail High by Archetype
    print("\n--- H1: Konami Code Hypothesis ---")
    
    qbs['is_fail_high'] = qbs['pit'] > 0.9
    
    print("Fail High (Target ~10%):")
    print(qbs.groupby('archetype')['is_fail_high'].mean())
    # 4. Analyze by Game Environment (Shootout)
    # We need Actual Game Total Score.
    # We don't have it in the CSV. But we have 'week' and 'season'.
    # We can fetch it from PBP.
    
    print("\n--- H2: Shootout Hypothesis ---")
    # Get Game Totals
    game_totals = pbp.groupby(['season', 'week', 'game_id'])[['total_home_score', 'total_away_score']].max()
    game_totals['total_score'] = game_totals['total_home_score'] + game_totals['total_away_score']
    
    # We need to map Player -> Game ID.
    # `loader` loaded data has 'game_id'.
    # We need to find which game the player played in.
    # Join qbs with pbp on player_id to get game_id?
    # Too slow.
    # Join on Team? Roster has team.
    # qbs has 'team' (from benchmark merge).
    
    # Map (Season, Week, Team) -> Game ID
    schedule_map = pbp[['season', 'week', 'home_team', 'away_team', 'total_home_score', 'total_away_score', 'game_id']].drop_duplicates()
    
    # This is tricky because player team might be Home or Away.
    # Let's try to merge on (Season, Week, Team=Home) OR (Season, Week, Team=Away).
    
    # Simplified: Create a mapping (Season, Week, Team) -> Total Score
    team_game_scores = []
    for _, row in schedule_map.iterrows():
        total = row['total_home_score'] + row['total_away_score']
        team_game_scores.append({'season': row['season'], 'week': row['week'], 'team': row['home_team'], 'game_total': total})
        team_game_scores.append({'season': row['season'], 'week': row['week'], 'team': row['away_team'], 'game_total': total})
        
    totals_df = pd.DataFrame(team_game_scores)
    
    qbs = qbs.merge(totals_df, on=['season', 'week', 'team'], how='left')
    
    # Bin Totals
    qbs['game_type'] = pd.cut(qbs['game_total'], bins=[0, 40, 50, 100], labels=['Low', 'Mid', 'Shootout'])
    
    print("Fail High by Game Type:")
    print(qbs.groupby('game_type')['is_fail_high'].mean())
    
    # Interaction
    print("\n--- Interaction: Archetype x Game Type ---")
    print(qbs.pivot_table(index='archetype', columns='game_type', values='is_fail_high', aggfunc='mean'))

if __name__ == "__main__":
    diagnose_qb_error()
