import hmac
import html
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
from sklearn.linear_model import Ridge
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
    hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=LINE, font=dict(family="Inter, sans-serif", color=TEXT, size=12)),
    legend=dict(font=dict(size=12, color=MUTED)),
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
[data-testid="stHeader"] { background: rgba(255,255,255,.92) !important; backdrop-filter: blur(8px); border-bottom: 1px solid #E4E8EF; }
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

/* ---- v2 polish ---- */
:root { --gp-blue:#2563EB; --gp-line:#E4E8EF; --gp-shadow:0 1px 2px rgba(16,24,40,.05), 0 4px 12px rgba(16,24,40,.04); }
.stApp h1 { margin-bottom: .1rem; }
/* Brand mark */
.gp-brand { display:flex; align-items:center; gap:.7rem; padding:.2rem .6rem 1rem; }
.gp-mark { width:2.5rem; height:2.5rem; border-radius:12px; background:linear-gradient(135deg,#2563EB,#14B8A6); display:flex; align-items:center; justify-content:center; box-shadow:0 4px 10px rgba(37,99,235,.28); flex:none; }
.gp-mark svg { width:1.35rem; height:1.35rem; }
.gp-brand-name { margin-top:0; line-height:1.1; }
.gp-brand-sub { margin-top:.15rem; }
/* Sidebar section labels */
[data-testid="stSidebar"] h3 { font-size:.72rem !important; text-transform:uppercase; letter-spacing:.08em; color:#667085 !important; font-weight:650; margin-top:.2rem; }
[data-testid="stSidebarNav"] [data-testid="stNavSectionHeader"], [data-testid="stSidebarNav"] header { text-transform:uppercase; letter-spacing:.08em; font-size:.7rem; }
/* Hero */
.gp-hero-wrap { background:linear-gradient(135deg,#EFF4FF 0%,#F0FDFA 100%); border:1px solid #D6E2FB; border-radius:16px; padding:1.25rem 1.5rem; margin:.2rem 0 1rem; }
/* Metrics: lift on hover, tidy label */
[data-testid="stMetric"] { transition: box-shadow .15s ease, border-color .15s ease; }
[data-testid="stMetric"]:hover { border-color:#C7D7FE; box-shadow:var(--gp-shadow); }
[data-testid="stMetricLabel"] p { font-size:.82rem; text-transform:none; }
/* Where-to-open recommendation cards (were unstyled before) */
.gp-pick { background:#FFFFFF; border:1px solid #E4E8EF; border-radius:14px; padding:1rem 1.15rem 1.05rem; box-shadow:0 1px 2px rgba(16,24,40,.05); height:100%; position:relative; transition: box-shadow .15s ease, transform .15s ease; }
.gp-pick:hover { box-shadow:var(--gp-shadow); transform:translateY(-1px); }
.gp-pick.first { border-color:#2563EB; background:linear-gradient(180deg,#F5F8FF 0%,#FFFFFF 70%); box-shadow:0 0 0 3px rgba(37,99,235,.10); }
.gp-pick-top { display:inline-block; font-size:.7rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase; color:#475467; background:#F2F4F7; border-radius:999px; padding:.15rem .6rem; }
.gp-pick.first .gp-pick-top { color:#FFFFFF; background:#2563EB; }
.gp-name { font-size:1.2rem; font-weight:700; letter-spacing:-.02em; color:#101828; margin:.55rem 0 .1rem; }
.gp-score { font-size:2.1rem; font-weight:750; letter-spacing:-.03em; color:#101828; line-height:1.1; font-variant-numeric:tabular-nums; }
.gp-score span { font-size:.9rem; font-weight:600; color:#667085; margin-left:.2rem; }
.gp-why { color:#475467; font-size:.88rem; line-height:1.5; margin-top:.5rem; }
/* Empty state */
.gp-empty { text-align:center; padding:2rem 1rem; border:1.5px dashed #D0D5DD; border-radius:14px; background:#FFFFFF; }
.gp-empty .ico { font-size:1.8rem; }
.gp-empty .t { font-weight:650; color:#101828; margin:.35rem 0 .15rem; }
.gp-empty .d { color:#667085; font-size:.92rem; }
/* Filter summary chip in sidebar */
.gp-filter-chip { background:#EFF4FF; color:#1D4ED8 !important; border:1px solid #C7D7FE; border-radius:10px; padding:.45rem .7rem; font-size:.8rem; font-weight:550; margin:.2rem 0 .5rem; }
/* Footer */
.gp-footer { margin-top:2rem; padding-top:1rem; border-top:1px solid #E4E8EF; color:#667085; font-size:.8rem; display:flex; justify-content:space-between; flex-wrap:wrap; gap:.4rem; }
/* Inputs */
[data-baseweb="select"] > div, [data-baseweb="input"] > div { border-radius:10px !important; }
[data-testid="stRadio"] [role="radiogroup"] { gap:.4rem; }
/* Download buttons: secondary look so the primary action stands out */
.stMain .stDownloadButton button { background:#FFFFFF; color:#1D4ED8; border:1px solid #C7D7FE; }
.stMain .stDownloadButton button:hover { background:#EFF4FF; color:#1D4ED8; }
.stMain .stDownloadButton button p { color:#1D4ED8 !important; }
/* Medium screens: let columns wrap instead of squeezing charts */
@media(max-width:1100px){ [data-testid="stHorizontalBlock"] { flex-wrap:wrap; } [data-testid="stColumn"] { min-width:260px; } }
@media(max-width:800px){ .block-container{ padding-top: 1.2rem; } .stApp h1{ font-size: 1.6rem; } }
@media (prefers-reduced-motion: reduce){ * { transition: none !important; scroll-behavior: auto !important; } }

/* ---- focused layout: one screen per view, minimal scrolling ---- */
.block-container { padding-top: 4rem !important; padding-bottom: .8rem !important; max-width: 1600px; }
[data-testid="stMainBlockContainer"] { padding-top: 4rem !important; padding-bottom: .8rem !important; }
.stMain [data-testid="stVerticalBlock"] { gap: .7rem; }
.gp-head { display:flex; justify-content:space-between; align-items:flex-end; gap:.6rem 1rem; flex-wrap:wrap; margin:0 0 .1rem; }
.gp-h1 { font-size:1.5rem; font-weight:700; letter-spacing:-.03em; color:#101828; line-height:1.15; }
.gp-sub2 { color:#667085; font-size:.9rem; margin-top:.15rem; }
.gp-head .gp-badges { margin:0; }
[data-testid="stMetric"] { padding:.6rem .95rem; min-height:0; }
[data-testid="stMetricValue"] { font-size: clamp(1.2rem, 1.7vw, 1.55rem); }
[class*="st-key-panel_"] { padding:.7rem .95rem !important; }
.gp-panel-title { margin:0 0 .4rem; font-size:.92rem; }
.gp-pick { padding:.75rem 1rem .85rem; }
.gp-name { font-size:1.1rem; margin:.4rem 0 .05rem; }
.gp-score { font-size:1.7rem; }
.gp-why { font-size:.82rem; margin-top:.3rem; line-height:1.4; }
.gp-takeaway { margin:.2rem 0 .2rem; padding:.55rem .85rem; font-size:.9rem; }
.gp-side-label { font-size:.72rem; text-transform:uppercase; letter-spacing:.08em; color:#667085; font-weight:650; margin:.1rem 0 .3rem; }
[data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding-top:.5rem; }
[data-testid="stSidebar"] [data-baseweb="select"] > div:first-child { max-height:6.2rem; overflow-y:auto; }
[data-testid="stSidebar"] [data-testid="stExpander"] { border-radius:10px; }
/* View switcher (segmented control) in the app's blue */
[data-testid="stBaseButton-segmented_controlActive"] { background:#EFF4FF !important; color:#1D4ED8 !important; border-color:#C7D7FE !important; }
[data-testid="stBaseButton-segmented_controlActive"] p { color:#1D4ED8 !important; }
[data-testid="stBaseButton-segmented_control"] p { color:#475467 !important; }
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


def empty_state(icon: str, title: str, text: str) -> None:
    """Friendly placeholder instead of a bare info box."""
    st.markdown(
        f'<div class="gp-empty"><div class="ico">{icon}</div><div class="t">{html.escape(title)}</div>'
        f'<div class="d">{html.escape(text)}</div></div>', unsafe_allow_html=True)


def light_map(center, zoom=13):
    """OpenStreetMap tiles (no API key needed), softened to match the light theme."""
    m = folium.Map(location=center, zoom_start=zoom, tiles="OpenStreetMap", control_scale=True, prefer_canvas=True)
    m.get_root().header.add_child(folium.Element(
        "<style>.leaflet-tile-pane{filter:grayscale(.45) saturate(.85) brightness(1.04) contrast(.95);}</style>"))
    return m


def panel(title: str):
    """A bordered card that really wraps the widgets drawn inside it."""
    key = "panel_" + re.sub(r"\W+", "_", title.lower()).strip("_")
    try:
        box = st.container(border=True, key=key)
    except TypeError:  # older Streamlit without container keys
        box = st.container(border=True)
    box.markdown(f'<div class="gp-panel-title">{html.escape(title)}</div>', unsafe_allow_html=True)
    return box




def card(key: str):
    """Bordered card without a title (styled by the panel_ key prefix)."""
    try:
        return st.container(border=True, key="panel_" + key)
    except TypeError:
        return st.container(border=True)


def switch(options: list, key: str) -> str:
    """Compact view switcher. Only the chosen view is drawn, which keeps pages light and short."""
    if hasattr(st, "segmented_control"):
        v = st.segmented_control("View", options, selection_mode="single", default=options[0], key=key, label_visibility="collapsed")
    else:
        v = st.radio("View", options, horizontal=True, key=key, label_visibility="collapsed")
    return v if v in options else options[0]


def page_header(title: str, sub: str = "") -> None:
    """One slim row: title and one-line summary on the left, data badges on the right."""
    mode = CTX["mode"]
    live = "live" if mode == "Your data" else ""
    tip = ' title="Visits, rent and trends are simulated. Upload your own files on the Data page."' if mode == "Demo data" else ""
    badges = (f'<span class="gp-badge {live}"{tip}>{html.escape(mode)}</span>'
              f'<span class="gp-badge">Stores: {html.escape(CTX["store_src"])}</span>'
              f'<span class="gp-badge">{len(CTX["areas"])} areas</span>')
    st.markdown(f'<div class="gp-head"><div><div class="gp-h1">{html.escape(title)}</div>'
                f'<div class="gp-sub2">{html.escape(sub)}</div></div><div class="gp-badges">{badges}</div></div>',
                unsafe_allow_html=True)


def takeaway(text: str) -> None:
    """One plain-language sentence. Pass text that is already HTML-escaped."""
    st.markdown(f'<div class="gp-takeaway">💡 {text}</div>', unsafe_allow_html=True)


def sample_stores(df: pd.DataFrame, cap: int = 1500) -> pd.DataFrame:
    """Keep maps fast when a source returns thousands of shops."""
    return df if len(df) <= cap else df.sample(cap, random_state=1)

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
    if amenity in {"cafe", "restaurant", "fast_food", "ice_cream"}:
        return "Food & Beverage"
    if amenity == "pharmacy" or shop in {"chemist", "pharmacy", "medical_supply", "optician", "beauty", "hairdresser", "cosmetics", "perfumery"}:
        return "Health & Beauty"
    if shop in {"supermarket", "convenience", "greengrocer", "grocery", "bakery", "butcher", "department_store", "kiosk", "general", "wholesale", "mall", "confectionery", "dairy"}:
        return "Grocery"
    if shop in {"clothes", "shoes", "boutique", "jewelry", "fashion_accessories", "bag", "tailor", "watches", "fabric"}:
        return "Fashion"
    if shop in {"electronics", "mobile_phone", "computer", "hifi", "electrical", "appliance", "telecommunication"}:
        return "Electronics"
    if shop in {"furniture", "hardware", "doityourself", "houseware", "kitchen", "interior_decoration", "bed", "carpet", "curtain", "paint"}:
        return "Home & Furniture"
    if shop:
        return "Other retail"
    return None


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_osm(south: float, west: float, north: float, east: float) -> pd.DataFrame:
    """Every shop and eatery OpenStreetMap has in the box. Raises on failure so errors are not cached."""
    bbox = f"{south},{west},{north},{east}"
    query = (
        f'[out:json][timeout:60];(nwr["shop"]({bbox});'
        f'nwr["amenity"~"^(cafe|restaurant|fast_food|ice_cream|pharmacy)$"]({bbox}););out center 8000;'
    )
    r, last = None, None
    for url in ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"):
        try:
            r = requests.post(url, data={"data": query}, timeout=75,
                              headers={"User-Agent": "GeoPulse/1.0 (retail analytics demo)"})
            r.raise_for_status()
            break
        except Exception as exc:
            r, last = None, exc
    if r is None:
        raise last
    rows = []
    for el in r.json().get("elements", []):
        tags = el.get("tags", {})
        cat = osm_category(tags)
        lat = el.get("lat", (el.get("center") or {}).get("lat"))
        lon = el.get("lon", (el.get("center") or {}).get("lon"))
        if cat and lat is not None and lon is not None:
            rows.append({"Store": tags.get("name") or f"{cat} store", "Category": cat, "Latitude": lat, "Longitude": lon})
    if not rows:
        raise ValueError("No stores returned for this area")
    return pd.DataFrame(rows, columns=["Store", "Category", "Latitude", "Longitude"]).drop_duplicates(["Store", "Latitude", "Longitude"])


GUWAHATI_BBOX = (26.05, 91.58, 26.25, 91.92)  # south, west, north, east


def label_area(stores: pd.DataFrame, areas: pd.DataFrame, max_km: float = 3.0) -> pd.DataFrame:
    """Keep every retailer. Name its nearest study area, or 'Outside study areas' if none is within max_km."""
    if stores.empty:
        return stores.assign(Area=pd.Series(dtype=str))[STORE_COLS]
    d = haversine_km(
        stores["Latitude"].to_numpy()[:, None], stores["Longitude"].to_numpy()[:, None],
        areas["Latitude"].to_numpy()[None, :], areas["Longitude"].to_numpy()[None, :],
    )
    out = stores.copy()
    out["Area"] = np.where(d.min(axis=1) <= max_km, areas["Area"].to_numpy()[d.argmin(axis=1)], "Outside study areas")
    return out[STORE_COLS].reset_index(drop=True)


# Google Places (New) Text Search. Needs a key with billing enabled; every request is billed by Google.
GOOGLE_URL = "https://places.googleapis.com/v1/places:searchText"
GOOGLE_QUERIES = {
    "Grocery": ["supermarket", "grocery store", "convenience store"],
    "Fashion": ["clothing store", "shoe store", "jewelry store"],
    "Electronics": ["electronics store", "mobile phone shop"],
    "Food & Beverage": ["restaurant", "cafe"],
    "Health & Beauty": ["pharmacy", "beauty salon"],
    "Home & Furniture": ["furniture store", "hardware store"],
}
GOOGLE_PAGES = 3


def google_request_estimate(n_areas: int) -> int:
    return n_areas * sum(len(v) for v in GOOGLE_QUERIES.values()) * GOOGLE_PAGES


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_google_places(api_key: str, centers: tuple, radius_m: int = 3000) -> pd.DataFrame:
    """Retailers around each area centre. The key is sent in a header, never in the URL."""
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.id,places.displayName,places.location,nextPageToken",
    }
    seen, rows = set(), []
    for cat, terms in GOOGLE_QUERIES.items():
        for term in terms:
            for lat, lon in centers:
                token = None
                for _ in range(GOOGLE_PAGES):
                    body = {"textQuery": term, "pageSize": 20,
                            "locationBias": {"circle": {"center": {"latitude": lat, "longitude": lon}, "radius": float(radius_m)}}}
                    if token:
                        body["pageToken"] = token
                    r = requests.post(GOOGLE_URL, json=body, headers=headers, timeout=20)
                    if r.status_code != 200:
                        try:
                            msg = r.json().get("error", {}).get("message", r.reason)
                        except Exception:
                            msg = r.reason
                        raise RuntimeError(f"Google returned {r.status_code}: {msg}")
                    data = r.json()
                    for pl in data.get("places", []):
                        pid = pl.get("id")
                        loc = pl.get("location") or {}
                        if pid in seen or "latitude" not in loc:
                            continue
                        seen.add(pid)
                        rows.append({"Store": (pl.get("displayName") or {}).get("text") or f"{cat} store", "Category": cat,
                                     "Latitude": loc["latitude"], "Longitude": loc["longitude"]})
                    token = data.get("nextPageToken")
                    if not token:
                        break
    if not rows:
        raise ValueError("Google returned no places for these areas")
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


def load_data(source: str, api_key: str = "") -> dict:
    up = st.session_state.get("upload", {})
    notes = []
    if "areas" in up:
        areas, mode = prepare_areas(up["areas"]), "Your data"
    else:
        areas, mode = prepare_areas(demo_areas()), "Demo data"

    all_stores = None
    if "stores" in up:
        stores, store_src = normalize_stores(up["stores"], areas), "Uploaded"
    elif source.startswith("OpenStreetMap"):
        try:
            with st.spinner("Loading every Guwahati retailer from OpenStreetMap"):
                if mode == "Demo data":
                    bounds = GUWAHATI_BBOX
                else:
                    bounds = (round(areas["Latitude"].min() - 0.05, 4), round(areas["Longitude"].min() - 0.05, 4),
                              round(areas["Latitude"].max() + 0.05, 4), round(areas["Longitude"].max() + 0.05, 4))
                raw = fetch_osm(*bounds)
                stores, all_stores = assign_area(raw, areas), label_area(raw, areas)
            if all_stores.empty:
                raise ValueError("no stores returned")
            store_src = "OpenStreetMap"
        except Exception as exc:
            notes.append(f"Could not load OpenStreetMap retailers ({exc}). Showing simulated stores instead.")
            stores, store_src, all_stores = make_stores(areas), "Simulated", None
    elif source.startswith("Google"):
        if not api_key:
            notes.append("Add your Google Places API key under Data source in the sidebar to load retailers from Google. Showing simulated stores for now.")
            stores, store_src = make_stores(areas), "Simulated"
        else:
            try:
                with st.spinner("Loading retailers from Google Places (first load can take a minute)"):
                    centers = tuple((round(float(a), 5), round(float(o), 5)) for a, o in zip(areas["Latitude"], areas["Longitude"]))
                    raw = fetch_google_places(api_key, centers)
                    stores, all_stores = assign_area(raw, areas), label_area(raw, areas)
                if all_stores.empty:
                    raise ValueError("no stores returned")
                store_src = "Google Places"
            except Exception as exc:
                notes.append(f"Could not load Google Places retailers ({exc}). Showing simulated stores instead.")
                stores, store_src, all_stores = make_stores(areas), "Simulated", None
    else:
        stores, store_src = make_stores(areas), "Simulated"
    if all_stores is None:
        all_stores = stores.copy()

    counts = stores.groupby("Area").size()
    areas = areas.copy()
    areas["Retail Stores"] = areas["Area"].map(counts).fillna(0).astype(int)

    weekly = prepare_weekly(up["weekly"]) if "weekly" in up else make_weekly(areas)
    hourly = prepare_hourly(up["hourly"]) if "hourly" in up else make_hourly(areas)
    return {"areas": areas, "stores": stores, "all_stores": all_stores, "weekly": weekly, "hourly": hourly,
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
# PAGES (focused set: five pages, each built to fit one screen)
# =====================================================================
def page_overview():
    areas, weekly, stores = CTX["areas"], CTX["weekly"], CTX["stores"]
    scored = score_areas(areas)
    lead = scored.iloc[0]
    sub = f'{lead["Area"]} leads on site score ({lead["Site Score"]:.0f}/100).'
    if not stores.empty:
        sub += f' {stores["Category"].value_counts().idxmax()} is the most common store type.'
    page_header("Overview", sub)

    k = st.columns(4)
    k[0].metric("Daily visits", f'{areas["Visits"].sum():,.0f}', help="Typical daily visits across the selected areas")
    k[1].metric("Retail stores", f'{int(areas["Retail Stores"].sum()):,}', help="Stores in the selected areas and categories")
    k[2].metric("Average opportunity", f'{areas["Opportunity Score"].mean():.0f} / 100')
    k[3].metric("Top area", str(lead["Area"]), help="Highest site score: demand, visits per store and baseline opportunity")

    left, right = st.columns([1.45, 1], gap="medium")
    with left, panel("Visit heat by area"):
        m = light_map([float(areas["Latitude"].mean()), float(areas["Longitude"].mean())], 12)
        top_v = max(float(areas["Visits"].max()), 1.0)
        HeatMap([[float(r.Latitude), float(r.Longitude), float(r.Visits) / top_v] for r in areas.itertuples()],
                radius=27, blur=20, min_opacity=.35, gradient={0.25: "#93C5FD", 0.5: "#2563EB", 0.75: GOLD, 1.0: GAMOSA}).add_to(m)
        for _, r in areas.iterrows():
            popup = (f"<b>{html.escape(str(r['Area']))}</b><br>Visits: {float(r['Visits']):,.0f}"
                     f"<br>Stores: {int(r['Retail Stores'])}<br>Opportunity: {float(r['Opportunity Score']):.0f}/100")
            folium.CircleMarker(location=[float(r["Latitude"]), float(r["Longitude"])], radius=7, color="#FFFFFF", weight=1.5,
                                fill=True, fill_color=RIVER, fill_opacity=.95, tooltip=str(r["Area"]), popup=popup).add_to(m)
        st_folium(m, key="overview_map", height=410, use_container_width=True, returned_objects=[])

    with right, card("overview_side"):
        t1, t2, t3 = st.tabs(["Top areas", "Categories", "Weekly trend"])
        with t1:
            top = areas.sort_values("Visits", ascending=False).head(8).sort_values("Visits")
            fig = px.bar(top, x="Visits", y="Area", orientation="h", text="Visits")
            fig.update_traces(marker_color=RIVER, texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)
            fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title=None)
            show(style(fig, 360).update_layout(margin=dict(l=0, r=30, t=6, b=0)))
        with t2:
            if stores.empty:
                st.caption("No store data for the current filters.")
            else:
                cat = stores.groupby("Category").size().reset_index(name="Stores").sort_values("Stores", ascending=False)
                colors = cat_colors(list(cat["Category"]))
                fig = px.pie(cat, names="Category", values="Stores", hole=.62, color="Category", color_discrete_map=colors)
                fig.update_traces(textposition="inside", textinfo="percent", marker=dict(line=dict(color="#FFFFFF", width=2)))
                fig.update_layout(legend=dict(orientation="h", x=.5, xanchor="center", y=-.02, font=dict(size=11)),
                                  margin=dict(l=0, r=0, t=4, b=0), height=360,
                                  annotations=[dict(text=f"{len(stores):,}<br><sup>Stores</sup>", x=.5, y=.5, showarrow=False, font=dict(size=19, color=TEXT))])
                st.plotly_chart(fig, theme=None, **STRETCH)
        with t3:
            if weekly.empty:
                st.caption("No weekly data for the current filters.")
            else:
                total = weekly.groupby("Week", as_index=False)["Visits"].sum()
                fig = px.area(total, x="Week", y="Visits")
                fig.update_traces(line_color=RIVER, fillcolor="rgba(37,99,235,.12)")
                fig.update_xaxes(title=None)
                show(style(fig, 360).update_layout(margin=dict(l=0, r=0, t=6, b=0)))


# ---------------------------------------------------------------- Explore
def page_explore():
    page_header("Explore", "The map, the busiest hours and the competition in the selected areas.")
    view = switch(["Heatmap", "Peak hours", "Competitors"], "explore_view")
    {"Heatmap": explore_heatmap, "Peak hours": explore_peak, "Competitors": explore_competitors}[view]()


def explore_heatmap():
    areas, stores = CTX["areas"], CTX["stores"]
    left, right = st.columns([3.2, 1], gap="medium")
    with right, card("heat_ctrl"):
        metric = st.selectbox("Heat intensity", ["Visits", "Opportunity Score"])
        radius = st.slider("Radius", 10, 60, 30)
        show_areas = st.toggle("Area pins", value=True)
        show_stores = st.toggle("Stores", value=False)
        st.caption("Blue is lighter traffic. Amber and red are heavier.")
    with left, card("heat_map"):
        m = light_map([areas["Latitude"].mean(), areas["Longitude"].mean()], 13)
        weights = (areas[metric] / max(float(areas[metric].max()), 1.0)).to_numpy()
        HeatMap([[la, lo, w] for la, lo, w in zip(areas["Latitude"], areas["Longitude"], weights)],
                radius=radius, blur=22, gradient={0.3: "#93C5FD", 0.6: GOLD, 1.0: GAMOSA}).add_to(m)
        if show_areas:
            for _, a in areas.iterrows():
                folium.Marker(location=[a["Latitude"], a["Longitude"]], tooltip=a["Area"],
                              popup=f'{html.escape(a["Area"])}<br>Visits: {a["Visits"]:,.0f}<br>Opportunity: {a["Opportunity Score"]}/100',
                              icon=folium.Icon(color="darkblue", icon="shopping-cart")).add_to(m)
        if show_stores and not stores.empty:
            colors = cat_colors(sorted(stores["Category"].unique()))
            for _, s in sample_stores(stores).iterrows():
                folium.CircleMarker(location=[s["Latitude"], s["Longitude"]], radius=4, color=colors[s["Category"]],
                                    fill=True, fill_opacity=0.85, tooltip=f'{s["Store"]} ({s["Category"]})').add_to(m)
        st_folium(m, key="heat_map", height=500, use_container_width=True, returned_objects=[])


def explore_peak():
    h = CTX["hourly"]
    h = h[h["Area"].isin(CTX["areas"]["Area"])]
    if h.empty:
        empty_state("🕒", "No hourly data for these areas", "Upload an hourly file on the Data page, or pick other areas in the sidebar.")
        return
    grid = h.pivot_table(index="Day", columns="Hour", values="Visits", aggfunc="sum").reindex(DAYS)
    top = grid.stack().sort_values(ascending=False).head(3)
    daily = h.groupby("Day")["Visits"].sum().reindex(DAYS).fillna(0)
    wk = daily[DAYS[:5]].mean()
    uplift = f"{daily[DAYS[5:]].mean() / wk - 1:+.0%}" if wk > 0 else "n/a"
    d0, h0 = top.index[0]

    left, right = st.columns([2.4, 1], gap="medium")
    with left, panel("Visits by day and hour"):
        fig = px.imshow(grid, aspect="auto", color_continuous_scale=["#EFF4FF", "#2563EB"], labels=dict(x="Hour of day", y="", color="Visits"))
        fig.update_xaxes(dtick=2)
        show(style(fig, 400).update_layout(margin=dict(l=0, r=0, t=6, b=0)))
    with right:
        st.metric("Busiest slot", f"{d0} {h0:02d}:00", help="Highest visits in any single day and hour")
        st.metric("Busiest day", str(daily.idxmax()))
        st.metric("Weekend vs weekday", uplift, help="Average weekend day compared with the average weekday")
        with card("peak_top"):
            st.markdown('<div class="gp-panel-title">Top 3 slots</div>', unsafe_allow_html=True)
            for (day, hour), v in top.items():
                st.markdown(f"**{day} {hour:02d}:00** · about {v:,.0f} visits")


def explore_competitors():
    stores, areas = CTX["stores"], CTX["areas"]
    view = stores[stores["Area"].isin(areas["Area"])]
    if view.empty:
        empty_state("🏪", "No stores match these filters", "Add a category or an area in the sidebar to see competitors.")
        return
    colors = cat_colors(sorted(view["Category"].unique()))
    counts = view.groupby("Area").size().rename("Stores").reset_index()
    crowded = counts.loc[counts["Stores"].idxmax()]

    left, right = st.columns([1.5, 1], gap="medium")
    with left, panel("Store locations by category"):
        shown = sample_stores(view)
        m = light_map([view["Latitude"].mean(), view["Longitude"].mean()], 13)
        for _, s in shown.iterrows():
            folium.CircleMarker(location=[s["Latitude"], s["Longitude"]], radius=6, color=colors[s["Category"]],
                                fill=True, fill_color=colors[s["Category"]], fill_opacity=0.85,
                                tooltip=f'{s["Store"]} ({s["Category"]})').add_to(m)
        st_folium(m, key="comp_map", height=400, use_container_width=True, returned_objects=[])
        if len(shown) < len(view):
            st.caption(f"Showing {len(shown):,} of {len(view):,} stores to keep the map fast. Charts use all of them.")
    with right:
        k = st.columns(2)
        k[0].metric("Stores", f"{len(view):,}")
        k[1].metric("Most crowded", f'{crowded["Area"]}', help=f'{int(crowded["Stores"])} stores')
        with panel("Stores by area"):
            by_cat = view.groupby(["Area", "Category"]).size().rename("Stores").reset_index()
            fig = px.bar(by_cat, x="Area", y="Stores", color="Category", color_discrete_map=colors)
            fig.update_xaxes(title=None)
            fig.update_layout(legend=dict(orientation="h", y=-0.25, x=0, title=None, font=dict(size=11)))
            show(style(fig, 300).update_layout(margin=dict(l=0, r=0, t=6, b=0)))


# ---------------------------------------------------------------- Where to open
def page_where():
    areas, stores = CTX["areas"], CTX["stores"]
    cats = sorted(stores["Category"].unique()) or list(CATS)
    page_header("Where to open", "Rank areas for a new store, then check whether it would pay.")
    view = switch(["Best areas", "Profit check"], "where_view")
    if view == "Best areas":
        where_rank(areas, stores, cats)
    else:
        where_profit(areas, stores, cats)


def where_rank(areas, stores, cats):
    left, right = st.columns([1, 2.1], gap="medium")
    with left, card("where_ctrl"):
        category = st.selectbox("Business type", cats)
        budget = st.radio("Rent budget", ["Low", "Medium", "High"], index=1, horizontal=True,
                          help="Low budgets favor areas with lower rent. High budgets ignore rent.")
    ranked = recommend(areas, stores, category, budget)
    mean_rent = areas["Rent Index"].mean()
    with left, panel("Fit score"):
        fig = bar_chart(ranked.head(8), "Area", "Score", "").update_layout(title=None, margin=dict(l=0, r=0, t=6, b=0))
        show(style(fig, 250).update_layout(margin=dict(l=0, r=0, t=6, b=0)))
    with right:
        labels = ["Best fit", "Second choice", "Third choice"]
        for i, col in enumerate(st.columns(min(3, len(ranked)), gap="small")):
            r = ranked.iloc[i]
            col.markdown(
                f'<div class="gp-pick{" first" if i == 0 else ""}"><div class="gp-pick-top">{labels[i]}</div>'
                f'<div class="gp-name">{html.escape(r["Area"])}</div>'
                f'<div class="gp-score">{r["Score"]:.0f}<span>/100</span></div>'
                f'<div class="gp-why">{html.escape(why_text(r, category, mean_rent))}</div></div>', unsafe_allow_html=True)
        with panel("Ranked areas on the map"):
            m = light_map([float(ranked["Latitude"].mean()), float(ranked["Longitude"].mean())], 12)
            for i, r in ranked.iterrows():
                bg = RIVER if i < 3 else "#98A2B3"
                icon = (f'<div style="background:{bg};color:#fff;width:26px;height:26px;border-radius:50%;display:flex;align-items:center;'
                        f'justify-content:center;font:700 12px Inter,sans-serif;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.3)">{i + 1}</div>')
                folium.Marker([float(r["Latitude"]), float(r["Longitude"])],
                              tooltip=f'{i + 1}. {html.escape(str(r["Area"]))} · {r["Score"]:.0f}/100',
                              icon=folium.DivIcon(html=icon, icon_size=(26, 26), icon_anchor=(13, 13))).add_to(m)
            st_folium(m, key="where_map", height=250, use_container_width=True, returned_objects=[])


def where_profit(areas, stores, cats):
    a = areas.set_index("Area")
    left, right = st.columns([1, 1.25], gap="medium")
    with left, card("profit_in"):
        c1, c2 = st.columns(2)
        area = c1.selectbox("Area", list(a.index))
        cat = c2.selectbox("Business type", cats)
        conv = st.slider("Visitors who buy (%)", 1.0, 15.0, 4.0, 0.5)
        s1, s2 = st.columns(2)
        spend = s1.number_input("Average spend (₹)", 50, 5000, 350, 25)
        cost = s2.number_input("Monthly running cost (₹)", 10000, 1000000, 120000, 5000)
    n = int(((stores["Area"] == area) & (stores["Category"] == cat)).sum())
    customers = a.loc[area, "Visits"] / (n + 1) * conv / 100
    revenue = customers * spend * 30
    profit = revenue - cost
    breakeven = cost / (spend * 30)
    with right:
        r1 = st.columns(2)
        r1[0].metric("Customers per day", f"{customers:,.0f}")
        r1[1].metric("Break-even customers/day", f"{breakeven:,.0f}")
        r2 = st.columns(2)
        r2[0].metric("Monthly revenue", f"₹{revenue:,.0f}")
        r2[1].metric("Monthly profit", f"₹{profit:,.0f}")
        if profit >= 0:
            st.success(f"At these assumptions a {cat} store in {area} covers its costs, with {n} similar store(s) nearby today.")
        else:
            st.warning(f"At these assumptions a {cat} store in {area} needs about {breakeven:,.0f} customers a day to break even.")
        st.caption("Estimate only: the area's daily visits are shared equally between existing stores of that type and the new one.")


# ---------------------------------------------------------------- Compare & forecast
def page_compare():
    page_header("Compare & forecast", "Put areas side by side, then see where weekly visits are heading.")
    view = switch(["Compare areas", "Forecast"], "cmp_view")
    compare_view() if view == "Compare areas" else forecast_view()


def compare_view():
    a = CTX["areas"].set_index("Area")
    names = list(a.index)
    if len(names) < 2:
        st.info("Select at least two areas in the sidebar to compare them.")
        return
    pick = st.multiselect("Areas to compare (up to 3)", names, default=names[:3], max_selections=3)
    if len(pick) < 2:
        st.info("Pick at least two areas to compare.")
        return
    left, right = st.columns([1, 1.1], gap="medium")
    with left, panel("Shape of each area (100 = highest)"):
        metrics = ["Visits", "Retail Stores", "Opportunity Score", "Rent Index"]
        scaled = a[metrics].apply(lambda s: 100 * s / max(s.max(), 1))
        fig = go.Figure()
        for i, n in enumerate(pick):
            v = scaled.loc[n].tolist()
            fig.add_trace(go.Scatterpolar(r=v + v[:1], theta=metrics + metrics[:1], name=n, fill="toself", line_color=SERIES[i], opacity=0.6))
        fig.update_layout(height=340, margin=dict(l=40, r=40, t=14, b=34), legend=dict(orientation="h", y=-0.12))
        st.plotly_chart(fig, theme=None, **STRETCH)
    with right, panel("Side by side"):
        rows = {"Daily visits": ("Visits", "{:,.0f}"), "Retail stores": ("Retail Stores", "{:,.0f}"),
                "Opportunity (0-100)": ("Opportunity Score", "{:,.0f}"), "Rent index": ("Rent Index", "{:,.0f}")}
        tbl = pd.DataFrame({n: [fmt.format(a.loc[n, col]) for col, fmt in rows.values()] for n in pick}, index=list(rows))
        st.dataframe(tbl, **STRETCH)
        best = a.loc[pick, "Opportunity Score"].idxmax()
        cheap = a.loc[pick, "Rent Index"].idxmin()
        takeaway(f"{html.escape(str(best))} has the highest opportunity score"
                 + (f", and {html.escape(str(cheap))} has the lowest rent." if cheap != best else " and also the lowest rent."))


def forecast_view():
    c1, c2, c3 = st.columns([1.2, 1, 1])
    area = c1.selectbox("Area", list(CTX["areas"]["Area"]))
    horizon = c2.slider("Weeks to project", 2, 12, 4)
    uplift = c3.slider("Scenario adjustment (%)", -20, 30, 0, help="Applies a flat increase or decrease to the projection.") / 100
    w = CTX["weekly"]
    if len(w[w["Area"] == area]) < 8:
        st.info("This area has fewer than 8 weeks of history. Widen the time window in the sidebar or upload more weekly data.")
        return
    hist, fc, scores, hold, chosen = forecast(area, horizon, uplift)
    left, right = st.columns([2.4, 1], gap="medium")
    with left, panel(f"{area}: weekly visits and projection"):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=list(fc["Week"]) + list(fc["Week"])[::-1], y=list(fc["High"]) + list(fc["Low"])[::-1],
                                 fill="toself", fillcolor="rgba(20,184,166,0.16)", line=dict(width=0), hoverinfo="skip", name="80% range"))
        fig.add_trace(go.Scatter(x=hist["Week"], y=hist["Visits"], mode="lines", name="Actual", line=dict(color=RIVER, width=2.5)))
        fig.add_trace(go.Scatter(x=[hist["Week"].iloc[-1]] + list(fc["Week"]), y=[hist["Visits"].iloc[-1]] + list(fc["Forecast"]),
                                 mode="lines+markers", name="Projection", line=dict(color=TEA, dash="dash", width=2.5)))
        fig.update_layout(title=None, legend=dict(orientation="h", y=1.1, x=0))
        fig.update_yaxes(title="Visits per week")
        show(style(fig, 330).update_layout(margin=dict(l=0, r=0, t=30, b=0)))
    recent, projected = hist["Visits"].tail(horizon).sum(), fc["Forecast"].sum()
    with right:
        st.metric(f"Last {horizon} weeks", f"{recent:,.0f}")
        st.metric(f"Next {horizon} weeks", f"{projected:,.0f}")
        st.metric("Change", f"{projected / recent - 1:+.1%}", delta=f"{projected - recent:+,.0f} visits")
        st.caption(f"Model: {chosen}, the lowest error ({scores[chosen]:.1f}% MAPE) when tested on the last {hold} weeks.")


# ---------------------------------------------------------------- Data
def page_data():
    up = st.session_state.get("upload", {})
    page_header("Data", "Use your own files, grab templates, or read how the numbers are made.")
    view = switch(["Upload", "Templates", "About the numbers"], "data_view")
    if view == "Upload":
        st.caption(("Using your uploaded files: " + ", ".join(up.keys()) + ".") if up else "Using the built-in demo data. Only the areas file is required. Retailer source is under Data source in the sidebar.")
        c1, c2 = st.columns(2, gap="medium")
        f_areas = c1.file_uploader("Areas (required)", type="csv", key="u_areas", help="Area, Latitude, Longitude, Visits. Optional: Retail Stores, Opportunity Score, Rent Index")
        f_stores = c2.file_uploader("Stores", type="csv", key="u_stores", help="Store, Category, Latitude, Longitude. Optional: Area")
        f_weekly = c1.file_uploader("Weekly visits", type="csv", key="u_weekly", help="Area, Week, Visits")
        f_hourly = c2.file_uploader("Hourly visits", type="csv", key="u_hourly", help="Area, Day, Hour, Visits (Day is Mon to Sun)")
        b1, b2, _ = st.columns([1, 1, 2])
        if b1.button("Use these files", **STRETCH):
            if f_areas is None:
                st.error("Add the areas file first. It is the only required one.")
            else:
                new, errors = {}, []
                specs = [("areas", f_areas, AREA_COLS, ["Area", "Latitude", "Longitude", "Visits"]),
                         ("stores", f_stores, STORE_COLS, ["Category", "Latitude", "Longitude"]),
                         ("weekly", f_weekly, ["Area", "Week", "Visits"], ["Area", "Week", "Visits"]),
                         ("hourly", f_hourly, ["Area", "Day", "Hour", "Visits"], ["Area", "Day", "Hour", "Visits"])]
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
                    st.rerun()
        if b2.button("Back to demo data", **STRETCH):
            st.session_state.pop("upload", None)
            st.rerun()
    elif view == "Templates":
        st.caption("Download a template, replace the rows with your own, then upload it on the Upload view.")
        demo = prepare_areas(demo_areas())
        t = st.columns(4)
        t[0].download_button("Areas template", demo.to_csv(index=False), file_name="areas_template.csv", mime="text/csv", **STRETCH)
        t[1].download_button("Stores template", make_stores(demo).to_csv(index=False), file_name="stores_template.csv", mime="text/csv", **STRETCH)
        t[2].download_button("Weekly template", make_weekly(demo).to_csv(index=False), file_name="weekly_template.csv", mime="text/csv", **STRETCH)
        t[3].download_button("Hourly template", make_hourly(demo).round(1).to_csv(index=False), file_name="hourly_template.csv", mime="text/csv", **STRETCH)
    else:
        c1, c2 = st.columns(2, gap="large")
        with c1:
            st.markdown(
                "**Where the data comes from**  \n"
                "Demo visits, rent, weekly and hourly patterns are simulated. Upload CSVs to use your own. "
                "Store locations can come from OpenStreetMap or Google Places (your API key) under Data source in the sidebar. "
                "Map data © OpenStreetMap contributors (ODbL). OpenStreetMap has no foot traffic, so visits stay simulated until you upload them.")
            st.markdown(
                "**Site score**  \n"
                "Demand (visits), under-served gap (visits per store) and baseline opportunity are each scaled 0 to 1 across the areas, then combined into a score out of 100.")
        with c2:
            st.markdown(
                "**Where to open**  \n"
                "For the chosen business type each area is scored on visits, the gap in stores of that type (visits divided by stores plus one) and rent. "
                "Budget sets the weights: Low 35/35/30, Medium 45/40/15, High 50/50/0 for demand, gap and affordability. "
                "A missing Rent Index is estimated from visits and is only a rough guide.")
            st.markdown(
                "**Forecast and limits**  \n"
                "Ridge regression on a trend term, plus yearly seasonality with 40+ weeks of history. The last weeks are held out to pick the lowest-error model. "
                "Distances are straight-line and projections assume recent patterns continue, so treat results as a starting point for site visits.")



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


def get_api_key(box) -> str:
    """Prefer Streamlit secrets (GOOGLE_PLACES_API_KEY). Fall back to a password box that lives only in this session."""
    try:
        k = st.secrets.get("GOOGLE_PLACES_API_KEY")
    except Exception:
        k = None
    if k:
        box.caption("Google Places key loaded from app secrets.")
        return str(k).strip()
    k = box.text_input("Google Places API key", type="password", key="gp_key",
                       help="Kept only for this browser session and never written to disk or shown again. For a deployed app, add GOOGLE_PLACES_API_KEY to Streamlit secrets instead.")
    n_areas = len(prepare_areas(st.session_state["upload"]["areas"])) if "areas" in st.session_state.get("upload", {}) else len(demo_areas())
    box.caption(f"One full load makes up to {google_request_estimate(n_areas):,} Google requests, billed to your key, then is cached for 24 hours.")
    return k.strip()


def build_context() -> dict:
    sb = st.sidebar
    filt = sb.container()  # drawn first, filled once the data (and so the filter options) is known
    src = sb.expander("Data source", expanded=str(st.session_state.get("store_source", "Simulated")).startswith("Google"))
    up = st.session_state.get("upload", {})
    has_upload = "stores" in up
    source = src.selectbox(
        "Retailer source", ["Simulated", "OpenStreetMap (all shops)", "Google Places (API key)"], key="store_source", index=0,
        disabled=has_upload, help="Simulated is instant. OpenStreetMap is free and lists most shops. Google Places usually has the most complete list but needs your own API key.",
    )
    api_key = ""
    if source.startswith("Google") and not has_upload:
        api_key = get_api_key(src)
    data = load_data("Uploaded" if has_upload else source, api_key)

    opts_a = list(data["areas"]["Area"])
    opts_c = sorted(data["stores"]["Category"].unique()) or list(CATS)
    st.session_state["f_areas"] = [a for a in st.session_state.get("f_areas", opts_a) if a in opts_a] or opts_a
    st.session_state["f_cats"] = [c for c in st.session_state.get("f_cats", opts_c) if c in opts_c] or opts_c
    st.session_state.setdefault("f_window", 52)
    with filt:
        for note in data["notes"]:
            st.warning(note)
        st.markdown('<div class="gp-side-label">Filters</div>', unsafe_allow_html=True)
        f_areas = st.multiselect("Areas", opts_a, key="f_areas")
        f_cats = st.multiselect("Store categories", opts_c, key="f_cats")
        window = st.select_slider("Time window", options=[12, 26, 52], key="f_window", format_func=lambda w: f"Last {w} weeks")
        st.markdown(f'<div class="gp-filter-chip">{len(f_areas)} of {len(opts_a)} areas · {len(f_cats)} of {len(opts_c)} categories · last {window} weeks</div>', unsafe_allow_html=True)
        st.button("Reset filters", on_click=reset_filters, **STRETCH)

    areas = data["areas"][data["areas"]["Area"].isin(f_areas)].copy()
    stores = data["stores"][data["stores"]["Area"].isin(f_areas) & data["stores"]["Category"].isin(f_cats)].reset_index(drop=True)
    areas["Retail Stores"] = areas["Area"].map(stores.groupby("Area").size()).fillna(0).astype(int)

    all_stores = data["all_stores"][data["all_stores"]["Category"].isin(f_cats)].reset_index(drop=True)
    weekly = data["weekly"][data["weekly"]["Area"].isin(f_areas)]
    if not weekly.empty:
        cutoff = sorted(weekly["Week"].unique())[-window:][0]
        weekly = weekly[weekly["Week"] >= cutoff]
    hourly = data["hourly"][data["hourly"]["Area"].isin(f_areas)]

    sb.caption("Guwahati, Assam · Map data © OpenStreetMap contributors")
    return {"areas": areas.reset_index(drop=True), "stores": stores, "all_stores": all_stores, "weekly": weekly, "hourly": hourly,
            "mode": data["mode"], "store_src": data["store_src"]}


password_gate()

st.sidebar.markdown(
    '<div class="gp-brand"><div class="gp-mark"><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.6"/></svg></div>'
    '<div><div class="gp-brand-name">GeoPulse</div><div class="gp-brand-sub">Retail mobility analytics</div></div></div>',
    unsafe_allow_html=True)

PAGES = [
    st.Page(page_overview, title="Overview", icon=":material/dashboard:", default=True),
    st.Page(page_explore, title="Explore", icon=":material/map:", url_path="explore"),
    st.Page(page_where, title="Where to open", icon=":material/pin_drop:", url_path="where-to-open"),
    st.Page(page_compare, title="Compare & forecast", icon=":material/compare_arrows:", url_path="compare"),
    st.Page(page_data, title="Data", icon=":material/upload_file:", url_path="data"),
]
try:
    pg = st.navigation(PAGES, position="top")
except TypeError:  # Streamlit older than 1.46 has no top navigation; pages go in the sidebar instead
    pg = st.navigation(PAGES)

CTX = build_context()
if CTX["areas"].empty:
    st.warning("No areas are selected. Choose at least one area in the sidebar.")
    st.stop()

pg.run()
