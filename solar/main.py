from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
import lightgbm as lgb
import warnings

warnings.filterwarnings('ignore')

app = FastAPI(title="Solar AI Dispatch API")

# Allow your frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, change this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os

# --- PATH RESOLUTION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'synthetic_base_model.txt')
DATA_PATH = os.path.join(BASE_DIR, 'karnataka_training_data_realistic.csv')

print("1. Loading Model and Data...")
bst = lgb.Booster(model_file=MODEL_PATH)
model_features = bst.feature_name()
rng = np.random.default_rng(42)

df = pd.read_csv(DATA_PATH, index_col='datetime', parse_dates=True)

# --- STRICT TIMEZONE SYNC ---
if df.index.tz is None:
    df.index = df.index.tz_localize('Asia/Kolkata')
else:
    df.index = df.index.tz_convert('Asia/Kolkata')

df.columns = [col.replace(' ', '_') for col in df.columns]

# --- ISOLATE UNSEEN TEST DATA (Last 20%) ---
n = len(df)
val_end = int(n * 0.80)
test_df = df.iloc[val_end:].copy()

# Grab a 2-day window right from the middle of the unseen Test set
start_idx = int(len(test_df) * 0.5)
start_date = test_df.index[start_idx].replace(hour=0, minute=0, second=0)
end_date = start_date + pd.Timedelta(days=2)
eval_df = test_df.loc[start_date:end_date].copy()

# --- PRE-COMPUTE 10-DAY DATA FOR INSTANT DASHBOARD LOADING ---
print("2. Pre-computing 10-Day Horizon Data...")
def simulate_horizon(data, noise_std):
    noisy_df = data.copy()
    if noise_std > 0:
        n_rows = len(noisy_df)
        noisy_df['GHI'] = np.clip(noisy_df['GHI'] * rng.normal(1.0, noise_std, n_rows), 0, 1500)
        noisy_df['TCC'] = np.clip(noisy_df['TCC'] + rng.normal(0, noise_std, n_rows), 0, 1.0)
        noisy_df['Temperature'] = noisy_df['Temperature'] + rng.normal(0, noise_std * 10, n_rows)
    
    preds = bst.predict(noisy_df[model_features])
    preds[noisy_df['SZA'] > 88] = 0.0
    return np.clip(preds, 0, None)

eval_df['Pred_Nowcast'] = simulate_horizon(eval_df, 0.00)
eval_df['Pred_Hourly'] = simulate_horizon(eval_df, 0.05)
eval_df['Pred_Intraday'] = simulate_horizon(eval_df, 0.15)
eval_df['Pred_NextDay'] = simulate_horizon(eval_df, 0.30)

# Calculate Anomalies (Grid Curtailment logic)
eval_df['Is_Anomaly'] = (eval_df['Pred_NextDay'] - eval_df['Generation_MW']) > 10.0

print("Backend Ready. Serving API...")


# ============================================================================
# ENDPOINT 1: THE 10-DAY DASHBOARD (Dynamic Window)
# ============================================================================
@app.get("/api/dashboard/10-day")
def get_10_day_dashboard(start_date: str = None):
    """Returns a 2-day performance payload. If no start_date is provided, uses the middle of the test set."""
    
    if start_date:
        try:
            requested_start = pd.to_datetime(start_date).tz_localize('Asia/Kolkata')
            requested_end = requested_start + pd.Timedelta(days=2)
            window_df = test_df.loc[requested_start:requested_end].copy()
            if window_df.empty:
                raise ValueError("No data for requested date")
        except Exception:
            # Fallback to default if date is invalid or out of range
            window_df = eval_df
    else:
        window_df = eval_df

    # Recalculate horizons for the dynamic window
    if len(window_df) > 0:
        window_df['Pred_Nowcast'] = simulate_horizon(window_df, 0.00)
        window_df['Pred_Hourly'] = simulate_horizon(window_df, 0.05)
        window_df['Pred_Intraday'] = simulate_horizon(window_df, 0.15)
        window_df['Pred_NextDay'] = simulate_horizon(window_df, 0.30)
        # Increased sensitivity: trigger anomaly if delta > 10 MW
        window_df['Is_Anomaly'] = (window_df['Pred_NextDay'] - window_df['Generation_MW']) > 10.0

    # Convert dataframe to a list of flat dictionaries
    payload = []
    
    # Use the first timestamp in the window as the baseline for hiding Day 2 actuals
    first_ts = window_df.index[0] if len(window_df) > 0 else None

    # Calculate mathematically accurate SHAP contributions (Feature Impacts)
    contribs = bst.predict(window_df[model_features], pred_contrib=True)
    
    for idx, (timestamp, row) in enumerate(window_df.iterrows()):
        # Hide actuals for Day 2 (anything 24h+ after the start)
        is_future = first_ts and (timestamp >= first_ts + pd.Timedelta(days=1))

        payload.append({
            "timestamp": timestamp.isoformat(),
            "actual_mw": round(row['Generation_MW'], 2) if not is_future else None,
            "pred_nextday": round(row['Pred_NextDay'], 2),
            "is_anomaly": bool(row['Is_Anomaly']),
            "weather_ghi": round(row['GHI'], 0),
            "weather_temp": round(row['Temperature'], 1),
            "weather_clouds": round(row['TCC'] * 100, 0),
            # Precise SHAP indices: 24:GHI, 18:TCC, 13:Temp, 0:SZA
            "contrib_ghi": round(contribs[idx][24], 2),
            "contrib_clouds": round(contribs[idx][18], 2),
            "contrib_temp": round(contribs[idx][13], 2),
            "contrib_time": round(contribs[idx][0], 2)
        })
    
    return payload


# ============================================================================
# ENDPOINT 2: THE "GOD MODE" SANDBOX (Live Inference)
# ============================================================================
class SimulationRequest(BaseModel):
    cloud_cover_multiplier: float
    temp_offset: float
    start_date: str = None

@app.post("/api/simulate")
def simulate_custom_weather(params: SimulationRequest):
    """Takes user weather tweaks, runs live LightGBM inference, and returns new curve."""
    
    # Select the correct base data window for simulation
    if params.start_date:
        try:
            ts = pd.to_datetime(params.start_date).tz_localize('Asia/Kolkata')
            sandbox_df = test_df.loc[ts : ts + pd.Timedelta(days=1)].copy()
        except:
            sandbox_df = eval_df.iloc[:48].copy()
    else:
        # Fallback to default Day 1
        day1_end = start_date + pd.Timedelta(days=1)
        sandbox_df = test_df.loc[start_date:day1_end].copy()
    
    # Apply user modifiers from the frontend sliders
    sandbox_df['TCC'] = np.clip(sandbox_df['TCC'] * params.cloud_cover_multiplier, 0, 1.0)
    sandbox_df['Temperature'] = sandbox_df['Temperature'] + params.temp_offset
    
    # Run Live Inference with contributions
    contribs = bst.predict(sandbox_df[model_features], pred_contrib=True)
    preds = bst.predict(sandbox_df[model_features])
    preds[sandbox_df['SZA'] > 88] = 0.0
    
    payload = []
    for idx, (timestamp, row) in enumerate(sandbox_df.iterrows()):
        payload.append({
            "timestamp": timestamp.isoformat(),
            "simulated_mw": round(float(np.clip(preds[idx], 0, None)), 2),
            "modified_ghi": round(row['GHI'], 0),
            "modified_clouds": round(row['TCC'] * 100, 0),
            "modified_temp": round(row['Temperature'], 1),
            "contrib_ghi": round(contribs[idx][24], 2),
            "contrib_clouds": round(contribs[idx][18], 2),
            "contrib_temp": round(contribs[idx][13], 2),
            "contrib_time": round(contribs[idx][0], 2)
        })
        
    return payload # Return flat array as requested