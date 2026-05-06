import pandas as pd
import numpy as np
from pathlib import Path
import sys
from typing import List

def adapt_kaggle_data(input_paths: List[str], output_scada: str, output_nwp: str):
    all_dfs = []
    for path in input_paths:
        p = Path(path)
        if p.is_dir():
            files = list(p.glob("*.csv"))
            print(f"Found {len(files)} CSVs in {path}")
            for f in files:
                all_dfs.append(pd.read_csv(f))
        elif p.exists():
            print(f"Loading {path}...")
            all_dfs.append(pd.read_csv(p))
    
    if not all_dfs:
        print("No data found to process.")
        return

    df = pd.concat(all_dfs, ignore_index=True)
    
    # 1. Mapping and Basic Conversions
    mapping = {
        'temperature_2m': 'temperature_c',
        'relativehumidity_2m': 'humidity_pct',
        'windspeed_10m': 'wind_speed_ms',
        'winddirection_10m': 'wind_direction_deg',
        'windspeed_100m': 'wind_speed_hub_ms',
        'Power': 'plf'
    }
    
    # Check if columns exist before mapping
    df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})
    
    # 2. Temperature Unit Conversion (F to C)
    if 'temperature_c' in df.columns:
        print("Converting temperature from Fahrenheit to Celsius...")
        df['temperature_c'] = (df['temperature_c'] - 32) * 5/9
        
    # 3. Timestamp Handling
    if 'Time' in df.columns:
        # Check if 'Time' is just an hour (0-23)
        # We need to sort by Time if we are concatenating multiple days
        df = df.sort_values('Time').reset_index(drop=True)
        if df['Time'].dtype in [np.int64, np.float64] and df['Time'].max() <= 23:
            print("Detected 'Time' as hour of day. Generating sequence starting from 2024-01-01...")
            df['timestamp'] = pd.date_range(start='2024-01-01', periods=len(df), freq='H')
        else:
            print("Parsing 'Time' as timestamp...")
            df['timestamp'] = pd.to_datetime(df['Time'])
    else:
        print("No time column found. Generating hourly sequence...")
        df['timestamp'] = pd.date_range(start='2024-01-01', periods=len(df), freq='H')

    # 4. Plant Metadata
    df['plant_id'] = 'KAGGLE_WIND_TURBINE'
    df['plant_type'] = 'wind'
    df['installed_capacity_mw'] = 1.0 
    df['generation_mw'] = df['plf'] * df['installed_capacity_mw']
    df['availability_flag'] = 1
    df['latitude'] = 15.0 
    df['longitude'] = 75.0 
    df['hub_height_m'] = 100.0 
    
    # 5. Split and Save
    scada_cols = [
        "timestamp", "plant_id", "plant_type", "installed_capacity_mw",
        "generation_mw", "availability_flag", "latitude", "longitude"
    ]
    nwp_cols = [
        "timestamp", "plant_id", "wind_speed_ms", "wind_direction_deg",
        "temperature_c", "humidity_pct", "wind_speed_hub_ms"
    ]
    
    scada_df = df[[c for c in scada_cols if c in df.columns]]
    nwp_df = df[[c for c in nwp_cols if c in df.columns]]
    
    Path(output_scada).parent.mkdir(parents=True, exist_ok=True)
    scada_df.to_csv(output_scada, index=False)
    nwp_df.to_csv(output_nwp, index=False)
    
    print(f"\nSuccess! Merged {len(all_dfs)} datasets.")
    print(f"SCADA saved to: {output_scada} \nNWP saved to: {output_nwp}")
    print("\nYou can now run: python src/models/train.py")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scratch/kaggle_adapter.py <dir_or_file1> <file2> ...")
    else:
        adapt_kaggle_data(
            sys.argv[1:], 
            "data/raw/kaggle_scada.csv", 
            "data/raw/kaggle_nwp.csv"
        )
