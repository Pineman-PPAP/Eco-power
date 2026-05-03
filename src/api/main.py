"""
FastAPI Backend — Renewable Forecasting Service

Endpoints:
  POST /predict/plant          → 96-block forecast for a single plant
  POST /predict/portfolio      → forecast for all plants in metadata
  POST /predict/cluster        → aggregated cluster-level forecast
  GET  /explain/{plant_id}     → SHAP explanation for a specific block
  GET  /health                 → service health check
  POST /upload/scada           → upload SCADA CSV for retraining
  POST /upload/nwp             → upload NWP weather CSV for inference

All forecast outputs include P10/P50/P90 quantiles and confidence flags.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import io
import logging
import json
from pathlib import Path
from datetime import date

from src.data.loader import load_scada, load_nwp, merge_datasets
from src.data.cleaner import clean
from src.features.engineering import build_features, SOLAR_FEATURES, WIND_FEATURES
from src.models.predict import (
    predict_plant, predict_portfolio, aggregate_cluster,
    format_sldc_schedule, persistence_fallback, load_models
)
from src.models.explainability import (
    explain_forecast_block, compute_global_importance
)
from src.models.train import load_feature_cols

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Temporary in-memory storage for uploaded data
_uploaded_scada: Optional[pd.DataFrame] = None
_uploaded_nwp:   Optional[pd.DataFrame] = None
_feature_df:     Optional[pd.DataFrame] = None

app = FastAPI(
    title="Renewable Generation Forecasting API",
    description=(
        "Physics-informed AI forecasting for solar and wind energy generation. "
        "Produces P10/P50/P90 quantile forecasts with SHAP explainability. "
        "Acts as a plug-in decision-support layer for Karnataka's grid (KREDL/KSPDCL)."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
# Pydantic request / response models
# --------------------------------------------------------------------------- #
class PlantForecastRequest(BaseModel):
    plant_id:              str = Field(..., description="Unique plant identifier")
    plant_type:            str = Field(..., description="'solar' or 'wind'")
    installed_capacity_mw: float = Field(..., gt=0, description="Nameplate capacity in MW")
    forecast_date:         str = Field(..., description="Date to forecast (YYYY-MM-DD)")
    use_fallback:          bool = Field(False, description="Force persistence fallback")


class PortfolioForecastRequest(BaseModel):
    forecast_date: str = Field(..., description="Date to forecast (YYYY-MM-DD)")
    plants: List[Dict] = Field(
        ...,
        description="List of {plant_id, plant_type, installed_capacity_mw}"
    )


class ClusterForecastRequest(BaseModel):
    forecast_date:   str = Field(..., description="Date to forecast (YYYY-MM-DD)")
    plants:          List[Dict]
    cluster_mapping: Optional[Dict[str, str]] = Field(
        None,
        description="Map of plant_id → cluster_id. If null, all plants are grouped."
    )


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _get_feature_df() -> pd.DataFrame:
    """Return cached feature DataFrame or raise if data not uploaded."""
    global _feature_df
    if _feature_df is None:
        raise HTTPException(
            status_code=400,
            detail="No data loaded. Upload SCADA and NWP files first via /upload/scada and /upload/nwp"
        )
    return _feature_df


def _rebuild_features() -> None:
    """Merge uploaded SCADA and NWP, clean, and build features."""
    global _uploaded_scada, _uploaded_nwp, _feature_df
    if _uploaded_scada is None or _uploaded_nwp is None:
        return
    merged = merge_datasets(_uploaded_scada, _uploaded_nwp)
    clean_df, _ = clean(merged)
    _feature_df  = build_features(clean_df)
    logger.info(f"Feature matrix rebuilt: {len(_feature_df):,} rows")


# --------------------------------------------------------------------------- #
# Upload endpoints
# --------------------------------------------------------------------------- #
@app.post("/upload/scada", summary="Upload SCADA generation data (CSV)")
async def upload_scada(file: UploadFile = File(...)):
    """Upload a SCADA generation CSV file. See README for required columns."""
    global _uploaded_scada
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        _uploaded_scada = df
        _rebuild_features()
        return {
            "status":    "ok",
            "rows":      len(df),
            "plants":    df["plant_id"].nunique() if "plant_id" in df.columns else "unknown",
            "message":   "SCADA data uploaded and processed successfully.",
        }
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/upload/nwp", summary="Upload NWP weather forecast data (CSV)")
async def upload_nwp(file: UploadFile = File(...)):
    """Upload an NWP weather forecast CSV file. See README for required columns."""
    global _uploaded_nwp
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        _uploaded_nwp = df
        _rebuild_features()
        return {
            "status":  "ok",
            "rows":    len(df),
            "message": "NWP data uploaded and processed successfully.",
        }
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


# --------------------------------------------------------------------------- #
# Forecast endpoints
# --------------------------------------------------------------------------- #
@app.post("/predict/plant", summary="Get 96-block SLDC forecast for a single plant")
async def predict_plant_endpoint(req: PlantForecastRequest):
    """
    Returns a 96-block SLDC-format schedule for the requested plant and date.
    Each block includes P10/P50/P90 values and a confidence flag.
    """
    feature_df = _get_feature_df()

    try:
        if req.use_fallback:
            forecast = persistence_fallback(feature_df, req.plant_id, req.installed_capacity_mw)
        else:
            models = load_models(req.plant_type)
            forecast = predict_plant(
                feature_df, req.plant_id, req.plant_type,
                req.installed_capacity_mw, models
            )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    sldc = format_sldc_schedule(forecast, req.forecast_date)
    return {
        "plant_id":      req.plant_id,
        "forecast_date": req.forecast_date,
        "n_blocks":      len(sldc),
        "schedule":      sldc.to_dict(orient="records"),
    }


@app.post("/predict/portfolio", summary="Get forecasts for multiple plants")
async def predict_portfolio_endpoint(req: PortfolioForecastRequest):
    """
    Run inference for all plants in the request and return per-plant SLDC schedules.
    """
    feature_df = _get_feature_df()
    plant_meta = pd.DataFrame(req.plants)

    portfolio_df = predict_portfolio(feature_df, plant_meta)
    if len(portfolio_df) == 0:
        raise HTTPException(status_code=404, detail="No forecasts could be generated.")

    # Format SLDC for each plant
    all_schedules = {}
    for plant_id in portfolio_df["plant_id"].unique():
        plant_fc = portfolio_df[portfolio_df["plant_id"] == plant_id]
        sldc = format_sldc_schedule(plant_fc, req.forecast_date)
        all_schedules[plant_id] = sldc.to_dict(orient="records")

    return {
        "forecast_date": req.forecast_date,
        "n_plants":      len(all_schedules),
        "schedules":     all_schedules,
    }


@app.post("/predict/cluster", summary="Get aggregated cluster-level forecast")
async def predict_cluster_endpoint(req: ClusterForecastRequest):
    """
    Aggregate plant-level forecasts into cluster/regional totals.
    """
    feature_df = _get_feature_df()
    plant_meta  = pd.DataFrame(req.plants)
    portfolio_df = predict_portfolio(feature_df, plant_meta)

    cluster_df = aggregate_cluster(portfolio_df, req.cluster_mapping)
    return {
        "forecast_date": req.forecast_date,
        "clusters":      cluster_df.to_dict(orient="records"),
    }


# --------------------------------------------------------------------------- #
# Explainability endpoint
# --------------------------------------------------------------------------- #
@app.get("/explain/{plant_id}", summary="SHAP explanation for a specific forecast block")
async def explain_block(
    plant_id:  str,
    timestamp: str = Query(..., description="ISO timestamp (YYYY-MM-DDTHH:MM:00)"),
    plant_type: str = Query(..., description="'solar' or 'wind'"),
    installed_capacity_mw: float = Query(..., description="Nameplate capacity in MW"),
):
    """
    Returns a SHAP-based explanation for a specific 15-minute forecast block,
    including the top 5 driving features and a plain-English narrative.
    """
    feature_df = _get_feature_df()
    try:
        ts = pd.Timestamp(timestamp)
    except Exception:
        raise HTTPException(status_code=422, detail=f"Invalid timestamp: {timestamp}")

    try:
        models       = load_models(plant_type)
        feature_cols = load_feature_cols(plant_type)
        explanation  = explain_forecast_block(
            model=models["p50"],
            feature_df=feature_df,
            plant_id=plant_id,
            timestamp=ts,
            feature_cols=feature_cols,
            installed_capacity_mw=installed_capacity_mw,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return explanation


# --------------------------------------------------------------------------- #
# Health check
# --------------------------------------------------------------------------- #
@app.get("/health", summary="Service health check")
async def health():
    global _uploaded_scada, _uploaded_nwp, _feature_df
    return {
        "status":        "healthy",
        "scada_loaded":  _uploaded_scada is not None,
        "nwp_loaded":    _uploaded_nwp is not None,
        "features_ready": _feature_df is not None,
        "feature_rows":  len(_feature_df) if _feature_df is not None else 0,
    }


@app.get("/", summary="API info")
async def root():
    return {
        "service": "Renewable Generation Forecasting API",
        "version": "1.0.0",
        "docs":    "/docs",
        "health":  "/health",
    }
