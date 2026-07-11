import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import warnings

# ==========================================
# 1. CONFIGURATION & STYLING
# ==========================================
st.set_page_config(layout="wide", page_title="Volve Field Analytics", page_icon="🛢️")

# Suppress FutureWarnings to clean up console output
warnings.simplefilter(action='ignore', category=FutureWarning)

# Custom CSS for Glassmorphism & Modern Typography
st.markdown("""
    <style>
    /* Font Import */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

    /* Global Font */
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
    }

    /* Header Colors */
    h1 { color: #2C3E50; font-weight: 700; }
    h2 { color: #34495E; font-weight: 600; border-bottom: 2px solid #ECF0F1; padding-bottom: 10px; }
    h3 { color: #16A085; font-weight: 600; } /* Emerald Green for Section Titles */
    h4 { color: #2980B9; font-weight: 500; } /* Blue for Sub-sections */
    h5 { color: #7F8C8D; font-weight: 500; }

    /* Metric Cards (Dark Console) */
    div[data-testid="stMetric"] {
        background-color: #161B22;
        border: 1px solid #30363D;
        padding: 15px;
        border-radius: 8px;
        transition: transform 0.2s, border-color 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: #4B5563;
    }
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] p {
        color: #8B949E !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #FAFAFA !important;
    }

    /* Glassmorphism Insight Box Class */
    .insight-box {
        background: rgba(235, 245, 251, 0.7); /* Light Blue Transparent */
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(52, 152, 219, 0.3); /* Darker Blue Border */
        border-left: 5px solid #3498DB; /* Accent Bar */
        border-radius: 10px;
        padding: 20px;
        margin-top: 15px;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    .insight-title {
        color: #2874A6;
        font-weight: bold;
        font-size: 1.1em;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
    }
    .insight-content {
        color: #2C3E50;
        line-height: 1.6;
        font-size: 0.95em;
    }
    </style>
""", unsafe_allow_html=True)


# Helper Function for Insight Boxes
def render_insight(title, content):
    html_code = f"""
    <div class="insight-box">
        <div class="insight-title">💡 {title}</div>
        <div class="insight-content">{content}</div>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)


@st.cache_data
def load_data():
    file_path = 'oilwell_production_data.xlsx'
    try:
        df = pd.read_excel(file_path, sheet_name='Daily Production Data')
        df['DATEPRD'] = pd.to_datetime(df['DATEPRD'])
        df = df[df['ON_STREAM_HRS'] > 0]
        return df
    except FileNotFoundError:
        st.error(f"File '{file_path}' not found. Please ensure it is in the directory.")
        return pd.DataFrame()


df = load_data()
if df.empty:
    st.stop()

# ==========================================
# 2. SIDEBAR NAVIGATION
# ==========================================
st.sidebar.title("🛢️ Volve Analytics")
page = st.sidebar.radio("Navigation:", ["1. Field Overview", "2. Well Diagnostics"])

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Settings")

min_date = df['DATEPRD'].min().date()
max_date = df['DATEPRD'].max().date()
start_date, end_date = st.sidebar.slider(
    "Analysis Period:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    format="YYYY-MM-DD"
)

resample_freq = st.sidebar.radio(
    "Data Resolution:",
    ["Monthly (Smoothed)", "Daily (Granular)"],
    index=0
)
is_monthly = "Monthly" in resample_freq

# ==========================================
# DATA PROCESSING
# ==========================================
mask = (df['DATEPRD'].dt.date >= start_date) & (df['DATEPRD'].dt.date <= end_date)
df_filtered = df.loc[mask].copy()


def get_field_data(df_in, monthly=True):
    agg_rules = {
        'BORE_OIL_VOL': 'sum',
        'BORE_GAS_VOL': 'sum',
        'BORE_WAT_VOL': 'sum',
        'BORE_WI_VOL': 'sum',
        'AVG_DOWNHOLE_PRESSURE': 'mean'
    }
    daily_field = df_in.groupby('DATEPRD').agg(agg_rules)

    if monthly:
        # UPDATED: Use 'ME' (Month End) instead of 'M' to fix Pandas warning
        data = daily_field.resample('ME').agg(agg_rules)
    else:
        data = daily_field

    data['Total_Liq'] = data['BORE_OIL_VOL'] + data['BORE_WAT_VOL']
    data['Water_Cut'] = (data['BORE_WAT_VOL'] / data['Total_Liq'].replace(0, 1)) * 100
    data['GOR'] = data['BORE_GAS_VOL'] / data['BORE_OIL_VOL'].replace(0, 1)
    data['VRR'] = data['BORE_WI_VOL'] / data['Total_Liq'].replace(0, 1)
    return data


field_data = get_field_data(df_filtered, monthly=is_monthly)

# ==========================================
# PAGE 1: FIELD OVERVIEW
# ==========================================
if page == "1. Field Overview":
    st.title("Field Analytics Dashboard")
    st.markdown("### Field-Wide Production Metrics")

    # KPI CARDS
    latest = field_data.iloc[-1]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Oil Rate", f"{latest['BORE_OIL_VOL']:,.0f} Sm³/d")
    col2.metric("Water Cut", f"{latest['Water_Cut']:.1f} %", delta_color="inverse")
    col3.metric("Voidage Rep. Ratio (VRR)", f"{latest['VRR']:.2f}", delta=f"{latest['VRR'] - 1:.2f}")
    col4.metric("Avg Reservoir Pressure", f"{latest['AVG_DOWNHOLE_PRESSURE']:.0f} Bar")

    st.markdown("---")

    # ROW 1: PRODUCTION
    st.markdown("### 1. Production Overview")
    max_liq = field_data['Total_Liq'].max() * 1.1
    fig_prod = make_subplots(specs=[[{"secondary_y": True}]])

    fig_prod.add_trace(
        go.Scatter(x=field_data.index, y=field_data['BORE_OIL_VOL'], mode='lines', name='Oil Rate', stackgroup='one',
                   line=dict(width=0, color='#27AE60')), secondary_y=False)
    fig_prod.add_trace(
        go.Scatter(x=field_data.index, y=field_data['BORE_WAT_VOL'], mode='lines', name='Water Rate', stackgroup='one',
                   line=dict(width=0, color='#2980B9')), secondary_y=False)
    fig_prod.add_trace(go.Scatter(x=field_data.index, y=field_data['BORE_GAS_VOL'], mode='lines', name='Gas Rate',
                                  line=dict(color='#C0392B', dash='dot', width=2)), secondary_y=True)

    # Breakthrough Marker
    breakthrough_check = field_data[field_data['BORE_WAT_VOL'] > field_data['BORE_OIL_VOL']]
    if not breakthrough_check.empty:
        bt_date = breakthrough_check.index[0]
        if start_date <= bt_date.date() <= end_date:
            bt_date_numeric = bt_date.timestamp() * 1000
            fig_prod.add_vline(x=bt_date_numeric, line_width=2, line_dash="dash", line_color="#2C3E50",
                               annotation_text="Water Breakthrough", annotation_position="top left")

    fig_prod.update_layout(height=450, hovermode="x unified", margin=dict(l=20, r=20, t=20, b=20))
    fig_prod.update_yaxes(title_text="Liquid Rate (Sm³/d)", range=[0, max_liq], secondary_y=False)
    fig_prod.update_yaxes(title_text="Gas Rate (Sm³/d)", secondary_y=True)
    st.plotly_chart(fig_prod, use_container_width=True)

    render_insight(
        "Reservoir Engineering Analysis",
        """
        <ul>
            <li><b>Water Breakthrough:</b> The 'Blue Wedge' expansion marks the arrival of the water front. The dashed line indicates the exact economic tipping point where water production exceeded oil production.</li>
            <li><b>Implication:</b> Post-breakthrough operations require shifting focus from 'Plateau Maintenance' to 'Decline Management' and handling increased lifting costs.</li>
        </ul>
        """
    )

    # ROW 2: VOIDAGE
    st.markdown("### 2. Reservoir Health (Voidage Replacement)")
    y_inj, y_prod = field_data['BORE_WI_VOL'], field_data['Total_Liq']
    fig_void = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, row_heights=[0.7, 0.3],
                             subplot_titles=("Voidage Volumes", "VRR Trend"))

    fig_void.add_trace(go.Scatter(x=field_data.index, y=y_prod, mode='lines', name='Total Production',
                                  line=dict(color='black', dash='dash')), row=1, col=1)
    fig_void.add_trace(go.Scatter(x=field_data.index, y=np.where(y_inj > y_prod, y_inj, y_prod), fill='tonexty',
                                  fillcolor='rgba(46, 204, 113, 0.3)', line=dict(width=0), name='Surplus'), row=1,
                       col=1)
    fig_void.add_trace(go.Scatter(x=field_data.index, y=np.where(y_prod > y_inj, y_prod, y_inj), fill='tonexty',
                                  fillcolor='rgba(231, 76, 60, 0.3)', line=dict(width=0), name='Deficit'), row=1, col=1)
    fig_void.add_trace(
        go.Scatter(x=field_data.index, y=y_inj, mode='lines', name='Injection Rate', line=dict(color='#3498DB')), row=1,
        col=1)
    fig_void.add_trace(go.Scatter(x=field_data.index, y=field_data['VRR'], line=dict(color='#8E44AD'), name='VRR'),
                       row=2, col=1)
    fig_void.add_shape(type="line", x0=field_data.index.min(), x1=field_data.index.max(), y0=1, y1=1,
                       line=dict(color="red", dash="dash"), row=2, col=1)

    fig_void.update_layout(height=500, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_void, use_container_width=True)

    render_insight(
        "Voidage Replacement Strategy",
        """
        <b>VRR Target = 1.0</b>. 
        <br>• <b>Green Zone (Surplus):</b> Injection > Production. Indicates successful repressurization efforts to support reservoir energy.
        <br>• <b>Red Zone (Deficit):</b> Production > Injection. Indicates pressure depletion, which can lead to gas cap expansion or compaction.
        """
    )

    # ROW 3: PHASE DIAGNOSTICS
    st.markdown("### 3. Phase Behavior Diagnostics")
    c_phase_toggle, _ = st.columns([1, 4])
    with c_phase_toggle:
        phase_res = st.radio("Resolution:", ["Daily (Granular)", "Monthly (Smooth)"], index=0, horizontal=True,
                             key="field_phase_res", label_visibility="collapsed")

    if "Daily" in phase_res:
        plot_data = df_filtered.groupby('DATEPRD')[['BORE_GAS_VOL', 'BORE_OIL_VOL', 'BORE_WAT_VOL']].sum()
        plot_data['Water_Cut'] = (plot_data['BORE_WAT_VOL'] / (
                    plot_data['BORE_OIL_VOL'] + plot_data['BORE_WAT_VOL']).replace(0, 1)) * 100
        plot_data['GOR'] = plot_data['BORE_GAS_VOL'] / plot_data['BORE_OIL_VOL'].replace(0, 1)
    else:
        plot_data = field_data

    fig_phase = make_subplots(specs=[[{"secondary_y": True}]])
    fig_phase.add_trace(go.Scatter(x=plot_data.index, y=plot_data['Water_Cut'], name='Water Cut %',
                                   line=dict(color='#2980B9', width=1.5), fill='tozeroy',
                                   fillcolor='rgba(41, 128, 185, 0.1)'), secondary_y=False)
    fig_phase.add_trace(
        go.Scatter(x=plot_data.index, y=plot_data['GOR'], name='GOR', line=dict(color='#D35400', width=1.5)),
        secondary_y=True)

    if start_date <= pd.Timestamp("2012-08-14").date() and end_date >= pd.Timestamp("2012-09-29").date():
        fig_phase.add_vrect(x0="2012-08-14", x1="2012-09-29", fillcolor="grey", opacity=0.2,
                            annotation_text="Facility Turnaround (TAR)", annotation_position="top left")

    fig_phase.update_layout(height=450, hovermode="x unified", margin=dict(l=20, r=20, t=20, b=20))
    fig_phase.update_yaxes(title_text="Water Cut (%)", range=[0, 100], secondary_y=False)
    fig_phase.update_yaxes(title_text="GOR (Sm³/Sm³)", secondary_y=True)
    st.plotly_chart(fig_phase, use_container_width=True)

    render_insight(
        "Drive Mechanism Diagnostics",
        """
        <b>Interpretation of GOR Trends:</b>
        <br>The remarkably flat GOR trend (visible in Granular view) confirms that reservoir pressure was successfully maintained <b>above the Bubble Point Pressure</b>. The primary drive mechanism is Water Injection Support, with no evidence of Gas Cap Blowdown.
        """
    )

    # ROW 4: STRATEGY
    st.markdown("### 4. Strategic Planning & Efficiency")

    # Calculate FULL history for Strat plots (needs all data to be accurate)
    df_full_sorted = df.sort_values('DATEPRD')
    field_daily_full = df_full_sorted.groupby('DATEPRD')[['BORE_OIL_VOL', 'BORE_WI_VOL']].sum()
    field_daily_full['Cum_Oil'] = field_daily_full['BORE_OIL_VOL'].cumsum() / 1e6
    field_daily_full['Cum_Inj'] = field_daily_full['BORE_WI_VOL'].cumsum() / 1e6
    mask_strat = (field_daily_full.index.date >= start_date) & (field_daily_full.index.date <= end_date)
    strat_data = field_daily_full.loc[mask_strat]

    c1, c2 = st.columns(2)
    with c1:
        fig_crm = go.Figure(
            go.Scatter(x=strat_data['Cum_Inj'], y=strat_data['Cum_Oil'], line=dict(color='#27AE60', width=3)))
        fig_crm.update_layout(title="Creaming Curve (Efficiency)", xaxis_title="Cum Injection (MM Sm³)",
                              yaxis_title="Cum Oil (MM Sm³)", height=400, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_crm, use_container_width=True)
    with c2:
        valid_rates = strat_data[strat_data['BORE_OIL_VOL'] > 10]
        fig_dcl = go.Figure(go.Scattergl(x=valid_rates['Cum_Oil'], y=valid_rates['BORE_OIL_VOL'], mode='markers',
                                         marker=dict(color='#E67E22', size=3, opacity=0.5)))
        fig_dcl.update_layout(title="Decline Curve Analysis", xaxis_title="Cum Oil (MM Sm³)",
                              yaxis_title="Oil Rate (Log Scale)", yaxis_type="log", height=400,
                              margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_dcl, use_container_width=True)

# ==========================================
# PAGE 2: WELL DIAGNOSTICS
# ==========================================
elif page == "2. Well Diagnostics":
    st.title("Well Performance Diagnostics")

    # CLASSIFICATION
    well_sums = df.groupby('NPD_WELL_BORE_NAME')[['BORE_OIL_VOL', 'BORE_WI_VOL']].sum()
    producers = well_sums[well_sums['BORE_OIL_VOL'] > 100].index.tolist()
    injectors = well_sums[well_sums['BORE_WI_VOL'] > 100].index.tolist()
    producers.sort()
    injectors.sort()

    c_sel1, c_sel2 = st.columns([1, 3])
    with c_sel1:
        well_type = st.radio("Select Well Type:", ["Producers ", "Injectors"])
    with c_sel2:
        well_list = producers if "Producers" in well_type else injectors
        default_ix = well_list.index('15/9-F-14') if '15/9-F-14' in well_list else 0
        selected_well = st.selectbox("Select Target Well:", well_list, index=default_ix)

    if "Producers" in well_type:
        tab1, tab2, tab3 = st.tabs(["📊 Individual Analysis", "📈 Comparative Analytics", "🕸️ Connectivity"])

        with tab1:
            st.markdown(f"### Deep Dive: {selected_well}")

            # Fetch Well Data
            well_full_hist = df[df['NPD_WELL_BORE_NAME'] == selected_well].sort_values('DATEPRD').copy()
            well_full_hist['Cum_Oil'] = well_full_hist['BORE_OIL_VOL'].cumsum() / 1e6
            mask_well = (well_full_hist['DATEPRD'].dt.date >= start_date) & (
                        well_full_hist['DATEPRD'].dt.date <= end_date)
            well_filtered = well_full_hist.loc[mask_well].copy()

            if is_monthly:
                wdata = well_filtered.resample('ME', on='DATEPRD').agg(
                    {'BORE_OIL_VOL': 'sum', 'BORE_WAT_VOL': 'sum', 'BORE_GAS_VOL': 'sum', 'ON_STREAM_HRS': 'mean',
                     'AVG_DOWNHOLE_PRESSURE': 'mean', 'Cum_Oil': 'last'})
                wdata['Total_Liq'] = wdata['BORE_OIL_VOL'] + wdata['BORE_WAT_VOL']
                wdata['WC'] = (wdata['BORE_WAT_VOL'] / wdata['Total_Liq'].replace(0, 1)) * 100
                wdata['GOR'] = wdata['BORE_GAS_VOL'] / wdata['BORE_OIL_VOL'].replace(0, 1)
            else:
                wdata = well_filtered.set_index('DATEPRD')
                wdata['Total_Liq'] = wdata['BORE_OIL_VOL'] + wdata['BORE_WAT_VOL']
                wdata['WC'] = (wdata['BORE_WAT_VOL'] / wdata['Total_Liq'].replace(0, 1)) * 100
                wdata['GOR'] = wdata['BORE_GAS_VOL'] / wdata['BORE_OIL_VOL'].replace(0, 1)

            if wdata.empty:
                st.warning("No data available.")
            else:
                # Plot 1
                st.markdown("#### 1. Production History & Support")
                show_field_inj = st.checkbox("Overlay Total Field Injection", value=False)
                fig_w = make_subplots(specs=[[{"secondary_y": True}]])
                fig_w.add_trace(go.Scatter(x=wdata.index, y=wdata['BORE_OIL_VOL'], stackgroup='one', name='Oil',
                                           line=dict(width=0, color='#27AE60')), secondary_y=False)
                fig_w.add_trace(go.Scatter(x=wdata.index, y=wdata['BORE_WAT_VOL'], stackgroup='one', name='Water',
                                           line=dict(width=0, color='#2980B9')), secondary_y=False)

                if show_field_inj:
                    field_inj = df.groupby('DATEPRD')['BORE_WI_VOL'].sum()
                    mask_fi = (field_inj.index.date >= start_date) & (field_inj.index.date <= end_date)
                    f_inj_data = field_inj.loc[mask_fi]
                    if is_monthly: f_inj_data = f_inj_data.resample('ME').sum()
                    fig_w.add_trace(go.Scatter(x=f_inj_data.index, y=f_inj_data, name='Total Field Inj',
                                               line=dict(color='#8E44AD', width=2, dash='solid')), secondary_y=True)
                    fig_w.update_yaxes(title_text="Field Inj Rate", secondary_y=True)
                else:
                    fig_w.add_trace(go.Scatter(x=wdata.index, y=wdata['BORE_GAS_VOL'], name='Gas',
                                               line=dict(color='#C0392B', dash='dot')), secondary_y=True)
                    fig_w.update_yaxes(title_text="Gas Rate", secondary_y=True)

                fig_w.update_yaxes(title_text="Liquid Rate", secondary_y=False)
                fig_w.update_layout(height=400, hovermode="x unified", margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig_w, use_container_width=True)

                # Plots 2 & 3
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("#### 2. Phase Diagnosis")
                    w_phase_res = st.radio("Res:", ["Daily", "Monthly"], index=0, horizontal=True,
                                           label_visibility="collapsed", key="wp_res")
                    if "Daily" in w_phase_res:
                        wp_data = well_filtered.set_index('DATEPRD').copy()
                        wp_data['Total_Liq'] = wp_data['BORE_OIL_VOL'] + wp_data['BORE_WAT_VOL']
                        wp_data['WC'] = (wp_data['BORE_WAT_VOL'] / wp_data['Total_Liq'].replace(0, 1)) * 100
                        wp_data['GOR'] = wp_data['BORE_GAS_VOL'] / wp_data['BORE_OIL_VOL'].replace(0, 1)
                    else:
                        wp_data = wdata

                    fig_rat = make_subplots(specs=[[{"secondary_y": True}]])
                    fig_rat.add_trace(go.Scatter(x=wp_data.index, y=wp_data['WC'], name='Water Cut',
                                                 line=dict(color='#2980B9', width=1)), secondary_y=False)
                    fig_rat.add_trace(
                        go.Scatter(x=wp_data.index, y=wp_data['GOR'], name='GOR', line=dict(color='#D35400', width=1)),
                        secondary_y=True)
                    fig_rat.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20),
                                          legend=dict(orientation="h", y=1.1))
                    st.plotly_chart(fig_rat, use_container_width=True)
                    render_insight("Phase Analysis",
                                   "Stable GOR + Rising Water Cut = Good Pressure Support, but Swept Zone Breakthrough.")

                with c2:
                    st.markdown("#### 3. Displacement Efficiency (Cum. Oil Produced vs Water Cut %)")
                    st.markdown('<div style="height: 28px;"></div>', unsafe_allow_html=True)  # Spacer
                    fig_eff = go.Figure()
                    fig_eff.add_trace(
                        go.Scatter(x=wdata['Cum_Oil'], y=wdata['WC'], mode='lines+markers', marker=dict(size=4),
                                   line=dict(color='#2C3E50', width=2)))
                    fig_eff.update_layout(xaxis_title="Cum Oil", yaxis_title="Water Cut %", height=400,
                                          margin=dict(l=20, r=20, t=20, b=20))
                    st.plotly_chart(fig_eff, use_container_width=True)
                    render_insight("Leucuta Plot",
                                   "Convex Curve = Piston-like displacement (Efficient). Concave = Channeling/Thief Zones.")

                # Plot 4
                st.markdown("#### 4. Pressure Transient & Uptime Analysis")
                w_daily_ops = well_filtered.set_index('DATEPRD')
                fig_ops = make_subplots(specs=[[{"secondary_y": True}]])
                fig_ops.add_trace(
                    go.Bar(x=w_daily_ops.index, y=w_daily_ops['ON_STREAM_HRS'], name='Hrs On', marker_color='#BDC3C7',
                           opacity=0.5), secondary_y=False)
                fig_ops.add_trace(go.Scatter(x=w_daily_ops.index, y=w_daily_ops['AVG_DOWNHOLE_PRESSURE'], name='BHP',
                                             line=dict(color='black', width=1.5)), secondary_y=True)
                fig_ops.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig_ops, use_container_width=True)
                render_insight("Pressure Transient",
                               "Pressure peaks during shut-ins (grey gaps) reveal true static Reservoir Pressure ($P_{res}$).")

        with tab2:
            st.markdown("### Multi-Well Performance Leaderboards")

            # Stats Prep
            well_stats = df_filtered.groupby('NPD_WELL_BORE_NAME').agg(
                {'BORE_OIL_VOL': 'sum', 'ON_STREAM_HRS': 'sum', 'DATEPRD': 'count'}).reset_index()
            well_stats['Cum_Oil_MM'] = well_stats['BORE_OIL_VOL'] / 1e6
            well_stats['PI'] = np.where(well_stats['ON_STREAM_HRS'] > 0,
                                        well_stats['BORE_OIL_VOL'] / well_stats['ON_STREAM_HRS'], 0)

            active_days = df_filtered[df_filtered['ON_STREAM_HRS'] > 0].groupby('NPD_WELL_BORE_NAME')[
                'DATEPRD'].count().reset_index()
            total_days = (end_date - start_date).days + 1
            well_stats = pd.merge(well_stats, active_days, on='NPD_WELL_BORE_NAME', how='left').fillna(0)
            well_stats['Uptime_Pct'] = (well_stats['DATEPRD_y'] / total_days) * 100

            # Trend Plots
            c1, c2 = st.columns(2)
            comp_ts = df_filtered.copy()
            if is_monthly:
                comp_ts = comp_ts.groupby(['NPD_WELL_BORE_NAME', pd.Grouper(key='DATEPRD', freq='ME')]).agg(
                    {'BORE_OIL_VOL': 'sum', 'BORE_WAT_VOL': 'sum'}).reset_index()
            comp_ts['WC'] = (comp_ts['BORE_WAT_VOL'] / (comp_ts['BORE_OIL_VOL'] + comp_ts['BORE_WAT_VOL']).replace(0,
                                                                                                                   1)) * 100

            with c1:
                st.markdown("#### 1. Oil Production Trends")
                st.plotly_chart(px.line(comp_ts, x='DATEPRD', y='BORE_OIL_VOL', color='NPD_WELL_BORE_NAME'),
                                use_container_width=True)
            with c2:
                st.markdown("#### 2. Water Cut Trends (vs Field Avg)")
                field_wc = df_filtered.groupby(pd.Grouper(key='DATEPRD', freq='ME' if is_monthly else 'D'))[
                    ['BORE_OIL_VOL', 'BORE_WAT_VOL']].sum()
                field_wc['Avg_WC'] = (field_wc['BORE_WAT_VOL'] / (
                            field_wc['BORE_OIL_VOL'] + field_wc['BORE_WAT_VOL']).replace(0, 1)) * 100
                fig_wc = px.line(comp_ts, x='DATEPRD', y='WC', color='NPD_WELL_BORE_NAME')
                fig_wc.add_trace(go.Scatter(x=field_wc.index, y=field_wc['Avg_WC'], name='Field Avg',
                                            line=dict(color='black', width=3, dash='dash')))
                st.plotly_chart(fig_wc, use_container_width=True)

            st.markdown("---")
            st.markdown("#### 🏆 Well Rankings")
            c3, c4 = st.columns(2)
            with c3:
                rank_cum = well_stats.sort_values('Cum_Oil_MM', ascending=True)
                fig_cum = px.bar(rank_cum, x='Cum_Oil_MM', y='NPD_WELL_BORE_NAME', orientation='h', text_auto='.2f',
                                 title="Total Volume (MM Sm³)")
                fig_cum.update_traces(marker_color='#27AE60')
                st.plotly_chart(fig_cum, use_container_width=True)
            with c4:
                rank_pi = well_stats.sort_values('PI', ascending=True)
                fig_pi = px.bar(rank_pi, x='PI', y='NPD_WELL_BORE_NAME', orientation='h', text_auto='.0f',
                                title="Productivity Index (Oil/Hour)")
                fig_pi.update_traces(marker_color='#2980B9')
                st.plotly_chart(fig_pi, use_container_width=True)

            c5, c6 = st.columns([2, 1])
            with c5:
                st.markdown("#### 🥉 Reliability: Operational Uptime %")
                rank_up = well_stats.sort_values('Uptime_Pct', ascending=True)
                fig_up = px.bar(rank_up, x='Uptime_Pct', y='NPD_WELL_BORE_NAME', orientation='h', text_auto='.1f',
                                title="Uptime %")
                fig_up.update_traces(marker_color='#8E44AD')
                fig_up.update_xaxes(range=[0, 100])
                st.plotly_chart(fig_up, use_container_width=True)
            with c6:
                render_insight("Performance Matrix",
                               "<b>• Star:</b> High Cum + High PI.<br><b>• Problem:</b> High WC + Low PI.<br><b>• Workhorse:</b> High Uptime + Low PI.")

            st.markdown("---")
            st.markdown("#### 🗓️ Field Reliability Timeline")
            fig_uptime = px.bar(df_filtered, x="DATEPRD", y="ON_STREAM_HRS", color="NPD_WELL_BORE_NAME", height=350)
            fig_uptime.update_layout(bargap=0, hovermode="x unified", title="Daily Activity Log")
            st.plotly_chart(fig_uptime, use_container_width=True)

        with tab3:
            st.markdown("### Reservoir Connectivity Analysis")

            st.markdown("#### 1. Connectivity Matrix")
            pivot_inj = df.pivot_table(index='DATEPRD', columns='NPD_WELL_BORE_NAME', values='BORE_WI_VOL',
                                       aggfunc='sum').fillna(0).resample('ME').sum()
            pivot_prod = df.pivot_table(index='DATEPRD', columns='NPD_WELL_BORE_NAME', values='BORE_OIL_VOL',
                                        aggfunc='sum').fillna(0).resample('ME').sum()

            valid_inj = pivot_inj.loc[:, (pivot_inj.sum() > 1000)]
            valid_prod = pivot_prod.loc[:, (pivot_prod.sum() > 1000)]

            if not valid_inj.empty and not valid_prod.empty:
                combined = pd.concat([valid_inj.add_suffix(' (INJ)'), valid_prod.add_suffix(' (PROD)')], axis=1)
                corr_matrix = combined.corr().loc[
                    [c for c in combined if '(INJ)' in c], [c for c in combined if '(PROD)' in c]]
                fig_mat = px.imshow(corr_matrix, text_auto=".2f", aspect="auto", color_continuous_scale="RdBu_r",
                                    zmin=-1, zmax=1, height=400)
                st.plotly_chart(fig_mat, use_container_width=True)

            st.markdown("---")
            st.markdown("#### 2. Injector Support per Producer ")
            st.caption("Overlay specific injectors to identify which source is driving production for the well.")
            c_dd1, c_dd2 = st.columns(2)
            with c_dd1:
                target_prod = st.selectbox("Producer:", producers, index=0)
            with c_dd2:
                source_injs = st.multiselect("Injectors:", injectors, default=injectors)

            if target_prod and source_injs:
                p_data = df[df['NPD_WELL_BORE_NAME'] == target_prod].set_index('DATEPRD')['BORE_OIL_VOL']
                if is_monthly: p_data = p_data.resample('ME').sum()

                fig_conn = make_subplots(specs=[[{"secondary_y": True}]])
                fig_conn.add_trace(
                    go.Scatter(x=p_data.index, y=p_data, mode='lines', fill='tozeroy', name=f'{target_prod} (Oil)',
                               line=dict(color='#27AE60', width=0)), secondary_y=False)

                colors = ['#2980B9', '#8E44AD', '#16A085']
                for idx, inj in enumerate(source_injs):
                    i_data = df[df['NPD_WELL_BORE_NAME'] == inj].set_index('DATEPRD')['BORE_WI_VOL']
                    if is_monthly: i_data = i_data.resample('ME').sum()
                    fig_conn.add_trace(go.Scatter(x=i_data.index, y=i_data, mode='lines', name=f'{inj} (Inj)',
                                                  line=dict(color=colors[idx % 3], width=3)), secondary_y=True)

                fig_conn.update_yaxes(title_text="Oil Rate", secondary_y=False)
                fig_conn.update_yaxes(title_text="Inj Rate", secondary_y=True)
                fig_conn.update_layout(height=500, hovermode="x unified",
                                       title=f"Correlation: {target_prod} vs Injectors")
                st.plotly_chart(fig_conn, use_container_width=True)

                render_insight("Forensic Tip",
                               "Look for peak matching between Injection Lines (Right Axis) and Oil Area (Left Axis). A 1-3 month lag is typical.")

    elif "Injectors" in well_type:
        st.markdown(f"### Injection Performance: {selected_well}")
        inj_data = df[df['NPD_WELL_BORE_NAME'] == selected_well].sort_values('DATEPRD')
        mask_inj = (inj_data['DATEPRD'].dt.date >= start_date) & (inj_data['DATEPRD'].dt.date <= end_date)
        inj_filtered = inj_data.loc[mask_inj].copy()

        if is_monthly:
            idata = inj_filtered.resample('ME', on='DATEPRD').agg({'BORE_WI_VOL': 'sum'})
        else:
            idata = inj_filtered.set_index('DATEPRD')

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 1. Injection History")
            fig_inj = go.Figure(go.Scatter(x=idata.index, y=idata['BORE_WI_VOL'], fill='tozeroy', name='Inj Rate',
                                           line=dict(color='#2980B9')))
            fig_inj.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_inj, use_container_width=True)

        with c2:
            st.markdown("#### 2. Influence Strength")
            my_inj = df[df['NPD_WELL_BORE_NAME'] == selected_well].set_index('DATEPRD')['BORE_WI_VOL'].resample(
                'ME').sum()
            prod_data = df[df['NPD_WELL_BORE_NAME'].isin(producers)].pivot_table(index='DATEPRD',
                                                                                 columns='NPD_WELL_BORE_NAME',
                                                                                 values='BORE_OIL_VOL',
                                                                                 aggfunc='sum').fillna(0).resample(
                'ME').sum()
            aligned = pd.concat([my_inj, prod_data], axis=1).dropna()

            if not aligned.empty:
                corrs = aligned.iloc[:, 1:].corrwith(aligned.iloc[:, 0]).sort_values(ascending=False)
                fig_corr = go.Figure(go.Bar(x=corrs.index, y=corrs.values,
                                            marker_color=np.where(corrs.values > 0, '#27AE60', '#95A5A6')))
                fig_corr.update_layout(title="Correlation with Producers", height=400,
                                       margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig_corr, use_container_width=True)
                render_insight("Interpretation",
                               "<b>Green:</b> Strong Support. <b>Grey:</b> No Connection/Inverse Relationship.")
