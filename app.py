import hmac
import html
import io
import os
import re

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import folium
import requests
import streamlit as st
from folium.plugins import HeatMap
from sklearn.cluster import KMeans
from sklearn.linear_model import Ridge
from sklearn.neighbors import BallTree
from streamlit_folium import st_folium

st.set_page_config(page_title="GeoPulse | Retail Location Intelligence", page_icon="🌍", layout="wide", initial_sidebar_state="expanded")

# =====================================================================
# DESIGN TOKENS — clean light analytics theme
# =====================================================================
INK = "#101828"
MIST = "#F6F8FB"
PAPER = "#FFFFFF"
LINE = "#E4E8EF"
TEXT = "#101828"
MUTED = "#667085"
TEA = "#14B8A6"
RIVER = "#2563EB"
GAMOSA = "#EF4444"
GOLD = "#F59E0B"
PLUM = "#8B5CF6"
SERIES = [RIVER, TEA, GOLD, PLUM, GAMOSA]

CATS = {"Grocery": TEA, "Fashion": PLUM, "Electronics": RIVER, "Food & Beverage": GOLD}
EXTRA_COLORS = ["#64748B", "#A16207", "#0F766E", "#BE185D", "#65A30D"]
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
AREA_COLS = ["Area", "Latitude", "Longitude", "Visits", "Retail Stores", "Opportunity Score", "Rent Index"]
STORE_COLS = ["Store", "Area", "Category", "Latitude", "Longitude"]

# Streamlit 1.50+ replaced use_container_width with width="stretch".
_ver = tuple(int(p) for p in st.__version__.split(".")[:2] if p.isdigit())
STRETCH = {"width": "stretch"} if _ver >= (1, 50) else {"use_container_width": True}

pio.templates["geopulse"] = go.layout.Template(layout=dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", colorway=SERIES,
    font=dict(family="Inter, sans-serif", color=TEXT),
    xaxis=dict(gridcolor="#EEF1F6", zeroline=False, linecolor=LINE),
    yaxis=dict(gridcolor="#EEF1F6", zeroline=False, linecolor=LINE)))
pio.templates.default = "plotly_white+geopulse"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, .stApp, .stApp p, .stApp label, .stApp li, .stApp button, .stApp input, .stApp textarea { font-family: 'Inter', sans-serif; }
#MainMenu, footer, .stDeployButton { visibility: hidden; }
html { scroll-behavior: smooth; }
.stApp { background: #F6F8FB; color: #101828; }
[data-testid="stHeader"] { height: 2.65rem !important; min-height: 2.65rem !important; background: rgba(255,255,255,.92) !important; backdrop-filter: blur(8px); border-bottom: 1px solid #E4E8EF; }
[data-testid="stHeader"] a, [data-testid="stHeader"] button p, [data-testid="stHeader"] span { color: #344054 !important; }
.block-container { padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1500px; }
.stApp h1 { font-weight: 700; font-size: clamp(1.7rem, 2.6vw, 2.2rem); letter-spacing: -0.03em; color: #101828; }
.stApp h2, .stApp h3 { font-weight: 650; letter-spacing: -0.02em; color: #101828; }
.stApp [data-testid="stMarkdownContainer"] p, .stApp [data-testid="stMarkdownContainer"] li, .stApp [data-testid="stWidgetLabel"] p { color: #344054; }
.stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] p { color: #667085 !important; }
:focus-visible { outline: 2px solid #2563EB !important; outline-offset: 2px; border-radius: 6px; }
::-webkit-scrollbar { width: 10px; height: 10px; } ::-webkit-scrollbar-thumb { background: #D0D5DD; border-radius: 8px; } ::-webkit-scrollbar-track { background: transparent; }
/* Sidebar: white, quiet, with a clear active page */
[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E4E8EF; }
[data-testid="stSidebar"] * { color: #344054; }
[data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding-top: 1.1rem; }
[data-testid="stSidebar"] hr { border-color: #E4E8EF; }
[data-testid="stSidebar"] [data-baseweb="select"] > div, [data-testid="stSidebar"] [data-baseweb="input"] > div { background: #F9FAFB; border: 1px solid #D0D5DD; }
[data-testid="stSidebarNav"] { padding: .35rem .55rem .75rem; }
[data-testid="stSidebarNav"] a { border: 1px solid transparent !important; border-radius: 10px !important; padding: .5rem .7rem !important; margin: .1rem 0 !important; transition: background .15s ease; }
[data-testid="stSidebarNav"] a:hover { background: #F2F4F7 !important; }
[data-testid="stSidebarNav"] a[aria-current="page"] { background: #EFF4FF !important; box-shadow: inset 3px 0 0 #2563EB; }
[data-testid="stSidebarNav"] a[aria-current="page"] span, [data-testid="stSidebarNav"] a[aria-current="page"] p { color: #1D4ED8 !important; }
[data-testid="stSidebarNav"] span, [data-testid="stSidebarNav"] p { font-weight: 550 !important; }
/* Cards */
[data-testid="stMetric"] { background: #FFFFFF; padding: 1rem 1.15rem; border-radius: 14px; border: 1px solid #E4E8EF; box-shadow: 0 1px 2px rgba(16,24,40,.05); min-height: 108px; }
[data-testid="stMetricLabel"] p { color: #667085 !important; font-weight: 550; }
[data-testid="stMetricValue"] { color: #101828; font-weight: 700; font-variant-numeric: tabular-nums; font-size: clamp(1.5rem, 2.2vw, 2rem); }
[data-testid="stMetricDelta"] { color: #12B76A !important; }
[class*="st-key-panel_"] { background: #FFFFFF; border: 1px solid #E4E8EF !important; border-radius: 14px !important; padding: 1.05rem 1.2rem !important; box-shadow: 0 1px 2px rgba(16,24,40,.05); }
.gp-panel-title { color: #101828; font-size: 1rem; font-weight: 650; margin: 0 0 .7rem; }
[data-testid="stAlert"] { background: #EFF4FF; border: 1px solid #C7D7FE; border-radius: 12px; }
[data-testid="stAlert"] * { color: #1D3A8A !important; }
[data-testid="stExpander"] { background: #FFFFFF; border: 1px solid #E4E8EF; border-radius: 12px; }
[data-testid="stExpander"] summary p { color: #101828 !important; font-weight: 600; }
[data-testid="stDataFrame"] { border: 1px solid #E4E8EF; border-radius: 12px; overflow: hidden; }
/* Controls */
.stMain .stButton button, .stMain .stDownloadButton button { background: #2563EB; color: #FFFFFF; border: 0; border-radius: 10px; font-weight: 600; box-shadow: 0 1px 2px rgba(16,24,40,.1); transition: background .15s ease; }
.stMain .stButton button:hover, .stMain .stDownloadButton button:hover { background: #1D4ED8; color: #FFFFFF; }
.stMain .stButton button p, .stMain .stDownloadButton button p { color: #FFFFFF !important; }
[data-testid="stSidebar"] .stButton button { background: #FFFFFF; border: 1px solid #D0D5DD; }
[data-baseweb="tab-list"] { gap: .25rem; border-bottom: 1px solid #E4E8EF; }
button[data-baseweb="tab"] { background: transparent; border-radius: 8px 8px 0 0; }
button[data-baseweb="tab"] p { color: #667085 !important; font-weight: 600; }
button[data-baseweb="tab"][aria-selected="true"] { background: #EFF4FF; }
button[data-baseweb="tab"][aria-selected="true"] p { color: #1D4ED8 !important; }
.gp-takeaway { background: #EFF4FF; border: 1px solid #C7D7FE; border-radius: 12px; padding: .7rem 1rem; margin: .4rem 0 .9rem; color: #1D3A8A; font-size: .95rem; font-weight: 500; }
.gp-guide-title { color: #101828; font-weight: 650; margin: .2rem 0 .4rem; }
[data-testid="stPageLink"] a { background: #FFFFFF; border: 1px solid #E4E8EF; border-radius: 12px; padding: .8rem 1rem; box-shadow: 0 1px 2px rgba(16,24,40,.05); transition: border-color .15s ease, background .15s ease; }
[data-testid="stPageLink"] a:hover { border-color: #2563EB; background: #EFF4FF; }
[data-testid="stPageLink"] a p { color: #1D4ED8 !important; font-weight: 600; }
/* Brand, hero, badges */
.gp-brand { text-align: left; padding: .3rem .6rem 1rem; }
.gp-logo { font-size: 1.8rem; line-height: 1; }
.gp-brand-name { color: #101828; font-size: 1.35rem; font-weight: 700; letter-spacing: -.03em; margin-top: .3rem; }
.gp-brand-sub { color: #667085; font-size: .78rem; line-height: 1.35; margin-top: .2rem; }
.gp-hero-wrap { padding: .2rem 0 1rem; }
.gp-hero { font-size: clamp(1.8rem, 3vw, 2.4rem); font-weight: 700; letter-spacing: -.035em; line-height: 1.15; color: #101828; margin: 0 0 .4rem; }
.gp-hero span { color: #2563EB; }
.gp-sub { color: #667085; font-size: 1rem; margin: 0; }
.gp-badges { margin: .6rem 0 .25rem; }
.gp-badge { display: inline-block; padding: .2rem .65rem; margin: 0 .35rem .25rem 0; border: 1px solid #E4E8EF; border-radius: 999px; font-size: .75rem; color: #475467; background: #FFFFFF; }
.gp-badge.live { border-color: #A6F4C5; color: #067647; background: #ECFDF3; }
.gp-insight { color: #475467; font-size: .9rem; line-height: 1.5; margin: .4rem 0; }
.gp-insight strong { color: #1D4ED8; }
.gp-kpi-icon { display: inline-flex; width: 2.6rem; height: 2.6rem; align-items: center; justify-content: center; border-radius: 12px; background: #EFF4FF; color: #2563EB; font-size: 1.4rem; margin-right: .65rem; }
.gp-map-note { color: #667085; font-size: .75rem; margin-top: .3rem; }
@media(max-width:800px){ .block-container{ padding-top: 1.2rem; } .stApp h1{ font-size: 1.6rem; } }
@media (prefers-reduced-motion: reduce){ * { transition: none !important; scroll-behavior: auto !important; } }
</style>
"""
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
        font=dict(family="Inter, sans-serif", color=TEXT),
        margin=dict(l=10, r=10, t=48, b=12),
        height=height,
        title_font=dict(size=15),
        colorway=SERIES,
    )
    fig.update_xaxes(gridcolor="#EEF1F6", zeroline=False, color=MUTED)
    fig.update_yaxes(gridcolor="#EEF1F6", zeroline=False, color=MUTED)
    return fig


def bar_chart(df, x, y, title):
    top = df[y].max()
    fig = px.bar(df, x=x, y=y, title=title)
    fig.update_traces(marker_color=[RIVER if v == top else "#BFD3FB" for v in df[y]])
    fig.update_xaxes(title=None)
    return style(fig)


def show(fig) -> None:
    st.plotly_chart(fig, theme=None, **STRETCH)


def table(df) -> None:
    st.dataframe(df, hide_index=True, **STRETCH)


def panel(title: str):
    """A bordered card that really wraps the widgets drawn inside it."""
    key = "panel_" + re.sub(r"\W+", "_", title.lower()).strip("_")
    try:
        box = st.container(border=True, key=key)
    except TypeError:  # older Streamlit without container keys
        box = st.container(border=True)
    box.markdown(f'<div class="gp-panel-title">{html.escape(title)}</div>', unsafe_allow_html=True)
    return box


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


def takeaway(text: str) -> None:
    """One plain-language sentence that says what the chart below shows."""
    st.markdown(f'<div class="gp-takeaway">💡 {text}</div>', unsafe_allow_html=True)


def guided_start() -> None:
    st.markdown('<div class="gp-guide-title">What do you want to do?</div>', unsafe_allow_html=True)
    options = [("Where to open", "Find a location", ":material/pin_drop:"),
               ("Compare areas", "Compare areas", ":material/compare_arrows:"),
               ("Peak hours", "See peak hours", ":material/access_time:")]
    for col, (title, label, icon) in zip(st.columns(3), options):
        with col:
            try:
                st.page_link(PAGE_BY_TITLE[title], label=label, icon=icon, **STRETCH)
            except TypeError:
                st.page_link(PAGE_BY_TITLE[title], label=label, icon=icon)


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
    areas, weekly, stores = CTX["areas"], CTX["weekly"], CTX["stores"]
    scored = score_areas(areas)
    lead = scored.iloc[0]
    total_visits = float(areas["Visits"].sum())
    total_stores = int(areas["Retail Stores"].sum())
    avg_score = float(areas["Opportunity Score"].mean())

    # Header and source indicators
    st.markdown(
        '<div class="gp-hero-wrap"><div class="gp-hero">Welcome to <span>GeoPulse</span></div>'
        '<p class="gp-sub">Hyper-local retail intelligence for Guwahati, Assam</p></div>',
        unsafe_allow_html=True,
    )
    mode_badges = f'<span class="gp-badge {"live" if CTX["mode"] == "Your data" else ""}">{html.escape(CTX["mode"])}</span>'
    mode_badges += f'<span class="gp-badge">Store source: {html.escape(CTX["store_src"])}</span>'
    mode_badges += f'<span class="gp-badge">{len(areas)} areas selected</span>'
    st.markdown(f'<div class="gp-badges">{mode_badges}</div>', unsafe_allow_html=True)
    demo_note()
    guided_start()

    # KPI row — values always come from the active filters and loaded data.
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Typical daily visits", f"{total_visits:,.0f}", help="Sum of visits across the selected areas")
    k2.metric("Retail stores", f"{total_stores:,}", help="Stores in the selected areas and categories")
    k3.metric("Areas analyzed", f"{len(areas):,}")
    k4.metric("Average opportunity", f"{avg_score:.1f} / 100")

    left, right = st.columns([0.92, 1.55], gap="large")
    with left:
        with panel("Retail category distribution"):
            if not stores.empty:
                cat = stores.groupby("Category").size().reset_index(name="Stores").sort_values("Stores", ascending=False)
                fig = px.pie(cat, names="Category", values="Stores", hole=.62, color="Category",
                             color_discrete_map={**CATS, **{c: EXTRA_COLORS[i % len(EXTRA_COLORS)] for i, c in enumerate(cat["Category"]) if c not in CATS}})
                fig.update_traces(textposition="inside", textinfo="percent", hole=.62, marker=dict(line=dict(color="#FFFFFF", width=2)))
                fig.update_layout(showlegend=True, legend=dict(orientation="h", x=.5, xanchor="center", y=-.04, font=dict(size=11)),
                                  margin=dict(l=0,r=0,t=4,b=0), height=300, annotations=[dict(text=f"{len(stores):,}<br><sup>Stores</sup>", x=.5, y=.5, showarrow=False, font=dict(size=19,color=TEXT))])
                st.plotly_chart(fig, theme=None, **STRETCH)
            else:
                st.info("No store category data is available for the current filters.")

        with panel("Top retail areas"):
            top = scored.sort_values("Visits", ascending=True).tail(6)
            fig = px.bar(top, x="Visits", y="Area", orientation="h", text="Visits")
            fig.update_traces(marker_color=TEA, texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)
            fig.update_layout(showlegend=False, height=280, margin=dict(l=0,r=25,t=4,b=0), yaxis_title=None, xaxis_title=None)
            st.plotly_chart(fig, theme=None, **STRETCH)

    with right:
        with panel("Guwahati retail opportunity map"):
            center = [float(areas["Latitude"].mean()), float(areas["Longitude"].mean())]
            m = folium.Map(location=center, zoom_start=12, tiles="OpenStreetMap", control_scale=True)
            max_visits = max(float(areas["Visits"].max()), 1.0)
            heat = [[float(r.Latitude), float(r.Longitude), float(r.Visits) / max_visits] for r in areas.itertuples()]
            HeatMap(heat, radius=27, blur=20, min_opacity=.35,
                    gradient={0.25: "#00C9D8", 0.5: "#28D86B", 0.75: "#FFD43B", 1.0: "#FF3D4F"}).add_to(m)
            for r in areas.itertuples():
                popup = (f"<b>{html.escape(str(r.Area))}</b><br>Visits: {float(r.Visits):,.0f}"
                         f"<br>Stores: {int(r._5) if hasattr(r, '_5') else int(getattr(r, '_5', 0))}"
                         f"<br>Opportunity: {float(r._6) if hasattr(r, '_6') else 0:.1f}/100")
                folium.CircleMarker(location=[float(r.Latitude), float(r.Longitude)], radius=7,
                                    color="#FFFFFF", weight=1.5, fill=True, fill_color="#087FF5",
                                    fill_opacity=.95, tooltip=str(r.Area), popup=popup).add_to(m)
            st_folium(m, key="overview_retail_map", height=390, use_container_width=True, returned_objects=[])
            st.markdown('<div class="gp-map-note">Heat intensity represents visits in the selected area set · Map data © OpenStreetMap contributors</div>', unsafe_allow_html=True)

        insight_col, compare_col = st.columns([1.05, .95], gap="medium")
        with insight_col:
            with panel("Retail insights"):
                st.markdown(f'<p class="gp-insight">✦ <strong>{html.escape(str(lead["Area"]))}</strong> currently leads the selected areas with an opportunity score of <strong>{float(lead["Opportunity Score"]):.1f}/100</strong>.</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="gp-insight">✦ Highest typical daily visits: <strong>{float(areas["Visits"].max()):,.0f}</strong>.</p>', unsafe_allow_html=True)
                if not stores.empty:
                    popular = stores["Category"].value_counts().idxmax()
                    share = stores["Category"].value_counts(normalize=True).max() * 100
                    st.markdown(f'<p class="gp-insight">✦ Most represented category: <strong>{html.escape(str(popular))}</strong> ({share:.1f}% of mapped stores).</p>', unsafe_allow_html=True)
                else:
                    st.markdown('<p class="gp-insight">✦ Add store data to reveal category patterns.</p>', unsafe_allow_html=True)
                st.markdown('<p class="gp-insight">✦ Use the heatmap and Where to open pages to explore location-level opportunities.</p>', unsafe_allow_html=True)
        with compare_col:
            with panel("Area comparison"):
                compare = areas.sort_values("Visits", ascending=False).head(5).sort_values("Visits")
                fig = go.Figure()
                fig.add_trace(go.Bar(name="Visits", x=compare["Area"], y=compare["Visits"], marker_color=RIVER))
                fig.add_trace(go.Bar(name="Stores", x=compare["Area"], y=compare["Retail Stores"], marker_color=TEA, yaxis="y2"))
                fig.update_layout(barmode="group", height=245, margin=dict(l=0,r=0,t=8,b=0),
                                  legend=dict(orientation="h", y=1.12, x=0), xaxis_title=None,
                                  yaxis=dict(title=None, gridcolor=LINE),
                                  yaxis2=dict(title=None, overlaying="y", side="right", showgrid=False))
                st.plotly_chart(fig, theme=None, **STRETCH)

    # Weekly trend remains available below the visual overview.
    if not weekly.empty:
        total = weekly.groupby("Week", as_index=False)["Visits"].sum()
        fig = px.area(total, x="Week", y="Visits", title="Weekly visit trend")
        fig.update_traces(line_color=RIVER, fillcolor="rgba(37,99,235,.12)")
        fig.update_xaxes(title=None)
        show(style(fig, 290))

    with st.expander("View area-level data"):
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
    takeaway(f"Visits peak around {peak_hour}:00 and {html.escape(str(daily.idxmax()))} is the busiest day. Weekend traffic is {html.escape(uplift)} versus weekdays.")

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
def page_compare():
    page_header("Compare areas", "Put two or three areas side by side before you decide.")
    demo_note()
    areas = CTX["areas"].set_index("Area")
    names = list(areas.index)
    pick = st.multiselect("Areas to compare", names, default=names[:3], max_selections=3)
    if len(pick) < 2:
        st.info("Pick at least two areas to compare.")
        return
    for col, n in zip(st.columns(len(pick)), pick):
        r = areas.loc[n]
        with col, panel(n):
            st.metric("Visits per day", f"{r['Visits']:,.0f}")
            st.metric("Retail stores", int(r["Retail Stores"]))
            st.metric("Opportunity score", f"{r['Opportunity Score']} / 100")
            st.metric("Rent index", int(r["Rent Index"]))
    best = areas.loc[pick, "Opportunity Score"].idxmax()
    cheap = areas.loc[pick, "Rent Index"].idxmin()
    takeaway(f"{html.escape(str(best))} has the highest opportunity score" + (f", and {html.escape(str(cheap))} has the lowest rent." if cheap != best else " and also the lowest rent."))
    metrics = ["Visits", "Retail Stores", "Opportunity Score", "Rent Index"]
    scaled = areas[metrics].apply(lambda s: 100 * s / max(s.max(), 1))
    fig = go.Figure()
    for i, n in enumerate(pick):
        v = scaled.loc[n].tolist()
        fig.add_trace(go.Scatterpolar(r=v + v[:1], theta=metrics + metrics[:1], name=n, fill="toself",
                                      line_color=SERIES[i], opacity=0.6))
    fig.update_layout(height=380, margin=dict(l=40, r=40, t=20, b=20), legend=dict(orientation="h", y=-0.1))
    with panel("Shape of each area (100 = highest among all areas)"):
        st.plotly_chart(fig, theme=None, **STRETCH)


def page_simulator():
    page_header("What-if simulator", "A rough estimate of what a new store could earn. Change the assumptions to test it.")
    demo_note()
    areas, stores = CTX["areas"].set_index("Area"), CTX["stores"]
    c1, c2 = st.columns(2)
    area = c1.selectbox("Area", list(areas.index))
    cat = c2.selectbox("Business type", sorted(stores["Category"].unique()) or list(CATS))
    s1, s2, s3 = st.columns(3)
    conv = s1.slider("Visitors who buy (%)", 1.0, 15.0, 4.0, 0.5)
    spend = s2.number_input("Average spend per customer (₹)", 50, 5000, 350, 25)
    cost = s3.number_input("Monthly running cost (₹)", 10000, 1000000, 120000, 5000)
    n = int(((stores["Area"] == area) & (stores["Category"] == cat)).sum())
    customers = areas.loc[area, "Visits"] / (n + 1) * conv / 100
    revenue = customers * spend * 30
    profit = revenue - cost
    breakeven = cost / (spend * 30)
    m = st.columns(4)
    m[0].metric("Customers per day", f"{customers:,.0f}")
    m[1].metric("Monthly revenue", f"₹{revenue:,.0f}")
    m[2].metric("Monthly profit", f"₹{profit:,.0f}")
    m[3].metric("Break-even customers/day", f"{breakeven:,.0f}")
    if profit >= 0:
        st.success(f"At these assumptions a {cat} store in {area} covers its costs, with {n} similar store(s) nearby today.")
    else:
        st.warning(f"At these assumptions a {cat} store in {area} would need about {breakeven:,.0f} customers a day to break even.")
    st.caption("Estimate only: it shares the area's daily visits equally between the existing stores of that type and the new one.")


def page_whitespace():
    page_header("Whitespace finder", "Spot business types that are missing in busy areas.")
    demo_note()
    areas, stores = CTX["areas"], CTX["stores"]
    cats = sorted(stores["Category"].unique())
    if not cats:
        st.info("There are no stores to analyze yet.")
        return
    cnt = stores.groupby(["Area", "Category"]).size().unstack(fill_value=0).reindex(index=areas["Area"], columns=cats, fill_value=0)
    visits0 = areas.set_index("Area")["Visits"]
    gap_cells = [(a, c) for a in cnt.index for c in cats if cnt.loc[a, c] == 0]
    if gap_cells:
        ga, gc = max(gap_cells, key=lambda t: visits0[t[0]])
        takeaway(f"Biggest opening: no {html.escape(gc)} store in {html.escape(ga)}, where about {visits0[ga]:,.0f} people visit on a typical day.")
    else:
        takeaway("Every category already has a store in every selected area, so look at crowding and rent instead.")
    fig = px.imshow(cnt, aspect="auto", text_auto=True, color_continuous_scale=["#FFFFFF", "#2563EB"])
    fig.update_layout(height=max(280, 60 * len(cnt)), coloraxis_showscale=False, margin=dict(l=10, r=10, t=10, b=10))
    with panel("Stores per area and category"):
        st.plotly_chart(fig, theme=None, **STRETCH)
    visits = areas.set_index("Area")["Visits"]
    gaps = pd.DataFrame([(a, c, visits[a]) for a in cnt.index for c in cats if cnt.loc[a, c] == 0],
                        columns=["Area", "Missing category", "Daily visits"])
    with panel("Biggest gaps (no store of this type, busiest areas first)"):
        if gaps.empty:
            st.write("Every selected category has at least one store in every selected area.")
        else:
            table(gaps.sort_values("Daily visits", ascending=False).head(10))


def page_peak():
    page_header("Peak hours", "The busiest hours of the week, to plan opening times and staffing.")
    demo_note()
    h = CTX["hourly"]
    h = h[h["Area"].isin(CTX["areas"]["Area"])]
    if h.empty:
        st.info("There is no hourly data for the selected areas.")
        return
    grid = h.pivot_table(index="Day", columns="Hour", values="Visits", aggfunc="sum").reindex(DAYS)
    top = grid.stack().sort_values(ascending=False).head(3)
    (d0, h0) = top.index[0]
    takeaway(f"The busiest slot of the week is {d0} at {h0:02d}:00. Staff up and keep stock ready for it.")
    fig = px.imshow(grid, aspect="auto", color_continuous_scale=["#EFF4FF", "#2563EB"], labels=dict(x="Hour of day", y="", color="Visits"))
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10))
    with panel("Visits by day and hour"):
        st.plotly_chart(fig, theme=None, **STRETCH)
    with panel("Top 3 busiest slots"):
        for (day, hour), v in top.items():
            st.markdown(f"**{day} {hour:02d}:00** – about {v:,.0f} visits")


def page_shortlist():
    page_header("Shortlist", "Save the areas you like, add notes, and download the list.")
    sl = st.session_state.setdefault("shortlist", {})
    areas = CTX["areas"]
    with st.form("add_short", clear_on_submit=True):
        c1, c2 = st.columns([1, 2])
        area = c1.selectbox("Area", list(areas["Area"]))
        note = c2.text_input("Note (optional)")
        if st.form_submit_button("Add to shortlist"):
            sl[area] = note
    saved = areas[areas["Area"].isin(sl)].copy()
    if saved.empty:
        st.info("Your shortlist is empty. Add an area above.")
        return
    saved["Note"] = saved["Area"].map(sl)
    table(saved)
    c1, c2 = st.columns(2)
    c1.download_button("Download shortlist (CSV)", saved.to_csv(index=False), "geopulse_shortlist.csv", "text/csv")
    drop = c2.multiselect("Remove areas", list(saved["Area"]))
    if drop and c2.button("Remove selected"):
        for a in drop:
            sl.pop(a, None)
        st.rerun()


def page_help():
    page_header("Help & FAQ", "Quick answers to common questions.")
    faq = {
        "What does the opportunity score mean?": "A 0 to 100 score that rewards busy areas where each store gets many visits. Higher means more room for a new store.",
        "Is the data real?": "By default, visits, rent and trends are simulated for illustration. Upload your own files on the Your data page to use real numbers.",
        "Where do the stores come from?": "Either simulated or, with the sidebar toggle on, real shops and eateries from OpenStreetMap.",
        "How do I use my own data?": "Open Your data, upload areas, stores, weekly or hourly CSV files, and the whole app switches to them.",
        "How do I save areas I like?": "Use the Shortlist page, then download the list as a CSV or include it in a report.",
        "How accurate is the forecast?": "It is a simple model tested on past weeks. See the Forecast page for its error and the Methodology page for details.",
    }
    for q, a in faq.items():
        with st.expander(q):
            st.write(a)


def page_quality():
    page_header("Data quality", "What was checked and cleaned before any chart is drawn.")
    sets = {"Areas": CTX["areas"], "Stores": CTX["stores"], "Hourly visits": CTX["hourly"], "Weekly visits": CTX["weekly"]}
    rows = [{"Dataset": n, "Rows": len(d), "Columns": d.shape[1], "Missing values": int(d.isna().sum().sum()),
             "Duplicate rows": int(d.duplicated().sum())} for n, d in sets.items()]
    with panel("Dataset health"):
        table(pd.DataFrame(rows))
    a, s = CTX["areas"], CTX["stores"]
    checks = [
        ("Area coordinates fall inside Assam", bool(a["Latitude"].between(24, 28).all() and a["Longitude"].between(89.5, 96.5).all())),
        ("No negative or zero visit counts", bool((a["Visits"] > 0).all())),
        ("Every area name is unique", bool(a["Area"].is_unique)),
        ("Every store is linked to an area", bool(s.empty or s["Area"].notna().all())),
        ("Hourly data uses hours 0 to 23 only", bool(CTX["hourly"].empty or CTX["hourly"]["Hour"].between(0, 23).all())),
    ]
    with panel("Automatic checks"):
        for label, ok in checks:
            st.markdown(f"{'✅' if ok else '⚠️'} {label}")
    with panel("Cleaning rules applied on load"):
        st.markdown(
            "- Column names are matched to the expected names, so small spelling differences still load.\n"
            "- Numbers are converted to numeric type, and rows without a name, location or visit count are dropped.\n"
            "- Duplicate area names are removed, keeping the first.\n"
            "- Day names are standardised to three letters and hours are limited to 0 to 23.\n"
            "- Each store is assigned to the nearest area within 3 km."
        )
    with panel("Data dictionary"):
        table(pd.DataFrame([
            ("Area", "Neighbourhood name", "text", "Areas file"),
            ("Latitude / Longitude", "Centre point of the area", "degrees", "Areas file"),
            ("Visits", "Typical daily visits", "people per day", "Areas file or simulated"),
            ("Retail Stores", "Stores in the area", "count", "Areas or stores file"),
            ("Opportunity Score", "Demand and gap score", "0 to 100", "Calculated or supplied"),
            ("Rent Index", "Relative rent level", "index", "Areas file or simulated"),
            ("Category", "Business type of a store", "text", "Stores file or OpenStreetMap"),
            ("Day / Hour", "Weekday and hour of day", "Mon to Sun / 0 to 23", "Hourly file"),
        ], columns=["Column", "Meaning", "Unit", "Source"]))
    with panel("Download cleaned data"):
        for col, (n, d) in zip(st.columns(len(sets)), sets.items()):
            col.download_button(n, d.to_csv(index=False), f"geopulse_{n.lower().replace(' ', '_')}.csv", "text/csv", key=f"dl_{n}")


def page_insights():
    page_header("Key insights", "The main findings from the data in the current filters, in plain language.")
    demo_note()
    areas, stores, hourly = CTX["areas"], CTX["stores"], CTX["hourly"]
    scored = score_areas(areas)
    top = areas.sort_values("Visits", ascending=False).iloc[0]
    share = top["Visits"] / areas["Visits"].sum()
    items = [
        f"**{top['Area']}** is the busiest area with about {top['Visits']:,.0f} visits a day, {share:.0%} of all visits in the selection.",
        f"**{scored.iloc[0]['Area']}** ranks first on the combined demand and gap score.",
    ]
    if not stores.empty:
        counts = stores["Category"].value_counts()
        items.append(f"**{counts.index[-1]}** is the least served category with {counts.iloc[-1]} stores, while **{counts.index[0]}** has the most ({counts.iloc[0]}).")
    h = hourly[hourly["Area"].isin(areas["Area"])]
    if not h.empty:
        slot = h.groupby(["Day", "Hour"])["Visits"].sum().idxmax()
        items.append(f"The busiest slot of the week is **{slot[0]} at {slot[1]:02d}:00**.")
        daily = h.groupby("Day")["Visits"].sum().reindex(DAYS)
        if daily[DAYS[:5]].mean() > 0:
            items.append(f"Weekend days see **{daily[DAYS[5:]].mean() / daily[DAYS[:5]].mean() - 1:+.0%}** visits compared with weekdays.")
    if len(areas) >= 3:
        r = areas["Visits"].corr(areas["Rent Index"])
        word = "strongly" if abs(r) > 0.7 else "moderately" if abs(r) > 0.4 else "only weakly"
        items.append(f"Rent and visits are {word} linked (correlation {r:.2f}), so {'busier areas tend to cost more' if r > 0 else 'busy areas are not always the expensive ones'}.")
    with panel("Findings"):
        for i, t in enumerate(items, 1):
            st.markdown(f"{i}. {t}")
    st.download_button("Download findings (Markdown)", "# GeoPulse key insights\n\n" + "\n".join(f"{i}. {t}" for i, t in enumerate(items, 1)),
                       "geopulse_insights.md", "text/markdown")


PERIODS = {"Morning (06-10)": (6, 10), "Midday (11-15)": (11, 15), "Evening (17-21)": (17, 21), "All day": (0, 24)}


@st.cache_data(show_spinner="Reading GPS file...")
def load_gps(raw: bytes) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(raw), usecols=["DeviceID", "Latitude", "Longitude", "Timestamp"], dtype={"DeviceID": "string"})
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    df = df.dropna().drop_duplicates(["DeviceID", "Timestamp"])
    df["Hour"] = df["Timestamp"].dt.hour
    return df


def store_footfall(d: pd.DataFrame, stores: pd.DataFrame, radius_m: float = 300):
    """Unique devices seen within radius_m of each store, and how many devices were near 2+ stores."""
    tree = BallTree(np.radians(d[["Latitude", "Longitude"]].values), metric="haversine")
    codes = pd.factorize(d["DeviceID"])[0]
    hits = tree.query_radius(np.radians(stores[["Latitude", "Longitude"]].values), r=radius_m / 6371000)
    per_store = [np.unique(codes[ix]) for ix in hits]
    table_df = pd.DataFrame({"Store": stores["Store"].values, "Devices": [len(u) for u in per_store]})
    seen = np.bincount(np.concatenate(per_store), minlength=len(np.unique(codes))) if per_store else np.array([])
    return table_df.sort_values("Devices", ascending=False), int((seen >= 1).sum()), int((seen >= 2).sum())


def page_gps():
    page_header("GPS movement", "Where simulated customers move, and which places and stores are busiest.")
    up = st.file_uploader("Upload gps_pings.csv (DeviceID, Latitude, Longitude, Timestamp)", type="csv")
    raw = up.getvalue() if up else None
    if raw is None:
        for p in ("gps_pipeline/gps_pings.csv", "sample_gps_pings.csv"):
            if os.path.exists(p):
                with open(p, "rb") as f:
                    raw = f.read()
                st.caption(f"No upload yet, showing {p}.")
                break
    if raw is None:
        st.info("Upload a GPS file to begin. You can generate one with gps_pipeline/generate_gps_data.py.")
        return
    try:
        df = load_gps(raw)
    except Exception as e:
        st.error(f"Could not read that file. Check the four column names. ({e})")
        return
    label = st.radio("Time of day", list(PERIODS), horizontal=True)
    lo, hi = PERIODS[label]
    d = df[(df["Hour"] >= lo) & (df["Hour"] < hi)]
    if d.empty:
        st.info("There are no pings in this time window.")
        return
    c = st.columns(3)
    c[0].metric("Pings", f"{len(d):,}")
    c[1].metric("Devices", f"{d['DeviceID'].nunique():,}")
    c[2].metric("Window", label.split(" (")[0])
    g = d.assign(Lat=(d["Latitude"] / 0.0025).round() * 0.0025, Lon=(d["Longitude"] / 0.0025).round() * 0.0025)
    hot = g.groupby(["Lat", "Lon"])["DeviceID"].nunique().sort_values(ascending=False).head(8).reset_index(name="Devices")
    takeaway(f"The busiest spot in the {label.split(' (')[0].lower()} is near {hot.iloc[0]['Lat']:.4f}, {hot.iloc[0]['Lon']:.4f}, seen by {hot.iloc[0]['Devices']:,} different devices.")
    m = folium.Map(location=[d["Latitude"].mean(), d["Longitude"].mean()], zoom_start=12, tiles="OpenStreetMap")
    HeatMap(d.sample(min(len(d), 30000), random_state=1)[["Latitude", "Longitude"]].values.tolist(), radius=9, blur=12).add_to(m)
    left, right = st.columns([3, 2])
    with left, panel("Movement density"):
        st_folium(m, height=440, returned_objects=[], use_container_width=True)
    with right, panel("Busiest 250 m cells"):
        table(hot.rename(columns={"Lat": "Latitude", "Lon": "Longitude"}))
    hours = df.groupby("Hour").size().reset_index(name="Pings")
    hours["Selected"] = hours["Hour"].between(lo, hi - 1)
    fig = px.bar(hours, x="Hour", y="Pings", color="Selected", color_discrete_map={True: RIVER, False: "#BFD3FB"})
    fig.update_layout(height=280, showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
    with panel("Pings by hour of day"):
        st.plotly_chart(fig, theme=None, **STRETCH)
    stores = CTX["stores"]
    if not stores.empty:
        with st.spinner("Matching pings to stores..."):
            foot, any_n, multi_n = store_footfall(d, stores[["Store", "Latitude", "Longitude"]])
        with panel("Footfall at stores (devices within 300 m)"):
            if any_n == 0:
                st.write("No GPS pings fall near the selected stores in this window.")
            else:
                table(foot.head(10))
                st.caption(f"{multi_n:,} of {any_n:,} devices ({multi_n / any_n:.0%}) were near two or more stores.")


def page_clusters():
    page_header("Area clusters", "Groups of areas with similar traffic, rent and competition.")
    demo_note()
    a = CTX["areas"].copy()
    if len(a) < 3:
        st.info("Select at least 3 areas to group them.")
        return
    kmax = min(5, len(a) - 1)
    k = st.slider("Number of groups", 2, kmax, min(3, kmax)) if kmax > 2 else 2
    feats = ["Visits", "Retail Stores", "Rent Index", "Opportunity Score"]
    X = (a[feats] - a[feats].mean()) / a[feats].std(ddof=0).replace(0, 1)
    a["Group"] = KMeans(n_clusters=k, n_init=10, random_state=1).fit_predict(X)
    order = a.groupby("Group")["Visits"].mean().sort_values(ascending=False).index
    names = {g: f"Group {i + 1}" + (" (busiest)" if i == 0 else " (quietest)" if i == k - 1 else "") for i, g in enumerate(order)}
    a["Group"] = a["Group"].map(names)
    takeaway(f"{html.escape(', '.join(a[a['Group'] == names[order[0]]]['Area']))} form the busiest group, with about {a[a['Group'] == names[order[0]]]['Visits'].mean():,.0f} visits a day on average.")
    fig = px.scatter(a, x="Visits", y="Rent Index", size="Retail Stores", color="Group", hover_name="Area",
                     color_discrete_sequence=SERIES, size_max=36)
    fig.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10))
    with panel("Areas by visits and rent (bubble size = number of stores)"):
        st.plotly_chart(fig, theme=None, **STRETCH)
    with panel("Group averages"):
        table(a.groupby("Group")[feats].mean().round(1).reset_index().sort_values("Group"))


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
    sb.subheader("Data & sources")
    use_osm = sb.toggle(
        "Real stores (OpenStreetMap)", key="use_osm", disabled="stores" in up,
        help="Replaces simulated stores with real shops and eateries. Needs an internet connection.",
    )
    data = load_data(bool(use_osm) and "stores" not in up)
    for note in data["notes"]:
        sb.warning(note)

    sb.divider()
    sb.subheader("Dashboard filters")
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

    sb.divider()
    sb.caption("Guwahati, Assam · Map data © OpenStreetMap contributors")
    return {"areas": areas.reset_index(drop=True), "stores": stores, "weekly": weekly, "hourly": hourly,
            "mode": data["mode"], "store_src": data["store_src"]}


password_gate()

st.sidebar.markdown('<div class="gp-brand"><div class="gp-logo">🌐📍</div><div class="gp-brand-name">GeoPulse</div><div class="gp-brand-sub">Hyper-Local Retail<br>Mobility Analytics</div></div>', unsafe_allow_html=True)

NAV_PAGES = {
        "Explore": [
            st.Page(page_overview, title="Overview", icon=":material/dashboard:", default=True),
            st.Page(page_heatmap, title="Mobility heatmap", icon=":material/map:", url_path="heatmap"),
            st.Page(page_mobility, title="Customer mobility", icon=":material/schedule:", url_path="mobility"),
            st.Page(page_gps, title="GPS movement", icon=":material/route:", url_path="gps-movement"),
            st.Page(page_peak, title="Peak hours", icon=":material/access_time:", url_path="peak-hours"),
            st.Page(page_competitors, title="Competitors", icon=":material/storefront:", url_path="competitors"),
        ],
        "Analyze": [
            st.Page(page_catchment, title="Catchment", icon=":material/radar:", url_path="catchment"),
            st.Page(page_retail, title="Retail intelligence", icon=":material/leaderboard:", url_path="retail-intelligence"),
            st.Page(page_clusters, title="Area clusters", icon=":material/bubble_chart:", url_path="clusters"),
            st.Page(page_whitespace, title="Whitespace finder", icon=":material/grid_view:", url_path="whitespace"),
            st.Page(page_forecast, title="Forecast", icon=":material/trending_up:", url_path="forecast"),
        ],
        "Decide": [
            st.Page(page_where, title="Where to open", icon=":material/pin_drop:", url_path="where-to-open"),
            st.Page(page_compare, title="Compare areas", icon=":material/compare_arrows:", url_path="compare"),
            st.Page(page_simulator, title="What-if simulator", icon=":material/calculate:", url_path="simulator"),
        ],
        "Share": [
            st.Page(page_insights, title="Key insights", icon=":material/lightbulb:", url_path="insights"),
            st.Page(page_shortlist, title="Shortlist", icon=":material/bookmark:", url_path="shortlist"),
            st.Page(page_reports, title="Reports", icon=":material/description:", url_path="reports"),
        ],
        "Data": [
            st.Page(page_data, title="Your data", icon=":material/upload_file:", url_path="your-data"),
            st.Page(page_about, title="Methodology", icon=":material/info:", url_path="methodology"),
            st.Page(page_quality, title="Data quality", icon=":material/fact_check:", url_path="data-quality"),
            st.Page(page_help, title="Help & FAQ", icon=":material/help:", url_path="help"),
        ],
}
PAGE_BY_TITLE = {p.title: p for pages in NAV_PAGES.values() for p in pages}
try:
    pg = st.navigation(NAV_PAGES, position="sidebar")
except TypeError:  # Streamlit older than 1.46 has no top navigation
    pg = st.navigation(NAV_PAGES)

CTX = build_context()
if CTX["areas"].empty:
    st.warning("No areas are selected. Choose at least one area in the sidebar.")
    st.stop()

pg.run()

st.divider()
st.caption("GeoPulse | Retail location intelligence for Guwahati")
