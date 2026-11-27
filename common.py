"""Shared helpers for GeoPulse Week 3 — Member 1."""
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
from pyproj import Transformer

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "outputs" / "week3" / "member1_movement"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# The Week 3 brief explicitly requests EPSG:32644. Override with
# GEOPULSE_CRS=EPSG:32646 if the team confirms the GPS points are in Guwahati.
import os
TARGET_CRS = os.getenv("GEOPULSE_CRS", "EPSG:32644")
TRANSFORMER = Transformer.from_crs("EPSG:4326", TARGET_CRS, always_xy=True)

ALIASES = {
    "DeviceID": ["deviceid", "device_id", "device", "device id"],
    "SessionID": ["sessionid", "session_id", "session", "session id"],
    "Timestamp": ["timestamp", "datetime", "date_time", "ping_time", "event_time"],
    "Latitude": ["latitude", "lat", "gps_latitude"],
    "Longitude": ["longitude", "lon", "lng", "gps_longitude"],
    "Speed": ["speed", "speed_kmh", "speed_kph", "velocity"],
}

def find_input(name="gps_pings.csv"):
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Put the original {name} in the project's data/ folder. "
            "The scripts never overwrite source files."
        )
    return path

def load_gps(path=None):
    path = Path(path) if path else find_input()
    df = pd.read_csv(path)
    # Match common column spelling/case variants without changing source file.
    lookup = {str(c).strip().lower(): c for c in df.columns}
    rename = {}
    for standard, candidates in ALIASES.items():
        for candidate in candidates:
            if candidate in lookup:
                rename[lookup[candidate]] = standard
                break
    df = df.rename(columns=rename)
    required = ["DeviceID", "SessionID", "Timestamp", "Latitude", "Longitude"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            "GPS file is missing required columns: " + ", ".join(missing) +
            ". Required fields: DeviceID, SessionID, Timestamp, Latitude, Longitude."
        )
    df["DeviceID"] = df["DeviceID"].astype("string").str.strip()
    df["SessionID"] = df["SessionID"].astype("string").str.strip()
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce", utc=True)
    for c in ["Latitude", "Longitude", "Speed"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def add_quality_flags(df):
    d = df.copy()
    d["missing_device_id"] = d["DeviceID"].isna() | d["DeviceID"].eq("")
    d["missing_session_id"] = d["SessionID"].isna() | d["SessionID"].eq("")
    d["missing_timestamp"] = d["Timestamp"].isna()
    d["invalid_coordinates"] = (
        d["Latitude"].isna() | d["Longitude"].isna() |
        ~d["Latitude"].between(-90, 90) | ~d["Longitude"].between(-180, 180)
    )
    d["duplicate_ping"] = d.duplicated(
        ["DeviceID", "SessionID", "Timestamp", "Latitude", "Longitude"], keep="first"
    )
    return d

def add_projected_coordinates(df):
    d = df.copy()
    valid = (
        d["Latitude"].notna() & d["Longitude"].notna() &
        d["Latitude"].between(-90, 90) & d["Longitude"].between(-180, 180)
    )
    d["x_m"] = np.nan
    d["y_m"] = np.nan
    if valid.any():
        x, y = TRANSFORMER.transform(
            d.loc[valid, "Longitude"].to_numpy(),
            d.loc[valid, "Latitude"].to_numpy()
        )
        d.loc[valid, "x_m"] = x
        d.loc[valid, "y_m"] = y
    return d

def ordered_valid(df):
    d = df.copy()
    d = d[
        d["DeviceID"].notna() & d["SessionID"].notna() &
        d["Timestamp"].notna() & d["x_m"].notna() & d["y_m"].notna()
    ].copy()
    return d.sort_values(
        ["DeviceID", "SessionID", "Timestamp"], kind="mergesort"
    ).reset_index(drop=True)

def build_segments(df, max_gap_minutes=30):
    """Distance only between adjacent points within the same device + session."""
    d = ordered_valid(add_projected_coordinates(df))
    if d.empty:
        return pd.DataFrame(columns=[
            "DeviceID", "SessionID", "Timestamp", "next_Timestamp",
            "distance_m", "time_gap_seconds", "derived_speed_kmh"
        ])
    keys = ["DeviceID", "SessionID"]
    d["next_x_m"] = d.groupby(keys)["x_m"].shift(-1)
    d["next_y_m"] = d.groupby(keys)["y_m"].shift(-1)
    d["next_Timestamp"] = d.groupby(keys)["Timestamp"].shift(-1)
    d["time_gap_seconds"] = (d["next_Timestamp"] - d["Timestamp"]).dt.total_seconds()
    d["distance_m"] = np.hypot(d["next_x_m"] - d["x_m"], d["next_y_m"] - d["y_m"])
    d["derived_speed_kmh"] = np.where(
        d["time_gap_seconds"] > 0,
        d["distance_m"] / d["time_gap_seconds"] * 3.6,
        np.nan
    )
    # A long ping gap is not treated as a continuous travelled path.
    d.loc[d["time_gap_seconds"] > max_gap_minutes * 60, "distance_m"] = np.nan
    d.loc[d["time_gap_seconds"] > max_gap_minutes * 60, "derived_speed_kmh"] = np.nan
    return d

def classify_mode(speed):
    if pd.isna(speed):
        return "Unknown"
    if speed < 1:
        return "Stationary"
    if speed <= 7:
        return "Walking"
    if speed <= 25:
        return "Cycling"
    return "Driving"

def write_csv(df, filename):
    path = OUT_DIR / filename
    df.to_csv(path, index=False)
    print(f"Saved {path} ({len(df):,} rows)")
    return path

def read_output(filename):
    path = OUT_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run the earlier numbered script first.")
    return pd.read_csv(path)
