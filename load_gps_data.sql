-- GeoPulse - Member 4: load gps_pings.csv into Snowflake and verify
USE WAREHOUSE GEOPULSE_WH;
USE SCHEMA GEOPULSE_DB.RAW;

-- Step 1 (run in SnowSQL or the Snowflake CLI, NOT in a web worksheet: PUT needs a local client)
--   snowsql -a <account> -u <user> -f load_gps_data.sql   (or run the PUT line by hand)
PUT file://./gps_pings.csv @GPS_STAGE AUTO_COMPRESS = TRUE OVERWRITE = TRUE;
LIST @GPS_STAGE;

-- Step 2: load the raw table (stops on the first bad row)
TRUNCATE TABLE GPS_PINGS_RAW;
COPY INTO GPS_PINGS_RAW (DEVICE_ID, LATITUDE, LONGITUDE, PING_TS)
FROM @GPS_STAGE/gps_pings.csv.gz
ON_ERROR = 'ABORT_STATEMENT';

-- Step 3: convert latitude/longitude to GEOGRAPHY points (ST_MAKEPOINT takes longitude first)
TRUNCATE TABLE GPS_PINGS;
INSERT INTO GPS_PINGS
SELECT DEVICE_ID, LATITUDE, LONGITUDE, PING_TS, ST_MAKEPOINT(LONGITUDE, LATITUDE)
FROM GPS_PINGS_RAW;

-- Step 4: verification
SELECT COUNT(*) AS raw_rows FROM GPS_PINGS_RAW;                         -- must equal the CSV record count
SELECT COUNT(*) AS final_rows, COUNT(LOCATION) AS rows_with_geography FROM GPS_PINGS;
SELECT COUNT_IF(DEVICE_ID IS NULL OR LATITUDE IS NULL OR LONGITUDE IS NULL OR PING_TS IS NULL) AS null_rows FROM GPS_PINGS;
SELECT COUNT_IF(LATITUDE NOT BETWEEN -90 AND 90 OR LONGITUDE NOT BETWEEN -180 AND 180) AS invalid_coordinates FROM GPS_PINGS;
SELECT COUNT(DISTINCT DEVICE_ID) AS devices, MIN(PING_TS) AS first_ping, MAX(PING_TS) AS last_ping FROM GPS_PINGS;
SELECT DEVICE_ID, LATITUDE, LONGITUDE, PING_TS, ST_ASWKT(LOCATION) AS wkt FROM GPS_PINGS LIMIT 5;
