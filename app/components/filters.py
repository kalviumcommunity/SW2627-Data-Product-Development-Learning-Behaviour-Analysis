import streamlit as st

from services.analytics_service import (
    ALL_COURSES,
    ALL_SEGMENTS,
    ALL_STATUSES,
)


def render_filters(
    courses=None,
    segments=None,
    statuses=None,
    key_prefix="filters",
    show_date=True,
    show_segment=True,
):
    """Render reusable dashboard filters."""

    courses = courses or [ALL_COURSES]
    segments = segments or [ALL_SEGMENTS]
    statuses = statuses or [ALL_STATUSES]

    visible_filters = 2 + int(show_date) + int(show_segment)
    columns = st.columns(visible_filters)

    column_index = 0

    with columns[column_index]:
        selected_course = st.selectbox(
            "Course",
            courses,
            label_visibility="collapsed",
            key=f"{key_prefix}_course",
        )

    column_index += 1

    if show_date:
        with columns[column_index]:
            selected_date = st.date_input(
                "Date",
                value=None,
                label_visibility="collapsed",
                key=f"{key_prefix}_date",
            )
        column_index += 1
    else:
        selected_date = None

    if show_segment:
        with columns[column_index]:
            selected_segment = st.selectbox(
                "Segment",
                segments,
                label_visibility="collapsed",
                key=f"{key_prefix}_segment",
            )
        column_index += 1
    else:
        selected_segment = ALL_SEGMENTS

    with columns[column_index]:
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
