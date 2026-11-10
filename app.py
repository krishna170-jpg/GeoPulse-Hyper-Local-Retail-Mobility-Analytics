import hmac
import html
import io

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
import requests
import streamlit as st
from folium.plugins import HeatMap
from sklearn.linear_model import Ridge
from streamlit_folium import st_folium

st.set_page_config(page_title="GeoPulse | Retail Location Intelligence", page_icon="🌍", layout="wide")

# =====================================================================
# DESIGN TOKENS
# Brahmaputra blue (ink), tea-garden green (data), gamosa red (best pick)
# =====================================================================
INK = "#12374A"
MIST = "#EEF3F2"
PAPER = "#FFFFFF"
LINE = "#D5DFDD"
TEXT = "#14262E"
MUTED = "#5E747B"
TEA = "#2F7D5B"
RIVER = "#2A7DA6"
GAMOSA = "#C8312B"
GOLD = "#D9A441"
PLUM = "#8B4F8F"
SERIES = [TEA, RIVER, GAMOSA, GOLD, PLUM]

CATS = {"Grocery": TEA, "Fashion": PLUM, "Electronics": RIVER, "Food & Beverage": GOLD}
EXTRA_COLORS = ["#7A8B91", "#A0724A", "#4C9F9F", "#B0678E", "#8A9A3B"]
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
AREA_COLS = ["Area", "Latitude", "Longitude", "Visits", "Retail Stores", "Opportunity Score", "Rent Index"]
STORE_COLS = ["Store", "Area", "Category", "Latitude", "Longitude"]

# Streamlit 1.50+ replaced use_container_width with width="stretch".
_ver = tuple(int(p) for p in st.__version__.split(".")[:2] if p.isdigit())
STRETCH = {"width": "stretch"} if _ver >= (1, 50) else {"use_container_width": True}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Schibsted+Grotesk:wght@400;500;600;700;800&display=swap');
html, body, .stApp, .stApp p, .stApp label, .stApp li, .stApp button, .stApp input, .stApp textarea {
    font-family: 'Schibsted Grotesk', sans-serif;
}
.stApp { background: @MIST@; color: @TEXT@; }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2.4rem; max-width: 1180px; }
.stApp h1 { font-weight: 800; font-size: 2.1rem; letter-spacing: -0.02em; color: @TEXT@; }
.stApp h2, .stApp h3 { font-weight: 700; letter-spacing: -0.01em; color: @TEXT@; }

/* Text colors that hold on any Streamlit theme */
.stMain [data-testid="stMarkdownContainer"] p,
.stMain [data-testid="stMarkdownContainer"] li,
.stMain [data-testid="stMarkdownContainer"] th,
.stMain [data-testid="stMarkdownContainer"] td,
.stMain [data-testid="stWidgetLabel"] p { color: @TEXT@ !important; }
.stMain [data-testid="stCaptionContainer"],
.stMain [data-testid="stCaptionContainer"] p { color: @MUTED@ !important; }
button[data-baseweb="tab"] p { color: @TEXT@ !important; }

/* Sidebar */
[data-testid="stSidebar"] { background: @INK@; }
.stApp [data-testid="stSidebar"] * { color: #E3EEF1; }
.stApp [data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.25);
}
.stApp [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.18); }

/* Metrics */
div[data-testid="stMetric"] {
    background: @PAPER@; padding: 14px 16px; border-radius: 6px; border: 1px solid @LINE@;
}
[data-testid="stMetricLabel"] p { color: @MUTED@ !important; font-weight: 500; }
[data-testid="stMetricValue"] { color: @TEXT@; font-weight: 700; font-variant-numeric: tabular-nums; }

/* Alerts, expanders, buttons */
[data-testid="stAlert"] { background: @PAPER@; border: 1px solid @LINE@; border-left: 4px solid @RIVER@; border-radius: 6px; }
[data-testid="stAlert"] * { color: @TEXT@ !important; }
[data-testid="stExpander"] { background: @PAPER@; border: 1px solid @LINE@; border-radius: 6px; }
[data-testid="stExpander"] summary p { color: @TEXT@ !important; font-weight: 600; }
.stMain .stButton button, .stMain .stDownloadButton button {
    background: @TEA@; border: none; border-radius: 6px; font-weight: 600;
}
.stMain .stButton button *, .stMain .stDownloadButton button * { color: #FFFFFF !important; }
.stMain .stButton button:hover, .stMain .stDownloadButton button:hover { background: #256349; }
.stApp [data-testid="stSidebar"] .stButton button { background: transparent; border: 1px solid rgba(255,255,255,0.35); }

/* Custom components */
.gp-badges { margin: -6px 0 6px 0; }
.gp-badge {
    display: inline-block; padding: 2px 10px; margin: 0 6px 4px 0; border: 1px solid @LINE@;
    border-radius: 999px; font-size: 0.8rem; color: @MUTED@; background: @PAPER@;
}
.gp-badge.live { border-color: @TEA@; color: @TEA@; }
.gp-hero { font-size: 1.75rem; font-weight: 700; line-height: 1.25; max-width: 30ch; color: @TEXT@; margin: 4px 0 6px 0; }
.gp-sub { color: @MUTED@; margin-bottom: 18px; }
.gp-pick { background: @PAPER@; border: 1px solid @LINE@; border-radius: 6px; padding: 18px 20px; min-height: 230px; }
.gp-pick.first { border-top: 6px solid @GAMOSA@; }
.gp-pick-top { color: @MUTED@; font-size: 0.9rem; font-weight: 600; }
.gp-pick.first .gp-pick-top { color: @GAMOSA@; }
.gp-name { font-size: 1.45rem; font-weight: 800; color: @TEXT@; margin: 2px 0; }
.gp-score { font-size: 2.3rem; font-weight: 800; color: @TEXT@; font-variant-numeric: tabular-nums; }
.gp-score span { font-size: 1rem; font-weight: 500; color: @MUTED@; }
.gp-why { color: @MUTED@; font-size: 0.95rem; line-height: 1.45; margin-top: 6px; }
</style>
"""
for _k, _v in {
    "MIST": MIST, "TEXT": TEXT, "MUTED": MUTED, "INK": INK, "PAPER": PAPER, "LINE": LINE,
    "RIVER": RIVER, "TEA": TEA, "GAMOSA": GAMOSA,
}.items():
    CSS = CSS.replace(f"@{_k}@", _v)
st.markdown(CSS, unsafe_allow_html=True)


# =====================================================================
# HELPERS
# =====================================================================
def norm(s) -> pd.Series:
    s = pd.Series(s, dtype=float)
    span = s.max() - s.min()
    return (s - s.min()) / span if span > 0 else s * 0 + 0.5


def haversine_km(lat1, lon1, lat2, lon2):
    p = np.pi / 180
    a = np.sin((lat2 - lat1) * p / 2) ** 2 + np.cos(lat1 * p) * np.cos(lat2 * p) * np.sin((lon2 - lon1) * p / 2) ** 2
    return 12742 * np.arcsin(np.sqrt(a))


def cat_colors(cats) -> dict:
    out, extra = {}, iter(EXTRA_COLORS * 3)
    for c in cats:
        out[c] = CATS.get(c) or next(extra)
    return out


def style(fig, height=360):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Schibsted Grotesk, sans-serif", color=TEXT),
        margin=dict(l=10, r=10, t=50, b=10),
        height=height,
        title_font=dict(size=15),
        colorway=SERIES,
    )
    fig.update_xaxes(gridcolor=LINE, zeroline=False)
    fig.update_yaxes(gridcolor=LINE, zeroline=False)
    return fig


def bar_chart(df, x, y, title):
    top = df[y].max()
    fig = px.bar(df, x=x, y=y, title=title)
    fig.update_traces(marker_color=[GAMOSA if v == top else TEA for v in df[y]])
    fig.update_xaxes(title=None)
    return style(fig)


def show(fig) -> None:
    st.plotly_chart(fig, **STRETCH)


def table(df) -> None:
    st.dataframe(df, hide_index=True, **STRETCH)


def page_header(title: str, sub: str) -> None:
    st.title(title)
    mode = CTX["mode"]
    live = "live" if mode == "Your data" else ""
    badges = f'<span class="gp-badge {live}">{html.escape(mode)}</span>'
    badges += f'<span class="gp-badge">Stores: {html.escape(CTX["store_src"])}</span>'
    badges += f'<span class="gp-badge">{len(CTX["areas"])} areas</span>'
    st.markdown(f'<div class="gp-badges">{badges}</div>', unsafe_allow_html=True)
    st.caption(sub)


def demo_note() -> None:
    if CTX["mode"] == "Demo data":
        st.caption("Visits, rent and trends are simulated for illustration. Upload your own files on the Your data page.")


# =====================================================================
# DATA LAYER
# =====================================================================
@st.cache_data
def demo_areas() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Area": ["Zone A", "Zone B", "Zone C", "Zone D", "Zone E"],
            "Latitude": [26.1445, 26.1500, 26.1380, 26.1580, 26.1300],
            "Longitude": [91.7362, 91.7450, 91.7280, 91.7320, 91.7500],
            "Visits": [1250, 980, 1560, 740, 1120],
            "Retail Stores": [12, 9, 15, 6, 11],
            "Opportunity Score": [78, 65, 89, 54, 73],
        }
    )


def prepare_areas(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    for c in ["Latitude", "Longitude", "Visits"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=["Area", "Latitude", "Longitude", "Visits"]).drop_duplicates("Area").reset_index(drop=True)
    d["Area"] = d["Area"].astype(str)
    if "Retail Stores" not in d.columns:
        d["Retail Stores"] = (d["Visits"] / 110).round()
    d["Retail Stores"] = pd.to_numeric(d["Retail Stores"], errors="coerce").fillna(0).astype(int)
    per_store = d["Visits"] / d["Retail Stores"].clip(lower=1)
    if "Opportunity Score" not in d.columns:
        d["Opportunity Score"] = (100 * (0.6 * norm(d["Visits"]) + 0.4 * norm(per_store))).round()
    d["Opportunity Score"] = pd.to_numeric(d["Opportunity Score"], errors="coerce").fillna(50).round().astype(int)
    if "Rent Index" not in d.columns:
        d["Rent Index"] = (30 + 60 * norm(d["Visits"])).round()
    d["Rent Index"] = pd.to_numeric(d["Rent Index"], errors="coerce").fillna(50).round().astype(int)
    return d[AREA_COLS]


@st.cache_data
def make_hourly(areas: pd.DataFrame) -> pd.DataFrame:
    """Simulated visits per area, day of week and hour."""
    rng = np.random.default_rng(7)
    hours = np.arange(24)

    def profile(lunch, evening):
        p = 0.7 * np.exp(-((hours - lunch) ** 2) / 10) + np.exp(-((hours - evening) ** 2) / 6)
        p = np.where((hours >= 8) & (hours <= 22), p, p * 0.05)
        return p / p.sum()

    weekday, weekend = profile(12.5, 18), profile(14.5, 19)
    day_factor = [0.9, 0.85, 0.9, 0.95, 1.1, 1.3, 1.2]
    rows = []
    for _, a in areas.iterrows():
        for i, (day, f) in enumerate(zip(DAYS, day_factor)):
            p = weekday if i < 5 else weekend
            v = a["Visits"] * f * p * rng.normal(1, 0.06, 24)
            rows += [(a["Area"], day, int(h), float(v[h])) for h in hours]
    return pd.DataFrame(rows, columns=["Area", "Day", "Hour", "Visits"])


@st.cache_data
def make_weekly(areas: pd.DataFrame) -> pd.DataFrame:
    """Simulated weekly visits for the last 52 weeks, with trend and yearly seasonality."""
    rng = np.random.default_rng(11)
    weeks = pd.date_range(end=pd.Timestamp.today().normalize(), periods=52, freq="W-MON")
    t = np.arange(len(weeks))
    growth = {"Zone A": 0.004, "Zone B": 0.0015, "Zone C": 0.006, "Zone D": -0.001, "Zone E": 0.003}
    frames = []
    for _, a in areas.iterrows():
        g = growth.get(a["Area"], rng.uniform(-0.001, 0.006))
        phase = rng.uniform(0, 2 * np.pi)
        vals = a["Visits"] * 7 * 0.85 * (1 + g * t) * (1 + 0.10 * np.sin(2 * np.pi * t / 52 + phase))
        vals = vals * rng.normal(1, 0.035, len(t))
        frames.append(pd.DataFrame({"Area": a["Area"], "Week": weeks, "Visits": vals}))
    return pd.concat(frames, ignore_index=True)


@st.cache_data
def make_stores(areas: pd.DataFrame) -> pd.DataFrame:
    """Simulated store locations that match each area's store count."""
    rng = np.random.default_rng(21)
    cats = list(CATS)
    rows = []
    for _, a in areas.iterrows():
        for i in range(int(a["Retail Stores"])):
            rows.append(
                {
                    "Store": f'{a["Area"]} store {i + 1}',
                    "Area": a["Area"],
                    "Category": str(rng.choice(cats)),
                    "Latitude": a["Latitude"] + rng.normal(0, 0.004),
                    "Longitude": a["Longitude"] + rng.normal(0, 0.004),
                }
            )
    return pd.DataFrame(rows, columns=STORE_COLS)


def assign_area(stores: pd.DataFrame, areas: pd.DataFrame, max_km: float = 3.0) -> pd.DataFrame:
    """Give each store the nearest area; drop stores farther than max_km from every area."""
    if stores.empty:
        return stores.assign(Area=pd.Series(dtype=str))[STORE_COLS]
    d = haversine_km(
        stores["Latitude"].to_numpy()[:, None], stores["Longitude"].to_numpy()[:, None],
        areas["Latitude"].to_numpy()[None, :], areas["Longitude"].to_numpy()[None, :],
    )
    out = stores.copy()
    out["Area"] = areas["Area"].to_numpy()[d.argmin(axis=1)]
    return out[d.min(axis=1) <= max_km][STORE_COLS].reset_index(drop=True)


def osm_category(tags: dict):
    shop, amenity = tags.get("shop"), tags.get("amenity")
    if amenity in {"cafe", "restaurant", "fast_food"}:
        return "Food & Beverage"
    if shop in {"supermarket", "convenience", "greengrocer", "grocery", "bakery", "butcher", "department_store"}:
        return "Grocery"
    if shop in {"clothes", "shoes", "boutique", "jewelry", "fashion_accessories"}:
        return "Fashion"
    if shop in {"electronics", "mobile_phone", "computer", "hifi"}:
        return "Electronics"
    return None


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_osm(south: float, west: float, north: float, east: float) -> pd.DataFrame:
    """Real shops and eateries from OpenStreetMap. Raises on failure so errors are not cached."""
    bbox = f"{south},{west},{north},{east}"
    shops = "supermarket|convenience|greengrocer|grocery|bakery|butcher|department_store|clothes|shoes|boutique|jewelry|fashion_accessories|electronics|mobile_phone|computer|hifi"
    query = (
        f'[out:json][timeout:30];(node["shop"~"{shops}"]({bbox});'
        f'node["amenity"~"cafe|restaurant|fast_food"]({bbox}););out body 800;'
    )
    r = requests.post(
        "https://overpass-api.de/api/interpreter",
        data={"data": query},
        timeout=40,
        headers={"User-Agent": "GeoPulse/1.0 (retail analytics demo)"},
    )
    r.raise_for_status()
    rows = []
    for el in r.json().get("elements", []):
        tags = el.get("tags", {})
        cat = osm_category(tags)
        if cat and "lat" in el:
            rows.append({"Store": tags.get("name") or f"{cat} store", "Category": cat, "Latitude": el["lat"], "Longitude": el["lon"]})
    if not rows:
        raise ValueError("No stores returned for this area")
    return pd.DataFrame(rows, columns=["Store", "Category", "Latitude", "Longitude"])


# ---- uploads ----
ALIASES = {
    "lat": "Latitude", "lng": "Longitude", "lon": "Longitude", "long": "Longitude",
    "stores": "Retail Stores", "opportunity": "Opportunity Score", "rent": "Rent Index",
}


def canon_cols(df: pd.DataFrame, wanted: list) -> pd.DataFrame:
    by_lower = {w.lower(): w for w in wanted}
    ren = {}
    for c in df.columns:
        key = str(c).strip().lower().replace("_", " ")
        target = by_lower.get(key) or ALIASES.get(key)
        if target in wanted:
            ren[c] = target
    return df.rename(columns=ren)


def read_upload(file, wanted, required):
    """Return (DataFrame or None, error message or None)."""
    try:
        df = pd.read_csv(file)
    except Exception as exc:
        return None, f"Could not read {file.name}: {exc}"
    df = canon_cols(df, wanted)
    missing = [c for c in required if c not in df.columns]
    if missing:
        return None, f'{file.name} is missing column(s): {", ".join(missing)}. Found: {", ".join(map(str, df.columns))}.'
    return df, None


def normalize_stores(df: pd.DataFrame, areas: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    for c in ["Latitude", "Longitude"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=["Latitude", "Longitude"]).reset_index(drop=True)
    if "Store" not in d.columns:
        d["Store"] = [f"Store {i + 1}" for i in range(len(d))]
    d["Category"] = d["Category"].fillna("Other").astype(str)
    if "Area" not in d.columns:
        return assign_area(d, areas, max_km=50)
    d["Area"] = d["Area"].astype(str)
    return d[STORE_COLS]


def prepare_weekly(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["Week"] = pd.to_datetime(d["Week"], errors="coerce")
    d["Visits"] = pd.to_numeric(d["Visits"], errors="coerce")
    d["Area"] = d["Area"].astype(str)
    return d.dropna(subset=["Week", "Visits"]).sort_values(["Area", "Week"]).reset_index(drop=True)


def prepare_hourly(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["Hour"] = pd.to_numeric(d["Hour"], errors="coerce")
    d["Visits"] = pd.to_numeric(d["Visits"], errors="coerce")
    d["Day"] = d["Day"].astype(str).str.strip().str[:3].str.title()
    d["Area"] = d["Area"].astype(str)
    d = d.dropna(subset=["Hour", "Visits"])
    d["Hour"] = d["Hour"].astype(int)
    return d[d["Day"].isin(DAYS) & d["Hour"].between(0, 23)].reset_index(drop=True)


def load_data(use_osm: bool) -> dict:
    up = st.session_state.get("upload", {})
    notes = []
    if "areas" in up:
        areas, mode = prepare_areas(up["areas"]), "Your data"
    else:
        areas, mode = prepare_areas(demo_areas()), "Demo data"

    if "stores" in up:
        stores, store_src = normalize_stores(up["stores"], areas), "Uploaded"
    elif use_osm:
        try:
            with st.spinner("Loading store locations from OpenStreetMap"):
                bounds = (
                    round(areas["Latitude"].min() - 0.02, 4), round(areas["Longitude"].min() - 0.02, 4),
                    round(areas["Latitude"].max() + 0.02, 4), round(areas["Longitude"].max() + 0.02, 4),
                )
                stores = assign_area(fetch_osm(*bounds), areas)
            if stores.empty:
                raise ValueError("no stores near the areas")
            store_src = "OpenStreetMap"
        except Exception as exc:
            notes.append(f"Could not load OpenStreetMap stores ({exc}). Showing simulated stores instead.")
            stores, store_src = make_stores(areas), "Simulated"
    else:
        stores, store_src = make_stores(areas), "Simulated"

    counts = stores.groupby("Area").size()
    areas = areas.copy()
    areas["Retail Stores"] = areas["Area"].map(counts).fillna(0).astype(int)

    weekly = prepare_weekly(up["weekly"]) if "weekly" in up else make_weekly(areas)
    hourly = prepare_hourly(up["hourly"]) if "hourly" in up else make_hourly(areas)
    return {"areas": areas, "stores": stores, "weekly": weekly, "hourly": hourly,
            "mode": mode, "store_src": store_src, "notes": notes}


# =====================================================================
# ANALYTICS
# =====================================================================
def score_areas(areas: pd.DataFrame, w_demand=40, w_gap=40, w_base=20) -> pd.DataFrame:
    """Weighted site score: demand, under-served gap (visits per store) and baseline opportunity."""
    d = areas.copy()
    d["Visits per Store"] = d["Visits"] / d["Retail Stores"].clip(lower=1)
    total = (w_demand + w_gap + w_base) or 1
    d["Site Score"] = 100 * (
        w_demand * norm(d["Visits"]) + w_gap * norm(d["Visits per Store"]) + w_base * norm(d["Opportunity Score"])
    ) / total
    d["Rank"] = d["Site Score"].rank(ascending=False, method="first").astype(int)
    return d.sort_values("Rank").reset_index(drop=True)


BUDGET_WEIGHTS = {"Low": (0.35, 0.35, 0.30), "Medium": (0.45, 0.40, 0.15), "High": (0.50, 0.50, 0.0)}


def recommend(areas: pd.DataFrame, stores: pd.DataFrame, category: str, budget: str) -> pd.DataFrame:
    """Rank areas for opening a store of one category: demand, category gap and rent."""
    d = areas.copy()
    n_cat = stores[stores["Category"] == category].groupby("Area").size()
    d["Category Stores"] = d["Area"].map(n_cat).fillna(0).astype(int)
    d["Visits per Category Store"] = d["Visits"] / (d["Category Stores"] + 1)
    w_demand, w_gap, w_rent = BUDGET_WEIGHTS[budget]
    d["Score"] = 100 * (
        w_demand * norm(d["Visits"]) + w_gap * norm(d["Visits per Category Store"]) + w_rent * (1 - norm(d["Rent Index"]))
    )
    return d.sort_values("Score", ascending=False).reset_index(drop=True)


def why_text(r: pd.Series, category: str, mean_rent: float) -> str:
    n = int(r["Category Stores"])
    existing = f"No {category} stores yet" if n == 0 else f'{n} {category} store{"s" if n != 1 else ""} today'
    if r["Rent Index"] > 1.1 * mean_rent:
        rent = "higher than average"
    elif r["Rent Index"] < 0.9 * mean_rent:
        rent = "lower than average"
    else:
        rent = "about average"
    return f'{r["Visits"]:,.0f} visits on a typical day. {existing}, or {r["Visits per Category Store"]:,.0f} visits per store. Rent is {rent}.'


def seasonal_feats(idx, seasonal: bool) -> np.ndarray:
    t = np.asarray(idx, dtype=float)
    cols = [t / 52.0]
    if seasonal:
        for k in (1, 2):
            cols += [np.sin(2 * np.pi * k * t / 52), np.cos(2 * np.pi * k * t / 52)]
    return np.column_stack(cols)


def mape(actual, pred) -> float:
    return float(np.mean(np.abs((actual - pred) / actual)) * 100)


def evaluate_models(y: np.ndarray):
    """Hold out the last weeks, fit on the rest and compare error (MAPE) across models."""
    n = len(y)
    hold = max(2, min(8, n // 4))
    train, test = y[:-hold], y[-hold:]
    future = np.arange(len(train), n)
    scores = {"Last value (baseline)": mape(test, np.repeat(train[-1], hold))}
    lin = Ridge(alpha=0.1).fit(seasonal_feats(np.arange(len(train)), False), train)
    scores["Linear trend"] = mape(test, lin.predict(seasonal_feats(future, False)))
    if n >= 40:
        sea = Ridge(alpha=0.1).fit(seasonal_feats(np.arange(len(train)), True), train)
        scores["Seasonal ridge"] = mape(test, sea.predict(seasonal_feats(future, True)))
    return scores, hold


def forecast(area: str, horizon: int, uplift: float = 0.0):
    w = CTX["weekly"]
    h = w[w["Area"] == area].sort_values("Week").reset_index(drop=True)
    y = h["Visits"].to_numpy(dtype=float)
    scores, hold = evaluate_models(y)
    candidates = {k: v for k, v in scores.items() if not k.startswith("Last")}
    chosen = min(candidates, key=candidates.get)
    seasonal = chosen == "Seasonal ridge"
    model = Ridge(alpha=0.1).fit(seasonal_feats(np.arange(len(y)), seasonal), y)
    sigma = float(np.std(y - model.predict(seasonal_feats(np.arange(len(y)), seasonal))))
    fx = np.arange(len(y), len(y) + horizon)
    fy = model.predict(seasonal_feats(fx, seasonal)) * (1 + uplift)
    dates = h["Week"].iloc[-1] + pd.to_timedelta(7 * np.arange(1, horizon + 1), unit="D")
    fc = pd.DataFrame({"Week": dates, "Forecast": fy, "Low": fy - 1.28 * sigma, "High": fy + 1.28 * sigma})
    return h, fc, scores, hold, chosen


# =====================================================================
# PAGES: EXPLORE
# =====================================================================
def page_overview():
    areas, weekly = CTX["areas"], CTX["weekly"]
    scored = score_areas(areas)
    lead = scored.iloc[0]

    st.title("Overview")
    mode_badges = f'<span class="gp-badge">{html.escape(CTX["mode"])}</span><span class="gp-badge">Stores: {html.escape(CTX["store_src"])}</span><span class="gp-badge">{len(areas)} areas</span>'
    st.markdown(f'<div class="gp-badges">{mode_badges}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="gp-hero">{html.escape(lead["Area"])} is the strongest area to open a store right now.</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="gp-sub">It combines {lead["Visits"]:,.0f} visits on a typical day with {lead["Retail Stores"]} existing stores. '
        f'Use Where to open for a pick by business type.</div>',
        unsafe_allow_html=True,
    )
    demo_note()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Visits (typical day)", f'{areas["Visits"].sum():,.0f}')
    c2.metric("Retail stores", f'{areas["Retail Stores"].sum():,}')
    c3.metric("Areas analyzed", f"{len(areas)}")
    c4.metric("Avg. opportunity score", f'{areas["Opportunity Score"].mean():.1f}/100')

    left, right = st.columns(2)
    with left:
        show(bar_chart(areas, "Area", "Visits", "Visits by area"))
    with right:
        show(bar_chart(areas, "Area", "Opportunity Score", "Opportunity score by area"))

    total = weekly.groupby("Week", as_index=False)["Visits"].sum()
    if not total.empty:
        fig = px.line(total, x="Week", y="Visits", title="Total weekly visits")
        fig.update_traces(line_color=RIVER)
        fig.update_xaxes(title=None)
        show(style(fig, 300))

    st.subheader("Area data")
    table(areas.drop(columns=["Latitude", "Longitude"]))


def page_heatmap():
    page_header("Mobility heatmap", "See where visits and opportunity concentrate on the map.")
    demo_note()
    areas, stores = CTX["areas"], CTX["stores"]

    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
    metric = c1.selectbox("Heat intensity", ["Visits", "Opportunity Score"])
    radius = c2.slider("Radius", 10, 60, 30)
    show_areas = c3.toggle("Area pins", value=True)
    show_stores = c4.toggle("Stores", value=False)

    m = folium.Map(location=[areas["Latitude"].mean(), areas["Longitude"].mean()], zoom_start=13, tiles="OpenStreetMap")
    weights = (areas[metric] / areas[metric].max()).to_numpy()
    heat = [[la, lo, w] for la, lo, w in zip(areas["Latitude"], areas["Longitude"], weights)]
    HeatMap(heat, radius=radius, blur=22, gradient={0.3: "#7FC8A9", 0.6: "#F0C24B", 1.0: GAMOSA}).add_to(m)

    if show_areas:
        for _, a in areas.iterrows():
            folium.Marker(
                location=[a["Latitude"], a["Longitude"]],
                tooltip=a["Area"],
                popup=f'{html.escape(a["Area"])}<br>Visits: {a["Visits"]:,.0f}<br>Opportunity: {a["Opportunity Score"]}/100',
                icon=folium.Icon(color="darkblue", icon="shopping-cart"),
            ).add_to(m)
    if show_stores:
        colors = cat_colors(sorted(stores["Category"].unique()))
        for _, s in stores.iterrows():
            folium.CircleMarker(
                location=[s["Latitude"], s["Longitude"]], radius=4, color=colors[s["Category"]],
                fill=True, fill_opacity=0.85, tooltip=f'{s["Store"]} ({s["Category"]})',
            ).add_to(m)

    st_folium(m, key="heat_map", height=540, use_container_width=True, returned_objects=[])
    st.subheader("Area data")
    table(areas)


def page_mobility():
    page_header("Customer mobility", "When people visit, by hour and day of the week.")
    demo_note()
    hourly = CTX["hourly"]
    base = hourly[hourly["Area"].isin(CTX["areas"]["Area"])]
    if base.empty:
        st.info("There is no hourly data for the selected areas. Upload an hourly file on the Your data page, or pick other areas.")
        return

    day_type = st.radio("Days", ["All days", "Weekdays", "Weekends"], horizontal=True)
    df = base
    if day_type == "Weekdays":
        df = base[base["Day"].isin(DAYS[:5])]
    elif day_type == "Weekends":
        df = base[base["Day"].isin(DAYS[5:])]
    if df.empty:
        st.info("No data for this day type.")
        return

    daily = base.groupby("Day")["Visits"].sum().reindex(DAYS).fillna(0)
    peak_hour = int(df.groupby("Hour")["Visits"].sum().idxmax())
    wk_mean = daily[DAYS[:5]].mean()
    uplift = f"{daily[DAYS[5:]].mean() / wk_mean - 1:+.0%}" if wk_mean > 0 else "n/a"

    m1, m2, m3 = st.columns(3)
    m1.metric("Peak hour", f"{peak_hour}:00")
    m2.metric("Busiest day", daily.idxmax())
    m3.metric("Weekend vs weekday", uplift)

    by_hour = df.groupby(["Area", "Hour"], as_index=False)["Visits"].mean()
    fig = px.line(by_hour, x="Hour", y="Visits", color="Area", title=f"Average visits per hour ({day_type.lower()})")
    fig.update_xaxes(dtick=2)
    fig.update_yaxes(title="Visits per hour")
    show(style(fig, 380))

    pivot = base.groupby(["Day", "Hour"])["Visits"].sum().unstack("Hour").reindex(DAYS)
    heat = px.imshow(
        pivot, aspect="auto", color_continuous_scale=[[0, "#E6F0EE"], [1, TEA]],
        labels=dict(x="Hour", y="Day", color="Visits"), title="Visits by day and hour",
    )
    show(style(heat, 340))


def page_competitors():
    page_header("Competitor analysis", "Where stores cluster and how crowded each area is.")
    demo_note()
    stores, areas = CTX["stores"], CTX["areas"]
    view = stores[stores["Area"].isin(areas["Area"])]
    if view.empty:
        st.info("No stores match the current filters. Add a category or an area in the sidebar.")
        return

    colors = cat_colors(sorted(view["Category"].unique()))
    counts = view.groupby("Area").size().rename("Stores").reset_index()
    crowded = counts.loc[counts["Stores"].idxmax()]
    m1, m2, m3 = st.columns(3)
    m1.metric("Stores shown", len(view))
    m2.metric("Most crowded area", f'{crowded["Area"]} ({crowded["Stores"]})')
    m3.metric("Most common category", view["Category"].mode().iloc[0])

    m = folium.Map(location=[view["Latitude"].mean(), view["Longitude"].mean()], zoom_start=13, tiles="OpenStreetMap")
    for _, s in view.iterrows():
        folium.CircleMarker(
            location=[s["Latitude"], s["Longitude"]], radius=7, color=colors[s["Category"]],
            fill=True, fill_color=colors[s["Category"]], fill_opacity=0.85,
            tooltip=f'{s["Store"]} ({s["Category"]})',
        ).add_to(m)
    st_folium(m, key="comp_map", height=460, use_container_width=True, returned_objects=[])

    by_cat = view.groupby(["Area", "Category"]).size().rename("Stores").reset_index()
    fig = px.bar(by_cat, x="Area", y="Stores", color="Category", color_discrete_map=colors, title="Stores by area and category")
    fig.update_xaxes(title=None)
    show(style(fig))

    st.subheader("Saturation")
    sat = counts.merge(areas[["Area", "Visits"]], on="Area")
    sat["Visits per Store"] = (sat["Visits"] / sat["Stores"]).round(1)
    sat = sat.sort_values("Visits per Store", ascending=False)
    table(sat)
    st.caption(f'{sat.iloc[0]["Area"]} has the most visits per store, so each store there shares the least competition.')


# =====================================================================
# PAGES: DECIDE
# =====================================================================
def page_where():
    page_header("Where to open", "Pick a business type and budget to see the three best areas.")
    demo_note()
    areas, stores = CTX["areas"], CTX["stores"]
    cats = sorted(stores["Category"].unique()) or list(CATS)

    c1, c2 = st.columns(2)
    category = c1.selectbox("Business type", cats)
    budget = c2.radio("Rent budget", ["Low", "Medium", "High"], index=1, horizontal=True,
                      help="Low budgets favor areas with lower rent. High budgets ignore rent.")

    ranked = recommend(areas, stores, category, budget)
    mean_rent = areas["Rent Index"].mean()
    labels = ["Best fit", "Second choice", "Third choice"]
    cols = st.columns(min(3, len(ranked)))
    for i, col in enumerate(cols):
        r = ranked.iloc[i]
        card = (
            f'<div class="gp-pick{" first" if i == 0 else ""}">'
            f'<div class="gp-pick-top">{labels[i]}</div>'
            f'<div class="gp-name">{html.escape(r["Area"])}</div>'
            f'<div class="gp-score">{r["Score"]:.0f}<span>/100</span></div>'
            f'<div class="gp-why">{html.escape(why_text(r, category, mean_rent))}</div>'
            f"</div>"
        )
        col.markdown(card, unsafe_allow_html=True)

    st.write("")
    show(bar_chart(ranked, "Area", "Score", f"Fit score for a new {category} store"))
    with st.expander("Details for every area"):
        out = ranked[["Area", "Score", "Visits", "Category Stores", "Visits per Category Store", "Rent Index"]].round(1)
        table(out)
    st.caption("Score weighs demand, the gap in existing stores of this type, and rent. See Methodology for the formula.")


def page_catchment():
    page_header("Catchment", "Click the map to see what is around a possible site.")
    demo_note()
    areas, stores = CTX["areas"], CTX["stores"]
    radius = st.select_slider("Radius", options=[500, 1000, 1500, 2000], value=1000, format_func=lambda m: f"{m / 1000:g} km")

    default_pt = (float(areas["Latitude"].mean()), float(areas["Longitude"].mean()))
    pt = st.session_state.get("catch_pt", default_pt)

    colors = cat_colors(sorted(stores["Category"].unique()))
    m = folium.Map(location=pt, zoom_start=14, tiles="OpenStreetMap")
    for _, s in stores.iterrows():
        folium.CircleMarker(
            location=[s["Latitude"], s["Longitude"]], radius=4, color=colors[s["Category"]],
            fill=True, fill_opacity=0.85, tooltip=f'{s["Store"]} ({s["Category"]})',
        ).add_to(m)
    folium.Circle(pt, radius=radius, color=GAMOSA, fill=True, fill_opacity=0.08).add_to(m)
    folium.Marker(pt, tooltip="Possible site", icon=folium.Icon(color="red", icon="map-marker")).add_to(m)

    out = st_folium(m, key="catch_map", height=460, use_container_width=True, returned_objects=["last_clicked"])
    clicked = (out or {}).get("last_clicked")
    if clicked:
        new_pt = (clicked["lat"], clicked["lng"])
        if new_pt != tuple(pt):
            st.session_state["catch_pt"] = new_pt
            st.rerun()

    dist_m = haversine_km(pt[0], pt[1], stores["Latitude"].to_numpy(), stores["Longitude"].to_numpy()) * 1000
    inside = stores[dist_m <= radius]
    area_d = haversine_km(pt[0], pt[1], areas["Latitude"].to_numpy(), areas["Longitude"].to_numpy()) * 1000
    near_areas = areas[area_d <= radius]

    m1, m2, m3 = st.columns(3)
    m1.metric("Stores inside", len(inside))
    m2.metric("Most common category", inside["Category"].mode().iloc[0] if len(inside) else "None")
    if len(near_areas):
        m3.metric("Visits in areas inside", f'{near_areas["Visits"].sum():,.0f}')
    else:
        j = int(area_d.argmin())
        m3.metric("Nearest area", f'{areas.iloc[j]["Area"]} ({area_d[j] / 1000:.1f} km)')

    if inside.empty:
        st.info("No stores inside this circle. Click elsewhere or increase the radius.")
        return
    mix = inside.groupby("Category").size().rename("Stores").reset_index()
    fig = px.bar(mix, x="Category", y="Stores", color="Category", color_discrete_map=colors, title="Store mix inside the circle")
    fig.update_xaxes(title=None)
    fig.update_layout(showlegend=False)
    show(style(fig, 300))
    st.caption("Visits are counted for areas whose center lies inside the circle. Areas are not split by partial overlap.")


def page_retail():
    page_header("Retail intelligence", "Rank areas by demand, under-served gap and baseline opportunity.")
    demo_note()
    st.write("Set how much each factor counts toward the site score.")
    c1, c2, c3 = st.columns(3)
    w_demand = c1.slider("Demand (visits)", 0, 100, 40, 5)
    w_gap = c2.slider("Under-served gap (visits per store)", 0, 100, 40, 5)
    w_base = c3.slider("Baseline opportunity score", 0, 100, 20, 5)
    if w_demand + w_gap + w_base == 0:
        st.warning("Give at least one factor a weight above zero.")
        return

    scored = score_areas(CTX["areas"], w_demand, w_gap, w_base)
    lead = scored.iloc[0]
    st.write(f'**{lead["Area"]}** ranks first with a site score of {lead["Site Score"]:.1f}, based on {lead["Visits"]:,.0f} visits across {lead["Retail Stores"]} stores.')

    left, right = st.columns(2)
    with left:
        show(bar_chart(scored, "Area", "Site Score", "Site score by area"))
    with right:
        fig = px.scatter(scored, x="Retail Stores", y="Visits", size="Site Score", color="Area",
                         title="Visits vs store count (bubble size = site score)", size_max=40)
        show(style(fig))
    st.subheader("Ranking")
    table(scored[["Rank", "Area", "Visits", "Retail Stores", "Visits per Store", "Site Score"]].round(1))


def page_forecast():
    page_header("Forecast", "Project weekly visits and see how accurate the model has been.")
    demo_note()
    area = st.selectbox("Area", list(CTX["areas"]["Area"]))
    c1, c2 = st.columns(2)
    horizon = c1.slider("Weeks to project", 2, 12, 4)
    uplift = c2.slider("Scenario adjustment (%)", -20, 30, 0, help="Applies a flat increase or decrease to the projection.") / 100

    w = CTX["weekly"]
    if len(w[w["Area"] == area]) < 8:
        st.info("This area has fewer than 8 weeks of history. Widen the time window in the sidebar or upload more weekly data.")
        return
    hist, fc, scores, hold, chosen = forecast(area, horizon, uplift)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(fc["Week"]) + list(fc["Week"])[::-1], y=list(fc["High"]) + list(fc["Low"])[::-1],
        fill="toself", fillcolor="rgba(200,49,43,0.14)", line=dict(width=0), hoverinfo="skip", name="80% range"))
    fig.add_trace(go.Scatter(x=hist["Week"], y=hist["Visits"], mode="lines", name="Actual", line=dict(color=TEA)))
    fig.add_trace(go.Scatter(
        x=[hist["Week"].iloc[-1]] + list(fc["Week"]), y=[hist["Visits"].iloc[-1]] + list(fc["Forecast"]),
        mode="lines+markers", name="Projection", line=dict(color=GAMOSA, dash="dash")))
    fig.update_layout(title=f"{area}: weekly visits")
    fig.update_yaxes(title="Visits per week")
    show(style(fig, 400))

    recent, projected = hist["Visits"].tail(horizon).sum(), fc["Forecast"].sum()
    m1, m2, m3 = st.columns(3)
    m1.metric(f"Last {horizon} weeks", f"{recent:,.0f}")
    m2.metric(f"Next {horizon} weeks", f"{projected:,.0f}")
    m3.metric("Change", f"{projected / recent - 1:+.1%}")

    st.subheader("How accurate is it?")
    err = pd.DataFrame({"Model": list(scores), f"Error on the last {hold} weeks (MAPE %)": [round(v, 1) for v in scores.values()]})
    table(err)
    st.caption(f"Each model was fitted on earlier weeks and tested on the last {hold}. The projection uses {chosen}, which had the lowest error.")


# =====================================================================
# PAGES: SHARE
# =====================================================================
def md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(out)


def build_sections(sel_sections: list) -> list:
    areas = CTX["areas"]
    scored = score_areas(areas)
    sections = []
    if "Summary" in sel_sections:
        top = scored.iloc[0]
        sections.append({"title": "Summary", "bullets": [
            f'Areas covered: {", ".join(areas["Area"])}',
            f'Visits on a typical day: {int(areas["Visits"].sum()):,}',
            f'Top site: {top["Area"]} (score {top["Site Score"]:.1f})',
            f'Data: {CTX["mode"]}; stores from {CTX["store_src"]}',
        ]})
    if "Site ranking" in sel_sections:
        t = scored[["Rank", "Area", "Visits", "Retail Stores", "Site Score"]].round(1)
        sections.append({"title": "Site ranking", "table": t, "chart": ("bar", t["Area"].tolist(), t["Site Score"].tolist(), "Site score")})
    if "Store saturation" in sel_sections:
        t = areas[["Area", "Retail Stores", "Visits"]].copy()
        t["Stores per 1,000 visits"] = (t["Retail Stores"] / t["Visits"] * 1000).round(1)
        sections.append({"title": "Store saturation", "table": t[["Area", "Retail Stores", "Stores per 1,000 visits"]]})
    if "Visit projection" in sel_sections:
        rows = []
        for a in areas["Area"]:
            try:
                h, fc, *_ = forecast(a, 4)
            except Exception:
                continue
            last, proj = h["Visits"].tail(4).sum(), fc["Forecast"].sum()
            rows.append({"Area": a, "Last 4 weeks": f"{last:,.0f}", "Next 4 weeks": f"{proj:,.0f}", "Change": f"{proj / last - 1:+.1%}",
                         "_last": last, "_proj": proj})
        if rows:
            t = pd.DataFrame(rows)
            sections.append({"title": "Visit projection", "table": t[["Area", "Last 4 weeks", "Next 4 weeks", "Change"]],
                             "chart": ("bar", t["Area"].tolist(), t["_proj"].tolist(), "Projected visits, next 4 weeks")})
    return sections


def sections_to_md(sections: list) -> str:
    lines = ["# GeoPulse retail report", f'Generated {pd.Timestamp.today().strftime("%d %b %Y")}.', ""]
    for s in sections:
        lines.append(f'## {s["title"]}')
        lines += [f"- {b}" for b in s.get("bullets", [])]
        if "table" in s:
            lines.append(md_table(s["table"]))
        lines.append("")
    return "\n".join(lines)


def ascii_text(s) -> str:
    return str(s).encode("latin-1", "replace").decode("latin-1")


def build_pdf(sections: list) -> bytes:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(True, 15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, "GeoPulse retail report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, ascii_text(f'Generated {pd.Timestamp.today().strftime("%d %b %Y")}'), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    for s in sections:
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 9, ascii_text(s["title"]), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        for b in s.get("bullets", []):
            pdf.multi_cell(0, 6, ascii_text("- " + b), new_x="LMARGIN", new_y="NEXT")
        if "table" in s:
            t = s["table"]
            w = pdf.epw / len(t.columns)
            pdf.set_font("Helvetica", "B", 9)
            for c in t.columns:
                pdf.cell(w, 7, ascii_text(c), border=1)
            pdf.ln(7)
            pdf.set_font("Helvetica", "", 9)
            for _, r in t.iterrows():
                for c in t.columns:
                    pdf.cell(w, 7, ascii_text(r[c]), border=1)
                pdf.ln(7)
        if "chart" in s:
            _, labels, values, title = s["chart"]
            fig, ax = plt.subplots(figsize=(6.5, 2.8))
            top = max(values)
            ax.bar(labels, values, color=[GAMOSA if v == top else TEA for v in values])
            ax.set_title(title, fontsize=10)
            ax.spines[["top", "right"]].set_visible(False)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)
            pdf.ln(3)
            pdf.image(buf, w=pdf.epw * 0.85)
        pdf.ln(6)
    return bytes(pdf.output())


def page_reports():
    page_header("Reports", "Build a summary of the current view and download it.")
    demo_note()
    all_sections = ["Summary", "Site ranking", "Store saturation", "Visit projection"]
    chosen = st.multiselect("Sections", all_sections, default=all_sections)
    if not chosen:
        st.info("Choose at least one section.")
        return
    sections = build_sections([s for s in all_sections if s in chosen])
    md = sections_to_md(sections)
    scored = score_areas(CTX["areas"])

    c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
    c1.download_button("Download .md", md, file_name="geopulse_report.md", mime="text/markdown")
    c2.download_button("Download .csv", scored.to_csv(index=False), file_name="geopulse_sites.csv", mime="text/csv")
    sig = hash(md)
    if c3.button("Prepare PDF"):
        try:
            st.session_state["pdf"] = (sig, build_pdf(sections))
        except ImportError:
            st.warning("PDF export needs the fpdf2 and matplotlib packages. Add them to requirements.txt.")
        except Exception as exc:
            st.warning(f"Could not build the PDF: {exc}")
    cached = st.session_state.get("pdf")
    if cached and cached[0] == sig:
        c4.download_button("Download PDF", cached[1], file_name="geopulse_report.pdf", mime="application/pdf")

    st.subheader("Preview")
    st.markdown(md)


# =====================================================================
# PAGES: DATA
# =====================================================================
def page_data():
    st.title("Your data")
    st.caption("Upload CSV files to run every page on your own numbers. Only the areas file is required.")
    up = st.session_state.get("upload", {})
    if up:
        st.success("Using your uploaded files: " + ", ".join(up.keys()) + ".")
    else:
        st.info("Using the built-in demo data.")

    tab_up, tab_tpl = st.tabs(["Upload files", "Templates"])
    with tab_up:
        f_areas = st.file_uploader("Areas (required): Area, Latitude, Longitude, Visits. Optional: Retail Stores, Opportunity Score, Rent Index", type="csv", key="u_areas")
        f_stores = st.file_uploader("Stores (optional): Store, Category, Latitude, Longitude. Optional: Area", type="csv", key="u_stores")
        f_weekly = st.file_uploader("Weekly visits (optional): Area, Week, Visits", type="csv", key="u_weekly")
        f_hourly = st.file_uploader("Hourly visits (optional): Area, Day, Hour, Visits (Day is Mon to Sun)", type="csv", key="u_hourly")

        b1, b2 = st.columns([1, 1])
        if b1.button("Use these files"):
            if f_areas is None:
                st.error("Add the areas file first. It is the only required one.")
            else:
                new, errors = {}, []
                specs = [
                    ("areas", f_areas, AREA_COLS, ["Area", "Latitude", "Longitude", "Visits"]),
                    ("stores", f_stores, STORE_COLS, ["Category", "Latitude", "Longitude"]),
                    ("weekly", f_weekly, ["Area", "Week", "Visits"], ["Area", "Week", "Visits"]),
                    ("hourly", f_hourly, ["Area", "Day", "Hour", "Visits"], ["Area", "Day", "Hour", "Visits"]),
                ]
                for key, f, wanted, required in specs:
                    if f is None:
                        continue
                    df, err = read_upload(f, wanted, required)
                    if err:
                        errors.append(err)
                    else:
                        new[key] = df
                if errors:
                    for e in errors:
                        st.error(e)
                elif prepare_areas(new["areas"]).empty:
                    st.error("The areas file has no usable rows. Check that Latitude, Longitude and Visits are numbers.")
                else:
                    st.session_state["upload"] = new
                    st.session_state.pop("catch_pt", None)
                    st.rerun()
        if b2.button("Back to demo data"):
            st.session_state.pop("upload", None)
            st.session_state.pop("catch_pt", None)
            st.rerun()

    with tab_tpl:
        st.write("Download a template, replace the rows with your own, and upload it on the other tab.")
        demo = prepare_areas(demo_areas())
        t1, t2, t3, t4 = st.columns(4)
        t1.download_button("Areas template", demo.to_csv(index=False), file_name="areas_template.csv", mime="text/csv")
        t2.download_button("Stores template", make_stores(demo).to_csv(index=False), file_name="stores_template.csv", mime="text/csv")
        t3.download_button("Weekly template", make_weekly(demo).to_csv(index=False), file_name="weekly_template.csv", mime="text/csv")
        t4.download_button("Hourly template", make_hourly(demo).round(1).to_csv(index=False), file_name="hourly_template.csv", mime="text/csv")


def page_about():
    st.title("Methodology")
    st.caption("How GeoPulse calculates what it shows, and what its limits are.")
    with st.expander("Where the data comes from", expanded=True):
        st.markdown(
            "- **Demo data:** visits, rent, weekly and hourly patterns are simulated for illustration.\n"
            "- **Your data:** upload CSV files on the Your data page and every page uses them.\n"
            "- **Store locations:** turn on the OpenStreetMap option in the sidebar to use real shops and eateries. "
            "Map data © OpenStreetMap contributors (ODbL). OpenStreetMap does not include foot traffic, so visits stay simulated until you upload your own."
        )
    with st.expander("Site score"):
        st.markdown(
            "Each factor is scaled from 0 to 1 across the areas, then combined with the weights you set: "
            "**demand** (visits), **under-served gap** (visits per store) and the **baseline opportunity score**. "
            "The result is shown out of 100."
        )
    with st.expander("Where to open"):
        st.markdown(
            "For the chosen business type, each area is scored on visits, the gap in existing stores of that type "
            "(visits divided by stores plus one) and rent. The rent budget sets the weights: Low is 35 / 35 / 30, "
            "Medium is 45 / 40 / 15 and High is 50 / 50 / 0 for demand, gap and affordability. "
            "If you do not upload a Rent Index, it is estimated from visits and is only a rough guide."
        )
    with st.expander("Catchment"):
        st.markdown(
            "Stores are counted inside a circle around the point you click, using straight-line distance. "
            "Visits are summed for areas whose center is inside the circle. Areas are not split by partial overlap."
        )
    with st.expander("Forecast"):
        st.markdown(
            "Weekly visits are fitted with a ridge regression on a trend term, plus yearly seasonal terms when there are at least 40 weeks of history. "
            "The last weeks are held out to measure error (MAPE) against a last-value baseline and a linear trend, "
            "and the model with the lowest error is used. The shaded band is an 80% range based on in-sample error."
        )
    with st.expander("Limits"):
        st.markdown(
            "Straight-line distances ignore roads and barriers. Projections assume the recent pattern continues and do not know about "
            "new openings, closures or events. Treat results as a starting point for site visits, not a final decision."
        )


# =====================================================================
# APP SHELL
# =====================================================================
def password_gate() -> None:
    """Optional login. Set APP_PASSWORD in Streamlit secrets to turn it on."""
    try:
        password = st.secrets.get("APP_PASSWORD")
    except Exception:
        password = None
    if not password or st.session_state.get("authed"):
        return
    st.title("GeoPulse")
    st.caption("Enter the password to continue.")
    entered = st.text_input("Password", type="password")
    if st.button("Sign in"):
        if hmac.compare_digest(str(entered), str(password)):
            st.session_state["authed"] = True
            st.rerun()
        else:
            st.error("That password is not correct.")
    st.stop()


def reset_filters() -> None:
    for k in ("f_areas", "f_cats", "f_window"):
        st.session_state.pop(k, None)


def build_context() -> dict:
    sb = st.sidebar
    up = st.session_state.get("upload", {})
    sb.divider()
    sb.subheader("Data")
    use_osm = sb.toggle(
        "Real stores (OpenStreetMap)", key="use_osm", disabled="stores" in up,
        help="Replaces simulated stores with real shops and eateries. Needs an internet connection.",
    )
    data = load_data(bool(use_osm) and "stores" not in up)
    for note in data["notes"]:
        sb.warning(note)

    sb.subheader("Filters")
    opts_a = list(data["areas"]["Area"])
    opts_c = sorted(data["stores"]["Category"].unique()) or list(CATS)
    st.session_state["f_areas"] = [a for a in st.session_state.get("f_areas", opts_a) if a in opts_a] or opts_a
    st.session_state["f_cats"] = [c for c in st.session_state.get("f_cats", opts_c) if c in opts_c] or opts_c
    st.session_state.setdefault("f_window", 52)
    f_areas = sb.multiselect("Areas", opts_a, key="f_areas")
    f_cats = sb.multiselect("Store categories", opts_c, key="f_cats")
    window = sb.select_slider("Time window", options=[12, 26, 52], key="f_window", format_func=lambda w: f"Last {w} weeks")
    sb.button("Reset filters", on_click=reset_filters)

    areas = data["areas"][data["areas"]["Area"].isin(f_areas)].copy()
    stores = data["stores"][data["stores"]["Area"].isin(f_areas) & data["stores"]["Category"].isin(f_cats)].reset_index(drop=True)
    areas["Retail Stores"] = areas["Area"].map(stores.groupby("Area").size()).fillna(0).astype(int)

    weekly = data["weekly"][data["weekly"]["Area"].isin(f_areas)]
    if not weekly.empty:
        cutoff = sorted(weekly["Week"].unique())[-window:][0]
        weekly = weekly[weekly["Week"] >= cutoff]
    hourly = data["hourly"][data["hourly"]["Area"].isin(f_areas)]

    sb.caption("Map data © OpenStreetMap contributors")
    return {"areas": areas.reset_index(drop=True), "stores": stores, "weekly": weekly, "hourly": hourly,
            "mode": data["mode"], "store_src": data["store_src"]}


password_gate()

pg = st.navigation(
    {
        "Explore": [
            st.Page(page_overview, title="Overview", icon=":material/dashboard:", default=True),
            st.Page(page_heatmap, title="Mobility heatmap", icon=":material/map:", url_path="heatmap"),
            st.Page(page_mobility, title="Customer mobility", icon=":material/schedule:", url_path="mobility"),
            st.Page(page_competitors, title="Competitors", icon=":material/storefront:", url_path="competitors"),
        ],
        "Decide": [
            st.Page(page_where, title="Where to open", icon=":material/pin_drop:", url_path="where-to-open"),
            st.Page(page_catchment, title="Catchment", icon=":material/radar:", url_path="catchment"),
            st.Page(page_retail, title="Retail intelligence", icon=":material/leaderboard:", url_path="retail-intelligence"),
            st.Page(page_forecast, title="Forecast", icon=":material/trending_up:", url_path="forecast"),
        ],
        "Share": [
            st.Page(page_reports, title="Reports", icon=":material/description:", url_path="reports"),
        ],
        "Data": [
            st.Page(page_data, title="Your data", icon=":material/upload_file:", url_path="your-data"),
            st.Page(page_about, title="Methodology", icon=":material/info:", url_path="methodology"),
        ],
    }
)

CTX = build_context()
if CTX["areas"].empty:
    st.warning("No areas are selected. Choose at least one area in the sidebar.")
    st.stop()

pg.run()

st.divider()
st.caption("GeoPulse | Retail location intelligence for Guwahati")
