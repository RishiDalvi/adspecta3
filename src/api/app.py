# src/api/app.py
import sys
import os
from typing import Optional

# Make sure project root is on sys.path (so src.* imports work)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
from src.model.features import build_features
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AdSpecta API")

# Enable CORS for frontend use
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------
# REQUEST MODEL
# --------------------------
class AdRequest(BaseModel):
    lat: float
    lng: float
    budget: float

    audience_age_min: int = 18
    audience_age_max: int = 60
    audience_type: str = "general"  # students, it_workers, shoppers, residents, tourists, general

    preferred_type: Optional[str] = None


# --------------------------
# PATHS (absolute)
# --------------------------
MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "xgb_model.joblib")
CSV_PATH = os.path.join(PROJECT_ROOT, "data", "sample_adspaces.csv")


# --------------------------
# LOAD MODEL (with safe error handling)
# --------------------------
MODEL = None
SCALER = None

try:
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
    bundle = joblib.load(MODEL_PATH)
    MODEL = bundle.get("model")
    SCALER = bundle.get("scaler")
    if MODEL is None:
        raise RuntimeError("Loaded model bundle doesn't contain 'model'")
except Exception as e:
    # Fail fast at startup with a clear message in logs
    # We raise so uvicorn shows the error during startup
    raise RuntimeError(f"Failed to load model: {e}")


# --------------------------
# AUDIENCE MATCHING LOGIC
# --------------------------
def calculate_audience_match(row, req: AdRequest):
    score = 0.0

    # Age-based targeting
    if req.audience_age_min <= 25:
        score += float(row.get("footfall_score", 0)) * 0.2

    # Audience type scoring
    aud = (req.audience_type or "general").lower()
    if aud == "students":
        score += float(row.get("landmark_score", 0)) * 0.3
        score += float(row.get("business_density", 0)) * 0.1
    elif aud == "it_workers":
        score += float(row.get("business_density", 0)) * 0.3
        score += float(row.get("visibility_score", 0)) * 0.1
    elif aud == "shoppers":
        score += float(row.get("landmark_score", 0)) * 0.4
    elif aud == "residents":
        score += float(row.get("population_density", 0)) * 0.4
    elif aud == "tourists":
        score += float(row.get("landmark_score", 0)) * 0.5

    score += float(row.get("traffic_score", 0)) * 0.1

    return score


# --------------------------
# PREDICT ENDPOINT
# --------------------------
@app.post("/predict")
def predict(req: AdRequest):
    # load CSV
    if not os.path.exists(CSV_PATH):
        raise HTTPException(status_code=500, detail=f"Adspace CSV not found: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)

    # local haversine (correct formula)
    def haversine(lat1, lon1, lat2, lon2):
        from math import radians, sin, cos, asin, sqrt

        R = 6371.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        return 2 * R * asin(sqrt(a))

    # compute distances
    df["distance_km"] = df.apply(lambda r: haversine(req.lat, req.lng, r["lat"], r["lng"]), axis=1)

    # NOTE: you may relax the radius during debugging
    df = df[df["distance_km"] <= 10]

    # filter by preferred type if provided
    if req.preferred_type:
        df = df[df["type"].str.lower() == req.preferred_type.lower()]

    if df.empty:
        raise HTTPException(status_code=404, detail="No adspaces match your filters")

    # build features and predict
    X, raw = build_features(df)

    # Ensure X has rows
    if X.shape[0] == 0:
        raise HTTPException(status_code=500, detail="Feature engineering produced no rows")

    # Predict
    try:
        preds = MODEL.predict(X)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model prediction failed: {e}")

    raw["predicted_impressions"] = pd.Series(preds).round().astype(int).values

    # Base adscore from model (guard divide-by-zero)
    pmin = preds.min()
    pmax = preds.max()
    if pmax - pmin == 0:
        raw["adscore"] = 50.0  # neutral score when all preds identical
    else:
        raw["adscore"] = (((preds - pmin) / (pmax - pmin)) * 100).round(1)

    # Budget filter
    raw = raw[raw["price_per_month"] <= req.budget]
    if raw.empty:
        raise HTTPException(status_code=404, detail="No adspaces fit your budget")

    # Audience matching
    raw["audience_match"] = raw.apply(lambda r: calculate_audience_match(r, req), axis=1)

    # Final score = 70% model + 30% audience match
    raw["final_score"] = (raw["adscore"] * 0.7) + (raw["audience_match"] * 0.3)

    # Sort by final_score and return
    raw = raw.sort_values("final_score", ascending=False)

    # Select columns for response (keep numbers native types)
    out = raw.head(10)[
        [
            "id",
            "name",
            "lat",
            "lng",
            "type",
            "price_per_month",
            "predicted_impressions",
            "audience_match",
            "final_score",
        ]
    ].to_dict(orient="records")

    return out


# --------------------------
# HEALTH CHECK
# --------------------------
@app.get("/health")
def health():
    return {"status": "ok"}
