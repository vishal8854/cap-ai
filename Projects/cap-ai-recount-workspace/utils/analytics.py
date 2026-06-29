"""Dashboard analytics and KPI computations."""

import pandas as pd

from database import get_complaints, get_dashboard_kpis, get_litigation_cases, get_transactions


def compute_kpi_cards() -> dict[str, tuple]:
    kpis = get_dashboard_kpis()
    return {
        "Total Cases": (kpis["total_cases"], f"{kpis['open_cases']} open"),
        "Open Cases": (kpis["open_cases"], "Active litigation"),
        "Closed Cases": (kpis["closed_cases"], "Resolved / dismissed"),
        "Pending Investigation": (kpis["pending_investigation"], "Under review"),
        "High Risk Cases": (kpis["high_risk_cases"], "Priority escalation"),
        "Total Complaints": (kpis["total_complaints"], "All categories"),
        "Financial Alerts": (kpis["financial_alerts"], "Requires action"),
        "Compliance Score": (f"{kpis['compliance_score']}%", "Platform health"),
    }


def cases_by_status() -> pd.DataFrame:
    df = get_litigation_cases()
    if df.empty:
        return pd.DataFrame({"status": ["Open", "In Progress", "Closed"], "count": [2, 2, 1]})
    counts = df["current_status"].value_counts().reset_index()
    counts.columns = ["status", "count"]
    return counts


def cases_by_state() -> pd.DataFrame:
    df = get_litigation_cases()
    if df.empty:
        return pd.DataFrame()
    return df.groupby("state").size().reset_index(name="count")


def cases_by_court() -> pd.DataFrame:
    df = get_litigation_cases()
    if df.empty:
        return pd.DataFrame()
    return df.groupby("court").size().reset_index(name="count")


def complaints_by_category() -> pd.DataFrame:
    df = get_complaints()
    if df.empty:
        return pd.DataFrame()
    return df.groupby("category").size().reset_index(name="count")


def financial_risk_summary() -> dict:
    kpis = get_dashboard_kpis()
    txns = get_transactions()
    high_risk = len(txns[txns["risk_score"] >= 60]) if not txns.empty and "risk_score" in txns.columns else 0
    return {
        "suspicious_transactions": kpis["suspicious_transactions"],
        "high_risk_txns": high_risk,
        "interest_deviations": kpis["interest_deviations"],
        "idle_accounts": kpis["idle_balances"],
    }


def compliance_timeline() -> pd.DataFrame:
    cases = get_litigation_cases()
    complaints = get_complaints()
    events = []
    if not cases.empty:
        for _, row in cases.iterrows():
            if row.get("filing_date"):
                events.append({"date": row["filing_date"], "event": f"Case filed: {row['case_id']}", "type": "Litigation"})
            if row.get("hearing_date"):
                events.append({"date": row["hearing_date"], "event": f"Hearing: {row['case_name']}", "type": "Hearing"})
    if not complaints.empty:
        for _, row in complaints.iterrows():
            events.append({"date": str(row.get("created_at", ""))[:10], "event": f"Complaint: {row['complaint_id']}", "type": "Complaint"})
    if not events:
        return pd.DataFrame(columns=["date", "event", "type"])
    return pd.DataFrame(events).sort_values("date")
