-- GeoPulse - Member 3: Snowflake environment setup
-- Run as a role that may create databases and warehouses (SYSADMIN, or ACCOUNTADMIN if your account requires it).
USE ROLE SYSADMIN;

CREATE DATABASE IF NOT EXISTS GEOPULSE_DB;
CREATE SCHEMA   IF NOT EXISTS GEOPULSE_DB.RAW;

-- Warehouse creation depends on account permissions. If this fails, ask the account admin,
-- or use an existing warehouse and change the name in the other scripts.
CREATE WAREHOUSE IF NOT EXISTS GEOPULSE_WH
  WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE INITIALLY_SUSPENDED = TRUE;

USE WAREHOUSE GEOPULSE_WH;
USE DATABASE  GEOPULSE_DB;
USE SCHEMA    RAW;

-- Connectivity and SQL execution test
SELECT CURRENT_ACCOUNT() AS account, CURRENT_ROLE() AS role, CURRENT_WAREHOUSE() AS warehouse,
       CURRENT_DATABASE() AS db, CURRENT_SCHEMA() AS schema, CURRENT_TIMESTAMP() AS server_time;
SELECT ST_MAKEPOINT(91.7362, 26.1445) AS test_geography_point;   -- confirms GEOGRAPHY functions work
