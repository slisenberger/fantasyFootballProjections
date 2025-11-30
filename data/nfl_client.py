import nflreadpy as nfl
import pandas as pd

def to_pandas(df):
    """Helper to ensure we return Pandas DataFrames."""
    if hasattr(df, "to_pandas"):
        return df.to_pandas()
    return df

def import_seasonal_rosters(years, columns=None):
    """Mimics nfl_data_py.import_seasonal_rosters"""
    df = to_pandas(nfl.load_rosters(years))
    
    # MAPPING: nflreadpy uses 'gsis_id', legacy uses 'player_id'
    rename_map = {}
    if 'gsis_id' in df.columns:
        rename_map['gsis_id'] = 'player_id'
    if 'full_name' in df.columns:
        rename_map['full_name'] = 'player_name'
        
    if rename_map:
        df = df.rename(columns=rename_map)
        
    if columns:
        # Ensure filtered columns exist (handle renames first)
        available_cols = [c for c in columns if c in df.columns]
        df = df[available_cols]
        
    return df

def import_schedules(years):
    return to_pandas(nfl.load_schedules(years))

def import_depth_charts(years):
    """Mimics nfl_data_py.import_depth_charts"""
    df = to_pandas(nfl.load_depth_charts(years))
    # nflreadpy already has 'depth_team' and 'position', which matches
    # what stats/players.py expects in its "modern" block.
    return df

def import_injuries(years):
    return to_pandas(nfl.load_injuries(years))

def import_ids(columns=None, ids=None):
    """Mimics nfl_data_py.import_ids"""
    df = to_pandas(nfl.load_players())
    
    # MAPPING: Fix column mismatches for stats/injuries.py
    rename_map = {
        'display_name': 'name',
        'latest_team': 'team',
        # 'gsis_id': 'player_id' # Removed: Legacy library keeps gsis_id here
    }
    df = df.rename(columns=rename_map)
    
    if columns:
         # Strict filtering like legacy lib
         available_cols = [c for c in columns if c in df.columns]
         df = df[available_cols]
    return df

def load_pbp_data(years):
    """New helper for loader.py"""
    return to_pandas(nfl.load_pbp(years))

def import_ftn_data(years):
    """Wraps nflreadpy.load_ftn_data"""
    return to_pandas(nfl.load_ftn_data(years))

def import_participation_data(years):
    """Wraps nflreadpy.load_participation"""
    return to_pandas(nfl.load_participation(years))

def import_snap_counts(years):
    """Wraps nflreadpy.load_snap_counts"""
    return to_pandas(nfl.load_snap_counts(years))
