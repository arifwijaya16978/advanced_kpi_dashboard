import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# =============================
# THEME
# =============================
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

st.button("TOGGLE THEME", on_click=toggle_theme)

template_style = "plotly_dark" if st.session_state.theme == "dark" else "plotly"

st.title("📊 KPI Dashboard Performance")

# =============================
# FILE UPLOAD
# =============================
file = st.file_uploader("Choose CSV File", type=["csv"])

if file:

    df = pd.read_csv(file)

    # CLEAN HEADER (ANTI SPASI)
    df.columns = df.columns.str.strip()

    st.success(f"{len(df)} rows ready.")

    # =============================
    # RENAME COLUMN BIAR SERAGAM
    # =============================
    df = df.rename(columns={
        "Date": "date",
        "eNodeBName": "site",
        "Sector": "sector",
        "Band": "band",
        "Payload": "payload",
        "PRB": "prb",
        "Availability": "availability",
        "Lat": "lat",
        "Lon": "lon"
    })

    # CONVERT DATE
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # =============================
    # FIX LAT LON (PENTING)
    # =============================
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")

    # AUTO DETECT KEBALIK (Indonesia logic)
    # Indonesia lat biasanya antara -11 sampai 6
    if df["lat"].abs().mean() > 50:
        st.warning("Lat/Lon seems reversed. Auto correcting...")
        df[["lat", "lon"]] = df[["lon", "lat"]]

    # DROP KOORDINAT INVALID
    df = df.dropna(subset=["lat", "lon"])

    # =============================
    # SIDEBAR FILTER
    # =============================
    st.sidebar.header("FILTER CONTROL")

    site = st.sidebar.selectbox("Site", ["All"] + list(df["site"].unique()))
    sector = st.sidebar.selectbox("Sector", ["All"] + list(df["sector"].unique()))
    band = st.sidebar.selectbox("Band", ["All"] + list(df["band"].unique()))

    hide_marker = st.sidebar.checkbox("Hide Markers")
    slim_line = st.sidebar.checkbox("Slim Lines")

    kpi_target = st.sidebar.number_input("Set KPI Target Line", value=0.0)

    start_date = st.sidebar.date_input("Start Date", df["date"].min())
    end_date = st.sidebar.date_input("End Date", df["date"].max())

    # =============================
    # APPLY FILTER
    # =============================
    if site != "All":
        df = df[df["site"] == site]

    if sector != "All":
        df = df[df["sector"] == sector]

    if band != "All":
        df = df[df["band"] == band]

    df = df[(df["date"] >= pd.to_datetime(start_date)) &
            (df["date"] <= pd.to_datetime(end_date))]

    # =============================
    # CHART FUNCTION
    # =============================
    def create_chart(title, column):

        mode = "lines"
        if not hide_marker:
            mode = "lines+markers"

        line_width = 1 if slim_line else 3

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df[column],
            mode=mode,
            line=dict(width=line_width),
            name=column
        ))

        if kpi_target != 0:
            fig.add_hline(y=kpi_target, line_dash="dash", line_color="red")

        fig.update_layout(
            title=title,
            template=template_style,
            height=350
        )

        return fig

    # =============================
    # TABS
    # =============================
    tab1, tab2, tab3 = st.tabs([
        "📈 Sector Productivity",
        "📊 Site Summary",
        "🗺 Geo Map"
    ])

    # =============================
    # TAB 1
    # =============================
    def create_chart(title, column):
    if column not in df.columns:
        st.warning(f"Column '{column}' not found")
        return px.line(title=f"{title} (No Data)")

    fig = px.line(df, x="date", y=column, title=title)
    return fig
    
    with tab1:
        st.plotly_chart(create_chart("Traffic Trend", "traffic_gb"), use_container_width=True)
        st.plotly_chart(create_chart("PRB Trend", "prb"), use_container_width=True)
        st.plotly_chart(create_chart("Availability Trend", "availability"), use_container_width=True)

    # =============================
    # TAB 2
    # =============================
    with tab2:
        summary = df.groupby("site").mean(numeric_only=True)
        st.dataframe(summary)

    # =============================
    # TAB 3 (GEO MAP FIXED)
    # =============================
    with tab3:

        st.subheader("Site Location Map")

        if len(df) > 0:
            st.map(df[["lat", "lon"]])
        else:

            st.info("No data available for selected filter.")
