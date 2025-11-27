import pandas as pd
import numpy as np
from data import loader
from settings import AppConfig

def analyze_clock_runoff():
    print("Loading data...")
    # Load 2023 data for analysis
    data = loader.load_data([2023, 2022])
    
    # Filter to relevant plays
    data = data.loc[data.play_type.isin(['pass', 'run', 'punt', 'field_goal'])]
    
    # Shift data to get previous play's time (to calc runoff)
    # We need to group by game to avoid diffing across games
    # Actually, quarter_seconds_remaining is for the START of the play.
    # Runoff = This Play Start - Next Play Start.
    # But we don't have next play easily aligned without shifting.
    # Alternative: Use 'time' column which is game clock at snap.
    # But easier: Data usually has a 'duration' or we can infer it.
    # Let's look at raw columns again from previous `head` output?
    # It has `quarter_seconds_remaining`.
    
    # Sort by game, play_id
    data = data.sort_values(['game_id', 'play_id'])
    
    # Calculate Runoff
    # Runoff = Current Play Time Remaining - Next Play Time Remaining
    # Only valid if same Quarter and Game.
    data['next_time'] = data.groupby(['game_id', 'qtr'])['quarter_seconds_remaining'].shift(-1)
    data['runoff'] = data['quarter_seconds_remaining'] - data['next_time']
    
    # Filter bad data (last play of quarter has NaN runoff)
    data = data.dropna(subset=['runoff'])
    # Filter huge outliers (timeouts, injuries, reviews) - Cap at 60s?
    # Play clock is 40s. Admin stoppages can make it longer.
    # For simulation, we want "effective" runoff. 
    # If we include timeouts, the average goes up. But `advance_clock` doesn't simulate timeouts explicitly yet?
    # Actually, `advance_clock` says "This is very unsophisticated".
    # If we want to simulate "Game Time Elapsed per Snap", we should include everything.
    data = data.loc[(data.runoff > 0) & (data.runoff < 100)]
    
    # Buckets
    def get_time_bucket(seconds):
        if seconds > 300: return 'high' # > 5 min
        if seconds > 120: return 'mid'  # 2-5 min
        return 'low' # < 2 min
    
    data['time_bucket'] = data['quarter_seconds_remaining'].apply(get_time_bucket)
    
    def get_score_bucket(diff):
        if diff >= 9: return 'leading_big'
        if diff > 0: return 'leading_close'
        if diff == 0: return 'tied'
        if diff > -9: return 'trailing_close'
        return 'trailing_big'
        
    data['score_bucket'] = data['score_differential'].apply(get_score_bucket)
    
    # Play Outcome Categories
    # Stopped Clock: Incomplete pass, Out of bounds
    # Running Clock: Run (in bounds), Complete pass (in bounds), Sack
    
    def get_clock_status(row):
        if row['play_type'] == 'pass':
            if row['incomplete_pass'] == 1: return 'stopped'
            # interception?
            if row['interception'] == 1: return 'stopped'
            # out of bounds? 'out_of_bounds' column exists in raw data? 
            # Not explicitly seen in `head`, but standard nflfastR has it. 
            # Assuming `complete_pass` == 1 implies running, unless out of bounds.
            # Let's simplify: Pass Complete vs Incomplete.
            return 'running' # Approximation. Better would be checking OOB.
        if row['play_type'] == 'run':
            return 'running'
        return 'running'

    # For now, let's just use play_type and simple buckets
    # Improve: check for 'out_of_bounds' if available.
    
    # Refine play_type column for grouping
    def get_detailed_play_type(row):
        if row['play_type'] == 'pass':
            if row['incomplete_pass'] == 1: return 'pass_incomplete'
            if row['interception'] == 1: return 'pass_intercepted' 
            return 'pass_complete'
        return row['play_type']

    data['play_type_detail'] = data.apply(get_detailed_play_type, axis=1)
    
    # Grouping
    # Q1-Q3 are usually similar. Q4 is special. OT is special.
    data['qtr_bucket'] = data['qtr'].apply(lambda x: 'regulation' if x < 4 else ('Q4' if x == 4 else 'OT'))
    
    # Group by: QtrBucket, TimeBucket, ScoreBucket, PlayType
    # We want Mean Runoff
    
    stats = data.groupby(['qtr_bucket', 'time_bucket', 'score_bucket', 'play_type_detail'])['runoff'].agg(['mean', 'count'])
    
    # Filter low sample size
    stats = stats.loc[stats['count'] > 10]
    
    print(stats)
    stats.to_csv("stats/clock_runoff.csv")
    print("Saved to stats/clock_runoff.csv")

if __name__ == "__main__":
    analyze_clock_runoff()
