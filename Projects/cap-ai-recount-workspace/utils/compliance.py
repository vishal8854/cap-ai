"""Financial compliance analysis engines."""

from datetime import datetime, timedelta

import networkx as nx
import pandas as pd
import plotly.graph_objects as go

from config import COLORS
from database import get_signatories, get_transactions, update_transaction_risk


def risk_level_from_score(score: float) -> str:
    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def risk_color(score: float) -> str:
    if score >= 70:
        return COLORS["danger"]
    if score >= 40:
        return COLORS["warning"]
    return COLORS["success"]


def detect_round_tripping(df: pd.DataFrame, return_window_days: int = 30) -> pd.DataFrame:
    if df.empty:
        txn_df = get_transactions()
        if txn_df.empty:
            return pd.DataFrame(columns=["Transaction ID", "Risk Score", "Risk Level", "Pattern", "Remarks"])
        df = txn_df.copy()
        df = df.rename(columns={
            "transaction_id": "Transaction ID", "txn_date": "Date",
            "from_account": "From Account", "to_account": "To Account", "amount": "Amount",
        })

    col_map = {
        "transaction_id": "Transaction ID", "txn_date": "Date",
        "from_account": "From Account", "to_account": "To Account", "amount": "Amount",
    }
    for old, new in col_map.items():
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old: new})

    results = []
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

    df_sorted = df.sort_values("Date")
    for i in range(len(df_sorted) - 1):
        row = df_sorted.iloc[i]
        window = df_sorted[
            (df_sorted["Date"] >= row["Date"])
            & (df_sorted["Date"] <= row["Date"] + timedelta(days=3))
        ]
        if len(window) >= 3:
            txn_id = row.get("Transaction ID", "Unknown")
            results.append({
                "Transaction ID": txn_id,
                "Risk Score": 55,
                "Risk Level": "Medium",
                "Pattern": "Multiple transfers within short time",
                "Remarks": f"{len(window)} transfers within 3 days",
            })

    amount_groups = df.groupby("Amount")
    for amount, group in amount_groups:
        if len(group) < 2:
            continue
        accounts = set(group["From Account"].tolist() + group["To Account"].tolist())
        for _, row in group.iterrows():
            risk = 0
            patterns = []
            reverse = group[
                (group["From Account"] == row["To Account"])
                & (group["To Account"] == row["From Account"])
                & (group["Amount"] == row["Amount"])
            ]
            if not reverse.empty:
                for _, rev in reverse.iterrows():
                    days_diff = abs((rev["Date"] - row["Date"]).days)
                    if days_diff <= return_window_days:
                        risk = max(risk, 85)
                        patterns.append("Circular return transfer")

            same_amount_count = len(group)
            if same_amount_count >= 3:
                risk = max(risk, 70)
                patterns.append("Repeated same-amount transfers")

            if len(accounts) <= 4 and same_amount_count >= 2:
                risk = max(risk, 60)
                patterns.append("Related account cluster activity")

            if risk > 0:
                txn_id = row.get("Transaction ID", row.get("transaction_id", "Unknown"))
                level = risk_level_from_score(risk)
                results.append({
                    "Transaction ID": txn_id,
                    "Risk Score": risk,
                    "Risk Level": level,
                    "Pattern": "; ".join(patterns) if patterns else "Suspicious flow",
                    "Remarks": f"Amount ₹{amount:,.0f} — {len(accounts)} accounts involved",
                })
                update_transaction_risk(
                    str(txn_id), risk, patterns[0] if patterns else "", results[-1]["Remarks"], level,
                )

    if not results:
        return pd.DataFrame(columns=["Transaction ID", "Risk Score", "Risk Level", "Pattern", "Remarks"])
    return pd.DataFrame(results).drop_duplicates(subset=["Transaction ID"])


def build_network_graph(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        txn_df = get_transactions()
        df = txn_df.copy()
        df = df.rename(columns={
            "from_account": "From Account", "to_account": "To Account", "amount": "Amount",
        })

    G = nx.DiGraph()
    for _, row in df.iterrows():
        src = str(row.get("From Account", row.get("from_account", "")))
        tgt = str(row.get("To Account", row.get("to_account", "")))
        amt = float(row.get("Amount", row.get("amount", 0)))
        if src and tgt:
            if G.has_edge(src, tgt):
                G[src][tgt]["weight"] += amt
            else:
                G.add_edge(src, tgt, weight=amt)

    if len(G.nodes) == 0:
        fig = go.Figure()
        fig.update_layout(title="No transaction data for network graph", paper_bgcolor="rgba(0,0,0,0)")
        return fig

    pos = nx.spring_layout(G, seed=42)
    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(width=2, color=COLORS["accent"]),
        hoverinfo="none",
    )
    node_x = [pos[n][0] for n in G.nodes()]
    node_y = [pos[n][1] for n in G.nodes()]
    node_text = list(G.nodes())
    node_trace = go.Scatter(
        x=node_x, y=node_y, mode="markers+text",
        text=node_text, textposition="top center",
        marker=dict(size=30, color=COLORS["secondary"], line=dict(width=2, color=COLORS["accent"])),
        hovertext=node_text,
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color=COLORS["text_dark"], height=500,
        title="Money Flow Network Graph",
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    )
    return fig


def verify_bank_charges(interest_df: pd.DataFrame) -> pd.DataFrame:
    if interest_df.empty:
        from database import get_interest_validations
        interest_df = get_interest_validations()
    if interest_df.empty:
        return pd.DataFrame()

    display = interest_df.copy()
    display["Expected Amount"] = display.get("expected_interest", display.get("Expected Interest", 0))
    display["Actual Amount"] = display.get("actual_interest", display.get("Actual Interest", 0))
    display["Difference"] = display["Actual Amount"] - display["Expected Amount"]
    display["Variance %"] = display.get("variance_pct", 0)
    display["Recovery Opportunity"] = display.get("recovery_opportunity", display["Difference"].clip(lower=0))
    return display


def analyze_idle_funds(idle_df: pd.DataFrame) -> dict:
    if idle_df.empty:
        from database import get_idle_accounts
        idle_df = get_idle_accounts()
    if idle_df.empty:
        return {"total_idle": 0, "accounts": 0, "projected_earnings": 0, "opportunities": []}

    total_idle = idle_df["balance"].sum()
    projected = idle_df.get("projected_earnings", pd.Series([0])).sum()
    opportunities = idle_df.sort_values("balance", ascending=False).head(5).to_dict("records")
    return {
        "total_idle": total_idle,
        "accounts": len(idle_df),
        "projected_earnings": projected,
        "opportunities": opportunities,
    }


def verify_signatories(txn_df: pd.DataFrame, signatory_df: pd.DataFrame) -> pd.DataFrame:
    if signatory_df.empty:
        signatory_df = get_signatories()
    if txn_df.empty:
        txn_df = get_transactions()

    auth_map = {}
    expiry_map = {}
    for _, row in signatory_df.iterrows():
        acc = str(row.get("account", ""))
        auth_map[acc] = str(row.get("authorized_signatory", ""))
        expiry_map[acc] = str(row.get("expiry_date", ""))

    results = []
    today = datetime.now().strftime("%Y-%m-%d")
    for _, row in txn_df.iterrows():
        from_acc = str(row.get("from_account", row.get("From Account", "")))
        approver = str(row.get("approved_by", row.get("Approved By", "")))
        txn_id = str(row.get("transaction_id", row.get("Transaction ID", "")))
        authorized = auth_map.get(from_acc, "")
        expiry = expiry_map.get(from_acc, "")

        issues = []
        risk = "Low"
        if not authorized:
            issues.append("No signatory on record")
            risk = "High"
        elif approver != authorized and approver not in ("", "None"):
            issues.append("Unauthorized approver")
            risk = "High"
        if expiry and expiry < today:
            issues.append("Expired authorization")
            if risk != "High":
                risk = "Medium"

        if issues or approver:
            results.append({
                "Transaction ID": txn_id,
                "Account": from_acc,
                "Approver": approver,
                "Authorized Signatory": authorized,
                "Risk": risk,
                "Issues": "; ".join(issues) if issues else "OK",
            })

    return pd.DataFrame(results)
