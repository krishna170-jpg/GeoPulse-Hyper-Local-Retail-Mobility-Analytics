"""Step 4: classify GPS movement segments into the four Week 3 modes."""
import pandas as pd
from common import read_output, classify_mode, write_csv

def main():
    seg = read_output("movement_segments.csv")
    if seg.empty:
        summary = pd.DataFrame(columns=["DeviceID", "SessionID", "MovementMode", "segment_count"])
    else:
        seg["MovementMode"] = seg["derived_speed_kmh"].apply(classify_mode)
        summary = seg.groupby(
            ["DeviceID", "SessionID", "MovementMode"], dropna=False
        ).size().reset_index(name="segment_count")
        totals = summary.groupby(["DeviceID", "SessionID"])["segment_count"].transform("sum")
        summary["segment_share"] = summary["segment_count"] / totals
        write_csv(seg, "movement_segments_with_modes.csv")

    write_csv(summary, "movement_mode_summary.csv")
    overall = summary.groupby("MovementMode", as_index=False)["segment_count"].sum()
    write_csv(overall, "overall_movement_mode_summary.csv")
    print("Mode thresholds (derived speed): <1 stationary; 1–7 walking; >7–25 cycling; >25 driving km/h.")

if __name__ == "__main__":
    main()
