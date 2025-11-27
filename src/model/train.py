import os
import pandas as pd
import joblib
from xgboost import XGBRegressor
from src.model.features import build_features, scaler


def train_and_save(csv_path='data/sample_adspaces.csv', model_path='models/xgb_model.joblib'):
    print("📌 Training started...")

    df = pd.read_csv(csv_path)
    X, raw = build_features(df)

    # Create pseudo target if missing
    if 'avg_monthly_impressions' not in raw.columns or raw['avg_monthly_impressions'].isnull().all():
        print("⚠️ No historical impressions found. Creating pseudo-labels...")
        pseudo = (
            0.3 * raw['traffic_score'] +
            0.3 * raw['footfall_score'] +
            0.2 * raw['landmark_score'] +
            0.2 * raw['visibility_score']
        ) * (raw['population_density'] / (raw['population_density'].max() + 1))

        raw['avg_monthly_impressions'] = (pseudo * 1000).round().astype(int)

    y = raw['avg_monthly_impressions'].fillna(0)

    model = XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        objective='reg:squarederror'
    )

    print("📊 Fitting model...")
    model.fit(X, y)

    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump({'model': model, 'scaler': scaler}, model_path)

    print(f"✅ Model saved at: {model_path}")


if __name__ == "__main__":
    train_and_save()
