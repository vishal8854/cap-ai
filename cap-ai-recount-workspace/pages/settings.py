"""Application settings and audit trail."""

import streamlit as st

from config import DEMO_USERS, ROLES
from database import get_activity_logs, get_audit_trail, log_activity
from utils.ui_helpers import check_permission, page_header


def render():
    page_header("Settings", "User roles, preferences, and audit trail")

    if not check_permission("settings"):
        st.markdown("#### User Profile")
        st.write(f"**User:** {st.session_state.get('username', 'Guest')}")
        st.write(f"**Role:** {st.session_state.get('role', 'Viewer')}")
        dark_mode = st.toggle("Dark Mode", value=st.session_state.get("dark_mode", False))
        st.session_state["dark_mode"] = dark_mode
        return

    tab1, tab2, tab3 = st.tabs(["Profile", "Roles & Permissions", "Audit Trail"])

    with tab1:
        st.markdown("#### User Profile")
        st.write(f"**User:** {st.session_state.get('username', 'Guest')}")
        st.write(f"**Role:** {st.session_state.get('role', 'Viewer')}")
        dark_mode = st.toggle("Dark Mode", value=st.session_state.get("dark_mode", False))
        st.session_state["dark_mode"] = dark_mode

    with tab2:
        st.markdown("#### Role Permissions Matrix")
        import pandas as pd
        modules = list(next(iter(ROLES.values())).keys())
        matrix = {role: [ROLES[role].get(m, False) for m in modules] for role in ROLES}
        df = pd.DataFrame(matrix, index=modules)
        st.dataframe(df, use_container_width=True)

        st.markdown("#### Demo Accounts")
        demo_df = pd.DataFrame([
            {"Login": k, "Password": v["password"], "Role": v["role"]}
            for k, v in DEMO_USERS.items()
        ])
        st.dataframe(demo_df, use_container_width=True, hide_index=True)

    with tab3:
        st.markdown("#### Activity Logs")
        activity = get_activity_logs(30)
        if not activity.empty:
            st.dataframe(activity, use_container_width=True, hide_index=True)

        st.markdown("#### Audit Trail")
        audit = get_audit_trail(30)
        if not audit.empty:
            st.dataframe(audit, use_container_width=True, hide_index=True)

        if st.button("Log Test Activity"):
            log_activity(
                st.session_state.get("username", "Admin"),
                st.session_state.get("role", "Admin"),
                "Settings viewed",
                "Settings",
            )
            st.success("Activity logged.")
            st.rerun()
