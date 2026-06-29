import streamlit as st


def render_kpi_grid(kpis: dict[str, tuple]) -> None:
    cols = st.columns(4)
    for i, (label, (value, delta)) in enumerate(kpis.items()):
        with cols[i % 4]:
            val_str = f"{value:,}" if isinstance(value, (int, float)) else str(value)
            delta_html = f'<div class="kpi-delta">{delta}</div>' if delta else ""
            st.markdown(
                f"""
                <div class="kpi-card" style="animation-delay: {i * 0.08}s;">
                    <div class="kpi-value">{val_str}</div>
                    <div class="kpi-label">{label}</div>
                    {delta_html}
                </div>
                """,
                unsafe_allow_html=True,
            )


def page_header(title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="cap-header">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="cap-subheader">{subtitle}</div>', unsafe_allow_html=True)
