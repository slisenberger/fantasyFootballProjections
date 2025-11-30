import pandas as pd

def analyze_failures():
    df = pd.read_csv("benchmarks/details_v440_full.csv")
    
    # Calculate Error
    # Bias = Predicted - Actual
    # Fail High = Actual > Predicted (Negative Bias)
    df['error'] = df['mean_projection'] - df['actual']
    
    # Filter for Under-Projections (Fail High)
    under_proj = df.loc[df['error'] < -10].sort_values('error', ascending=True)
    
    print(f"--- Top 20 Under-Projected (Fail High) ---")
    print(f"Total Sample: {len(df)}")
    print(f"Total Large Fail Highs (<-10 pts): {len(under_proj)}")
    
    print(under_proj[['player_id', 'position', 'season', 'week', 'mean_projection', 'actual', 'error']].head(20))
    
    # Group by Position
    print("\n--- Failures by Position ---")
    print(under_proj.groupby('position')['error'].count())
    
    # Group by Team
    # Note: 'team' is not in details CSV, we need to merge it or just look at player_id
    # I'll remove the team breakdown for now unless I load roster
    # print(under_proj.groupby('team')['error'].count().sort_values(ascending=False).head(5))

if __name__ == "__main__":
    analyze_failures()
