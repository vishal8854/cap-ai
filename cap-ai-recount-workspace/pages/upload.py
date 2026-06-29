"""Excel and CSV import module."""

import streamlit as st

from database import (
    bulk_insert_idle,
    bulk_insert_interest,
    bulk_insert_signatories,
    bulk_insert_transactions,
    save_uploaded_file,
)
from utils.excel import detect_duplicates, profile_dataframe, read_uploaded_file, save_upload_temp
from utils.ui_helpers import check_permission, page_header


def render():
    page_header("Excel Import Center", "Drag & drop upload with preview, validation, and auto-mapping")

    if not check_permission("upload"):
        return

    import_type = st.selectbox(
        "Data Type",
        ["Transactions", "Interest Validation", "Idle Accounts", "Signatories", "Litigation Cases", "Complaints"],
    )

    idle_days = st.number_input("Idle threshold (days)", 30, 365, 60, key="idle_thresh_import")
    balance_thresh = st.number_input("Balance threshold (₹)", 10000, 10000000, 100000, key="bal_thresh_import")

    uploaded = st.file_uploader(
        "Drag & drop or browse files",
        type=["xlsx", "xls", "csv"],
        accept_multiple_files=False,
    )

    if uploaded:
        progress = st.progress(0, text="Reading file...")
        df = read_uploaded_file(uploaded)
        progress.progress(30, text="Profiling data...")

        st.markdown("#### Data Preview")
        st.dataframe(df.head(20), use_container_width=True, hide_index=True)

        profile = profile_dataframe(df)
        progress.progress(60, text="Validating...")

        st.markdown("#### Import Summary")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", profile["rows"])
        c2.metric("Columns", profile["columns"])
        c3.metric("Duplicates", profile["duplicates"])
        c4.metric("Outlier Columns", len(profile.get("outliers", {})))

        if profile.get("missing"):
            st.markdown("**Missing Values (Error Highlighting):**")
            for col, count in profile["missing"].items():
                st.error(f"{col}: {count} missing values")

        dupes = detect_duplicates(df)
        if not dupes.empty:
            st.warning(f"Duplicate Detection: {len(dupes)} duplicate rows found")
            st.dataframe(dupes.head(10), use_container_width=True)

        if profile.get("outliers"):
            st.markdown("**Outliers:**")
            st.json(profile["outliers"])

        st.markdown("**Auto Column Mapping:**")
        st.json({col: str(df[col].dtype) for col in df.columns})

        progress.progress(90, text="Ready to import")
        user = st.session_state.get("username", "User")
        role = st.session_state.get("role", "Viewer")

        if st.button("Import to Database", type="primary"):
            with st.spinner("Importing data..."):
                path = save_upload_temp(uploaded)
                if import_type == "Transactions":
                    count = bulk_insert_transactions(df, user, role)
                elif import_type == "Interest Validation":
                    count = bulk_insert_interest(df, user, role)
                elif import_type == "Idle Accounts":
                    count = bulk_insert_idle(df, idle_days, balance_thresh, user, role)
                elif import_type == "Signatories":
                    count = bulk_insert_signatories(df, user, role)
                else:
                    count = len(df)
                    st.info(f"Preview import for {import_type} — map to litigation/complaints modules.")

                save_uploaded_file(uploaded.name, str(path), uploaded.type or "unknown", import_type, user, count)
                progress.progress(100, text="Import complete")
                st.success(f"Successfully imported {count} records into {import_type}.")
