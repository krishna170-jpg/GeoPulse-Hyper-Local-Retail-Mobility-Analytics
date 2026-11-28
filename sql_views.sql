-- GeoPulse PostgreSQL reporting views
-- The application creates these tables and views during the Sync action.
CREATE OR REPLACE VIEW vw_area_performance AS
SELECT area, SUM(visits) AS visits, SUM(retail_stores) AS retail_stores,
       AVG(opportunity_score) AS avg_opportunity, AVG(rent_index) AS avg_rent,
       SUM(visits) / GREATEST(SUM(retail_stores), 1) AS visits_per_store
FROM area_data GROUP BY area;

CREATE OR REPLACE VIEW vw_category_competition AS
SELECT area, category, COUNT(*) AS store_count
FROM store_data GROUP BY area, category;

CREATE OR REPLACE VIEW vw_weekly_trend AS
SELECT area, week, SUM(visits) AS total_visits
FROM weekly_data GROUP BY area, week;

CREATE OR REPLACE VIEW vw_hourly_demand AS
SELECT area, day, hour, SUM(visits) AS total_visits
FROM hourly_data GROUP BY area, day, hour;

CREATE OR REPLACE VIEW vw_product_performance AS
SELECT product, category, SUM(units) AS units_sold, SUM(revenue) AS revenue,
       COUNT(*) AS transaction_rows
FROM transaction_data GROUP BY product, category;
