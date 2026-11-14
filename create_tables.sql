-- GeoPulse - Member 3: raw GPS tables
USE WAREHOUSE GEOPULSE_WH;
USE SCHEMA GEOPULSE_DB.RAW;

-- 1) Landing table: mirrors gps_pings.csv exactly.
CREATE OR REPLACE TABLE GPS_PINGS_RAW (
  DEVICE_ID VARCHAR(20)   NOT NULL,
  LATITUDE  FLOAT         NOT NULL,
  LONGITUDE FLOAT         NOT NULL,
  PING_TS   TIMESTAMP_NTZ NOT NULL
);

-- 2) Analysis table: same columns plus a GEOGRAPHY point, filled in by load_gps_data.sql.
CREATE OR REPLACE TABLE GPS_PINGS (
  DEVICE_ID VARCHAR(20)   NOT NULL,
  LATITUDE  FLOAT         NOT NULL,
  LONGITUDE FLOAT         NOT NULL,
  PING_TS   TIMESTAMP_NTZ NOT NULL,
  LOCATION  GEOGRAPHY                -- built with ST_MAKEPOINT(LONGITUDE, LATITUDE): longitude comes first
);

DESCRIBE TABLE GPS_PINGS;
