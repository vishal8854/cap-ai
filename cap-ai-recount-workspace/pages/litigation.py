"""Election litigation and case management module."""

import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder

from database import (
    create_litigation_case,
    delete_litigation_case,
    get_litigation_cases,
    update_litigation_case,
)
from utils.ui_helpers import check_permission, export_buttons, page_header


STATUSES = ["Open", "In Progress", "Pending Investigation", "Closed", "Dismissed"]
PRIORITIES = ["Low", "Medium", "High"]
ELECTION_TYPES = ["Parliamentary", "Assembly", "Local", "Rajya Sabha"]


def _case_form(prefix: str = "new") -> dict:
    with st.form(f"case_form_{prefix}"):
        col1, col2 = st.columns(2)
        with col1:
            case_id = st.text_input("Case ID", key=f"{prefix}_case_id")
            case_name = st.text_input("Case Name", key=f"{prefix}_case_name")
            election_type = st.selectbox("Election Type", ELECTION_TYPES, key=f"{prefix}_etype")
            state = st.text_input("State", key=f"{prefix}_state")
            district = st.text_input("District", key=f"{prefix}_district")
            court = st.text_input("Court", key=f"{prefix}_court")
        with col2:
            petitioner = st.text_input("Petitioner", key=f"{prefix}_petitioner")
            respondent = st.text_input("Respondent", key=f"{prefix}_respondent")
            filing_date = st.date_input("Filing Date", key=f"{prefix}_filing")
            hearing_date = st.date_input("Hearing Date", key=f"{prefix}_hearing")
            status = st.selectbox("Current Status", STATUSES, key=f"{prefix}_status")
            priority = st.selectbox("Priority", PRIORITIES, key=f"{prefix}_priority")
            advocate = st.text_input("Advocate", key=f"{prefix}_advocate")
        documents = st.text_input("Documents (reference)", key=f"{prefix}_docs")
        remarks = st.text_area("Remarks", key=f"{prefix}_remarks")
        submitted = st.form_submit_button("Save Case", type="primary")
        if submitted:
            return {
                "submitted": True,
                "case_id": case_id,
                "case_name": case_name,
                "election_type": election_type,
                "state": state,
                "district": district,
                "court": court,
                "petitioner": petitioner,
                "respondent": respondent,
                "filing_date": str(filing_date),
                "hearing_date": str(hearing_date),
                "current_status": status,
                "priority": priority,
                "advocate": advocate,
                "documents": documents,
                "remarks": remarks,
            }
    return {"submitted": False}


def render(mode: str = "litigation"):
    title = "Election Litigation Tracker" if mode == "litigation" else "Case Management"
    page_header(title, "Track election petitions, hearings, and legal proceedings")

    if not check_permission("litigation"):
        return

    user = st.session_state.get("username", "User")
    role = st.session_state.get("role", "Viewer")

    with st.expander("Filters & Search", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            search = st.text_input("Search", placeholder="Case ID, name, court...")
        with col2:
            status_filter = st.selectbox("Status", ["All"] + STATUSES)
        with col3:
            state_filter = st.text_input("State filter")
        with col4:
            priority_filter = st.selectbox("Priority", ["All"] + PRIORITIES)

    df = get_litigation_cases(
        search=search,
        status=status_filter,
        state=state_filter if state_filter else "All",
        priority=priority_filter,
    )

    tab1, tab2, tab3 = st.tabs(["Case Registry", "Add Case", "Manage"])

    with tab1:
        if df.empty:
            st.info("No cases found. Add a new case to get started.")
        else:
            display = df[[
                "case_id", "case_name", "election_type", "state", "court",
                "current_status", "priority", "hearing_date", "advocate",
            ]].copy()
            gb = GridOptionsBuilder.from_dataframe(display)
            gb.configure_pagination(paginationPageSize=10)
            gb.configure_default_column(filterable=True, sortable=True)
            AgGrid(display, gridOptions=gb.build(), height=400, theme="streamlit")
            export_buttons(display, "litigation_cases")

    with tab2:
        data = _case_form("new")
        if data.get("submitted"):
            if not data["case_id"] or not data["case_name"]:
                st.error("Case ID and Case Name are required.")
            elif create_litigation_case(data, user, role):
                st.success(f"Case {data['case_id']} created successfully.")
                st.rerun()
            else:
                st.error("Case ID already exists.")

    with tab3:
        if df.empty:
            st.info("No cases to manage.")
        else:
            case_ids = df["case_id"].tolist()
            selected = st.selectbox("Select Case", case_ids)
            case_row = df[df["case_id"] == selected].iloc[0]
            new_status = st.selectbox("Update Status", STATUSES, index=STATUSES.index(case_row["current_status"]) if case_row["current_status"] in STATUSES else 0)
            new_priority = st.selectbox("Update Priority", PRIORITIES, index=PRIORITIES.index(case_row["priority"]) if case_row["priority"] in PRIORITIES else 1)
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Update Case", type="primary"):
                    update_litigation_case(selected, {"current_status": new_status, "priority": new_priority, "case_name": case_row["case_name"]}, user, role)
                    st.success("Case updated.")
                    st.rerun()
            with col_b:
                if st.button("Delete Case"):
                    delete_litigation_case(selected, user, role)
                    st.warning("Case deleted.")
                    st.rerun()
