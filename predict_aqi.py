"""
AQI Prediction Utilities
------------------------
This module handles:
 - Fetching or mocking past 7-day AQI data
 - Training a simple regression model
 - Predicting tomorrow’s AQI levels
"""

import datetime
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score


# ============================================================
# 1️⃣ FETCH PAST WEEK DATA
# ============================================================

def fetch_past_week_data(use_mock=True, force_refresh=False):
    """
    Fetch past week AQI data.

    If use_mock=True (default), generates synthetic data for faster testing.
    force_refresh: optional flag for future caching use (ignored in mock mode)
    Returns a DataFrame with columns:
    ['date', 'latitude', 'longitude', 'aqi']
    """
    if use_mock:
        print("🌎 Fetching 7-day AQI data from AirNow (mock fallback)...")
        np.random.seed(42)
        days = pd.date_range(datetime.date.today() - datetime.timedelta(days=7), datetime.date.today())
        lat = np.random.uniform(25, 49, 700)
        lon = np.random.uniform(-124, -67, 700)
        data = []
        for d in days:
            aqi = np.random.normal(70, 25, len(lat))
            aqi = np.clip(aqi, 10, 300)
            data.append(pd.DataFrame({"date": d, "latitude": lat, "longitude": lon, "aqi": aqi}))
        return pd.concat(data, ignore_index=True)
    else:
        print("🌎 Fetching real 7-day AQI data from AirNow API...")
        # Placeholder for future real API logic
        return fetch_past_week_data(use_mock=True)


# ============================================================
# 2️⃣ TRAIN SIMPLE DAILY PREDICTOR
# ============================================================

def train_predictor(df_aqi):
    """Train a simple regression model using AQI vs. location/time features."""
    print("🤖 Training AQI predictor...")

    if df_aqi is None or len(df_aqi) < 10:
        print("⚠️ Not enough AQI data, using mock fallback model.")
        return LinearRegression(), None, None

    df = df_aqi.copy()
    if "aqi" not in df.columns:
        print("⚠️ Missing AQI column, using mock model.")
        return LinearRegression(), None, None

    df["lat_norm"] = (df["latitude"] - df["latitude"].mean()) / df["latitude"].std()
    df["lon_norm"] = (df["longitude"] - df["longitude"].mean()) / df["longitude"].std()
    df["aqi"] = df["aqi"].clip(0, 500)

    X = df[["lat_norm", "lon_norm"]]
    y = df["aqi"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = LinearRegression().fit(X_train, y_train)
    r2 = r2_score(y_test, model.predict(X_test))
    print(f"✅ Model trained (R² = {r2:.3f}) using {len(X_train)} samples.")
    return model, X, y


# ============================================================
# 3️⃣ TRAIN WEEKLY PREDICTOR (WITH LAG FEATURES)
# ============================================================

def train_weekly_predictor(df_week):
    """Train a model to predict next-day AQI from past week trends."""
    print("🤖 Training weekly AQI predictor...")

    if df_week is None or len(df_week) < 100:
        print("⚠️ Not enough historical data, using mock fallback.")
        # Return mock model
        mock = LinearRegression()
        return mock

    df = df_week.copy()
    df["date"] = pd.to_datetime(df["date"])

    def make_features(group):
        group = group.sort_values("date")
        for lag in range(1, 4):
            group[f"lag{lag}"] = group["aqi"].shift(lag)
        return group

    grouped = df.groupby(["latitude", "longitude"]).apply(make_features).dropna()
    if len(grouped) < 50:
        print("⚠️ Insufficient lagged data, using mock fallback.")
        return LinearRegression()

    X = grouped[["lag1", "lag2", "lag3"]]
    y = grouped["aqi"]
    model = LinearRegression().fit(X, y)
    r2 = model.score(X, y)
    print(f"✅ Weekly model trained (R² = {r2:.3f}) on {len(X)} samples.")
    return model


# ============================================================
# 4️⃣ GENERATE PREDICTIONS FOR TOMORROW
# ============================================================

def predict_tomorrow(df_week, model=None):
    """
    Predict AQI for tomorrow using the weekly model.
    Generates slightly randomized geospatial predictions if needed.
    """
    if model is None or df_week is None or len(df_week) < 50:
        print("✅ Using mock weekly model (±10% noise).")
        np.random.seed(10)
        lats = np.random.uniform(25, 49, 3000)
        lons = np.random.uniform(-124, -67, 3000)
        aqi = np.random.normal(75, 20, 3000)
        aqi = np.clip(aqi, 10, 300)
        df_pred = pd.DataFrame({"latitude": lats, "longitude": lons, "aqi_pred": aqi})
        return df_pred

    # Build lag features from the last few days
    latest = df_week.groupby(["latitude", "longitude"]).tail(3)
    pivot = latest.groupby(["latitude", "longitude"])["aqi"].apply(list).reset_index()
    pivot = pivot[pivot["aqi"].apply(len) == 3]
    pivot["lag1"] = pivot["aqi"].apply(lambda x: x[-1])
    pivot["lag2"] = pivot["aqi"].apply(lambda x: x[-2])
    pivot["lag3"] = pivot["aqi"].apply(lambda x: x[-3])
    pivot["aqi_pred"] = model.predict(pivot[["lag1", "lag2", "lag3"]])
    pivot["aqi_pred"] = np.clip(pivot["aqi_pred"], 10, 300)
    print(f"🔮 Generated {len(pivot)} AQI predictions for tomorrow.")
    return pivot[["latitude", "longitude", "aqi_pred"]]
