"""AI-style insight generation for CAP AI."""

from database import (
    get_complaints,
    get_dashboard_kpis,
    get_idle_accounts,
    get_interest_validations,
    get_litigation_cases,
    get_signatories,
    get_transactions,
)
from utils.compliance import detect_round_tripping, verify_signatories


def generate_insights() -> list[dict]:
    kpis = get_dashboard_kpis()
    cases = get_litigation_cases()
    complaints = get_complaints()
    txns = get_transactions()
    idle = get_idle_accounts()
    interest = get_interest_validations()

    insights = []

    high_risk_cases = len(cases[cases["priority"] == "High"]) if not cases.empty else 0
    if high_risk_cases > 0:
        insights.append({
            "title": "High Risk Litigation",
            "message": f"{high_risk_cases} election litigation cases flagged as high priority require immediate legal review.",
            "risk_level": "High",
            "recommendation": "Assign senior legal officers and schedule expedited hearings.",
            "action": "Escalate to Legal Officer",
            "priority": "P1",
        })

    open_complaints = len(complaints[complaints["status"] == "Open"]) if not complaints.empty else 0
    if open_complaints > 0:
        insights.append({
            "title": "Open Complaints",
            "message": f"{open_complaints} complaints remain unresolved across constituencies.",
            "risk_level": "Medium",
            "recommendation": "Prioritize booth malpractice and vote counting complaints.",
            "action": "Assign investigating officers",
            "priority": "P2",
        })

    if not txns.empty:
        display = txns[["transaction_id", "txn_date", "from_account", "to_account", "amount"]].copy()
        display.columns = ["Transaction ID", "Date", "From Account", "To Account", "Amount"]
        risk_df = detect_round_tripping(display)
        if not risk_df.empty:
            high = len(risk_df[risk_df["Risk Score"] >= 70])
            insights.append({
                "title": "Round-Tripping Alert",
                "message": f"This account cluster appears involved in possible round-tripping. {high} high-risk circular transfer patterns detected.",
                "risk_level": "High",
                "recommendation": "Freeze suspicious accounts and initiate forensic audit.",
                "action": "Run full network analysis",
                "priority": "P1",
            })

    if not interest.empty:
        overcharges = interest[interest["status"] == "Overcharge"]
        if not overcharges.empty:
            total_recovery = overcharges["recovery_opportunity"].sum()
            insights.append({
                "title": "Bank Charge Deviation",
                "message": f"Interest charged exceeds sanctioned terms on {len(overcharges)} accounts. Recovery opportunity: ₹{total_recovery:,.0f}.",
                "risk_level": "High",
                "recommendation": "Compare loan agreements with actual deductions and file recovery claims.",
                "action": "Initiate charge reconciliation",
                "priority": "P1",
            })

    if not idle.empty:
        total_idle = idle["balance"].sum()
        projected = idle.get("projected_earnings", idle["balance"] * 0.05).sum()
        insights.append({
            "title": "Idle Fund Opportunity",
            "message": f"Idle balances of ₹{total_idle:,.0f} could have earned additional investment income. Projected earnings: ₹{projected:,.0f}.",
            "risk_level": "Medium",
            "recommendation": "Implement sweep accounts and short-term investment policies.",
            "action": "Review idle fund analysis report",
            "priority": "P2",
        })

    signatory_report = verify_signatories(txns, get_signatories())
    if not signatory_report.empty:
        unauthorized = signatory_report[signatory_report["Risk"] == "High"]
        if not unauthorized.empty:
            insights.append({
                "title": "Signatory Violation",
                "message": f"Unauthorized approver detected on {len(unauthorized)} transactions.",
                "risk_level": "High",
                "recommendation": "Review approval matrix and revoke expired authorizations.",
                "action": "Generate exception report",
                "priority": "P1",
            })

    insights.append({
        "title": "Compliance Overview",
        "message": f"Platform compliance score: {kpis['compliance_score']}%. {kpis['financial_alerts']} financial alerts active.",
        "risk_level": "Low" if kpis["compliance_score"] >= 80 else "Medium",
        "recommendation": "Maintain audit trail and schedule weekly compliance reviews.",
        "action": "Generate compliance report",
        "priority": "P3",
    })

    return insights
