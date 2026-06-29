# CAP AI — Election Litigation & Financial Compliance Management System

Enterprise-grade Streamlit application for election litigation tracking, complaint management, and financial compliance monitoring.

## Features

- **Executive Dashboard** — KPI cards, interactive Plotly charts, risk heatmaps, compliance score gauge, AI insights
- **Election Litigation Tracker** — Full case lifecycle with search, filters, AG Grid tables, Excel/CSV export
- **Complaint Management** — Complaint registry, timeline, status progress, evidence uploads
- **Financial Compliance**
  - Round tripping detection with network graphs
  - Bank charges verification and recovery analysis
  - Idle fund analysis with projected earnings
  - Authorized signatory verification and exception reports
- **Excel Import Center** — CSV/XLS/XLSX upload with preview, validation, duplicate detection
- **Reports** — Daily, weekly, monthly, risk, compliance, and financial alert reports
- **Role-based access** — Admin, Investigator, Compliance Officer, Legal Officer, Viewer
- **Audit trail** — Login, edit, delete, upload, and export tracking

## Project Structure

```
├── app.py              # Main application entry point
├── config.py           # Branding, roles, menu configuration
├── database.py         # SQLite schema and CRUD operations
├── requirements.txt
├── assets/
│   ├── cap_ai_logo.svg
│   ├── cap_ai_logo.png
│   └── styles.css
├── pages/
│   ├── dashboard.py
│   ├── litigation.py
│   ├── complaints.py
│   ├── finance.py
│   ├── reports.py
│   ├── upload.py
│   └── settings.py
├── utils/
│   ├── analytics.py
│   ├── excel.py
│   ├── compliance.py
│   ├── ai_engine.py
│   ├── charts.py
│   └── ui_helpers.py
└── database/
    └── cap_ai.db       # Created on first run
```

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501

## Demo Accounts

| Username       | Password  | Role                |
|----------------|-----------|---------------------|
| admin          | admin123  | Admin               |
| investigator   | inv123    | Investigator        |
| compliance     | comp123   | Compliance Officer  |
| legal          | legal123  | Legal Officer       |
| viewer         | view123   | Viewer              |

## Branding

- Primary: `#1F4E79`
- Secondary: `#2E75B6`
- Accent: `#00AEEF`

## License

Internal use — CAP AI
