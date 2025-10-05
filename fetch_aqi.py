"""
fetch_aqi.py — Fast concurrent AQI fetcher for the entire U.S.
Queries the AirNow 'current observation' endpoint in parallel threads.
"""

import concurrent.futures
import requests
import pandas as pd
import random

API_KEY = "19F42E70-7F2F-4F4E-98DA-BA7572BE37AD"
URL = "https://www.airnowapi.org/aq/observation/latLong/current/"

# Representative U.S. coordinates (~25 points = full coverage)
COORDS = [
    (47.61, -122.33), (34.05, -118.24), (36.16, -115.15), (37.77, -122.42),
    (40.76, -111.89), (39.74, -104.99), (41.88, -87.63), (29.76, -95.37),
    (32.78, -96.80), (38.63, -90.20), (40.71, -74.00), (42.36, -71.06),
    (39.95, -75.16), (33.75, -84.39), (25.76, -80.19), (38.90, -77.04),
    (45.52, -122.68), (44.95, -93.09), (43.04, -87.90),
    (30.33, -81.65), (29.42, -98.49), (35.22, -80.84),
    (46.87, -96.78), (35.15, -90.05), (33.45, -112.07)
]


def _fetch_point(lat, lon):
    """Fetch AQI for one coordinate pair."""
    params = {
        "format": "application/json",
        "latitude": lat,
        "longitude": lon,
        "distance": 500,
        "API_KEY": API_KEY,
    }
    try:
        r = requests.get(URL, params=params, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data:
                print(f"✅ {len(data):>2} near ({lat:.1f},{lon:.1f})")
                return data
        else:
            print(f"⚠️ {r.status_code} for ({lat:.1f},{lon:.1f})")
    except Exception as e:
        print(f"⚠️ {lat:.1f},{lon:.1f} failed: {str(e)}")
    return []


def load_aqi_data(use_mock: bool = False):
    """Fetch AQI data concurrently across the U.S."""
    if use_mock:
        return _mock_aqi_data()

    print("🌎 Fetching real-time AQI data (multi-threaded)...")

    all_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(_fetch_point, lat, lon) for lat, lon in COORDS]
        for f in concurrent.futures.as_completed(futures):
            all_data.extend(f.result())

    if not all_data or len(all_data) < 10:
        print("⚠️ Not enough data returned — using mock.")
        return _mock_aqi_data()

    # Normalize to DataFrame
    rows = []
    for row in all_data:
        try:
            rows.append({
                "latitude": row.get("Latitude"),
                "longitude": row.get("Longitude"),
                "parameter": row.get("ParameterName") or row.get("Parameter"),
                "aqi": row.get("AQI"),
                "category": (
                    row.get("Category", {}).get("Name")
                    if isinstance(row.get("Category"), dict)
                    else row.get("Category")
                ),
                "unit": row.get("Unit"),
                "reportingArea": row.get("ReportingArea"),
                "stateCode": row.get("StateCode"),
                "utc": row.get("DateObserved"),
            })
        except Exception:
            continue

    df = pd.DataFrame(rows).dropna(subset=["latitude", "longitude", "aqi"])
    df = df.drop_duplicates(subset=["latitude", "longitude", "parameter"])
    color_map = {
        "Good": "green",
        "Moderate": "yellow",
        "Unhealthy for Sensitive Groups": "orange",
        "Unhealthy": "red",
        "Very Unhealthy": "purple",
        "Hazardous": "maroon",
    }
    df["color"] = df["category"].map(color_map).fillna("gray")
    df["region"] = "USA"

    print(f"✅ Retrieved {len(df)} clean AQI points in total.")
    return df


def _mock_aqi_data(n: int = 1000):
    """Fallback: generate mock AQI points when API unavailable."""
    random.seed(42)
    rows = []
    for _ in range(n):
        category = random.choice(["Good", "Moderate", "Unhealthy"])
        rows.append({
            "latitude": random.uniform(24, 49),
            "longitude": random.uniform(-125, -67),
            "parameter": random.choice(["PM2.5", "NO2"]),
            "unit": "UG/M3",
            "aqi": random.randint(5, 150),
            "category": category,
            "color": {"Good": "green", "Moderate": "yellow", "Unhealthy": "red"}[category],
            "region": "USA",
            "utc": "2025-10-04T12:00",
        })
    print("🌍 Using mock AQI data.")
    return pd.DataFrame(rows)
