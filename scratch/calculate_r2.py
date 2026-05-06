import pandas as pd
import joblib
from sklearn.metrics import r2_score
from src.data.loader import load_scada, load_nwp, merge_datasets
from src.data.cleaner import clean
from src.features.engineering import build_features
from src.models.train import load_feature_cols

def calculate_r2():
    print("Loading data...")
    scada_df = load_scada("data/raw/scada_generation.csv")
    nwp_df = load_nwp("data/raw/nwp_weather.csv")
    
    # Merge and clean
    merged = merge_datasets(scada_df, nwp_df)
    clean_df, _ = clean(merged)
    
    # Build features
    print("Building features...")
    feature_df = build_features(clean_df)
    
    for plant_type in ["solar", "wind"]:
        subset_df = feature_df[feature_df["plant_type"] == plant_type].copy()
        
        if len(subset_df) == 0:
            print(f"No {plant_type} data found.")
            continue
            
        print(f"Calculating R2 for {plant_type} on {len(subset_df)} records...")
        
        # Load trained P50 model
        try:
            model_p50 = joblib.load(f"models/saved/{plant_type}_p50.pkl")
        except FileNotFoundError:
            print(f"Trained {plant_type} model not found.")
            continue
            
        # Get feature columns
        feature_cols = getattr(model_p50, "feature_name_", None) or load_feature_cols(plant_type)
        feature_cols = [col for col in feature_cols if col in subset_df.columns]
            
        X = subset_df[feature_cols].copy()
        categories = getattr(getattr(model_p50, "booster_", None), "pandas_categorical", None)
        if categories and "plant_id" in X.columns:
            # Note: The categorical encoding might be different for solar/wind
            # but usually plant_id is the first category in this codebase
            X["plant_id"] = pd.Categorical(X["plant_id"], categories=categories[0])
        
        y_true = subset_df["plf"].fillna(0)
        
        # Predict
        y_pred = model_p50.predict(X).clip(0, 1)
        
        r2 = r2_score(y_true, y_pred)
        print(f"[{plant_type}] R-squared (R2): {r2:.4f}")

if __name__ == "__main__":
    calculate_r2()
