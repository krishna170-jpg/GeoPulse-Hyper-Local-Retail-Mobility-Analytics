import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="GeoPulse | Retail Intelligence",
    page_icon="🌍",
    layout="wide"
)

# ---------- DESIGN ----------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #081827, #102c42);
    color: #ffffff;
}
[data-testid="stSidebar"] {
    background: #0d2039;
}
h1, h2, h3, p, label {
    color: #e8f4fa !important;
}
div[data-testid="stMetric"] {
    background: #16364d;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #24556a;
}
</style>
""", unsafe_allow_html=True)

# ---------- SIDEBAR ----------
st.sidebar.title("🌍 GeoPulse")
st.sidebar.caption("Hyper-Local Retail Mobility Analytics")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Mobility Heatmaps",
        "Customer Mobility",
        "Retail Intelligence",
        "Competitor Analysis",
        "Predictive Analytics",
        "Reports"
    ]
)

st.sidebar.divider()
st.sidebar.success("System initialized")
st.sidebar.caption("Dataset: Illustrative simulated data")

# ---------- SAMPLE DATA ----------
data = pd.DataFrame({
    "Area": ["Zone A", "Zone B", "Zone C", "Zone D", "Zone E"],
    "Visits": [1250, 980, 1560, 740, 1120],
    "Retail Stores": [12, 9, 15, 6, 11],
    "Opportunity Score": [78, 65, 89, 54, 73]
})

# ---------- DASHBOARD ----------
st.title("🌍 GeoPulse")
st.caption("Hyper-Local Retail Mobility Analytics")
st.divider()

if page == "Dashboard":

    st.subheader("Retail Intelligence Overview")

    st.info(
        "Demo mode: All figures below are simulated examples, "
        "not actual customer visits or retail measurements."
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Sample Visits", "5,650")
    c2.metric("Retail Locations", "53")
    c3.metric("Areas Analyzed", "5")
    c4.metric("Avg. Opportunity Score", "71.8/100")

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Mobility by Area")
        fig = px.bar(
            data,
            x="Area",
            y="Visits",
            color="Visits",
            title="Illustrative Area Visits"
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Retail Opportunity")
        fig2 = px.bar(
            data,
            x="Area",
            y="Opportunity Score",
            color="Opportunity Score",
            title="Illustrative Opportunity Scores"
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Area Data")
    st.dataframe(data, use_container_width=True)

elif page == "Mobility Heatmaps":
    st.title("🗺️ Mobility Heatmaps")
    st.caption("Interactive geographic retail mobility explorer")

    st.warning(
        "Demo mode: These are simulated locations and mobility values, "
        "not verified customer movements or real retail locations."
    )

    locations = pd.DataFrame({
        "Area": ["Zone A", "Zone B", "Zone C", "Zone D", "Zone E"],
        "Latitude": [26.1445, 26.1500, 26.1380, 26.1580, 26.1300],
        "Longitude": [91.7362, 91.7450, 91.7280, 91.7320, 91.7500],
        "Visits": [1250, 980, 1560, 740, 1120],
        "Opportunity": [78, 65, 89, 54, 73]
    })

    m = folium.Map(
        location=[26.1445, 91.7362],
        zoom_start=13,
        tiles="OpenStreetMap"
    )

    heat_data = locations[["Latitude", "Longitude", "Visits"]].values.tolist()

    from folium.plugins import HeatMap
    HeatMap(heat_data, radius=25, blur=20).add_to(m)

    for _, item in locations.iterrows():
        folium.Marker(
            location=[item["Latitude"], item["Longitude"]],
            tooltip=item["Area"],
            popup=(
                f'Area: {item["Area"]}<br>'
                f'Simulated visits: {item["Visits"]}<br>'
                f'Opportunity: {item["Opportunity"]}/100'
            ),
            icon=folium.Icon(color="cadetblue", icon="shopping-cart")
        ).add_to(m)

    st_folium(m, width=None, height=550, use_container_width=True)

    st.subheader("Mobility Area Data")
    st.dataframe(locations, use_container_width=True)

elif page == "Customer Mobility":
    st.title("Customer Mobility Analytics")
    st.info("Time-based mobility analysis will be added here.")

elif page == "Retail Intelligence":
    st.title("Retail Location Intelligence")
    st.info("Retail location scoring will be added here.")

elif page == "Competitor Analysis":
    st.title("Competitor Analysis")
    st.info("Competitor mapping will be added here.")

elif page == "Predictive Analytics":
    st.title("Predictive Analytics")
    st.info("Machine learning models will be added here.")

elif page == "Reports":
    st.title("Analytics Reports")
    st.info("Report generation will be added here.")

st.divider()
st.caption("GeoPulse | Retail Location Intelligence Platform")
