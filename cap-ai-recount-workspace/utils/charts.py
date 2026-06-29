"""Plotly chart builders for CAP AI dashboards."""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import COLORS
from utils.analytics import (
    cases_by_court,
    cases_by_state,
    cases_by_status,
    complaints_by_category,
    compliance_timeline,
)


def _base_layout(fig: go.Figure, title: str, height: int = 350) -> go.Figure:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color=COLORS["text_dark"],
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        title=title,
    )
    fig.update_xaxes(gridcolor="rgba(0,0,0,0.08)")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0.08)")
    return fig


def cases_status_pie() -> go.Figure:
    df = cases_by_status()
    fig = go.Figure(data=[go.Pie(
        labels=df["status"], values=df["count"], hole=0.55,
        marker=dict(colors=[COLORS["accent"], COLORS["warning"], COLORS["success"], COLORS["secondary"], COLORS["muted"]]),
    )])
    return _base_layout(fig, "Cases by Status")


def cases_by_state_bar() -> go.Figure:
    df = cases_by_state()
    if df.empty:
        df = pd.DataFrame({"state": ["Maharashtra", "Delhi", "Karnataka"], "count": [2, 1, 2]})
    fig = px.bar(df, x="state", y="count", color_discrete_sequence=[COLORS["secondary"]])
    return _base_layout(fig, "Cases by State")


def cases_by_court_bar() -> go.Figure:
    df = cases_by_court()
    if df.empty:
        df = pd.DataFrame({"court": ["Supreme Court", "High Court"], "count": [1, 4]})
    fig = px.bar(df, x="court", y="count", color_discrete_sequence=[COLORS["primary"]])
    return _base_layout(fig, "Cases by Court")


def complaints_category_pie() -> go.Figure:
    df = complaints_by_category()
    if df.empty:
        df = pd.DataFrame({"category": ["Booth Malpractice", "Vote Counting"], "count": [2, 2]})
    fig = px.pie(df, names="category", values="count", color_discrete_sequence=px.colors.sequential.Blues_r)
    return _base_layout(fig, "Complaints by Category")


def transaction_trend_chart() -> go.Figure:
    dates = pd.date_range("2026-01-01", periods=90, freq="D")
    values = np.cumsum(np.random.randint(50, 200, 90)) + np.sin(np.arange(90) / 7) * 500
    df = pd.DataFrame({"Date": dates, "Transactions": values.astype(int)})
    fig = px.area(df, x="Date", y="Transactions", color_discrete_sequence=[COLORS["accent"]])
    return _base_layout(fig, "Transaction Trend")


def round_trip_trend() -> go.Figure:
    dates = pd.date_range("2026-01-01", periods=12, freq="ME")
    alerts = np.random.randint(2, 15, 12)
    df = pd.DataFrame({"Month": dates, "Alerts": alerts})
    fig = px.line(df, x="Month", y="Alerts", markers=True, color_discrete_sequence=[COLORS["danger"]])
    return _base_layout(fig, "Round Tripping Trend")


def bank_charge_recovery_chart() -> go.Figure:
    categories = ["Interest", "Charges", "Penalties", "Late Fees"]
    expected = [120000, 45000, 12000, 8000]
    actual = [145000, 48000, 15000, 9500]
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Expected", x=categories, y=expected, marker_color=COLORS["secondary"]))
    fig.add_trace(go.Bar(name="Actual", x=categories, y=actual, marker_color=COLORS["danger"]))
    fig.update_layout(barmode="group")
    return _base_layout(fig, "Bank Charge Recovery")


def idle_funds_chart() -> go.Figure:
    accounts = ["ACC-201", "ACC-202", "ACC-203", "ACC-204", "ACC-205"]
    balances = [850000, 1200000, 450000, 680000, 320000]
    fig = px.bar(x=accounts, y=balances, color_discrete_sequence=[COLORS["warning"]])
    fig.update_layout(xaxis_title="Account", yaxis_title="Idle Balance (₹)")
    return _base_layout(fig, "Idle Funds by Account")


def risk_heatmap() -> go.Figure:
    states = ["Maharashtra", "Delhi", "Karnataka", "Tamil Nadu", "Telangana"]
    categories = ["Litigation", "Complaints", "Round Trip", "Charges", "Signatory"]
    z = np.random.randint(10, 100, size=(len(states), len(categories)))
    fig = go.Figure(data=go.Heatmap(
        z=z, x=categories, y=states,
        colorscale=[[0, COLORS["success"]], [0.5, COLORS["warning"]], [1, COLORS["danger"]]],
    ))
    return _base_layout(fig, "Risk Heatmap")


def compliance_timeline_chart() -> go.Figure:
    df = compliance_timeline()
    if df.empty:
        df = pd.DataFrame({
            "date": ["2026-01-15", "2026-02-20", "2026-03-05"],
            "event": ["Case filed", "Hearing scheduled", "Complaint received"],
            "type": ["Litigation", "Hearing", "Complaint"],
        })
    fig = px.scatter(df, x="date", y="type", text="event", color="type",
                     color_discrete_sequence=[COLORS["primary"], COLORS["accent"], COLORS["secondary"]])
    fig.update_traces(textposition="top center")
    return _base_layout(fig, "Compliance Timeline", height=400)


def compliance_score_gauge(score: float) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": "Compliance Score"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": COLORS["accent"]},
            "steps": [
                {"range": [0, 50], "color": "rgba(239,68,68,0.3)"},
                {"range": [50, 80], "color": "rgba(245,158,11,0.3)"},
                {"range": [80, 100], "color": "rgba(16,185,129,0.3)"},
            ],
        },
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=280)
    return fig
