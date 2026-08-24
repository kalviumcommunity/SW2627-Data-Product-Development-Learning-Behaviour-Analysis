import streamlit as st


def render_executive_summary(items):
    """Render the executive summary card."""

    with st.container(border=True):
        st.markdown("### ✨ Executive Summary")

        for item in items:
            st.markdown(f"- {item}")