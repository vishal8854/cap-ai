COLORS = {
    "navy": "#0A192F",
    "navy_light": "#112240",
    "navy_lighter": "#1D3557",
    "electric_blue": "#00AEEF",
    "electric_blue_dark": "#0077B6",
    "white": "#E6F1FF",
    "muted": "#8892B0",
    "success": "#64FFDA",
    "warning": "#FFB347",
    "danger": "#FF6B6B",
    "glass": "rgba(17, 34, 64, 0.72)",
}


def get_css(dark_mode: bool = True) -> str:
    bg = COLORS["navy"] if dark_mode else "#F8FAFC"
    card_bg = COLORS["glass"] if dark_mode else "rgba(255, 255, 255, 0.85)"
    text = COLORS["white"] if dark_mode else "#1E293B"
    muted = COLORS["muted"] if dark_mode else "#64748B"
    sidebar_bg = COLORS["navy_light"] if dark_mode else "#FFFFFF"

    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    .stApp {{
        background: linear-gradient(135deg, {bg} 0%, {COLORS["navy_light"] if dark_mode else "#E2E8F0"} 50%, {bg} 100%);
    }}

    [data-testid="stSidebar"] {{
        background: {sidebar_bg} !important;
        border-right: 1px solid rgba(0, 174, 239, 0.15);
    }}

    [data-testid="stSidebar"] .block-container {{
        padding-top: 1rem;
    }}

    .cap-header {{
        font-size: 1.75rem;
        font-weight: 700;
        color: {text};
        margin-bottom: 0.25rem;
        letter-spacing: -0.02em;
    }}

    .cap-subheader {{
        font-size: 0.875rem;
        color: {muted};
        margin-bottom: 1.5rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }}

    .kpi-card {{
        background: {card_bg};
        backdrop-filter: blur(12px);
        border: 1px solid rgba(0, 174, 239, 0.2);
        border-radius: 16px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        animation: fadeInUp 0.6s ease forwards;
        opacity: 0;
    }}

    .kpi-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0, 174, 239, 0.15);
    }}

    .kpi-value {{
        font-size: 2rem;
        font-weight: 700;
        color: {COLORS["electric_blue"]};
        line-height: 1.2;
    }}

    .kpi-label {{
        font-size: 0.8rem;
        color: {muted};
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 0.5rem;
    }}

    .kpi-delta {{
        font-size: 0.75rem;
        color: {COLORS["success"]};
        margin-top: 0.25rem;
    }}

    .glass-card {{
        background: {card_bg};
        backdrop-filter: blur(12px);
        border: 1px solid rgba(0, 174, 239, 0.15);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
    }}

    .insight-card {{
        background: linear-gradient(135deg, rgba(0,174,239,0.1) 0%, rgba(17,34,64,0.8) 100%);
        border-left: 4px solid {COLORS["electric_blue"]};
        border-radius: 0 12px 12px 0;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
    }}

    .insight-title {{
        font-weight: 600;
        color: {COLORS["electric_blue"]};
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }}

    .insight-body {{
        color: {text};
        font-size: 0.9rem;
        margin-top: 0.35rem;
        line-height: 1.5;
    }}

    .risk-low {{ color: {COLORS["success"]}; font-weight: 600; }}
    .risk-medium {{ color: {COLORS["warning"]}; font-weight: 600; }}
    .risk-high {{ color: {COLORS["danger"]}; font-weight: 600; }}

    .stButton > button {{
        background: linear-gradient(135deg, {COLORS["electric_blue"]} 0%, {COLORS["electric_blue_dark"]} 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 174, 239, 0.3);
    }}

    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 174, 239, 0.4);
    }}

    div[data-testid="stMetric"] {{
        background: {card_bg};
        backdrop-filter: blur(12px);
        border: 1px solid rgba(0, 174, 239, 0.15);
        border-radius: 12px;
        padding: 1rem;
    }}

    @keyframes fadeInUp {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.6; }}
    }}

    .loading-pulse {{
        animation: pulse 1.5s ease-in-out infinite;
    }}

    .section-divider {{
        border-top: 1px solid rgba(0, 174, 239, 0.15);
        margin: 1.5rem 0;
    }}

    .role-badge {{
        display: inline-block;
        background: rgba(0, 174, 239, 0.15);
        color: {COLORS["electric_blue"]};
        padding: 0.2rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    </style>
    """
