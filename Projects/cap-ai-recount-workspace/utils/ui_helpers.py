"""Shared UI helpers for CAP AI pages."""

import streamlit as st

from config import COLORS


def page_header(title: str, subtitle: str = "") -> None:
    st.markdown(
        f'<div class="gradient-header"><div class="cap-header" style="color:white;">{title}</div>'
        f'<div class="cap-subheader" style="color:rgba(255,255,255,0.85);">{subtitle}</div></div>',
        unsafe_allow_html=True,
    )


def render_kpi_grid(kpis: dict[str, tuple]) -> None:
    cols = st.columns(4)
    for i, (label, (value, delta)) in enumerate(kpis.items()):
        with cols[i % 4]:
            val_str = f"{value:,}" if isinstance(value, (int, float)) and not isinstance(value, bool) else str(value)
            delta_html = f'<div class="kpi-delta">{delta}</div>' if delta else ""
            st.markdown(
                f"""
                <div class="kpi-card" style="animation-delay: {i * 0.08}s;">
                    <div class="kpi-value">{val_str}</div>
                    <div class="kpi-label">{label}</div>
                    {delta_html}
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_ai_insights(insights: list[dict]) -> None:
    st.markdown("#### AI Insights")
    for item in insights:
        risk_class = "risk-low" if item["risk_level"] == "Low" else "risk-medium" if item["risk_level"] == "Medium" else "risk-high"
        st.markdown(
            f"""
            <div class="insight-card">
                <div class="insight-title">{item['title']} — <span class="{risk_class}">{item['risk_level']}</span> — {item['priority']}</div>
                <div class="insight-body">{item['message']}</div>
                <div class="insight-body"><strong>Recommendation:</strong> {item['recommendation']}</div>
                <div class="insight-body"><strong>Action:</strong> {item['action']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def check_permission(module: str) -> bool:
    from config import ROLES
    role = st.session_state.get("role", "Viewer")
    perms = ROLES.get(role, ROLES["Viewer"])
    if not perms.get(module, False):
        st.warning("Your role does not have access to this module.")
        return False
    return True


def export_buttons(df, label: str = "data") -> None:
    from utils.excel import export_dataframe_csv, export_dataframe_excel
    if df.empty:
        return
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("Download Excel", export_dataframe_excel(df), f"{label}.xlsx", "application/vnd.ms-excel")
    with col2:
        st.download_button("Download CSV", export_dataframe_csv(df), f"{label}.csv", "text/csv")
