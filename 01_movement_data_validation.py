"""Step 1: validate source GPS fields and create a clean working copy + anomaly list."""
from common import load_gps, add_quality_flags, add_projected_coordinates, write_csv, find_input

def main():
    source = find_input("gps_pings.csv")
    df = load_gps(source)
    flagged = add_projected_coordinates(add_quality_flags(df))

    flag_cols = [
        "missing_device_id", "missing_session_id", "missing_timestamp",
        "invalid_coordinates", "duplicate_ping"
    ]
    flagged["quality_issue_count"] = flagged[flag_cols].sum(axis=1)
    anomalies = flagged[flagged["quality_issue_count"] > 0].copy()

    # Keep valid rows for subsequent movement calculations; do not modify original input.
    valid = flagged[
        (flagged["quality_issue_count"] == 0) &
        flagged["x_m"].notna() & flagged["y_m"].notna()
    ].copy()

    write_csv(valid, "validated_gps.csv")
    write_csv(anomalies, "gps_anomalies.csv")

    print("\nValidation summary")
    print(f"Source rows: {len(df):,}")
    print(f"Valid rows: {len(valid):,}")
    print(f"Rows with one or more quality issues: {len(anomalies):,}")
    print(f"Coordinate CRS used: {__import__('common').TARGET_CRS}")
    print("Original gps_pings.csv was not changed.")

if __name__ == "__main__":
    main()
