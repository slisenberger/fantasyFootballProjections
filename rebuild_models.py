import time
import os
import shutil
import joblib
import argparse
import datetime

# Import models
from models import playcall, completion, kicking, rushers, int_return, receivers

def clear_models():
    print("Cleaning old models...")
    model_dir = "models/trained_models"
    if os.path.exists(model_dir):
        shutil.rmtree(model_dir)
    os.makedirs(model_dir)

def backup_models():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    src = "models/trained_models"
    dst = f"models/backups/backup_{timestamp}"
    
    if not os.path.exists(src):
        print("No existing models to backup.")
        return

    print(f"Backing up models to {dst}...")
    os.makedirs("models/backups", exist_ok=True) # Ensure backup dir exists
    shutil.copytree(src, dst)

def build_all(force=False, backup=False, fast=False):
    if not force:
        print("⚠️  SAFETY LOCK ENGAGED ⚠️")
        print("Rebuilding models is expensive. Use '--force' to proceed.")
        print("Use '--backup' to save current models first.")
        print("Use '--fast' for a quicker, but less accurate, rebuild (e.g., for development).")
        return

    if backup:
        backup_models()

    start_global = time.time()
    # DO NOT CALL clear_models() automatically. Models are rebuilt on demand or forced.
    
    # Ensure the base directory exists
    model_dir = "models/trained_models"
    os.makedirs(model_dir, exist_ok=True) # Ensure main model dir exists
    
    print("\n--- Starting Full Model Rebuild (2021-2024) ---")
    if fast:
        print("--- FAST REBUILD MODE ACTIVE (Reduced years, fixed bandwidth for KDEs) ---")
    
    tasks = [
        ("Playcall Model", playcall.build_playcall_model, playcall.model_name),
        ("Completion Model", completion.build_completion_model, completion.model_name),
        ("Kicking Model", kicking.build_kicking_model, kicking.model_name),
        ("Rusher Open KDE", rushers.build_rush_open_kde, rushers.rush_open_model_name),
        ("Rusher RZ KDE", rushers.build_rush_rz_kde, rushers.rush_rz_model_name),
        ("Scramble KDE", rushers.build_scramble_kde, rushers.scramble_model_name),
        ("Int Return KDE", int_return.build_int_return_kde, int_return.int_return_model_name),
        ("Receivers (Air Yards)", receivers.build_all_air_yards_kdes, None), # Handled specially
        ("Receivers (YAC)", receivers.build_all_yac_kdes, None) # Handled specially
    ]

    for name, build_func, path in tasks:
        print(f"\nBuilding {name}...")
        t0 = time.time()
        
        if "Receivers" in name: # Pass fast=fast to receivers' build functions
            if name == "Receivers (Air Yards)": result = build_func(fast=fast)
            else: result = build_func(fast=fast)
        elif "KDE" in name: # Pass fast=fast to KDE build functions
            result = build_func(fast=fast)
        else: # Other models don't need fast flag, just build
            result = build_func()

        # Save the result if path is provided and it's a single model
        if path:
            joblib.dump(result, path)
        # For receivers, their build functions already save multiple models
            
        dt = time.time() - t0
        print(f"Done in {dt:.2f}s")

    print(f"\n--- All Models Built in {time.time() - start_global:.2f}s ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rebuild Machine Learning Models")
    parser.add_argument("--force", action="store_true", help="Force rebuild (ignores safety lock)")
    parser.add_argument("--backup", action="store_true", help="Backup existing models before rebuilding")
    parser.add_argument("--fast", action="store_true", help="Perform a fast rebuild (less accurate, for dev/quick testing)")
    
    args = parser.parse_args()
    
    build_all(force=args.force, backup=args.backup, fast=args.fast)
