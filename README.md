# GeoPulse Week 3 — Member 1: GPS Movement Analysis and Data Quality

This folder implements the Member 1 tasks in the Week 3 plan:
- GPS movement-field validation
- Device- and session-level statistics
- Distance and speed analysis
- Walking / Driving / Cycling / Stationary classification
- GPS data-quality anomaly reporting
- CSV outputs for team integration

## 1. Expected project layout

Place this folder inside your existing `GeoPulse/` project. Keep Week 1 and Week 2 files unchanged.

```text
GeoPulse/
├── data/
│   ├── gps_pings.csv       # original 100,000-row source file
│   └── stores.csv          # used by Member 2; not modified by this package
├── member1_movement_analysis/
│   ├── common.py
│   ├── 01_movement_data_validation.py
│   ├── 02_device_movement_analysis.py
│   ├── 03_speed_distance_analysis.py
│   ├── 04_movement_mode_analysis.py
│   ├── 05_movement_quality_report.py
│   ├── requirements.txt
│   └── README.md
└── outputs/
    └── week3/
        └── member1_movement/
```

The GPS input must contain these fields (case-insensitive aliases are accepted):
`DeviceID`, `SessionID`, `Timestamp`, `Latitude`, `Longitude`.
An optional `Speed` column is retained, but movement speed is derived from projected consecutive-point distances and timestamp gaps.

## 2. Install dependencies

From the `GeoPulse/` project root:

```bash
python -m pip install -r member1_movement_analysis/requirements.txt
```

## 3. Run the scripts in order

```bash
python member1_movement_analysis/01_movement_data_validation.py
python member1_movement_analysis/02_device_movement_analysis.py
python member1_movement_analysis/03_speed_distance_analysis.py
python member1_movement_analysis/04_movement_mode_analysis.py
python member1_movement_analysis/05_movement_quality_report.py
```

Run from the project root. The original `data/gps_pings.csv` is read-only from the scripts' perspective. All generated files go into `outputs/week3/member1_movement/`.

## 4. Generated outputs

- `validated_gps.csv` — valid working rows with projected coordinates
- `gps_anomalies.csv` — rows with missing IDs/timestamps, invalid coordinates or duplicate pings
- `session_movement_summary.csv` — ping count, duration, distance, speed and ping-gap statistics per device/session
- `device_movement_summary.csv` — aggregated device-level metrics
- `movement_segments.csv` — consecutive-point distance, time gap and derived speed
- `speed_distance_summary.csv` — distance/speed summary per device/session
- `movement_segments_with_modes.csv` — segments with movement-mode labels
- `movement_mode_summary.csv` — movement-mode counts per device/session
- `overall_movement_mode_summary.csv` — overall mode totals
- `movement_analysis_report.csv` — device-level report with anomaly counts
- `session_analysis_report.csv` — session-level report with mode counts
- `movement_quality_kpis.csv` — headline validation and movement KPIs

## 5. Calculation rules

1. Points are sorted by `DeviceID`, `SessionID`, and `Timestamp`.
2. Distances are calculated only between adjacent points belonging to the same device and session.
3. Coordinates are projected from EPSG:4326 into the configured projected CRS before calculating metres.
4. Segments separated by more than 30 minutes are excluded from travelled-distance and derived-speed totals, but the gap remains available for quality review.
5. Derived speed = segment distance / elapsed seconds × 3.6.
6. Mode thresholds are simple analytical heuristics, not ground-truth transport labels:
   - Stationary: below 1 km/h
   - Walking: 1–7 km/h
   - Cycling: above 7–25 km/h
   - Driving: above 25 km/h
7. Speeds above 160 km/h are flagged for review, not automatically removed.
8. A GPS ping inside a store catchment is not proof of a physical store visit. This Member 1 package does not infer store visits.

## 6. Coordinate reference system check — important

The Week 3 brief specifies **EPSG:32644**, so that is the default used by the scripts. However, EPSG:32644 is UTM zone 44N, while Guwahati is around 91–92°E and is normally within UTM zone 46N. Before using the distance outputs in final results, confirm the CRS with your project lead/data owner. If the team confirms UTM zone 46N is appropriate, run:

**macOS / Linux**
```bash
export GEOPULSE_CRS=EPSG:32646
python member1_movement_analysis/01_movement_data_validation.py
python member1_movement_analysis/02_device_movement_analysis.py
python member1_movement_analysis/03_speed_distance_analysis.py
python member1_movement_analysis/04_movement_mode_analysis.py
python member1_movement_analysis/05_movement_quality_report.py
```

On Windows PowerShell:
```powershell
$env:GEOPULSE_CRS="EPSG:32646"
python member1_movement_analysis/01_movement_data_validation.py
```

Do not silently change the CRS in the submitted project; document the team's confirmed choice.

## 7. Notes and limitations

- Missing required columns cause a clear error; the scripts do not invent DeviceID or SessionID values.
- Invalid rows are written to the anomaly file and excluded from movement calculations.
- The 30-minute gap and 160 km/h anomaly thresholds are review rules and can be adjusted with the team.
- Device identifiers are treated as strings to preserve IDs such as leading-zero values.
- Results are descriptive estimates based on simulated GPS pings, not verified customer journeys or actual store transactions.
