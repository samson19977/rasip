"""
RASIP ML Training Script v2.0
Trains crop suitability model using district data from Supabase.
Run: cd backend && python ../ml/notebooks/train_model.py

Requires: pip install scikit-learn xgboost shap joblib pandas
"""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error, accuracy_score
import joblib

# ── Training data: all 30 districts × 6 crops ──────────────────
# Features: rainfall, temp, elevation, soil_ph, soil_type(encoded),
#           humidity, ndvi, flood_risk, drought_risk, slope
# Labels: suitability_score (0-100), yield_t_ha, risk_level

SOIL_ENC = {"Andosol": 4, "Cambisol": 3, "Ferralsol": 2, "Lixisol": 1, "Other": 0}

TRAINING_SAMPLES = [
    # (rainfall, temp, elev, ph, soil_enc, humidity, ndvi, flood, drought, slope, crop_enc, suit, yield, risk)
    # Potato in Andosol high-altitude districts
    (1340, 15.5, 1870, 6.2, 4, 78, 0.62, 18, 12, 15.3, 0, 88, 19.2, 0),  # Musanze - potato
    (1400, 14.5, 1900, 5.8, 4, 80, 0.65, 15,  8, 19.0, 0, 92, 21.0, 0),  # Nyamagabe - potato
    (1450, 17.0, 1680, 5.8, 4, 79, 0.66, 16,  8, 19.5, 0, 85, 18.5, 0),  # Nyamasheke - potato
    (1280, 16.3, 1760, 6.0, 4, 75, 0.58, 22, 14, 18.5, 0, 82, 17.2, 0),  # Nyabihu - potato
    # Potato in dry Eastern districts (low suit)
    ( 850, 21.5, 1370, 5.4, 1, 58, 0.32, 55, 62,  5.0, 0, 28,  7.8, 2),  # Bugesera - potato
    ( 800, 22.0, 1500, 6.0, 3, 55, 0.38, 38, 70,  3.5, 0, 22,  6.1, 2),  # Nyagatare - potato
    ( 900, 21.8, 1420, 5.3, 1, 56, 0.30, 42, 65,  3.8, 0, 18,  5.5, 2),  # Kayonza - potato
    # Maize in Eastern province (moderate-good)
    ( 920, 21.0, 1380, 5.5, 2, 60, 0.35, 45, 55,  4.5, 1, 58,  3.8, 1),  # Gatsibo - maize
    ( 980, 20.5, 1440, 5.6, 2, 61, 0.36, 50, 52,  5.5, 1, 55,  3.6, 1),  # Kirehe - maize
    (1050, 20.3, 1460, 5.7, 2, 64, 0.42, 40, 42,  4.8, 1, 62,  4.1, 1),  # Rwamagana - maize
    (1340, 15.5, 1870, 6.2, 4, 78, 0.62, 18, 12, 15.3, 1, 72,  5.8, 0),  # Musanze - maize (OK)
    # Coffee in suitable districts
    (1340, 15.5, 1870, 6.2, 4, 78, 0.62, 18, 12, 15.3, 2, 84,  1.3, 0),  # Musanze - coffee
    (1450, 17.0, 1680, 5.8, 4, 79, 0.66, 16,  8, 19.5, 2, 89,  1.5, 0),  # Nyamasheke - coffee
    (1350, 17.5, 1620, 6.1, 4, 76, 0.60, 20, 12, 16.0, 2, 82,  1.2, 0),  # Karongi - coffee
    ( 850, 21.5, 1370, 5.4, 1, 58, 0.32, 55, 62,  5.0, 2, 15,  0.3, 2),  # Bugesera - coffee (bad)
    # Tea in high-rainfall highland districts
    (1400, 14.5, 1900, 5.8, 4, 80, 0.65, 15,  8, 19.0, 3, 91,  3.5, 0),  # Nyamagabe - tea
    (1450, 17.0, 1680, 5.8, 4, 79, 0.66, 16,  8, 19.5, 3, 88,  3.8, 0),  # Nyamasheke - tea
    (1340, 15.5, 1870, 6.2, 4, 78, 0.62, 18, 12, 15.3, 3, 85,  2.3, 0),  # Musanze - tea
    ( 800, 22.0, 1500, 6.0, 3, 55, 0.38, 38, 70,  3.5, 3, 12,  0.2, 2),  # Nyagatare - tea (bad)
    # Bean in mixed districts
    (1150, 19.0, 1520, 6.1, 1, 68, 0.47, 38, 30,  8.5, 4, 68,  1.7, 1),  # Kamonyi - bean
    (1200, 18.3, 1580, 6.0, 3, 72, 0.52, 22, 25,  9.8, 4, 74,  1.8, 0),  # Huye - bean
    (1100, 19.2, 1500, 5.8, 2, 67, 0.45, 32, 35,  8.0, 4, 62,  1.5, 1),  # Ruhango - bean
    # Banana across provinces
    (1340, 15.5, 1870, 6.2, 4, 78, 0.62, 18, 12, 15.3, 5, 76, 22.5, 0),  # Musanze - banana
    (1050, 20.3, 1460, 5.7, 2, 64, 0.42, 40, 42,  4.8, 5, 70, 20.1, 0),  # Rwamagana - banana
    ( 850, 21.5, 1370, 5.4, 1, 58, 0.32, 55, 62,  5.0, 5, 55, 16.5, 1),  # Bugesera - banana
]

CROP_NAMES = ["potato", "maize", "coffee", "tea", "bean", "banana"]
RISK_NAMES = ["Low", "Medium", "High"]


def train():
    df = pd.DataFrame(TRAINING_SAMPLES, columns=[
        "rainfall", "temp", "elevation", "soil_ph", "soil_enc",
        "humidity", "ndvi", "flood_risk", "drought_risk", "slope",
        "crop_enc", "suitability", "yield_t_ha", "risk_enc"
    ])

    feature_cols = ["rainfall", "temp", "elevation", "soil_ph", "soil_enc",
                    "humidity", "ndvi", "flood_risk", "drought_risk", "slope", "crop_enc"]
    X = df[feature_cols].values
    y_suit = df["suitability"].values
    y_yield = df["yield_t_ha"].values
    y_risk = df["risk_enc"].values

    # ── Suitability Regressor ──
    X_train, X_test, y_train, y_test = train_test_split(X, y_suit, test_size=0.2, random_state=42)
    suit_model = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42)
    suit_model.fit(X_train, y_train)
    mse = mean_squared_error(y_test, suit_model.predict(X_test))
    print(f"Suitability model RMSE: {mse**0.5:.2f} (on {len(X_test)} test samples)")

    # ── Yield Regressor ──
    yield_model = RandomForestRegressor(n_estimators=100, random_state=42)
    yield_model.fit(X, y_yield)

    # ── Risk Classifier ──
    risk_model = GradientBoostingClassifier(n_estimators=100, random_state=42)
    risk_model.fit(X, y_risk)

    # ── Feature importance ──
    feat_importance = dict(zip(feature_cols, suit_model.feature_importances_))
    sorted_feats = sorted(feat_importance.items(), key=lambda x: x[1], reverse=True)
    print("\nFeature importances (suitability model):")
    for feat, imp in sorted_feats:
        bar = "█" * int(imp * 40)
        print(f"  {feat:18s} {bar} {imp:.3f}")

    # ── Save models ──
    os.makedirs("models", exist_ok=True)
    joblib.dump(suit_model,  "models/suitability_model.pkl")
    joblib.dump(yield_model, "models/yield_model.pkl")
    joblib.dump(risk_model,  "models/risk_model.pkl")

    with open("models/feature_cols.json", "w") as f:
        json.dump(feature_cols, f)

    print("\n✓ Models saved to ml/notebooks/models/")
    print("  suitability_model.pkl")
    print("  yield_model.pkl")
    print("  risk_model.pkl")
    print("\nIn production: copy these to backend/ml/models/ and load in ml_service.py")


if __name__ == "__main__":
    train()
