"""Reports generation module."""

import streamlit as st

from database import (
    get_complaints,
    get_dashboard_kpis,
    get_idle_accounts,
    get_interest_validations,
    get_litigation_cases,
    get_transactions,
)
from utils.ai_engine import generate_insights
from utils.excel import export_dataframe_csv, export_dataframe_excel
from utils.ui_helpers import check_permission, page_header


REPORT_TYPES = [
    "Daily Report",
    "Weekly Report",
    "Monthly Report",
    "Risk Report",
    "Case Summary",
    "Compliance Report",
    "Financial Alerts",
]


def _get_report_data(report_type: str):
    if report_type == "Case Summary":
        return get_litigation_cases(), "litigation_cases"
    if report_type == "Financial Alerts":
        txns = get_transactions()
        if not txns.empty and "risk_score" in txns.columns:
            return txns[txns["risk_score"] >= 40], "financial_alerts"
        return txns, "financial_alerts"
    if report_type == "Risk Report":
        insights = generate_insights()
        import pandas as pd
        return pd.DataFrame(insights), "risk_report"
    if report_type == "Compliance Report":
        kpis = get_dashboard_kpis()
        import pandas as pd
        return pd.DataFrame([kpis]), "compliance_report"
    cases = get_litigation_cases()
    complaints = get_complaints()
    interest = get_interest_validations()
    idle = get_idle_accounts()
    import pandas as pd
    summary = pd.DataFrame({
        "metric": ["Cases", "Complaints", "Interest Records", "Idle Accounts"],
        "count": [len(cases), len(complaints), len(interest), len(idle)],
    })
    return summary, report_type.lower().replace(" ", "_")


def render():
    page_header("Reports", "Generate and download compliance and operational reports")

    if not check_permission("reports"):
        return

    report_type = st.selectbox("Report Type", REPORT_TYPES)
    date_range = st.date_input("Report Date", value=None)

    if st.button("Generate Report", type="primary"):
        with st.spinner(f"Generating {report_type}..."):
            df, filename = _get_report_data(report_type)
            st.session_state["report_df"] = df
            st.session_state["report_filename"] = filename
            st.success(f"{report_type} generated with {len(df)} records.")

    if "report_df" in st.session_state:
        df = st.session_state["report_df"]
        st.dataframe(df, use_container_width=True, hide_index=True)
        fname = st.session_state.get("report_filename", "report")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button("Download Excel", export_dataframe_excel(df), f"{fname}.xlsx", "application/vnd.ms-excel")
        with col2:
            st.download_button("Download CSV", export_dataframe_csv(df), f"{fname}.csv", "text/csv")
        with col3:
            st.download_button("Download PDF (text)", export_dataframe_csv(df), f"{fname}.txt", "text/plain")
