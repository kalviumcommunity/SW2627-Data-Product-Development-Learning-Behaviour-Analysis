import streamlit as st


def render_filters(
    courses=None,
    segments=None,
    statuses=None,
):
    """
    Render reusable dashboard filters.

    Returns:
        selected_course,
        selected_date,
        selected_segment,
        selected_status
    """

    # Default options
    courses = courses or ["All Courses"]
    segments = segments or ["All Segments"]
    statuses = statuses or ["Any Status"]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        selected_course = st.selectbox(
            "Course",
            courses,
            label_visibility="collapsed",
        )

    with col2:
        selected_date = st.date_input(
            "Date",
            value=None,
            label_visibility="collapsed",
        )

    with col3:
        selected_segment = st.selectbox(
            "Segment",
            segments,
            label_visibility="collapsed",
        )

    with col4:
        selected_status = st.selectbox(
            "Status",
            statuses,
            label_visibility="collapsed",
        )

    return (
        selected_course,
        selected_date,
        selected_segment,
        selected_status,
    )