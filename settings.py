from pydantic import BaseModel, Field
from typing import Dict, Optional

class ScoringSettings(BaseModel):
    """Configuration for Fantasy Scoring Rules."""
    
    name: str = Field("Half PPR", description="Name of the scoring profile")
    
    # Rushing
    rush_td: float = Field(6.0, description="Points per Rushing TD")
    rush_yard: float = Field(0.1, description="Points per Rushing Yard")
    
    # Receiving
    rec_td: float = Field(6.0, description="Points per Receiving TD")
    rec_yard: float = Field(0.1, description="Points per Receiving Yard")
    reception: float = Field(0.5, description="Points per Reception (PPR)")
    
    # Passing
    pass_td: float = Field(4.0, description="Points per Passing TD")
    pass_yard: float = Field(0.04, description="Points per Passing Yard")
    intercept: float = Field(-1.5, description="Points per Interception Thrown (QB)") # Currently -1.5 in code, often -2 in standard
    sack: float = Field(0.0, description="Points deducted from QB per sack (usually 0)")
    
    # Misc
    fumble_lost: float = Field(-2.0, description="Points per Fumble Lost")
    two_pt_conv: float = Field(2.0, description="Points for 2-point conversion")
    ret_td: float = Field(6.0, description="Points for Return TD")
    
    # Kicking
    fg_0_39: float = Field(3.0, description="FG 0-39 yards")
    fg_40_49: float = Field(4.0, description="FG 40-49 yards")
    fg_50_plus: float = Field(5.0, description="FG 50+ yards")
    pat_made: float = Field(1.0, description="Extra Point Made")
    
    # Defense (DST)
    def_sack: float = Field(1.0, description="DST points per sack")
    def_int: float = Field(2.0, description="DST points per interception")
    def_fumble_rec: float = Field(2.0, description="DST points per fumble recovery")
    def_safety: float = Field(2.0, description="DST points per safety")
    def_td: float = Field(6.0, description="DST points per TD")
    def_block: float = Field(2.0, description="DST points per blocked kick")
    
    # DST Points Allowed (Thresholds)
    pa_0: float = Field(10.0, description="Points Allowed 0")
    pa_1_6: float = Field(7.0, description="Points Allowed 1-6")
    pa_7_13: float = Field(4.0, description="Points Allowed 7-13")
    pa_14_20: float = Field(1.0, description="Points Allowed 14-20")
    pa_21_27: float = Field(0.0, description="Points Allowed 21-27")
    pa_28_34: float = Field(-1.0, description="Points Allowed 28-34")
    pa_35_plus: float = Field(-4.0, description="Points Allowed 35+")


class RuntimeSettings(BaseModel):
    """Configuration for the Simulation Engine runtime."""
    season: int = Field(2024, description="NFL Season to simulate")
    week: int = Field(1, description="Week to simulate")
    n_simulations: int = Field(5, description="Number of Monte Carlo simulations per game")
    backtest_year: Optional[int] = Field(None, description="Year to backtest (if different from season)")
    backtest_week: Optional[int] = Field(None, description="Week to backtest")
    output_dir: str = Field("projections", description="Directory to save results")
    version: str = Field("v1.0", description="Version tag for output files")
    
    # Derived/Logic flags
    use_parallel: bool = Field(True, description="Use joblib for parallel execution")


class AppConfig(BaseModel):
    """Master Configuration."""
    scoring: ScoringSettings = Field(default_factory=ScoringSettings)
    runtime: RuntimeSettings = Field(default_factory=RuntimeSettings)

    @classmethod
    def load(cls):
        # In the future, we can load from yaml/json/env here.
        # For now, just return defaults.
        return cls()
