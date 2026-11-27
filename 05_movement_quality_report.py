"""Step 5: combine movement and quality indicators into final CSV report."""
import pandas as pd
from common import read_output, load_gps, write_csv, find_input

def main():
    sessions = read_output("session_movement_summary.csv")
    devices = read_output("device_movement_summary.csv")
    anomalies = read_output("gps_anomalies.csv")
    modes = read_output("movement_mode_summary.csv")
    raw = load_gps(find_input("gps_pings.csv"))

    anomaly_counts = (
        anomalies.groupby("DeviceID").size().rename("anomaly_count").reset_index()
        if not anomalies.empty and "DeviceID" in anomalies.columns
        else pd.DataFrame(columns=["DeviceID", "anomaly_count"])
    )
    device_report = devices.merge(anomaly_counts, on="DeviceID", how="left")
    device_report["anomaly_count"] = device_report["anomaly_count"].fillna(0).astype(int)

    mode_wide = (
        modes.pivot_table(
            index=["DeviceID", "SessionID"], columns="MovementMode",
            values="segment_count", aggfunc="sum", fill_value=0
        ).reset_index()
        if not modes.empty else pd.DataFrame(columns=["DeviceID", "SessionID"])
    )
    session_report = sessions.merge(mode_wide, on=["DeviceID", "SessionID"], how="left")
    write_csv(device_report, "movement_analysis_report.csv")
    write_csv(session_report, "session_analysis_report.csv")

    metrics = [
        ("source_gps_rows", len(raw)),
        ("unique_devices", raw["DeviceID"].nunique()),
        ("unique_sessions", raw[["DeviceID", "SessionID"]].drop_duplicates().shape[0]),
        ("rows_with_quality_anomalies", len(anomalies)),
        ("sessions_analysed", len(sessions)),
        ("devices_analysed", len(devices)),
        ("total_distance_km", round(pd.to_numeric(sessions.get("total_distance_km", 0), errors="coerce").sum(), 3)),
    ]
    write_csv(pd.DataFrame(metrics, columns=["metric", "value"]), "movement_quality_kpis.csv")
    print("\nWeek 3 Member 1 report complete.")
    print(f"Input rows: {len(raw):,}; anomaly rows: {len(anomalies):,}")

if __name__ == "__main__":
    main()
