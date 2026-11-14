# GeoPulse – Retail Location Intelligence

Streamlit dashboard for hyper-local retail and mobility analytics in Guwahati.

## Pages
- **Explore:** Overview, Mobility heatmap, Customer mobility, GPS movement, Peak hours, Competitors
- **Analyze:** Catchment, Retail intelligence, Area clusters, Whitespace finder, Forecast
- **Decide:** Where to open, Compare areas, What-if simulator
- **Share:** Key insights, Shortlist, Reports
- **Data:** Your data, Methodology, Data quality, Help & FAQ

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
Push to GitHub, then create the app at https://share.streamlit.io with `app.py` as the main file.
After a push the app redeploys by itself (use Manage app, then Reboot app, if the look does not change).

## GPS data pipeline (`gps_pipeline/`)
1. `python generate_gps_data.py` creates `gps_pings.csv` (about 1 million simulated pings) and `generation_summary.txt`.
2. `python validate_gps_data.py` checks it and writes the validation report, preview image and data quality report.
3. The `.sql` files set up Snowflake (`GEOPULSE_DB`) and load the data.

`gps_pings.csv` is about 55 MB and is not stored in Git. Regenerate it with step 1 (the seed is fixed).
`sample_gps_pings.csv` (200 devices) is in the repo root so the GPS movement page works online.

## Optional login
Set `APP_PASSWORD` in Streamlit secrets (see `.streamlit/secrets.toml.example`).

## Data
Visits, rent and trends are simulated for illustration. Upload your own CSV files on the **Your data** page.
Store locations can be loaded from OpenStreetMap.
