# GPS data quality report

File: `gps_pings.csv`  |  Records: 1,048,290  |  Devices: 5,000  |  Result: **1 check(s) need attention**

| Check | Status | Issues | Detail |
|---|---|---|---|
| Columns match schema | PASS | 0 | found ['DeviceID', 'Latitude', 'Longitude', 'Timestamp'] |
| Missing values | PASS | 0 | any column |
| Latitude within -90..90 | PASS | 0 |  |
| Longitude within -180..180 | PASS | 0 |  |
| Inside simulated city boundary | PASS | 0 | box (26.05, 26.25, 91.55, 91.9) |
| Timestamps parse correctly | PASS | 0 |  |
| Covers all 24 hours | PASS | 0 | hours with no pings |
| Timestamps in chronological order per device | PASS | 0 |  |
| Duplicate rows | PASS | 0 |  |
| Duplicate device + timestamp | PASS | 0 |  |
| Impossible speed between pings | FAIL | 1167 | over 120 km/h |
| Devices with fewer than 10 pings | PASS | 0 | pings per device min 206, median 210, max 210 |

Time range: 2026-11-02 00:00:00 to 2026-11-02 23:59:59.
Movement preview: `gps_movement_preview.png`. Full results: `gps_validation_report.csv`.
