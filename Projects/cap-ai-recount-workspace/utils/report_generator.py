import io
from datetime import datetime
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from database import crud

LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "cap_ai_logo.svg"


def generate_pdf_report(title: str = "CAP AI Audit Report") -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=22, spaceAfter=20, textColor=colors.HexColor("#00AEEF"))
    body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, spaceAfter=8)

    kpis = crud.get_dashboard_kpis()
    elements = [
        Paragraph("CAP AI — Recount Management Workspace", title_style),
        Paragraph(f"<b>{title}</b>", styles["Heading2"]),
        Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", body_style),
        Spacer(1, 0.3 * inch),
        Paragraph("<b>Executive Summary</b>", styles["Heading3"]),
        Paragraph(
            f"This report summarizes audit findings across {kpis.get('total_accounts', 0)} accounts "
            f"with {kpis.get('transactions_analyzed', 0)} transactions analyzed. "
            f"{kpis.get('suspicious_transactions', 0)} suspicious transactions and "
            f"{kpis.get('idle_balances', 0)} idle balance accounts were identified.",
            body_style,
        ),
        Spacer(1, 0.2 * inch),
        Paragraph("<b>Key Metrics</b>", styles["Heading3"]),
    ]

    data = [["Metric", "Value"]]
    for key, val in kpis.items():
        label = key.replace("_", " ").title()
        data.append([label, str(val)])

    table = Table(data, colWidths=[3.5 * inch, 2 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0A192F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F4F8")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph("<b>Recommendations</b>", styles["Heading3"]))
    elements.append(Paragraph("1. Complete pending recount cases within SLA.", body_style))
    elements.append(Paragraph("2. Sweep idle balances exceeding threshold.", body_style))
    elements.append(Paragraph("3. Investigate round-tripping patterns.", body_style))
    elements.append(Paragraph("4. Resolve unauthorized signatory approvals.", body_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()


def generate_excel_report() -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        crud.get_recount_cases().to_excel(writer, sheet_name="Recount Cases", index=False)
        crud.get_transactions().to_excel(writer, sheet_name="Transactions", index=False)
        crud.get_interest_validations().to_excel(writer, sheet_name="Interest Validation", index=False)
        crud.get_idle_accounts().to_excel(writer, sheet_name="Idle Accounts", index=False)
        crud.get_activity_logs().to_excel(writer, sheet_name="Activity Logs", index=False)
    buffer.seek(0)
    return buffer.read()


def generate_risk_summary() -> bytes:
    buffer = io.BytesIO()
    kpis = crud.get_dashboard_kpis()
    summary = pd.DataFrame([{
        "Report": "Risk Summary",
        "Generated": datetime.now().isoformat(),
        **{k.replace("_", " ").title(): v for k, v in kpis.items()},
    }])
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        summary.to_excel(writer, sheet_name="Risk Summary", index=False)
        crud.get_transactions().to_excel(writer, sheet_name="Flagged Transactions", index=False)
    buffer.seek(0)
    return buffer.read()
