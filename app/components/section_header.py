import streamlit as st


def render_section_header(title, description=None):
    """Render a reusable section heading."""

    st.subheader(title)

    if description:
        st.caption(description)