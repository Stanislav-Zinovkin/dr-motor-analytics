import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go

from core.config import NORMS_CACHE_PATH
from core.validators import clean_and_validate_logs
from core.metrics import get_or_update_sku_norms, calculate_worker_performance

# Page Configuration
st.set_page_config(
    page_title="DR Motor - Warehouse Productivity Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📦 DR Motor — Warehouse Analytics Engine")
st.markdown("Automated KPI tracking & dynamic SKU norm estimation based on operational medians.")

# Sidebar Controls
st.sidebar.header("🕹️ Data & Control Panel")
data_source = st.sidebar.file_uploader("Upload ERP Logs (CSV)", type=['csv'])
force_recalc = st.sidebar.button("🔄 Force Recalculate SKU Norms")

# Load Default Data
default_mock_path = "data/raw/erp_export_mock.csv"

if data_source is not None:
    raw_df = pd.read_csv(data_source)
    st.sidebar.success("Custom ERP file uploaded successfully!")
elif os.path.exists(default_mock_path):
    raw_df = pd.read_csv(default_mock_path)
    st.sidebar.info("Using default mock ERP dataset")
else: 
    raw_df = None
    st.warning("⚠️ No dataset found! Please upload a valid ERP CSV file via the sidebar or place `erp_export_mock.csv` in `data/raw/`.")

if raw_df is not None:
    # Step 1: Clean and validate raw operational logs
    clean_df = clean_and_validate_logs(raw_df)

    # Step 2: Retrieve cached SKU norms or recalculate medians
    norms_df = get_or_update_sku_norms(clean_df, force_recalculate=force_recalc)

    # Step 3: Month-over-Month Period Selection
    clean_df['year_month'] = clean_df['czas_start'].dt.to_period('M').astype(str)
    available_months = sorted(clean_df['year_month'].unique(), reverse=True)

    st.sidebar.markdown("---")
    st.sidebar.header("📅 Period Selection")
    
    selected_month = st.sidebar.selectbox("Select Target Month:", available_months if available_months else ["All"])
    
    if selected_month != "All":
        current_month_logs = clean_df[clean_df['year_month'] == selected_month]
        
        # Previous month calculation for comparison
        month_idx = available_months.index(selected_month)
        has_prev_month = month_idx < len(available_months) - 1
        prev_month = available_months[month_idx + 1] if has_prev_month else None
    else:
        current_month_logs = clean_df
        prev_month = None

    # Step 4: Calculate KPIs
    worker_kpis = calculate_worker_performance(current_month_logs, norms_df)
    
    prev_avg_kpi = None
    if prev_month:
        prev_month_logs = clean_df[clean_df['year_month'] == prev_month]
        prev_worker_kpis = calculate_worker_performance(prev_month_logs, norms_df)
        if not prev_worker_kpis.empty:
            prev_avg_kpi = round(prev_worker_kpis['avg_kpi'].mean(), 1)

    # Worker Filter
    st.sidebar.header("🔍 Worker Filter")
    worker_list = ["All Workers"] + sorted(worker_kpis['id_pracownika'].astype(str).tolist())
    selected_worker = st.sidebar.selectbox("Filter by Worker ID:", worker_list)

    if selected_worker != "All Workers":
        filtered_kpis = worker_kpis[worker_kpis['id_pracownika'].astype(str) == selected_worker]
        filtered_logs = current_month_logs[current_month_logs['id_pracownika'].astype(str) == selected_worker]
    else:
        filtered_kpis = worker_kpis
        filtered_logs = current_month_logs

    # High-Level Executive Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Processed Operations", f"{len(filtered_logs):,}")
    col2.metric("Active Catalog SKUs", f"{len(norms_df):,}")
    
    avg_warehouse_kpi = round(filtered_kpis['avg_kpi'].mean(), 1) if not filtered_kpis.empty else 0
    kpi_delta = round(avg_warehouse_kpi - prev_avg_kpi, 1) if prev_avg_kpi is not None else None
    
    col3.metric(
        label=f"Average Warehouse KPI ({selected_month})", 
        value=f"{avg_warehouse_kpi}%", 
        delta=f"{kpi_delta}% vs {prev_month}" if kpi_delta is not None else None
    )

    st.markdown("---")

    # Layout Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Executive Overview (Trend & Zones)", "🏷️ SKU Norms Catalog", "🔍 Operational Logs"])

    with tab1:
        st.subheader("Warehouse Performance Trend & Zones")

        # Daily KPI Trend Chart with Color Zones
        if 'czas_start' in filtered_logs.columns and not filtered_logs.empty:
            daily_merged = filtered_logs.merge(norms_df, on="sku", how="left")
            daily_merged['median_minutes_per_unit'] = daily_merged['median_minutes_per_unit'].fillna(1.0)
            daily_merged['expected_duration'] = daily_merged['ilosc'] * daily_merged['median_minutes_per_unit']
            daily_merged['performance_kpi'] = (daily_merged['expected_duration'] / daily_merged['duration_minutes']) * 100.0

            daily_merged['date'] = daily_merged['czas_start'].dt.date
            daily_kpi = daily_merged.groupby('date')['performance_kpi'].mean().reset_index()
            daily_kpi['date'] = pd.to_datetime(daily_kpi['date'])
            daily_kpi = daily_kpi.sort_values('date')

            if not daily_kpi.empty:
                fig_line = go.Figure()

                # Main trend line
                fig_line.add_trace(go.Scatter(
                    x=daily_kpi['date'],
                    y=daily_kpi['performance_kpi'],
                    mode='lines+markers',
                    name='Daily Average KPI',
                    line=dict(color='#1F2937', width=3),
                    marker=dict(size=8)
                ))

                # Threshold lines
                fig_line.add_hline(y=110, line_dash="dash", line_color="#16A34A", annotation_text="High Norm (110%)", annotation_position="top left")
                fig_line.add_hline(y=90, line_dash="dash", line_color="#DC2626", annotation_text="Min Norm (90%)", annotation_position="bottom left")

                max_y = max(daily_kpi['performance_kpi'].max() * 1.1, 130)
                min_y = min(daily_kpi['performance_kpi'].min() * 0.9, 50)

                # Colored Background Zones
                fig_line.update_layout(
                    shapes=[
                        dict(type="rect", xref="paper", yref="y", x0=0, x1=1, y0=115, y1=max_y,
                             fillcolor="#DCFCE7", opacity=0.4, layer="below", line_width=0),
                        dict(type="rect", xref="paper", yref="y", x0=0, x1=1, y0=85, y1=115,
                             fillcolor="#FEF3C7", opacity=0.4, layer="below", line_width=0),
                        dict(type="rect", xref="paper", yref="y", x0=0, x1=1, y0=min_y, y1=85,
                             fillcolor="#FEE2E2", opacity=0.4, layer="below", line_width=0),
                    ],
                    height=380,
                    margin=dict(l=20, r=20, t=30, b=20),
                    xaxis_title="Date",
                    yaxis_title="KPI (%)",
                    yaxis=dict(range=[min_y, max_y])
                )

                st.plotly_chart(fig_line, use_container_width=True)

        st.markdown("---")
        st.subheader("Detailed Worker Breakdown")

        def highlight_kpi(val):
            if val < 85:
                return 'background-color: #FEE2E2; color: #991B1B; font-weight: bold;'
            elif val <= 115:
                return 'background-color: #FEF3C7; color: #92400E; font-weight: bold;'
            else:
                return 'background-color: #DCFCE7; color: #166534; font-weight: bold;'

        styled_kpis = filtered_kpis.style.map(highlight_kpi, subset=['avg_kpi'])

        st.dataframe(styled_kpis, use_container_width=True)

        csv_report = filtered_kpis.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            label="📥 Download Monthly KPI Report (CSV)",
            data=csv_report,
            file_name=f"worker_kpi_report_{selected_month}.csv",
            mime="text/csv"
        )

    with tab2:
        st.subheader("Dynamic SKU Norms (3-Month Median)")
        st.dataframe(norms_df, use_container_width=True)

    with tab3:
        st.subheader("Filtered Operational Dataset")
        st.dataframe(filtered_logs.head(100), use_container_width=True)