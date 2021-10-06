# The set of possible fantasy positions.

QB = "QB"
WR = "WR"
RB = "RB"
TE = "TE"
K = "K"
DEF = "DEF"

# Returns true if the position can be started at flex.
def is_flex(position):
    return position == WR or position == TE or position == RB

