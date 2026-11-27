"""Step 2: calculate device- and session-level movement statistics."""
import pandas as pd
from common import read_output, build_segments, write_csv

def main():
    gps = read_output("validated_gps.csv")
    gps["Timestamp"] = pd.to_datetime(gps["Timestamp"], utc=True, errors="coerce")
    seg = build_segments(gps)
    keys = ["DeviceID", "SessionID"]

    ping_stats = gps.groupby(keys).agg(
        total_gps_pings=("Timestamp", "size"),
        first_ping=("Timestamp", "min"),
        last_ping=("Timestamp", "max"),
    ).reset_index()
    ping_stats["active_duration_minutes"] = (
        ping_stats["last_ping"] - ping_stats["first_ping"]
    ).dt.total_seconds() / 60

    if not seg.empty:
        segment_stats = seg.groupby(keys).agg(
            total_distance_m=("distance_m", "sum"),
            average_derived_speed_kmh=("derived_speed_kmh", "mean"),
            maximum_derived_speed_kmh=("derived_speed_kmh", "max"),
            average_ping_gap_seconds=("time_gap_seconds", "mean"),
            maximum_ping_gap_seconds=("time_gap_seconds", "max"),
        ).reset_index()
    else:
        segment_stats = pd.DataFrame(columns=keys + [
            "total_distance_m", "average_derived_speed_kmh",
            "maximum_derived_speed_kmh", "average_ping_gap_seconds",
            "maximum_ping_gap_seconds"
        ])

    summary = ping_stats.merge(segment_stats, on=keys, how="left")
    summary["total_distance_km"] = summary["total_distance_m"] / 1000
    write_csv(summary, "session_movement_summary.csv")

    device = summary.groupby("DeviceID").agg(
        sessions=("SessionID", "nunique"),
        total_gps_pings=("total_gps_pings", "sum"),
        total_distance_km=("total_distance_km", "sum"),
        average_session_duration_minutes=("active_duration_minutes", "mean"),
        average_speed_kmh=("average_derived_speed_kmh", "mean"),
        maximum_speed_kmh=("maximum_derived_speed_kmh", "max"),
    ).reset_index()
    write_csv(device, "device_movement_summary.csv")

    print(f"Devices: {len(device):,}; sessions: {len(summary):,}")

if __name__ == "__main__":
    main()
