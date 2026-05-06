from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
import lightgbm as lgb
import warnings
import requests
from pvlib import solarposition, atmosphere
import os

warnings.filterwarnings('ignore')

app = FastAPI(title="Solar AI Dispatch API")

# Allow your frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- PATH RESOLUTION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'synthetic_base_model.txt')
DATA_PATH = os.path.join(BASE_DIR, 'karnataka_training_data_realistic.csv')

print("1. Loading Model and Data...")
bst = lgb.Booster(model_file=MODEL_PATH)
model_features = bst.feature_name()
rng = np.random.default_rng(42)

# Find SHAP indices dynamically to prevent hardcoding errors
ghi_idx = model_features.index('GHI') if 'GHI' in model_features else 24
tcc_idx = model_features.index('TCC') if 'TCC' in model_features else 18
temp_idx = model_features.index('Temperature') if 'Temperature' in model_features else 13
sza_idx = model_features.index('SZA') if 'SZA' in model_features else 0

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
            window_df = eval_df
    else:
        window_df = eval_df

    if len(window_df) > 0:
        window_df['Pred_Nowcast'] = simulate_horizon(window_df, 0.00)
        window_df['Pred_Hourly'] = simulate_horizon(window_df, 0.05)
        window_df['Pred_Intraday'] = simulate_horizon(window_df, 0.15)
        window_df['Pred_NextDay'] = simulate_horizon(window_df, 0.30)
        window_df['Is_Anomaly'] = (window_df['Pred_NextDay'] - window_df['Generation_MW']) > 10.0

    payload = []
    first_ts = window_df.index[0] if len(window_df) > 0 else None
    contribs = bst.predict(window_df[model_features], pred_contrib=True)
    
    for idx, (timestamp, row) in enumerate(window_df.iterrows()):
        is_future = first_ts and (timestamp >= first_ts + pd.Timedelta(days=1))
        payload.append({
            "timestamp": timestamp.isoformat(),
            "actual_mw": round(row['Generation_MW'], 2) if not is_future else None,
            "pred_nextday": round(row['Pred_NextDay'], 2),
            "is_anomaly": bool(row['Is_Anomaly']),
            "weather_ghi": round(row['GHI'], 0),
            "weather_temp": round(row['Temperature'], 1),
            "weather_clouds": round(row['TCC'] * 100, 0),
            "contrib_ghi": round(contribs[idx][ghi_idx], 2),
            "contrib_clouds": round(contribs[idx][tcc_idx], 2),
            "contrib_temp": round(contribs[idx][temp_idx], 2),
            "contrib_time": round(contribs[idx][sza_idx], 2)
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
    if params.start_date:
        try:
            ts = pd.to_datetime(params.start_date).tz_localize('Asia/Kolkata')
            sandbox_df = test_df.loc[ts : ts + pd.Timedelta(days=1)].copy()
        except:
            sandbox_df = eval_df.iloc[:48].copy()
    else:
        day1_end = start_date + pd.Timedelta(days=1)
        sandbox_df = test_df.loc[start_date:day1_end].copy()
    
    sandbox_df['TCC'] = np.clip(sandbox_df['TCC'] * params.cloud_cover_multiplier, 0, 1.0)
    sandbox_df['Temperature'] = sandbox_df['Temperature'] + params.temp_offset
    
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
            "contrib_ghi": round(contribs[idx][ghi_idx], 2),
            "contrib_clouds": round(contribs[idx][tcc_idx], 2),
            "contrib_temp": round(contribs[idx][temp_idx], 2),
            "contrib_time": round(contribs[idx][sza_idx], 2)
        })
        
    return payload


# ============================================================================
# ENDPOINT 3: MULTI-TENANT LIVE AI FORECAST
# ============================================================================
class PlantRequest(BaseModel):
    latitude: float
    longitude: float
    capacity_mw: float

@app.post("/api/live-prediction")
def get_live_prediction_for_plant(plant: PlantRequest):
    """Fetches weather for specific coordinates and scales the prediction."""
    
    # 1. Fetch Live Data from Open-Meteo for requested coordinates
    url = "https://api.open-meteo.com/v1/forecast"
    query_params = {
        "latitude": plant.latitude,
        "longitude": plant.longitude,
        "hourly": "temperature_2m,relative_humidity_2m,cloud_cover,wind_speed_10m,shortwave_radiation,direct_normal_irradiance,diffuse_radiation",
        "timezone": "Asia/Kolkata",
        "past_days": 1,
        "forecast_days": 2
    }
    
    response = requests.get(url, params=query_params)
    if response.status_code != 200:
        print(f"OPEN-METEO ERROR: {response.text}")
    data = response.json()
    
    # 2. Build the Base DataFrame
    live_df = pd.DataFrame({
        'datetime': pd.to_datetime(data['hourly']['time']).tz_localize('Asia/Kolkata'),
        'Temperature': data['hourly']['temperature_2m'],
        'Relative_Humidity': data['hourly']['relative_humidity_2m'],
        'TCC': np.array(data['hourly']['cloud_cover']) / 100.0,
        'Wind_Speed': data['hourly']['wind_speed_10m'],
        'GHI': data['hourly']['shortwave_radiation'],
        'DNI': data['hourly']['direct_normal_irradiance'],
        'DHI': data['hourly']['diffuse_radiation'],
    })
    live_df.set_index('datetime', inplace=True)
    
    # 3. Engineer Astrophysical Features using pvlib
    solpos = solarposition.get_solarposition(live_df.index, plant.latitude, plant.longitude)
    live_df['SZA'] = solpos['zenith']
    live_df['cos_SZA'] = np.cos(np.radians(live_df['SZA']))
    live_df['Solar_Azimuth'] = solpos['azimuth']
    live_df['Solar_Elevation'] = solpos['elevation']
    live_df['Solar_Declination'] = solpos['declination']
    live_df['AM_relative'] = atmosphere.get_relative_airmass(solpos['zenith'])
    
    # 4. Engineer Cyclical Time Features
    live_df['hour'] = live_df.index.hour
    live_df['dayofyear'] = live_df.index.dayofyear
    live_df['hour_sin'] = np.sin(2 * np.pi * live_df['hour'] / 24)
    live_df['hour_cos'] = np.cos(2 * np.pi * live_df['hour'] / 24)
    live_df['doy_sin'] = np.sin(2 * np.pi * live_df['dayofyear'] / 365)
    live_df['doy_cos'] = np.cos(2 * np.pi * live_df['dayofyear'] / 365)
    
    # 5. Engineer Rolling & Lag Features
    live_df['GHI_lag1'] = live_df['GHI'].shift(1).fillna(0)
    live_df['GHI_rollmean_1h'] = live_df['GHI'].rolling(window=2, min_periods=1).mean()
    live_df['dGHI_dt'] = live_df['GHI'].diff().fillna(0)
    live_df['dTCC_dt'] = live_df['TCC'].diff().fillna(0)
    
    # 6. MOCK Operational Features 
    live_df['rolling_gen_efficiency'] = 0.85 
    live_df['rolling_PR_proxy'] = 0.80
    live_df['Shading_Flag'] = 0
    
    for col in model_features:
        if col not in live_df.columns:
            live_df[col] = 0.0

    # 7. Run Live AI Inference & Apply Capacity Scaling
    BASE_MODEL_CAPACITY = 50.0  # Training baseline
    
    contribs = bst.predict(live_df[model_features], pred_contrib=True)
    raw_preds = bst.predict(live_df[model_features])
    raw_preds[live_df['SZA'] > 88] = 0.0 
    
    # Scale predictions dynamically
    scaled_preds = (raw_preds / BASE_MODEL_CAPACITY) * plant.capacity_mw
    live_df['Live_Predicted_MW'] = np.clip(scaled_preds, 0, plant.capacity_mw) # Cap max output
    
    # 8. Filter payload to just "Today" and "Tomorrow"
    now = pd.Timestamp.now(tz='Asia/Kolkata').replace(hour=0, minute=0, second=0)
    future_df = live_df.loc[now : now + pd.Timedelta(days=2)]
    
    # 9. Format JSON Payload 
    payload = []
    
    for current_timestamp, row in future_df.iterrows():
        idx = live_df.index.get_loc(current_timestamp)
        
        # Calculate scaling factor for SHAP values so they match the new UI
        scale_factor = plant.capacity_mw / BASE_MODEL_CAPACITY
        
        payload.append({
            "timestamp": current_timestamp.isoformat(),
            "pred_nextday": round(row['Live_Predicted_MW'], 2), 
            "actual_mw": None, 
            "is_anomaly": False,
            "weather_ghi": round(row['GHI'], 0),
            "weather_temp": round(row['Temperature'], 1),
            "weather_clouds": round(row['TCC'] * 100, 0),
            
            # Scale SHAP values so the tooltip math makes sense for smaller/larger plants
            "contrib_ghi": round(contribs[idx][ghi_idx] * scale_factor, 2),
            "contrib_clouds": round(contribs[idx][tcc_idx] * scale_factor, 2),
            "contrib_temp": round(contribs[idx][temp_idx] * scale_factor, 2),
            "contrib_time": round(contribs[idx][sza_idx] * scale_factor, 2)
        })
        
    return payload