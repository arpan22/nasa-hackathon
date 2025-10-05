"""
fetch_aod.py — Retrieves NASA MERRA-2 AOD data via earthaccess or generates mock.
"""

import numpy as np
import pandas as pd

def load_aod_data():
    """Return a cropped NASA AOD dataset (mocked if earthaccess not available)."""
    try:
        import earthaccess, xarray as xr
        sess = earthaccess.login(strategy="netrc")
        results = earthaccess.search_data(short_name="M2T1NXAER", temporal=("2024-09-01", "2024-09-03"), count=1)
        files = earthaccess.download(results)
        ds = xr.open_dataset(files[0])
        aod = ds["TOTEXTTAU"].isel(time=0)
        lat, lon = ds["lat"].values, ds["lon"].values
        df = pd.DataFrame({
            "latitude": np.repeat(lat, len(lon)),
            "longitude": np.tile(lon, len(lat)),
            "aod": aod.values.flatten()
        })
    except Exception:
        df = _mock_aod_data()
    # Crop to continental US
    df = df[(df.latitude >= 24) & (df.latitude <= 49.5) & (df.longitude >= -125) & (df.longitude <= -66.5)]
    return df

def _mock_aod_data(n=3000):
    np.random.seed(1)
    return pd.DataFrame({
        "latitude": np.random.uniform(24, 49.5, n),
        "longitude": np.random.uniform(-125, -66.5, n),
        "aod": np.random.uniform(0, 1, n),
    })
