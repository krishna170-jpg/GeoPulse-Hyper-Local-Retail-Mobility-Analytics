#!/usr/bin/env python3
"""GeoPulse - Member 2: validate gps_pings.csv.
Writes gps_validation_report.csv, gps_movement_preview.png and data_quality_report.md
Usage: python validate_gps_data.py [gps_pings.csv]
"""
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PATH = sys.argv[1] if len(sys.argv) > 1 else "gps_pings.csv"
BBOX = (26.05, 26.25, 91.55, 91.90)
MAX_KMH = 120
EXPECTED = ["DeviceID", "Latitude", "Longitude", "Timestamp"]

raw = pd.read_csv(PATH, dtype={"DeviceID": "string"})
df = raw.copy()
df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
res = []


def check(name, bad, detail="", warn=False):
    res.append({"check": name, "status": "PASS" if bad == 0 else ("WARN" if warn else "FAIL"), "issues_found": int(bad), "detail": detail})


check("Columns match schema", 0 if list(raw.columns) == EXPECTED else 1, f"found {list(raw.columns)}")
check("Missing values", int(raw.isna().sum().sum()), "any column")
check("Latitude within -90..90", int((~df.Latitude.between(-90, 90)).sum()))
check("Longitude within -180..180", int((~df.Longitude.between(-180, 180)).sum()))
check("Inside simulated city boundary", int((~(df.Latitude.between(*BBOX[:2]) & df.Longitude.between(*BBOX[2:]))).sum()), f"box {BBOX}")
check("Timestamps parse correctly", int(df.Timestamp.isna().sum()))
check("Covers all 24 hours", 24 - df.Timestamp.dt.hour.nunique(), "hours with no pings")
check("Timestamps in chronological order per device", int((df.groupby("DeviceID")["Timestamp"].diff().dt.total_seconds() < 0).sum()))
check("Duplicate rows", int(df.duplicated().sum()))
check("Duplicate device + timestamp", int(df.duplicated(["DeviceID", "Timestamp"]).sum()))

d = df.sort_values(["DeviceID", "Timestamp"])
la, lo = np.radians(d.Latitude.values), np.radians(d.Longitude.values)
dist = 6371 * 2 * np.arcsin(np.sqrt(np.sin(np.diff(la) / 2) ** 2 + np.cos(la[:-1]) * np.cos(la[1:]) * np.sin(np.diff(lo) / 2) ** 2))
dt = np.diff(d.Timestamp.values).astype("timedelta64[s]").astype(float) / 3600
same = (d.DeviceID.values[1:] == d.DeviceID.values[:-1]) & (dt > 0)
speed = np.where(same, dist / np.where(dt > 0, dt, 1), 0)
check("Impossible speed between pings", int((speed > MAX_KMH).sum()), f"over {MAX_KMH} km/h")
per = df.groupby("DeviceID").size()
check("Devices with fewer than 10 pings", int((per < 10).sum()), f"pings per device min {per.min()}, median {int(per.median())}, max {per.max()}", warn=True)
pd.DataFrame(res).to_csv("gps_validation_report.csv", index=False)

# Preview image
fig, ax = plt.subplots(1, 3, figsize=(17, 5))
hb = ax[0].hexbin(df.Longitude, df.Latitude, gridsize=60, cmap="Blues", mincnt=1, bins="log")
ax[0].set_title("Ping density (log scale)"); fig.colorbar(hb, ax=ax[0], label="pings")
for dev in df.DeviceID.drop_duplicates().iloc[:6]:
    s = d[d.DeviceID == dev]; ax[1].plot(s.Longitude, s.Latitude, lw=.8, marker=".", ms=2, label=dev)
ax[1].set_title("Sample device trajectories"); ax[1].legend(fontsize=7)
ax[2].bar(range(24), df.groupby(df.Timestamp.dt.hour).size().reindex(range(24), fill_value=0), color="#2563EB")
ax[2].set_title("Pings by hour of day"); ax[2].set_xlabel("Hour")
for x in ax[:2]: x.set_xlabel("Longitude"); x.set_ylabel("Latitude")
plt.tight_layout(); plt.savefig("gps_movement_preview.png", dpi=130)

r = pd.DataFrame(res)
rows = "\n".join(f"| {x.check} | {x.status} | {x.issues_found} | {x.detail} |" for x in r.itertuples())
overall = "all checks passed" if (r.status == "PASS").all() else f"{(r.status != 'PASS').sum()} check(s) need attention"
open("data_quality_report.md", "w").write(f"""# GPS data quality report

File: `{PATH}`  |  Records: {len(df):,}  |  Devices: {df.DeviceID.nunique():,}  |  Result: **{overall}**

| Check | Status | Issues | Detail |
|---|---|---|---|
{rows}

Time range: {df.Timestamp.min()} to {df.Timestamp.max()}.
Movement preview: `gps_movement_preview.png`. Full results: `gps_validation_report.csv`.
""")
print(r[["check", "status", "issues_found"]].to_string(index=False))
