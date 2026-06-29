from pathlib import Path

import streamlit as st
from streamlit_option_menu import option_menu

from components.theme import COLORS

LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "cap_ai_logo.svg"

MENU_ITEMS = [
    "Dashboard",
    "Recount Management",
    "Fund Round-Tripping Detection",
    "Interest & Bank Charge Validation",
    "Idle Balance Monitoring",
    "Signatory Verification",
    "Excel Import Center",
    "Reports",
    "Settings",
]

MENU_ICONS = [
    "speedometer2",
    "clipboard-check",
    "arrow-repeat",
    "bank",
    "hourglass-split",
    "shield-check",
    "file-earmark-spreadsheet",
    "file-earmark-bar-graph",
    "gear",
]


def render_sidebar() -> str:
    with st.sidebar:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), use_container_width=True)
        else:
            st.markdown(
                f'<div style="text-align:center;padding:1rem;">'
                f'<span style="font-size:1.5rem;font-weight:700;color:{COLORS["electric_blue"]};">CAP AI</span></div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")

        role = st.session_state.get("role", "Auditor")
        user = st.session_state.get("username", "Guest")
        st.markdown(
            f'<span class="role-badge">{role}</span> &nbsp; **{user}**',
            unsafe_allow_html=True,
        )
        st.markdown("---")

        selected = option_menu(
            menu_title="Navigation",
            options=MENU_ITEMS,
            icons=MENU_ICONS,
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0", "background-color": "transparent"},
                "icon": {"color": COLORS["electric_blue"], "font-size": "16px"},
                "nav-link": {
                    "font-size": "14px",
                    "text-align": "left",
                    "margin": "2px 0",
                    "padding": "10px 14px",
                    "border-radius": "10px",
                },
                "nav-link-selected": {
                    "background": f"linear-gradient(90deg, {COLORS['electric_blue']}33, transparent)",
                    "border-left": f"3px solid {COLORS['electric_blue']}",
                    "color": COLORS["white"],
                },
            },
        )

        st.markdown("---")
        dark_mode = st.toggle("Dark Mode", value=st.session_state.get("dark_mode", True), key="dark_mode_toggle")
        st.session_state["dark_mode"] = dark_mode

        global_search = st.text_input("🔍 Search everywhere", placeholder="Cases, accounts, transactions...", key="global_search")

        if global_search:
            st.caption(f'Searching: "{global_search}"')

    return selected
