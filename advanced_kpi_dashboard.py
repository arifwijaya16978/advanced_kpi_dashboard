import streamlit as st
import pandas as pd
import plotly.express as px

# =========================================
# PAGE CONFIG
# =========================================

st.set_page_config(
    page_title="Advanced NOC KPI Dashboard",
    layout="wide"
)

st.title("📊 Advanced NOC KPI Monitoring")

# =========================================
# FILE UPLOADER
# =========================================

uploaded_file = st.file_uploader("Upload KPI CSV File", type=["csv"])

if uploaded_file is None:
    st.info("Please upload a CSV file to start.")
    st.stop()

# =========================================
# LOAD DATA
# =========================================

df = pd.read_csv(uploaded_file)
df.columns = df.columns.str.strip().str.lower()

# =========================================
# VALIDATION
# =========================================

required_cols = ["date", "site", "traffic_gb", "availability", "lat", "lon"]

for col in required_cols:
    if col not in df.columns:
        st.error(f"Missing required column: {col}")
        st.stop()

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])

# =========================================
# SIDEBAR FILTER
# =========================================

st.sidebar.header("🔎 Filters")

site_list = ["All"] + sorted(df["site"].dropna().unique())
selected_site = st.sidebar.selectbox("Select Site", site_list)

date_range = st.sidebar.date_input(
    "Select Date Range",
    [df["date"].min(), df["date"].max()]
)

if selected_site != "All":
    df = df[df["site"] == selected_site]

df = df[
    (df["date"] >= pd.to_datetime(date_range[0])) &
    (df["date"] <= pd.to_datetime(date_range[1]))
]

# =========================================
# KPI SUMMARY
# =========================================

col1, col2, col3 = st.columns(3)

col1.metric("Total Sites", df["site"].nunique())
col2.metric("Avg Availability (%)", f"{df['availability'].mean():.2f}")
col3.metric("Total Traffic (GB)", f"{df['traffic_gb'].sum():,.0f}")

st.divider()

# =========================================
# CONGESTION DETECTION
# =========================================

st.subheader("🚨 Congestion Detection")

avail_threshold = st.slider("Availability Threshold (%)", 90, 100, 95)

if "prb" in df.columns:
    prb_threshold = st.slider("PRB Threshold (%)", 70, 100, 85)
    df["congestion"] = (df["availability"] < avail_threshold) | (df["prb"] > prb_threshold)
else:
    df["congestion"] = df["availability"] < avail_threshold

congested = df[df["congestion"]]

st.write("Total Congested Records:", congested.shape[0])

if not congested.empty:
    st.dataframe(congested)
else:
    st.success("No congestion detected")

st.divider()

# =========================================
# CHART FUNCTION
# =========================================

def create_chart(title, column):

    if column not in df.columns:
        st.warning(f"Column '{column}' not found")
        return None

    chart_df = df.groupby("date")[column].mean().reset_index()

    fig = px.line(
        chart_df,
        x="date",
        y=column,
        title=title,
        markers=True
    )

    return fig

# =========================================
# TRAFFIC TREND
# =========================================

st.subheader("📈 Traffic Trend")

traffic_chart = create_chart("Traffic (GB) Trend", "traffic_gb")

if traffic_chart:
    st.plotly_chart(traffic_chart, use_container_width=True)

# =========================================
# AVAILABILITY TREND
# =========================================

st.subheader("📉 Availability Trend")

avail_chart = create_chart("Availability Trend", "availability")

if avail_chart:
    st.plotly_chart(avail_chart, use_container_width=True)

st.divider()

# =========================================
# MAP
# =========================================

st.subheader("🗺 Site Location Map")

map_df = df.dropna(subset=["lat", "lon"])

if not map_df.empty:

    fig_map = px.scatter_mapbox(
        map_df,
        lat="lat",
        lon="lon",
        color="availability",
        hover_name="site",
        zoom=6,
        height=600
    )

    fig_map.update_layout(mapbox_style="open-street-map")

    st.plotly_chart(fig_map, use_container_width=True)

else:
    st.warning("No valid lat/lon data available")
