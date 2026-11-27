# GeoPulse: Hyper-Local Retail Mobility Analytics

GeoPulse is a Streamlit dashboard that shows where visitors go, what competition looks like and where a new store could do well. It is built for Guwahati, Assam, and works with built-in demo data or your own CSV files.

## Pages

| Page | What it does |
|---|---|
| **Overview** | Key numbers, a visit heat map, top areas, store categories and the weekly trend |
| **Explore** | Heat map, peak hours (weekday vs weekend) and competitor map |
| **Where to open** | Ranks areas for a business type and rent budget, plus a profit check |
| **Compare & forecast** | Side-by-side areas, and a weekly visit forecast with its error |
| **Data** | Upload CSVs, download templates, read how the numbers are made |
| **Project plan** | The Week 3 plan: team, schedule, folders, files and rules |
| **Help** | Quick start, FAQ and contact |

Every map has a **Map / Satellite** switch (top right).

## Run it locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Push this folder to a GitHub repository.
2. On [share.streamlit.io](https://share.streamlit.io) choose **New app**, pick the repository and set the main file to `app.py`.
3. Optional: open **App settings > Secrets** and add the keys from `.streamlit/secrets.toml.example`.

## Data

The demo data is simulated (visits, rent, weekly and hourly patterns), so numbers are illustrative until you upload real files on the **Data** page. Only the areas file is required.

| File | Required columns | Optional columns |
|---|---|---|
| Areas | Area, Latitude, Longitude, Visits | Retail Stores, Opportunity Score, Rent Index |
| Stores | Store, Category, Latitude, Longitude | Area |
| Weekly visits | Area, Week, Visits | |
| Hourly visits | Area, Day (Mon to Sun), Hour, Visits | |

Store locations can come from three sources, chosen under **Data source** in the sidebar:
- Simulated (instant)
- OpenStreetMap (free, no foot traffic)
- Google Places (needs your own API key; results are cached for 24 hours)

## Secrets (optional)

| Key | Purpose |
|---|---|
| `APP_PASSWORD` | Turns on a password screen |
| `GOOGLE_PLACES_API_KEY` | Loads shops from Google Places |

## Project structure

```
geopulse/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
└── .streamlit/
    ├── config.toml              # blue theme
    └── secrets.toml.example     # copy to secrets.toml; never commit it
```

## Credits

- Street map data © OpenStreetMap contributors (ODbL)
- Satellite imagery © Esri, Maxar, Earthstar Geographics
- Built with Streamlit, Plotly, pandas and scikit-learn

## Contact

doleykrishna170@gmail.com
