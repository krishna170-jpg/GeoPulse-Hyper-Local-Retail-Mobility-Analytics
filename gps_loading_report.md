# Snowflake GPS loading report (to complete after you run the load)

Status: **NOT YET RUN.** This file was prepared without access to a Snowflake account, so no results below are real until you fill them in.

## Inputs
- File: `gps_pings.csv` (1,081,302 records expected, from `generation_summary.txt`)
- Target: `GEOPULSE_DB.RAW.GPS_PINGS_RAW`, then `GPS_PINGS` with a GEOGRAPHY column

## Steps
1. Member 3 has run `snowflake_setup.sql`, `create_tables.sql`, `create_stage.sql`.
2. Run `PUT` and `LIST @GPS_STAGE` (SnowSQL or CLI).
3. Run `COPY INTO`, then the `INSERT` that builds GEOGRAPHY points.
4. Run the verification queries in `load_gps_data.sql` and fill in the table.

## Results (fill in)
| Check | Expected | Actual |
|---|---|---|
| Rows in GPS_PINGS_RAW | 1,081,302 | |
| Rows in GPS_PINGS | 1,081,302 | |
| Rows with GEOGRAPHY | 1,081,302 | |
| Rows with nulls | 0 | |
| Invalid coordinates | 0 | |
| Distinct devices | 5,000 | |
| First / last ping | 2026-11-02 00:00:00 / 23:59:59 | |

## Screenshots to capture
- `snowflake_load_screenshot.png`: the COPY INTO result and the verification queries
- Query results for the table above

## Issues and notes
(write any errors, permission problems or row rejections here)
