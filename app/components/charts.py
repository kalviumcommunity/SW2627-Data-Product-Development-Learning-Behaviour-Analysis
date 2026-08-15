import streamlit as st


def render_chart(fig, use_container_width=True):
    """Render a Plotly chart."""

    st.plotly_chart(
        fig,
        use_container_width=use_container_width,
    )