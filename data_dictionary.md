# GPS pings data dictionary

File: `gps_pings.csv` | Records: 1,081,302 | Header row: yes | Delimiter: comma | Encoding: UTF-8

| Column | Type (CSV) | Snowflake type | Unit / format | Description |
|---|---|---|---|---|
| DeviceID | text | VARCHAR(20) | `DEV00001` to `DEV05000` | Anonymous device label. Simulated, not linked to any real person. |
| Latitude | decimal | FLOAT | degrees, 6 decimals | North/south position. Simulated range about 26.10 to 26.20 (Guwahati). |
| Longitude | decimal | FLOAT | degrees, 6 decimals | East/west position. Simulated range about 91.64 to 91.82. |
| Timestamp | datetime | TIMESTAMP_NTZ | `YYYY-MM-DD HH:MM:SS` | Ping time on the simulated day, covering all 24 hours. |

Notes: pings are at least 10 seconds apart per device. GPS noise of about 17 m is added. Rows are sorted by DeviceID and Timestamp.
In Snowflake the `LOCATION` GEOGRAPHY column is added by `load_gps_data.sql` using `ST_MAKEPOINT(LONGITUDE, LATITUDE)`.
