"""CAP AI - Election Litigation & Financial Compliance Management System."""

import streamlit as st
from pathlib import Path
from streamlit_option_menu import option_menu

from config import (
    APP_TITLE,
    COLORS,
    DEMO_USERS,
    LOGO_PNG,
    LOGO_SVG,
    MENU_ICONS,
    MENU_ITEMS,
    MENU_PERMISSION_MAP,
    ROLES,
    STYLES_CSS,
)
from database import init_db, log_activity
from pages import dashboard, complaints, finance, litigation, reports, settings, upload

PAGE_ROUTER = {
    "Dashboard": lambda: dashboard.render(),
    "Election Litigation": lambda: litigation.render(mode="litigation"),
    "Case Management": lambda: litigation.render(mode="case_management"),
    "Complaints": lambda: complaints.render(),
    "Financial Compliance": lambda: finance.render(module="overview"),
    "Round Tripping Detection": lambda: finance.render(module="round_trip"),
    "Bank Charges Verification": lambda: finance.render(module="bank_charges"),
    "Idle Fund Analysis": lambda: finance.render(module="idle_funds"),
    "Authorized Signatory Verification": lambda: finance.render(module="signatory"),
    "Reports": lambda: reports.render(),
    "Excel Upload": lambda: upload.render(),
    "Settings": lambda: settings.render(),
}


def get_theme_css(dark_mode: bool) -> str:
    css_path = STYLES_CSS
    base_css = css_path.read_text(encoding="utf-8") if css_path.exists() else ""
    bg = "#0F172A" if dark_mode else COLORS["background"]
    card_bg = "rgba(17, 34, 64, 0.72)" if dark_mode else "rgba(255, 255, 255, 0.92)"
    text = COLORS["text_light"] if dark_mode else COLORS["text_dark"]
    muted = "#8892B0" if dark_mode else COLORS["muted"]
    sidebar_bg = COLORS["primary"] if dark_mode else "#FFFFFF"

    return f"""
    <style>
    {base_css}
    :root {{
        --cap-text: {text};
        --cap-muted: {muted};
        --cap-card-bg: {card_bg};
    }}
    .stApp {{
        background: linear-gradient(135deg, {bg} 0%, {"#1E293B" if dark_mode else "#F1F5F9"} 50%, {bg} 100%);
    }}
    [data-testid="stSidebar"] {{
        background: {sidebar_bg} !important;
        border-right: 1px solid rgba(0, 174, 239, 0.15);
    }}
    [data-testid="stSidebar"] * {{
        color: {"#E6F1FF" if dark_mode else COLORS["text_dark"]} !important;
    }}
    </style>
    """


def init_session():
    defaults = {
        "authenticated": False,
        "role": "Viewer",
        "username": "Guest",
        "login_id": "",
        "dark_mode": False,
        "db_initialized": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def render_login():
    logo = LOGO_PNG if LOGO_PNG.exists() else LOGO_SVG
    st.markdown(
        """
        <div class="login-container">
            <div class="login-title">CAP AI</div>
            <div class="login-subtitle">Election Litigation & Financial Compliance Management System</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if logo.exists():
        st.image(str(logo), width=280)

    with st.form("login_form"):
        login_id = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)

    if submitted:
        user_info = DEMO_USERS.get(login_id.lower())
        if user_info and user_info["password"] == password:
            st.session_state["authenticated"] = True
            st.session_state["username"] = user_info["username"]
            st.session_state["role"] = user_info["role"]
            st.session_state["login_id"] = login_id
            log_activity(user_info["username"], user_info["role"], "Login", "Auth", ip="local")
            st.rerun()
        else:
            st.error("Invalid credentials. Try demo: admin / admin123")

    st.caption("Demo: admin/admin123, investigator/inv123, compliance/comp123, legal/legal123, viewer/view123")


def render_sidebar() -> str:
    role = st.session_state.get("role", "Viewer")
    perms = ROLES.get(role, ROLES["Viewer"])
    visible_items = [item for item in MENU_ITEMS if perms.get(MENU_PERMISSION_MAP[item], False)]
    visible_icons = [MENU_ICONS[i] for i, item in enumerate(MENU_ITEMS) if item in visible_items]

    with st.sidebar:
        logo = LOGO_PNG if LOGO_PNG.exists() else LOGO_SVG
        if logo.exists():
            st.image(str(logo), use_container_width=True)
        else:
            st.markdown(f'<div style="text-align:center;font-weight:700;color:{COLORS["accent"]};">CAP AI</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(
            f'<span class="role-badge">{role}</span> &nbsp; **{st.session_state.get("username", "Guest")}**',
            unsafe_allow_html=True,
        )
        st.markdown("---")

        selected = option_menu(
            menu_title="Navigation",
            options=visible_items,
            icons=visible_icons,
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0", "background-color": "transparent"},
                "icon": {"color": COLORS["accent"], "font-size": "16px"},
                "nav-link": {"font-size": "14px", "text-align": "left", "margin": "2px 0", "padding": "10px 14px", "border-radius": "10px"},
                "nav-link-selected": {
                    "background": f"linear-gradient(90deg, {COLORS['accent']}33, transparent)",
                    "border-left": f"3px solid {COLORS['accent']}",
                },
            },
        )

        st.markdown("---")
        dark_mode = st.toggle("Dark Mode", value=st.session_state.get("dark_mode", False))
        st.session_state["dark_mode"] = dark_mode

        global_search = st.text_input("Global Search", placeholder="Cases, courts, accounts...", key="global_search")
        if global_search:
            from database import global_search as db_search
            results = db_search(global_search)
            for label, df in results.items():
                if not df.empty:
                    st.caption(f"{label}: {len(df)} results")

        if st.button("Logout", use_container_width=True):
            st.session_state["authenticated"] = False
            st.session_state["username"] = "Guest"
            st.session_state["role"] = "Viewer"
            st.rerun()

    return selected


def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="⚖️", layout="wide", initial_sidebar_state="expanded")
    init_session()

    if not st.session_state.get("db_initialized"):
        init_db()
        st.session_state["db_initialized"] = True

    dark_mode = st.session_state.get("dark_mode", False)
    st.markdown(get_theme_css(dark_mode), unsafe_allow_html=True)

    if not st.session_state.get("authenticated"):
        render_login()
        return

    selected = render_sidebar()
    handler = PAGE_ROUTER.get(selected, PAGE_ROUTER["Dashboard"])
    handler()


if __name__ == "__main__":
    main()
