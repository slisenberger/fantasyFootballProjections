# Wide Receiver Linear Model tries to estimate the number of points a wide receiver will score using QB intent from
# previous games.
# 1. Figure out a number of total targets for each team
# 1a. This is different in the red zone, where targets matter more.
# 2. Distribute the targets, using previous snap counts and target shares, and defensive PI
# 3. determine the YAC for

# I will use simulations with variance and random chance to create a distribution of outcomes.