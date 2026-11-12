#!/usr/bin/env python3
"""GeoPulse - Member 1: generate anonymized, simulated mobile GPS pings for Guwahati.
Usage: python generate_gps_data.py [--devices 5000] [--pings 210] [--date 2026-11-02] [--seed 42]
Output: gps_pings.csv (DeviceID, Latitude, Longitude, Timestamp) and generation_summary.txt
"""
import argparse
import time
import numpy as np
import pandas as pd

HOODS = {  # approximate neighbourhood centres (lat, lon)
    "Paltan Bazaar": (26.1823, 91.7506), "Dispur": (26.1433, 91.7898), "Ganeshguri": (26.1527, 91.7850),
    "Beltola": (26.1196, 91.7971), "Maligaon": (26.1590, 91.6980), "Jalukbari": (26.1510, 91.6640),
    "Chandmari": (26.1739, 91.7642), "Six Mile": (26.1387, 91.8039)}
HUBS = ["Paltan Bazaar", "Ganeshguri", "Chandmari", "Dispur", "Maligaon"]  # workplaces / commercial hubs
BBOX = (26.05, 26.25, 91.55, 91.90)  # lat_min, lat_max, lon_min, lon_max (simulated city boundary)
# Relative chance that a ping is logged in each hour: peaks at morning commute, lunch and evening.
HOUR_W = np.array([1, 1, 1, 1, 1, 2, 4, 8, 9, 6, 4, 4, 6, 7, 5, 4, 5, 8, 9, 8, 6, 4, 2, 1], float)


def place(rng, names, n, spread):
    centres = np.array([HOODS[k] for k in rng.choice(names, n)])
    return centres + rng.normal(0, spread, (n, 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--devices", type=int, default=5000)
    ap.add_argument("--pings", type=int, default=220, help="pings per device (before removing slot collisions)")
    ap.add_argument("--date", default="2026-11-02")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="gps_pings.csv")
    a = ap.parse_args()
    t0, rng, D = time.time(), np.random.default_rng(a.seed), a.devices

    home = place(rng, list(HOODS), D, 0.006)
    work = place(rng, HUBS, D, 0.004)
    stores = place(rng, list(HOODS), 40, 0.004)          # 40 simulated stores
    lunch = np.where(rng.random((D, 1)) < 0.6, stores[rng.integers(0, 40, D)], work)   # 60% visit a store at lunch
    evening = np.where(rng.random((D, 1)) < 0.5, stores[rng.integers(0, 40, D)], (work + home) / 2)
    leave = np.clip(rng.normal(8, 0.6, D), 6.5, 9.5)
    commute = rng.uniform(0.4, 1.0, D)
    back = np.clip(rng.normal(17.5, 0.7, D), 15.5, 19.5)
    prob = HOUR_W / HOUR_W.sum()

    ids, lats, lons, secs = [], [], [], []
    for i in range(D):
        # Pings fall on a 10-second grid (unique slots), so two pings are never closer than 10 s.
        slots = np.unique(((rng.choice(24, a.pings, p=prob) + rng.random(a.pings)) * 360).astype(int))
        sec = slots * 10 + rng.integers(0, 10)
        h, n = sec / 3600, len(sec)
        t = [0, leave[i], leave[i] + commute[i], 12.5, 12.9, 13.4, 13.8, back[i], back[i] + .4, back[i] + 1, back[i] + 1.6, 24]
        pts = np.array([home[i], home[i], work[i], work[i], lunch[i], lunch[i], work[i], work[i],
                        evening[i], evening[i], home[i], home[i]])
        lats.append(np.interp(h, t, pts[:, 0]) + rng.normal(0, 0.00015, n))  # about 17 m GPS noise
        lons.append(np.interp(h, t, pts[:, 1]) + rng.normal(0, 0.00015, n))
        secs.append(sec)
        ids.append(np.full(n, f"DEV{i + 1:05d}"))

    df = pd.DataFrame({"DeviceID": np.concatenate(ids), "Latitude": np.concatenate(lats).clip(BBOX[0], BBOX[1]),
                       "Longitude": np.concatenate(lons).clip(BBOX[2], BBOX[3]),
                       "Timestamp": pd.Timestamp(a.date) + pd.to_timedelta(np.concatenate(secs), unit="s")})
    before = len(df)
    df = df.drop_duplicates(["DeviceID", "Timestamp"]).sort_values(["DeviceID", "Timestamp"])
    df.to_csv(a.out, index=False, float_format="%.6f", date_format="%Y-%m-%d %H:%M:%S")

    with open("generation_summary.txt", "w") as f:
        f.write(f"""GeoPulse synthetic GPS generation summary
Generated at (UTC)   : {pd.Timestamp.now('UTC'):%Y-%m-%d %H:%M:%S}
City                 : Guwahati, Assam (simulated)
Seed                 : {a.seed}
Simulated date       : {a.date} (24 hours)
Devices              : {df.DeviceID.nunique():,}
Pings generated      : {before:,}
Duplicate pings removed (same device and second): {before - len(df):,}
Final records        : {len(df):,}
Missing values       : {int(df.isna().sum().sum())}
Latitude range       : {df.Latitude.min():.6f} to {df.Latitude.max():.6f}
Longitude range      : {df.Longitude.min():.6f} to {df.Longitude.max():.6f}
First / last ping    : {df.Timestamp.min()} / {df.Timestamp.max()}
Runtime (seconds)    : {time.time() - t0:.1f}
Output file          : {a.out}
Behaviour model      : home -> morning commute -> work -> lunch (60% visit a store) -> evening (50% visit a store) -> home
Privacy              : DeviceIDs are anonymous labels; all movement is simulated, no real people.
""")
    print(f"{len(df):,} records written to {a.out}")


if __name__ == "__main__":
    main()
