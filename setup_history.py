from data import loader
from stats import injuries

print("Downloading historical data (2017-2018) for backtesting...")
loader.clean_and_save_data([2017, 2018])
injuries.clean_and_save_data([2017, 2018])
print("Done.")
