import streamlit as st


def render_insight(title, message, insight_type="info"):
    """Render an insight message."""

    if insight_type == "success":
        st.success(f"**{title}**\n\n{message}")

    elif insight_type == "warning":
        st.warning(f"**{title}**\n\n{message}")

    elif insight_type == "error":
        st.error(f"**{title}**\n\n{message}")

    else:
        st.info(f"**{title}**\n\n{message}")