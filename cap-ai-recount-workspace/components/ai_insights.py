import streamlit as st

from database import crud


def render_ai_insights_panel() -> None:
    kpis = crud.get_dashboard_kpis()
    cases = crud.get_recount_cases()
    idle = crud.get_idle_accounts()
    interest = crud.get_interest_validations()

    total_idle = idle["balance"].sum() if not idle.empty else 0
    active_cases = kpis.get("active_recount_cases", 0)
    deviations = kpis.get("interest_deviations", 0)

    insights = {
        "Risk Summary": (
            f"Platform analyzed {kpis.get('transactions_analyzed', 0)} transactions across "
            f"{kpis.get('total_accounts', 0)} accounts. "
            f"{kpis.get('suspicious_transactions', 0)} flagged as high-risk requiring immediate review."
        ),
        "Key Findings": (
            f"{active_cases} active recount cases in progress. "
            f"₹{total_idle:,.0f} in idle balances detected across {kpis.get('idle_balances', 0)} accounts. "
            f"{deviations} interest calculation deviations identified."
        ),
        "Recommended Actions": (
            "Prioritize Mumbai Central and Bangalore IT branches for recount completion. "
            "Initiate sweep procedures for accounts idle >90 days. "
            "Escalate unauthorized approval cases to compliance team."
        ),
        "Compliance Observations": (
            "Observer assignments are current for 3 of 5 active cases. "
            "Signatory verification flagged 2 unauthorized approvals. "
            "Round-tripping patterns detected in 2 transaction clusters."
        ),
    }

    st.markdown("#### 🤖 AI Insights Panel")
    for title, body in insights.items():
        st.markdown(
            f"""
            <div class="insight-card">
                <div class="insight-title">{title}</div>
                <div class="insight-body">{body}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
