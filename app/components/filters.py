import streamlit as st


def render_filters(
    courses=None,
    segments=None,
    statuses=None,
    key_prefix="filters",
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
    if courses is None:
        courses = ["All Courses"]

    if segments is None:
        segments = ["All Segments"]

    if statuses is None:
        statuses = ["Any Status"]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        selected_course = st.selectbox(
            "Course",
            courses,
            label_visibility="collapsed",
            key=f"{key_prefix}_course",
        )

    with col2:
        selected_date = st.date_input(
            "Date",
            value=None,
            label_visibility="collapsed",
            key=f"{key_prefix}_date",
        )

    with col3:
        selected_segment = st.selectbox(
            "Segment",
            segments,
            label_visibility="collapsed",
            key=f"{key_prefix}_segment",
        )

    with col4:
        selected_status = st.selectbox(
            "Status",
            statuses,
            label_visibility="collapsed",
            key=f"{key_prefix}_status",
        )

    st.session_state[f"{key_prefix}_filters"] = {
        "course": selected_course,
        "date": selected_date,
        "segment": selected_segment,
        "status": selected_status,
    }

    return (
        selected_course,
        selected_date,
        selected_segment,
        selected_status,
    )