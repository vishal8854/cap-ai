"""CAP AI application configuration and branding constants."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
DATABASE_DIR = BASE_DIR / "database"
DB_PATH = DATABASE_DIR / "cap_ai.db"
LOGO_SVG = ASSETS_DIR / "cap_ai_logo.svg"
LOGO_PNG = ASSETS_DIR / "cap_ai_logo.png"
STYLES_CSS = ASSETS_DIR / "styles.css"
UPLOADS_DIR = BASE_DIR / "uploads"

# Brand colors
COLORS = {
    "primary": "#1F4E79",
    "secondary": "#2E75B6",
    "accent": "#00AEEF",
    "background": "#FFFFFF",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "muted": "#64748B",
    "text_dark": "#1E293B",
    "text_light": "#F8FAFC",
}

APP_TITLE = "CAP AI - Election Litigation & Financial Compliance Management System"
APP_SHORT = "CAP AI"

# User roles and permissions
ROLES = {
    "Admin": {
        "dashboard": True, "litigation": True, "complaints": True,
        "finance": True, "round_trip": True, "bank_charges": True,
        "idle_funds": True, "signatory": True, "reports": True,
        "upload": True, "settings": True,
    },
    "Investigator": {
        "dashboard": True, "litigation": True, "complaints": True,
        "finance": True, "round_trip": True, "bank_charges": True,
        "idle_funds": True, "signatory": True, "reports": True,
        "upload": True, "settings": False,
    },
    "Compliance Officer": {
        "dashboard": True, "litigation": False, "complaints": True,
        "finance": True, "round_trip": True, "bank_charges": True,
        "idle_funds": True, "signatory": True, "reports": True,
        "upload": True, "settings": False,
    },
    "Legal Officer": {
        "dashboard": True, "litigation": True, "complaints": True,
        "finance": False, "round_trip": False, "bank_charges": False,
        "idle_funds": False, "signatory": False, "reports": True,
        "upload": True, "settings": False,
    },
    "Viewer": {
        "dashboard": True, "litigation": True, "complaints": True,
        "finance": True, "round_trip": True, "bank_charges": True,
        "idle_funds": True, "signatory": True, "reports": True,
        "upload": False, "settings": False,
    },
}

DEMO_USERS = {
    "admin": {"password": "admin123", "username": "Admin User", "role": "Admin"},
    "investigator": {"password": "inv123", "username": "Investigator User", "role": "Investigator"},
    "compliance": {"password": "comp123", "username": "Compliance Officer", "role": "Compliance Officer"},
    "legal": {"password": "legal123", "username": "Legal Officer", "role": "Legal Officer"},
    "viewer": {"password": "view123", "username": "Viewer User", "role": "Viewer"},
}

MENU_ITEMS = [
    "Dashboard",
    "Election Litigation",
    "Case Management",
    "Complaints",
    "Financial Compliance",
    "Round Tripping Detection",
    "Bank Charges Verification",
    "Idle Fund Analysis",
    "Authorized Signatory Verification",
    "Reports",
    "Excel Upload",
    "Settings",
]

MENU_ICONS = [
    "house", "scale", "folder2", "envelope",
    "bank", "arrow-repeat", "cash-coin", "hourglass-split",
    "shield-check", "file-earmark-bar-graph", "file-earmark-spreadsheet", "gear",
]

MENU_PERMISSION_MAP = {
    "Dashboard": "dashboard",
    "Election Litigation": "litigation",
    "Case Management": "litigation",
    "Complaints": "complaints",
    "Financial Compliance": "finance",
    "Round Tripping Detection": "round_trip",
    "Bank Charges Verification": "bank_charges",
    "Idle Fund Analysis": "idle_funds",
    "Authorized Signatory Verification": "signatory",
    "Reports": "reports",
    "Excel Upload": "upload",
    "Settings": "settings",
}
