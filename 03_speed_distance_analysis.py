"""Step 3: create segment-level distance/speed data and summary metrics."""
import pandas as pd
from common import read_output, build_segments, write_csv

def main():
    gps = read_output("validated_gps.csv")
    gps["Timestamp"] = pd.to_datetime(gps["Timestamp"], utc=True, errors="coerce")
    segments = build_segments(gps)

    # Flag suspicious derived speeds for review; do not silently delete them.
    segments["abnormal_speed"] = segments["derived_speed_kmh"] > 160
    segments["long_ping_gap"] = segments["time_gap_seconds"] > 30 * 60
    write_csv(segments, "movement_segments.csv")

    grouped = segments.groupby(["DeviceID", "SessionID"], dropna=False).agg(
        valid_segments=("distance_m", "count"),
        total_distance_m=("distance_m", "sum"),
        average_speed_kmh=("derived_speed_kmh", "mean"),
        maximum_speed_kmh=("derived_speed_kmh", "max"),
        maximum_ping_gap_seconds=("time_gap_seconds", "max"),
        abnormal_speed_segments=("abnormal_speed", "sum"),
        long_gap_segments=("long_ping_gap", "sum"),
    ).reset_index()
    grouped["total_distance_km"] = grouped["total_distance_m"] / 1000
    write_csv(grouped, "speed_distance_summary.csv")
    print(f"Movement segments: {len(segments):,}")
    print(f"Segments over 160 km/h: {int(segments['abnormal_speed'].sum()):,}")

if __name__ == "__main__":
    main()
