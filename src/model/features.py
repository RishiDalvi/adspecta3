import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# Expanded numeric columns to match improved CSV for better predictions
NUMERIC_COLS = [
    'price_per_month','size_m2','visibility_score','night_visibility',
    'traffic_score','footfall_score','business_density','population_density','landmark_score',

    # NEW columns from extended CSV
    'history_impressions','history_ctr',
    'nearby_colleges','nearby_it_offices','nearby_malls','nearby_bus_stops',
    'pedestrian_per_hour','vehicle_per_hour','avg_dwell_time_min',
    'avg_income_area','is_night_active','digital_brightness',
    'dominant_gender_male_pct','owner_rating'
]

scaler = MinMaxScaler()

def build_features(adspaces_df: pd.DataFrame):
    df = adspaces_df.copy()

    # Fill missing values with safe defaults
    fill_defaults = {
        'history_impressions': 0,
        'history_ctr': 0.0,
        'nearby_colleges': 0,
        'nearby_it_offices': 0,
        'nearby_malls': 0,
        'nearby_bus_stops': 0,
        'pedestrian_per_hour': 0,
        'vehicle_per_hour': 0,
        'avg_dwell_time_min': 0.0,
        'avg_income_area': df.get('avg_income_area', pd.Series([0])).fillna(0).iloc[0],
        'is_night_active': 0,
        'digital_brightness': 0,
        'dominant_gender_male_pct': 50,
        'owner_rating': 3.0
    }

    df = df.fillna(value=fill_defaults)

    # ---------------------------
    # Derived Features
    # ---------------------------

    # 1) Cheaper price → better value
    df['price_value_score'] = 1 - (df['price_per_month'] / (df['price_per_month'].max() + 1))

    # 2) Visibility + landmark + digital brightness combined
    df['combined_vis'] = (
        df['visibility_score'] * 0.5 +
        df['landmark_score'] * 0.3 +
        (df['digital_brightness'] / 100) * 0.2
    )

    # 3) Pedestrian to vehicle ratio ⇒ useful for campaign type targeting
    df['ped_vehicle_ratio'] = df['pedestrian_per_hour'] / (df['vehicle_per_hour'] + 1)

    # 4) Income normalization (higher-income area = premium audience)
    if 'avg_income_area' in df.columns:
        df['income_norm'] = df['avg_income_area'] / (df['avg_income_area'].max() + 1)
    else:
        df['income_norm'] = 0.5

    # Build final feature list
    model_cols = [
        c for c in NUMERIC_COLS if c in df.columns
    ] + ['price_value_score', 'combined_vis', 'ped_vehicle_ratio', 'income_norm']

    X = df[model_cols].astype(float).fillna(0)

    # Scale all numeric features
    X_scaled = pd.DataFrame(
        scaler.fit_transform(X),
        columns=X.columns,
        index=df.index
    )

    return X_scaled, df