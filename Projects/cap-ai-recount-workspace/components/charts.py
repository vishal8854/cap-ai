import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.theme import COLORS


def transaction_trend_chart() -> go.Figure:
    dates = pd.date_range("2026-01-01", periods=90, freq="D")
    values = np.cumsum(np.random.randint(50, 200, 90)) + np.sin(np.arange(90) / 7) * 500
    df = pd.DataFrame({"Date": dates, "Transactions": values.astype(int)})
    fig = px.area(
        df, x="Date", y="Transactions",
        color_discrete_sequence=[COLORS["electric_blue"]],
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color=COLORS["white"], height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        title="Transaction Trend",
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.1)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.1)")
    return fig


def risk_heatmap() -> go.Figure:
    branches = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Kolkata"]
    categories = ["Cash", "Transfer", "Interest", "Signatory", "Idle"]
    z = np.random.randint(10, 100, size=(len(branches), len(categories)))
    fig = go.Figure(data=go.Heatmap(
        z=z, x=categories, y=branches,
        colorscale=[[0, COLORS["success"]], [0.5, COLORS["warning"]], [1, COLORS["danger"]]],
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color=COLORS["white"], height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        title="Risk Heatmap",
    )
    return fig


def branch_risk_distribution() -> go.Figure:
    branches = ["Mumbai Central", "Delhi North", "Bangalore IT", "Chennai South", "Hyderabad West"]
    risks = [72, 45, 88, 33, 61]
    colors = [COLORS["danger"] if r > 70 else COLORS["warning"] if r > 50 else COLORS["success"] for r in risks]
    fig = go.Figure(data=[go.Bar(x=branches, y=risks, marker_color=colors)])
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color=COLORS["white"], height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        title="Branch Wise Risk Distribution",
        yaxis_title="Risk Score",
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.1)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.1)")
    return fig


def recount_progress_tracker(cases_df: pd.DataFrame) -> go.Figure:
    if cases_df.empty:
        status_counts = {"Open": 1, "In Progress": 2, "Scheduled": 1, "Closed": 1}
    else:
        status_counts = cases_df["status"].value_counts().to_dict()

    fig = go.Figure(data=[go.Pie(
        labels=list(status_counts.keys()),
        values=list(status_counts.values()),
        hole=0.55,
        marker=dict(colors=[COLORS["electric_blue"], COLORS["warning"], COLORS["success"], COLORS["muted"]]),
    )])
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", font_color=COLORS["white"],
        height=350, margin=dict(l=20, r=20, t=40, b=20),
        title="Recount Progress Tracker",
    )
    return fig
