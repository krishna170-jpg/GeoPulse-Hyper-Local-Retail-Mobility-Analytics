import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
import streamlit as st
from folium.plugins import HeatMap
from streamlit_folium import st_folium

st.set_page_config(
    page_title="GeoPulse | Retail Intelligence",
    page_icon="🌍",
    layout="wide",
)

# ---------- DESIGN TOKENS ----------
INK = "#0b1d26"
PANEL = "#12303d"
LINE = "#24505f"
TEXT = "#e6f1f4"
MUTED = "#8fb0bb"
AMBER = "#f2a93b"
TEAL = "#3fb8af"
BLUE = "#5aa9ff"
VIOLET = "#c77dff"
RED = "#e5484d"
SERIES = [TEAL, AMBER, BLUE, VIOLET, RED]

# Streamlit 1.50+ replaced use_container_width with width="stretch".
_ver = tuple(int(p) for p in st.__version__.split(".")[:2] if p.isdigit())
STRETCH = {"width": "stretch"} if _ver >= (1, 50) else {"use_container_width": True}

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@500;700&family=Public+Sans:wght@400;500;600&display=swap');
.stApp, .stApp p, .stApp label, .stApp li {{
    font-family: 'Public Sans', sans-serif;
}}
.stApp h1, .stApp h2, .stApp h3 {{
    font-family: 'Bricolage Grotesque', sans-serif;
    letter-spacing: -0.01em;
    color: {TEXT};
}}
.stApp {{ background: {INK}; color: {TEXT}; }}
[data-testid="stSidebar"] {{ background: #0e2430; border-right: 1px solid {LINE}; }}
div[data-testid="stMetric"] {{
    background: {PANEL};
    padding: 16px 18px;
    border-radius: 8px;
    border: 1px solid {LINE};
}}
[data-testid="stMetricLabel"] p {{ color: {MUTED} !important; }}
[data-testid="stMetricValue"] {{ color: {TEXT}; }}
</style>
""",
    unsafe_allow_html=True,
)

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
CATEGORY_COLORS = {
    "Grocery": TEAL,
    "Fashion": VIOLET,
    "Electronics": BLUE,
    "Food & Beverage": AMBER,
}


# ---------- SIMULATED DATA ----------
@st.cache_data
def get_areas() -> pd.DataFrame:
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


@st.cache_data
def get_hourly() -> pd.DataFrame:
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
    for _, a in get_areas().iterrows():
        for i, (day, f) in enumerate(zip(DAYS, day_factor)):
            p = weekday if i < 5 else weekend
            v = a["Visits"] * f * p * rng.normal(1, 0.06, 24)
            rows += [(a["Area"], day, int(h), float(v[h])) for h in hours]
    return pd.DataFrame(rows, columns=["Area", "Day", "Hour", "Visits"])


@st.cache_data
def get_weekly() -> pd.DataFrame:
    """Simulated weekly visits for the last 12 weeks."""
    rng = np.random.default_rng(11)
    weeks = pd.date_range(end=pd.Timestamp.today().normalize(), periods=12, freq="W-MON")
    growth = {"Zone A": 0.012, "Zone B": 0.004, "Zone C": 0.018, "Zone D": -0.003, "Zone E": 0.008}
    frames = []
    for _, a in get_areas().iterrows():
        base = a["Visits"] * 7 * 0.9
        vals = base * (1 + growth[a["Area"]] * np.arange(12)) * rng.normal(1, 0.04, 12)
        frames.append(pd.DataFrame({"Area": a["Area"], "Week": weeks, "Visits": vals}))
    return pd.concat(frames, ignore_index=True)


@st.cache_data
def get_stores() -> pd.DataFrame:
    """Simulated store locations, matching each area's store count."""
    rng = np.random.default_rng(21)
    cats = list(CATEGORY_COLORS)
    rows = []
    for _, a in get_areas().iterrows():
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
    return pd.DataFrame(rows)


# ---------- HELPERS ----------
def header(title: str, caption: str) -> None:
    st.title(title)
    st.caption(caption)


def demo_note() -> None:
    st.info("Demo mode: all figures are simulated examples, not real customer visits or retail measurements.")


def style(fig, height=360):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Public Sans, sans-serif", color=TEXT),
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
    fig.update_traces(marker_color=[AMBER if v == top else TEAL for v in df[y]])
    fig.update_xaxes(title=None)
    return style(fig)


def show(fig) -> None:
    st.plotly_chart(fig, **STRETCH)


def table(df) -> None:
    st.dataframe(df, hide_index=True, **STRETCH)


def score_areas(w_demand=40, w_gap=40, w_base=20) -> pd.DataFrame:
    """Weighted site score: demand, under-served gap (visits per store) and baseline opportunity."""
    d = get_areas().copy()
    d["Visits per Store"] = d["Visits"] / d["Retail Stores"]

    def norm(s):
        return (s - s.min()) / (s.max() - s.min()) if s.max() > s.min() else s * 0 + 0.5

    total = (w_demand + w_gap + w_base) or 1
    d["Site Score"] = 100 * (
        w_demand * norm(d["Visits"])
        + w_gap * norm(d["Visits per Store"])
        + w_base * norm(d["Opportunity Score"])
    ) / total
    d["Rank"] = d["Site Score"].rank(ascending=False, method="first").astype(int)
    return d.sort_values("Rank").reset_index(drop=True)


def forecast(area: str, horizon: int, uplift: float = 0.0):
    """Linear trend projection with an 80% range. Not a trained ML model."""
    w = get_weekly()
    h = w[w["Area"] == area].reset_index(drop=True)
    x = np.arange(len(h))
    y = h["Visits"].to_numpy()
    slope, intercept = np.polyfit(x, y, 1)
    sigma = (y - (slope * x + intercept)).std(ddof=2)
    fx = np.arange(len(h), len(h) + horizon)
    fy = (slope * fx + intercept) * (1 + uplift)
    dates = h["Week"].iloc[-1] + pd.to_timedelta(7 * np.arange(1, horizon + 1), unit="D")
    fc = pd.DataFrame({"Week": dates, "Forecast": fy, "Low": fy - 1.28 * sigma, "High": fy + 1.28 * sigma})
    return h, fc


# ---------- PAGES ----------
def page_dashboard():
    header("Retail Intelligence Overview", "Hyper-local retail mobility analytics")
    demo_note()
    data = get_areas()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sample visits", f'{data["Visits"].sum():,}')
    c2.metric("Retail locations", f'{data["Retail Stores"].sum()}')
    c3.metric("Areas analyzed", f"{len(data)}")
    c4.metric("Avg. opportunity score", f'{data["Opportunity Score"].mean():.1f}/100')

    top = data.loc[data["Visits"].idxmax()]
    best = data.loc[data["Opportunity Score"].idxmax()]
    st.write(
        f'**{top["Area"]}** has the most visits ({top["Visits"]:,}), '
        f'and **{best["Area"]}** has the highest opportunity score ({best["Opportunity Score"]}/100).'
    )

    left, right = st.columns(2)
    with left:
        show(bar_chart(data, "Area", "Visits", "Simulated visits by area"))
    with right:
        show(bar_chart(data, "Area", "Opportunity Score", "Opportunity score by area"))

    st.subheader("Area data")
    table(data.drop(columns=["Latitude", "Longitude"]))


def page_heatmap():
    header("Mobility Heatmaps", "Interactive geographic retail mobility explorer")
    demo_note()
    locations = get_areas()

    c1, c2, c3 = st.columns([2, 1, 1])
    metric = c1.selectbox("Heat intensity", ["Visits", "Opportunity Score"])
    radius = c2.slider("Radius", 10, 50, 25)
    markers = c3.toggle("Show markers", value=True)

    m = folium.Map(location=[26.1445, 91.7362], zoom_start=13, tiles="CartoDB dark_matter")
    weights = (locations[metric] / locations[metric].max()).to_numpy()
    heat = [[la, lo, w] for la, lo, w in zip(locations["Latitude"], locations["Longitude"], weights)]
    HeatMap(heat, radius=radius, blur=20, gradient={0.3: TEAL, 0.6: AMBER, 1.0: RED}).add_to(m)

    if markers:
        for _, item in locations.iterrows():
            folium.Marker(
                location=[item["Latitude"], item["Longitude"]],
                tooltip=item["Area"],
                popup=(
                    f'Area: {item["Area"]}<br>'
                    f'Simulated visits: {item["Visits"]}<br>'
                    f'Opportunity: {item["Opportunity Score"]}/100'
                ),
                icon=folium.Icon(color="cadetblue", icon="shopping-cart"),
            ).add_to(m)

    st_folium(m, height=550, use_container_width=True, returned_objects=[])

    st.subheader("Mobility area data")
    table(locations)


def page_mobility():
    header("Customer Mobility", "When people visit each area, by hour and day")
    demo_note()
    hourly = get_hourly()
    all_areas = list(get_areas()["Area"])

    c1, c2 = st.columns([2, 1])
    selected = c1.multiselect("Areas", all_areas, default=all_areas)
    day_type = c2.selectbox("Days", ["All days", "Weekdays", "Weekends"])

    base = hourly[hourly["Area"].isin(selected)]
    if base.empty:
        st.info("Select at least one area to see mobility patterns.")
        return

    df = base
    if day_type == "Weekdays":
        df = base[base["Day"].isin(DAYS[:5])]
    elif day_type == "Weekends":
        df = base[base["Day"].isin(DAYS[5:])]

    daily = base.groupby("Day")["Visits"].sum().reindex(DAYS)
    peak_hour = int(df.groupby("Hour")["Visits"].sum().idxmax())
    uplift = daily[DAYS[5:]].mean() / daily[DAYS[:5]].mean() - 1

    m1, m2, m3 = st.columns(3)
    m1.metric("Peak hour", f"{peak_hour}:00")
    m2.metric("Busiest day", daily.idxmax())
    m3.metric("Weekend vs weekday", f"{uplift:+.0%}")

    by_hour = df.groupby(["Area", "Hour"], as_index=False)["Visits"].mean()
    fig = px.line(by_hour, x="Hour", y="Visits", color="Area", title=f"Average visits per hour ({day_type.lower()})")
    fig.update_xaxes(dtick=2)
    fig.update_yaxes(title="Visits per hour")
    show(style(fig, 380))

    pivot = base.groupby(["Day", "Hour"])["Visits"].sum().unstack("Hour").reindex(DAYS)
    heat = px.imshow(
        pivot,
        aspect="auto",
        color_continuous_scale=[[0, PANEL], [1, AMBER]],
        labels=dict(x="Hour", y="Day", color="Visits"),
        title="Visits by day and hour",
    )
    show(style(heat, 340))


def page_retail():
    header("Retail Location Intelligence", "Rank areas by demand, under-served gap and baseline opportunity")
    demo_note()

    st.write("Set how much each factor counts toward the site score.")
    c1, c2, c3 = st.columns(3)
    w_demand = c1.slider("Demand (visits)", 0, 100, 40, 5)
    w_gap = c2.slider("Under-served gap (visits per store)", 0, 100, 40, 5)
    w_base = c3.slider("Baseline opportunity score", 0, 100, 20, 5)

    if w_demand + w_gap + w_base == 0:
        st.warning("Give at least one factor a weight above zero.")
        return

    scored = score_areas(w_demand, w_gap, w_base)
    lead = scored.iloc[0]
    st.write(
        f'**{lead["Area"]}** ranks first with a site score of {lead["Site Score"]:.1f}, '
        f'driven by {lead["Visits"]:,} visits across {lead["Retail Stores"]} stores.'
    )

    left, right = st.columns(2)
    with left:
        show(bar_chart(scored, "Area", "Site Score", "Site score by area"))
    with right:
        fig = px.scatter(
            scored,
            x="Retail Stores",
            y="Visits",
            size="Site Score",
            color="Area",
            title="Visits vs store count (bubble = site score)",
            size_max=40,
        )
        show(style(fig))

    st.subheader("Ranking")
    out = scored[["Rank", "Area", "Visits", "Retail Stores", "Visits per Store", "Site Score"]].round(1)
    table(out)


def page_competitors():
    header("Competitor Analysis", "Where stores cluster and how crowded each area is")
    demo_note()
    stores = get_stores()
    areas = get_areas()

    c1, c2 = st.columns(2)
    cats = c1.multiselect("Store categories", list(CATEGORY_COLORS), default=list(CATEGORY_COLORS))
    sel_areas = c2.multiselect("Areas", list(areas["Area"]), default=list(areas["Area"]))

    view = stores[stores["Category"].isin(cats) & stores["Area"].isin(sel_areas)]
    if view.empty:
        st.info("No stores match these filters. Add a category or an area.")
        return

    counts = view.groupby("Area").size().rename("Stores").reset_index()
    crowded = counts.loc[counts["Stores"].idxmax()]
    m1, m2, m3 = st.columns(3)
    m1.metric("Stores shown", len(view))
    m2.metric("Most crowded area", f'{crowded["Area"]} ({crowded["Stores"]})')
    m3.metric("Most common category", view["Category"].mode().iloc[0])

    m = folium.Map(
        location=[view["Latitude"].mean(), view["Longitude"].mean()],
        zoom_start=13,
        tiles="CartoDB dark_matter",
    )
    for _, s in view.iterrows():
        color = CATEGORY_COLORS[s["Category"]]
        folium.CircleMarker(
            location=[s["Latitude"], s["Longitude"]],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            tooltip=f'{s["Store"]} ({s["Category"]})',
        ).add_to(m)
    st_folium(m, height=480, use_container_width=True, returned_objects=[])

    by_cat = view.groupby(["Area", "Category"]).size().rename("Stores").reset_index()
    fig = px.bar(
        by_cat,
        x="Area",
        y="Stores",
        color="Category",
        color_discrete_map=CATEGORY_COLORS,
        title="Stores by area and category (map colors match)",
    )
    fig.update_xaxes(title=None)
    show(style(fig))

    st.subheader("Saturation")
    sat = counts.merge(areas[["Area", "Visits"]], on="Area")
    sat["Visits per Store"] = (sat["Visits"] / sat["Stores"]).round(1)
    table(sat.sort_values("Visits per Store", ascending=False))
    st.caption("A higher visits-per-store figure means fewer stores share the same footfall.")


def page_predictive():
    header("Predictive Analytics", "Weekly visit projection from the recent trend")
    demo_note()

    c1, c2, c3 = st.columns(3)
    area = c1.selectbox("Area", list(get_areas()["Area"]))
    horizon = c2.slider("Weeks to project", 2, 8, 4)
    uplift = c3.slider("Scenario adjustment (%)", -20, 30, 0) / 100

    hist, fc = forecast(area, horizon, uplift)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=list(fc["Week"]) + list(fc["Week"])[::-1],
            y=list(fc["High"]) + list(fc["Low"])[::-1],
            fill="toself",
            fillcolor="rgba(242,169,59,0.18)",
            line=dict(width=0),
            hoverinfo="skip",
            name="80% range",
        )
    )
    fig.add_trace(go.Scatter(x=hist["Week"], y=hist["Visits"], mode="lines+markers", name="Actual (simulated)", line=dict(color=TEAL)))
    fig.add_trace(
        go.Scatter(
            x=[hist["Week"].iloc[-1]] + list(fc["Week"]),
            y=[hist["Visits"].iloc[-1]] + list(fc["Forecast"]),
            mode="lines+markers",
            name="Projection",
            line=dict(color=AMBER, dash="dash"),
        )
    )
    fig.update_layout(title=f"{area}: weekly visits")
    fig.update_yaxes(title="Visits per week")
    show(style(fig, 400))

    recent = hist["Visits"].tail(horizon).sum()
    projected = fc["Forecast"].sum()
    m1, m2, m3 = st.columns(3)
    m1.metric(f"Last {horizon} weeks", f"{recent:,.0f}")
    m2.metric(f"Next {horizon} weeks", f"{projected:,.0f}")
    m3.metric("Change", f"{projected / recent - 1:+.1%}")
    st.caption(
        "Method: straight-line trend fitted to 12 weeks of simulated data, shown with an 80% range. "
        "This is a simple projection, not a trained machine-learning model."
    )


def md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(out)


def page_reports():
    header("Analytics Reports", "Build a summary and download it")
    demo_note()
    areas = list(get_areas()["Area"])
    all_sections = ["Summary", "Site ranking", "Store saturation", "Visit projection"]

    c1, c2 = st.columns(2)
    sel = c1.multiselect("Areas", areas, default=areas)
    sections = c2.multiselect("Sections", all_sections, default=all_sections)
    if not sel or not sections:
        st.info("Choose at least one area and one section.")
        return

    scored = score_areas()
    scored = scored[scored["Area"].isin(sel)]
    lines = [
        "# GeoPulse retail report",
        f'Generated {pd.Timestamp.today().strftime("%d %b %Y")}. Data: simulated, for illustration only.',
        "",
    ]

    if "Summary" in sections:
        top = scored.iloc[0]
        lines += [
            "## Summary",
            f"- Areas covered: {', '.join(sel)}",
            f'- Total simulated visits: {int(scored["Visits"].sum()):,}',
            f'- Top site: {top["Area"]} (score {top["Site Score"]:.1f})',
            "",
        ]
    if "Site ranking" in sections:
        t = scored[["Rank", "Area", "Visits", "Retail Stores", "Site Score"]].round(1)
        lines += ["## Site ranking", md_table(t), ""]
    if "Store saturation" in sections:
        t = scored[["Area", "Retail Stores", "Visits"]].copy()
        t["Stores per 1,000 visits"] = (t["Retail Stores"] / t["Visits"] * 1000).round(1)
        lines += ["## Store saturation", md_table(t[["Area", "Retail Stores", "Stores per 1,000 visits"]]), ""]
    if "Visit projection" in sections:
        rows = []
        for a in sel:
            h, fc = forecast(a, 4)
            last, proj = h["Visits"].tail(4).sum(), fc["Forecast"].sum()
            rows.append({"Area": a, "Last 4 weeks": f"{last:,.0f}", "Next 4 weeks": f"{proj:,.0f}", "Change": f"{proj / last - 1:+.1%}"})
        lines += ["## Visit projection (simple trend)", md_table(pd.DataFrame(rows)), ""]

    report = "\n".join(lines)
    d1, d2, _ = st.columns([1, 1, 3])
    d1.download_button("Download report (.md)", report, file_name="geopulse_report.md", mime="text/markdown")
    d2.download_button("Download data (.csv)", scored.to_csv(index=False), file_name="geopulse_sites.csv", mime="text/csv")

    st.subheader("Preview")
    st.markdown(report)


# ---------- NAVIGATION ----------
PAGES = {
    "Dashboard": page_dashboard,
    "Mobility Heatmaps": page_heatmap,
    "Customer Mobility": page_mobility,
    "Retail Intelligence": page_retail,
    "Competitor Analysis": page_competitors,
    "Predictive Analytics": page_predictive,
    "Reports": page_reports,
}

st.sidebar.title("🌍 GeoPulse")
st.sidebar.caption("Hyper-local retail mobility analytics")
page = st.sidebar.radio("Navigation", list(PAGES), label_visibility="collapsed")
st.sidebar.divider()
st.sidebar.caption("Dataset: illustrative simulated data")

PAGES[page]()

st.divider()
st.caption("GeoPulse | Retail Location Intelligence Platform")
