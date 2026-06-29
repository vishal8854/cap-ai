import streamlit as st


def render_filters(status_options: list[str] | None = None, branch_options: list[str] | None = None) -> tuple[str, str, str]:
    col1, col2, col3 = st.columns(3)
    with col1:
        search = st.text_input("Search", placeholder="Filter records...", key="filter_search")
    with col2:
        status = "All"
        if status_options:
            status = st.selectbox("Status", ["All"] + status_options, key="filter_status")
    with col3:
        branch = "All"
        if branch_options:
            branch = st.selectbox("Branch", ["All"] + branch_options, key="filter_branch")
    return search, status, branch
