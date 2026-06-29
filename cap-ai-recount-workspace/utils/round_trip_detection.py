from datetime import datetime, timedelta
from collections import defaultdict

import networkx as nx
import pandas as pd
import plotly.graph_objects as go

from components.theme import COLORS
from database import crud


def detect_round_tripping(df: pd.DataFrame, return_window_days: int = 30) -> pd.DataFrame:
    if df.empty:
        txn_df = crud.get_transactions()
        if txn_df.empty:
            return pd.DataFrame(columns=["Transaction ID", "Risk Score", "Pattern", "Remarks"])
        df = txn_df.copy()
        df = df.rename(columns={
            "transaction_id": "Transaction ID",
            "txn_date": "Date",
            "from_account": "From Account",
            "to_account": "To Account",
            "amount": "Amount",
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
                results.append({
                    "Transaction ID": txn_id,
                    "Risk Score": risk,
                    "Pattern": "; ".join(patterns) if patterns else "Suspicious flow",
                    "Remarks": f"Amount ₹{amount:,.0f} — {len(accounts)} accounts involved",
                })
                crud.update_transaction_risk(str(txn_id), risk, patterns[0] if patterns else "", results[-1]["Remarks"])

    if not results:
        return pd.DataFrame(columns=["Transaction ID", "Risk Score", "Pattern", "Remarks"])
    return pd.DataFrame(results).drop_duplicates(subset=["Transaction ID"])


def build_network_graph(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        txn_df = crud.get_transactions()
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

    edge_trace = go.Scatter(x=edge_x, y=edge_y, mode="lines",
                            line=dict(width=2, color=COLORS["electric_blue"]),
                            hoverinfo="none")

    node_x = [pos[n][0] for n in G.nodes()]
    node_y = [pos[n][1] for n in G.nodes()]
    node_text = list(G.nodes())
    node_trace = go.Scatter(
        x=node_x, y=node_y, mode="markers+text",
        text=node_text, textposition="top center",
        marker=dict(size=30, color=COLORS["electric_blue"], line=dict(width=2, color=COLORS["white"])),
        hovertext=node_text,
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color=COLORS["white"], height=500,
        title="Money Flow Network Graph", margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    )
    return fig


def risk_color(score: float) -> str:
    if score >= 70:
        return COLORS["danger"]
    if score >= 40:
        return COLORS["warning"]
    return COLORS["success"]
