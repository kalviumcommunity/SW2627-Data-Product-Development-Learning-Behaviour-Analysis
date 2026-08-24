import streamlit as st


def render_kpi_card(title, value, delta=None):
    """Render a simple KPI metric."""

    if delta is None or delta == "0%":
        st.metric(
            label=title,
            value=value,
        )
    else:
        st.metric(
            label=title,
            value=value,
            delta=delta,
        )