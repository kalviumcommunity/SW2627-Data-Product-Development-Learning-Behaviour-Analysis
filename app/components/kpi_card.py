import streamlit as st


def render_kpi_card(title, value, delta=None):
    """Render a simple KPI metric."""

    st.metric(
        label=title,
        value=value,
        delta=delta,
    )