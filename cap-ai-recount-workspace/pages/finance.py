"""Financial compliance modules — round tripping, bank charges, idle funds, signatory."""

import streamlit as st

from database import get_idle_accounts, get_interest_validations, get_transactions
from utils.compliance import (
    analyze_idle_funds,
    build_network_graph,
    detect_round_tripping,
    risk_color,
    verify_bank_charges,
    verify_signatories,
)
from utils.ui_helpers import check_permission, export_buttons, page_header


def _render_round_tripping():
    page_header("Round Tripping Detection", "Identify circular transfers and suspicious fund movement")
    if not check_permission("round_trip"):
        return

    col1, col2 = st.columns([2, 1])
    with col2:
        return_window = st.slider("Return Window (days)", 7, 90, 30)
        if st.button("Run Detection", type="primary", use_container_width=True):
            st.session_state["rt_run"] = True

    txn_df = get_transactions()
    if txn_df.empty:
        st.info("Import bank statement data via Excel Upload.")
        return

    display = txn_df[["transaction_id", "txn_date", "from_account", "to_account", "amount"]].copy()
    display.columns = ["Transaction ID", "Date", "From Account", "To Account", "Amount"]

    if st.session_state.get("rt_run", True):
        with st.spinner("Analyzing round-tripping patterns..."):
            risk_df = detect_round_tripping(display, return_window)

        if not risk_df.empty:
            st.markdown("#### Risk Score Table")
            styled = risk_df.style.map(lambda v: f"color: {risk_color(v)}; font-weight: bold", subset=["Risk Score"])
            st.dataframe(styled, use_container_width=True, hide_index=True)
            export_buttons(risk_df, "round_trip_risks")
        else:
            st.success("No round-tripping patterns detected.")

        st.markdown("#### Network Graph — Money Flow")
        st.plotly_chart(build_network_graph(display), use_container_width=True)

        st.markdown("#### Transaction Timeline")
        timeline = display.sort_values("Date")
        st.dataframe(timeline, use_container_width=True, hide_index=True)


def _render_bank_charges():
    page_header("Bank Charges Verification", "Recalculate interest, charges, and penalties vs actual deductions")
    if not check_permission("bank_charges"):
        return

    uploaded_stmt = st.file_uploader("Upload Bank Statement", type=["xlsx", "csv"], key="bank_stmt")
    uploaded_loan = st.file_uploader("Upload Loan Agreement / Sanction Terms", type=["pdf", "xlsx"], key="bank_loan")

    interest_df = get_interest_validations()
    if uploaded_stmt:
        from utils.excel import read_uploaded_file
        stmt_df = read_uploaded_file(uploaded_stmt)
        st.dataframe(stmt_df.head(10), use_container_width=True)

    result = verify_bank_charges(interest_df)
    if result.empty:
        st.info("No interest validation data. Import via Excel Upload.")
        return

    display_cols = ["account", "Expected Amount", "Actual Amount", "Difference", "Variance %", "Recovery Opportunity", "status"]
    available = [c for c in display_cols if c in result.columns]
    st.dataframe(result[available], use_container_width=True, hide_index=True)

    total_recovery = result["Recovery Opportunity"].sum() if "Recovery Opportunity" in result.columns else 0
    st.metric("Total Recovery Opportunity", f"₹{total_recovery:,.0f}")
    export_buttons(result[available], "bank_charges")


def _render_idle_funds():
    page_header("Idle Fund Analysis", "Identify idle balances and missed sweep opportunities")
    if not check_permission("idle_funds"):
        return

    uploaded_cash = st.file_uploader("Upload Cash Position", type=["xlsx", "csv"], key="idle_cash")
    uploaded_stmt = st.file_uploader("Upload Bank Statement", type=["xlsx", "csv"], key="idle_stmt")
    uploaded_inv = st.file_uploader("Upload Investment Register", type=["xlsx", "csv"], key="idle_inv")

    idle_df = get_idle_accounts()
    analysis = analyze_idle_funds(idle_df)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Idle Balance", f"₹{analysis['total_idle']:,.0f}")
    col2.metric("Idle Accounts", analysis["accounts"])
    col3.metric("Projected Earnings", f"₹{analysis['projected_earnings']:,.0f}")

    if not idle_df.empty:
        st.markdown("#### Opportunity Report")
        st.dataframe(idle_df, use_container_width=True, hide_index=True)
        export_buttons(idle_df, "idle_funds")

    if uploaded_cash or uploaded_stmt or uploaded_inv:
        st.success("Files uploaded — analysis will incorporate uploaded data on next import cycle.")


def _render_signatory():
    page_header("Authorized Signatory Verification", "Verify approvals, dual compliance, and expired authorizations")
    if not check_permission("signatory"):
        return

    master = st.file_uploader("Authorized Signatory Master", type=["xlsx", "csv"], key="sig_master")
    approval_report = st.file_uploader("Transaction Approval Report", type=["xlsx", "csv"], key="sig_approval")

    txn_df = get_transactions()
    from database import get_signatories
    report = verify_signatories(txn_df, get_signatories())

    if report.empty:
        st.info("No signatory verification data available.")
        return

    st.markdown("#### Risk Report")
    st.dataframe(report, use_container_width=True, hide_index=True)

    exceptions = report[report["Risk"] != "Low"]
    if not exceptions.empty:
        st.markdown("#### Exception Report")
        st.dataframe(exceptions, use_container_width=True, hide_index=True)

    st.markdown("#### Approval Matrix")
    sig_df = get_signatories()
    if not sig_df.empty:
        st.dataframe(sig_df, use_container_width=True, hide_index=True)

    export_buttons(report, "signatory_verification")


def render_overview():
    page_header("Financial Compliance", "Central hub for financial risk and compliance monitoring")
    if not check_permission("finance"):
        return
    st.markdown("Select a financial compliance module from the sidebar, or use the tabs below.")
    tab1, tab2, tab3, tab4 = st.tabs([
        "Round Tripping", "Bank Charges", "Idle Funds", "Signatory Verification",
    ])
    with tab1:
        _render_round_tripping()
    with tab2:
        _render_bank_charges()
    with tab3:
        _render_idle_funds()
    with tab4:
        _render_signatory()


def render(module: str = "overview"):
    if module == "overview":
        render_overview()
    elif module == "round_trip":
        _render_round_tripping()
    elif module == "bank_charges":
        _render_bank_charges()
    elif module == "idle_funds":
        _render_idle_funds()
    elif module == "signatory":
        _render_signatory()
    else:
        render_overview()
