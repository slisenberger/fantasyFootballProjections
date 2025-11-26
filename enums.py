from enum import Enum

class StrEnum(str, Enum):
    """Base class for string enums to allow easy comparison."""
    def __str__(self):
        return self.value

class PlayType(StrEnum):
    PASS = "pass"
    RUN = "run"
    PUNT = "punt"
    FIELD_GOAL = "field_goal"
    NO_PLAY = "no_play"
    KICKOFF = "kickoff"
    EXTRA_POINT = "extra_point"

class Position(StrEnum):
    QB = "QB"
    RB = "RB"
    WR = "WR"
    TE = "TE"
    K = "K"
    DEF = "DEF"

class StatKey(StrEnum):
    """Keys used in statistics dictionaries."""
    AIR_YARDS = "air_yards"
    YAC = "yards_after_catch"
    RUSHING_YARDS = "rushing_yards"
    TARGETS = "targets"
    CARRIES = "carries"
