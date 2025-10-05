"""
main.py — Orchestrates AQI fetching, prediction, and interactive map generation.
"""

import argparse
from fetch_aod import load_aod_data
from predict_aqi import fetch_past_week_data, train_predictor, predict_tomorrow
from map_builder import build_map


def main():
    parser = argparse.ArgumentParser(description="Build AQI + AOD interactive map with predictions.")
    parser.add_argument("--force-refresh", action="store_true", help="Force re-fetch of weekly AQI data (ignore cache).")
    args = parser.parse_args()

    print("🌎 Loading data...")

    # Step 1 — Fetch past week’s AQI data (cached)
    df_aqi = fetch_past_week_data(force_refresh=args.force_refresh)
    if df_aqi is None or df_aqi.empty:
        print("⚠️ No AQI data available — using fallback mock dataset.")
        from predict_aqi import _mock_weekly_data
        df_aqi = _mock_weekly_data()

    # Step 2 — Load NASA MERRA-2 aerosol (AOD) data
    try:
        df_aod = load_aod_data()
    except Exception as e:
        print(f"⚠️ Failed to load AOD data: {e}")
        df_aod = None

    # Step 3 — Train predictor using historical AQI data
    print("🤖 Training AQI predictor...")
    try:
        model = train_predictor(df_aqi)
    except Exception as e:
        print(f"⚠️ Model training failed: {e}")
        model = None

    # Step 4 — Predict tomorrow’s AQI
    df_pred = None
    if model is not None:
        try:
            df_pred = predict_tomorrow(model, df_aqi)
        except Exception as e:
            print(f"⚠️ Prediction failed: {e}")

    # Step 5 — Count and summarize
    def safe_len(df):
        try:
            return len(df)
        except Exception:
            return 0

    print(f"AQI points: {safe_len(df_aqi)} | AOD points: {safe_len(df_aod)} | Predictions: {safe_len(df_pred)}")

    # Step 6 — Build and save interactive map
    print("🗺️ Building map...")
    try:
        build_map(df_aqi, df_aod, df_pred)
    except Exception as e:
        print(f"⚠️ Map generation failed: {e}")
        return

    print("✅ Done — Open 'air_quality_map.html' to view your interactive map!")


if __name__ == "__main__":
    main()
