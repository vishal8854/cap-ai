"""Complaint management module."""

import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder

from database import create_complaint, delete_complaint, get_complaints, update_complaint
from utils.ui_helpers import check_permission, export_buttons, page_header

CATEGORIES = ["Booth Malpractice", "Vote Counting", "Agent Conduct", "Infrastructure", "EVM/VVPAT", "Other"]
STATUSES = ["Open", "In Progress", "Resolved", "Escalated", "Closed"]
PRIORITIES = ["Low", "Medium", "High"]


def render():
    page_header("Complaint Management", "Track booth complaints, evidence, and resolution workflow")

    if not check_permission("complaints"):
        return

    user = st.session_state.get("username", "User")
    role = st.session_state.get("role", "Viewer")

    with st.expander("Filters", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            search = st.text_input("Search complaints")
        with col2:
            status_filter = st.selectbox("Status", ["All"] + STATUSES, key="cmp_status")
        with col3:
            category_filter = st.selectbox("Category", ["All"] + CATEGORIES, key="cmp_cat")

    df = get_complaints(search=search, status=status_filter, category=category_filter)

    tab1, tab2, tab3 = st.tabs(["Complaint Registry", "New Complaint", "Timeline & Notes"])

    with tab1:
        if df.empty:
            st.info("No complaints recorded.")
        else:
            display = df[[
                "complaint_id", "complainant_name", "booth", "constituency",
                "category", "status", "priority", "assigned_officer", "resolution_date",
            ]].copy()
            gb = GridOptionsBuilder.from_dataframe(display)
            gb.configure_pagination(paginationPageSize=10)
            gb.configure_default_column(filterable=True, sortable=True)
            AgGrid(display, gridOptions=gb.build(), height=400, theme="streamlit")
            export_buttons(display, "complaints")

    with tab2:
        with st.form("complaint_form"):
            col1, col2 = st.columns(2)
            with col1:
                complaint_id = st.text_input("Complaint ID")
                complainant = st.text_input("Complainant Name")
                booth = st.text_input("Booth")
                constituency = st.text_input("Constituency")
                category = st.selectbox("Complaint Category", CATEGORIES)
            with col2:
                officer = st.text_input("Assigned Officer")
                status = st.selectbox("Status", STATUSES)
                priority = st.selectbox("Priority", PRIORITIES)
                resolution = st.text_input("Resolution")
                resolution_date = st.date_input("Resolution Date")
            description = st.text_area("Description")
            notes = st.text_area("Case Notes")
            evidence = st.file_uploader("Evidence Upload", type=["pdf", "png", "jpg", "xlsx"])
            submitted = st.form_submit_button("Submit Complaint", type="primary")
            if submitted:
                data = {
                    "complaint_id": complaint_id,
                    "complainant_name": complainant,
                    "booth": booth,
                    "constituency": constituency,
                    "category": category,
                    "description": description,
                    "evidence_path": evidence.name if evidence else "",
                    "assigned_officer": officer,
                    "status": status,
                    "resolution": resolution,
                    "resolution_date": str(resolution_date) if resolution else "",
                    "priority": priority,
                    "notes": notes,
                }
                if not complaint_id or not complainant:
                    st.error("Complaint ID and Complainant Name are required.")
                elif create_complaint(data, user, role):
                    st.success("Complaint registered.")
                    st.rerun()
                else:
                    st.error("Complaint ID already exists.")

    with tab3:
        if df.empty:
            st.info("No complaints for timeline view.")
        else:
            selected = st.selectbox("Select Complaint", df["complaint_id"].tolist())
            row = df[df["complaint_id"] == selected].iloc[0]
            st.markdown("#### Status Progress")
            status_idx = STATUSES.index(row["status"]) if row["status"] in STATUSES else 0
            st.progress((status_idx + 1) / len(STATUSES))
            st.caption(f"Current: {row['status']}")

            st.markdown("#### Complaint Timeline")
            timeline = [
                ("Registered", str(row.get("created_at", ""))[:10], row.get("description", "")),
                ("Assigned", row.get("assigned_officer", "—"), f"Officer: {row.get('assigned_officer', 'N/A')}"),
                ("Resolution", row.get("resolution_date", "Pending"), row.get("resolution", "Pending")),
            ]
            for event, date, detail in timeline:
                st.markdown(f"**{event}** ({date}): {detail}")

            st.markdown("#### Notes & Attachments")
            st.write(row.get("notes", "No notes"))
            if row.get("evidence_path"):
                st.caption(f"Attachment: {row['evidence_path']}")

            with st.form("update_complaint"):
                new_status = st.selectbox("Update Status", STATUSES, index=status_idx)
                new_notes = st.text_area("Add Note", value=row.get("notes", ""))
                if st.form_submit_button("Update"):
                    update_complaint(selected, {"status": new_status, "notes": new_notes, "complainant_name": row["complainant_name"]}, user, role)
                    st.success("Complaint updated.")
                    st.rerun()

            if st.button("Delete Complaint"):
                delete_complaint(selected, user, role)
                st.warning("Complaint deleted.")
                st.rerun()
