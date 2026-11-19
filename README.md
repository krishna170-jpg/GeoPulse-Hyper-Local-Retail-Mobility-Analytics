# GeoPulse — Week 2 implementation (Guwahati)

This package continues the uploaded GeoPulse Streamlit application and updates its catchment calculations to use a projected metric coordinate system.

## Study-area spatial reference

- Study area: Guwahati, Assam, India
- Input coordinates: WGS 84 latitude/longitude (`EPSG:4326`)
- Projected calculations: WGS 84 / UTM zone 46N (`EPSG:32646`)
- Catchment options in the dashboard: 500 m, 1,000 m, 1,500 m and 2,000 m

**Important correction:** EPSG:32644 is not the appropriate UTM zone for Guwahati. Guwahati is around 91.7°E, which falls in UTM zone 46N. The app therefore uses EPSG:32646 for metric catchment distance calculations. Folium still receives latitude/longitude for map display.

## Four-member work split

The uploaded source did not include a named four-person role sheet. The following is a practical four-way division for this implementation; replace the labels with your actual team members' names.

1. **Member 1 — Data collection and cleaning:** area/store CSV inputs, OpenStreetMap/Google Places source handling, field validation, and data provenance. Main file areas: `app.py` data layer.
2. **Member 2 — Spatial analysis:** Guwahati coordinate reference system, point projection, distance calculations, and 500 m–2 km catchments. Main file: `geo_utils.py`; integrated into `app.py` Catchment page.
3. **Member 3 — Retail analytics:** site scoring, competitor/category mix, visit summaries, clustering, and forecasting. Main file areas: `app.py` analytics and Analyze pages.
4. **Member 4 — Dashboard integration and QA:** Streamlit navigation, visualizations, user workflow, test execution, and final report/demo. Main file: `app.py`; tests: `tests/`.

## Setup

Use Python 3.10 or newer.

### macOS / Linux

```bash
cd geopulse_week2
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

### Windows PowerShell

```powershell
cd geopulse_week2
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit (normally `http://localhost:8501`).

## Tests

```bash
pytest -q
```

The spatial tests verify the selected CRS, finite projected coordinates, zero distance for identical points, a 500 m inclusion check, and rejection of negative radii.

## Data and interpretation notes

- The built-in area, visit, rent, weekly and hourly demo data are simulated. Do not present them as observed customer counts.
- OpenStreetMap retailer records are real mapped features but may be incomplete, outdated, or misclassified. Attribute map data to OpenStreetMap contributors.
- Google Places requires a separately configured API key and may incur charges. The app sends the key in a request header; do not commit keys to source control.
- Uploaded GPS traces can be sensitive. Use only data you are authorized to analyze, remove direct identifiers where possible, and avoid publishing individual movement paths.
- A 500 m circle is a straight-line radius, not a true walk-time or road-network catchment. It also does not imply that all people within the circle visit the site.
- The current visit forecast is a lightweight Ridge baseline. Treat it as exploratory until evaluated on representative, real historical data.

## What changed from the uploaded app

1. Added `geo_utils.py` with reusable WGS84-to-UTM conversion and metric distance functions.
2. Updated the Catchment page's nearby-store rendering and inside-radius counts to use projected metre distances.
3. Added automated spatial tests and a reproducible dependency list.
4. Preserved the existing Streamlit dashboard pages and its Guwahati demo-data framing.
