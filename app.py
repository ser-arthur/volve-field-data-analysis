import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


# Increase the limit for styled dataframes
pd.set_option("styler.render.max_elements", 500000)

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Volve Field Analytics Dashboard", layout="wide")

# --- DATA LOADING (CACHED) ---
@st.cache_data
def load_data():
    # Loading from the main cumulative sheet as per notebook logic
    file_path = "oilwell_production_data.xlsx"
    sheets_dict = pd.read_excel(file_path, sheet_name=None)

    # Process main production data
    df = sheets_dict["Daily Production Data"]
    df["DATEPRD"] = pd.to_datetime(df["DATEPRD"])
    df.rename(columns={"NPD_WELL_BORE_NAME": "WELL_NAME"}, inplace=True)

    # Cleaning and sorting
    df = df.dropna(subset=['DATEPRD'])
    df = df.sort_values('DATEPRD')
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}. Ensure 'oilwell_production_data.xlsx' is in the directory.")
    st.stop()

# --- SIDEBAR FILTERS ---
st.sidebar.header("Dashboard Filters")
well_list = sorted(df["WELL_NAME"].unique())
selected_well = st.sidebar.selectbox("Select Wellbore", ["All Wells"] + well_list)

min_date = df["DATEPRD"].min()
max_date = df["DATEPRD"].max()
date_range = st.sidebar.date_input("Date Range", [min_date, max_date])

# Filter Data
filtered_df = df.copy()
if selected_well != "All Wells":
    filtered_df = filtered_df[filtered_df["WELL_NAME"] == selected_well]
filtered_df = filtered_df[(filtered_df["DATEPRD"] >= pd.Timestamp(date_range[0])) &
                          (filtered_df["DATEPRD"] <= pd.Timestamp(date_range[1]))]

# --- MAIN DASHBOARD ---
st.title("🛢️ Volve Field Production Analytics")
st.markdown("Interactive dashboard for Equinor's Volve Field dataset analysis.")

# KPI Metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    total_oil = filtered_df["BORE_OIL_VOL"].sum()
    st.metric("Total Oil (Sm³)", f"{total_oil:,.0f}")
with col2:
    total_gas = filtered_df["BORE_GAS_VOL"].sum()
    st.metric("Total Gas (Sm³)", f"{total_gas:,.0f}")
with col3:
    total_water = filtered_df["BORE_WAT_VOL"].sum()
    st.metric("Total Water (Sm³)", f"{total_water:,.0f}")
with col4:
    avg_press = filtered_df["AVG_DOWNHOLE_PRESSURE"].mean()
    st.metric("Avg. DH Pressure (bar)", f"{avg_press:.1f}")

# --- TABS FOR ORGANIZED ANALYSIS ---
tab1, tab2, tab3 = st.tabs(["Performance Trends", "Reservoir Analytics", "Operations"])

with tab1:
    st.subheader("Production & Pressure Profiles")
    # Multi-axis chart: Oil Rate and Downhole Pressure
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=filtered_df["DATEPRD"], y=filtered_df["BORE_OIL_VOL"],
                             name="Oil Volume", line=dict(color="#1f4e79")))
    fig.add_trace(go.Scatter(x=filtered_df["DATEPRD"], y=filtered_df["AVG_DOWNHOLE_PRESSURE"],
                             name="DH Pressure", yaxis="y2", line=dict(color="red", dash='dot')))

    fig.update_layout(
        yaxis=dict(title="Oil Volume (Sm³)"),
        yaxis2=dict(title="Pressure (bar)", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Fluid Behavior & Depletion")
    col_a, col_b = st.columns(2)

    with col_a:
        # GOR Trend Analysis
        fig_gor = px.line(filtered_df, x="DATEPRD", y="GOR", color="WELL_NAME",
                          title="Gas-Oil Ratio (GOR) Trend")
        st.plotly_chart(fig_gor, use_container_width=True)

    with col_b:
        # Water-Oil Ratio (WOR) for breakthrough detection
        if "WOR" in filtered_df.columns:
            fig_wor = px.line(filtered_df, x="DATEPRD", y="WOR", color="WELL_NAME",
                              title="Water-Oil Ratio (WOR) Trend")
            st.plotly_chart(fig_wor, use_container_width=True)

with tab3:
    st.subheader("Well Operational Status")
    # On-Stream Hours visualization
    fig_uptime = px.bar(filtered_df, x="DATEPRD", y="ON_STREAM_HRS", color="WELL_NAME",
                        title="Daily On-Stream Hours per Well")
    st.plotly_chart(fig_uptime, use_container_width=True)

# Data Table Preview
# Data Table Preview
with st.expander("View Raw Filtered Data"):
    if selected_well == "All Wells":
        # Display without heavy styling for performance on large datasets
        st.dataframe(filtered_df, use_container_width=True)
        st.info("💡 Pro-tip: Select a specific well in the sidebar to see highlighted performance peaks.")
    # Data Table Preview
with st.expander("View Raw Filtered Data"):
    if selected_well == "All Wells":
        # Keep it simple for large data to avoid memory/render errors
        st.dataframe(filtered_df, use_container_width=True)
    else:
        # Define specific numeric columns that actually matter for highlighting
        # Based on your Volve pynb file analysis
        analysis_cols = [
            'ON_STREAM_HRS', 'AVG_DOWNHOLE_PRESSURE', 'BORE_OIL_VOL',
            'BORE_GAS_VOL', 'BORE_WAT_VOL', 'GOR'
        ]

        # Ensure we only try to style columns that exist in the filtered data
        cols_to_style = [c for c in analysis_cols if c in filtered_df.columns]

        st.dataframe(
            filtered_df.style.highlight_max(axis=0, subset=cols_to_style, color='#2e7d32'),
            use_container_width=True
        )