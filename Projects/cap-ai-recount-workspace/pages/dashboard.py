"""Executive dashboard for CAP AI."""

import streamlit as st

from database import get_dashboard_kpis
from utils.ai_engine import generate_insights
from utils.analytics import compute_kpi_cards
from utils.charts import (
    bank_charge_recovery_chart,
    cases_by_court_bar,
    cases_by_state_bar,
    cases_status_pie,
    complaints_category_pie,
    compliance_score_gauge,
    compliance_timeline_chart,
    idle_funds_chart,
    risk_heatmap,
    round_trip_trend,
    transaction_trend_chart,
)
from utils.ui_helpers import page_header, render_ai_insights, render_kpi_grid


def render():
    page_header("Executive Dashboard", "Real-time election litigation & compliance intelligence")

    with st.spinner("Loading dashboard metrics..."):
        kpis = compute_kpi_cards()
        score = get_dashboard_kpis()["compliance_score"]

    render_kpi_grid(kpis)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.plotly_chart(transaction_trend_chart(), use_container_width=True)
    with col2:
        st.plotly_chart(risk_heatmap(), use_container_width=True)
    with col3:
        st.plotly_chart(compliance_score_gauge(score), use_container_width=True)

    col4, col5, col6 = st.columns(3)
    with col4:
        st.plotly_chart(cases_status_pie(), use_container_width=True)
    with col5:
        st.plotly_chart(cases_by_state_bar(), use_container_width=True)
    with col6:
        st.plotly_chart(complaints_category_pie(), use_container_width=True)

    col7, col8 = st.columns(2)
    with col7:
        st.plotly_chart(cases_by_court_bar(), use_container_width=True)
    with col8:
        st.plotly_chart(round_trip_trend(), use_container_width=True)

    col9, col10 = st.columns(2)
    with col9:
        st.plotly_chart(bank_charge_recovery_chart(), use_container_width=True)
    with col10:
        st.plotly_chart(idle_funds_chart(), use_container_width=True)

    st.plotly_chart(compliance_timeline_chart(), use_container_width=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    render_ai_insights(generate_insights())
