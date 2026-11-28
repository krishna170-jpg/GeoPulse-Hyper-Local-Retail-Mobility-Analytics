# GeoPulse — Guwahati Retail Analytics

A Streamlit retail-location intelligence application upgraded with data quality checks, PostgreSQL persistence, SQL analytical views, and PDF/CSV/Excel management reporting.

## Features
- Existing GeoPulse overview, maps, zone comparison, location recommendations and weekly forecasting.
- Multiple source support: demo data, CSV uploads, OpenStreetMap, and optional Google Places API.
- Standardization and validation of area, store, weekly and hourly datasets.
- Data quality issue table (duplicates, invalid coordinates, negative measures, malformed dates and invalid references).
- Reports & Insights page with executive findings, zone ranking, category mix and report dataset previews.
- Exportable PDF management report, Excel workbook and ZIP of CSV reporting datasets.
- PostgreSQL warehouse sync and four SQL views:
  - `vw_area_performance`
  - `vw_category_competition`
  - `vw_weekly_trend`
  - `vw_hourly_demand`\n  - `vw_product_performance`

## Run locally

Python 3.10–3.12 recommended.

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1

pip install -r requirements.txt
streamlit run app.py
```

The app works in demo mode without PostgreSQL. Demo visits, rent and time-series values are simulated and are clearly identified in the reporting page.

## Configure PostgreSQL

Create a PostgreSQL database, then set `DATABASE_URL`.

macOS/Linux:
```bash
export DATABASE_URL="postgresql+psycopg2://USERNAME:PASSWORD@HOST:5432/DATABASE"
```

Windows PowerShell:
```powershell
$env:DATABASE_URL="postgresql+psycopg2://USERNAME:PASSWORD@HOST:5432/DATABASE"
```

Or create `.streamlit/secrets.toml`:
```toml
DATABASE_URL = "postgresql+psycopg2://USERNAME:PASSWORD@HOST:5432/DATABASE"
```

Never commit a real password or API key. Add `.streamlit/secrets.toml` to `.gitignore`.

Open **Reports & Insights → PostgreSQL data warehouse → Sync current filtered data and refresh SQL views**. The app creates the four source tables and SQL views automatically. Sync replaces the current contents of those tables with the selected/filtered dataset, so use a dedicated GeoPulse database/schema.

## Optional Google Places
Set `GOOGLE_PLACES_API_KEY` in Streamlit secrets. Google Places requires an eligible API key and billing; requests may incur charges. OpenStreetMap remains the free real-store source.

## Input CSV templates
Use **Data → Templates** in the app. Existing supported files:
- Areas: `Area, Latitude, Longitude, Visits` (optional `Retail Stores, Opportunity Score, Rent Index`)
- Stores: `Store, Category, Latitude, Longitude` (optional `Area`)
- Weekly: `Area, Week, Visits`
- Hourly: `Area, Day, Hour, Visits`\n- Transactions: `Date, Area, Product, Category, Units, Revenue` (optional `Gender`)

## Important analytical limitations
- OpenStreetMap and Google Places supply mapped place listings, not verified footfall, revenue or customer purchases.
- Demo visit, rent and time-series fields are simulated.
- Product analytics uses transaction rows when uploaded. Without client transactions, the built-in product transactions are simulated examples. Profit margin and basket size require additional cost and transaction/customer identifiers.
- Gender normalization helper is included for future optional demographic datasets, but no gender dataset is currently ingested or displayed.
- Site scores are screening indicators, not guarantees. Validate with field visits and verified commercial data.

## GitHub
Upload the project folder contents, including `app.py`, `requirements.txt`, `README.md`, and `.gitignore`. Do not upload secrets.
