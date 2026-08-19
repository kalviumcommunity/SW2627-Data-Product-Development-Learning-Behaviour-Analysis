import streamlit as st

from components.filters import render_filters
from components.kpi_card import render_kpi_card
from components.insight_card import render_insight
from components.section_header import render_section_header


def render_course_performance():
    """Render the Course Performance dashboard."""

    st.title("Course Performance")

    st.caption(
        "Compare course completion, engagement, and learning performance."
    )

    # -----------------------------
    # FILTERS
    # -----------------------------

    course, date, segment, status = render_filters(
        courses=[
            "All Courses",
            "Python Fundamentals",
            "Data Science",
            "Web Development",
        ],
        segments=[
            "All Segments",
            "High Achievers",
            "Consistent Learners",
            "Silent At-Risk",
        ],
        statuses=[
            "Any Status",
            "Completed",
            "In Progress",
            "Dropped",
        ],
        key_prefix="course_performance"
    )

    st.divider()

    # -----------------------------
    # KPI METRICS
    # -----------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_kpi_card(
            "Total Courses",
            "24",
            "↑ 2 new",
        )

    with col2:
        render_kpi_card(
            "Avg Completion Rate",
            "68.2%",
            "↑ 3.4%",
        )

    with col3:
        render_kpi_card(
            "Avg Quiz Score",
            "76.4%",
            "↑ 2.1%",
        )

    with col4:
        render_kpi_card(
            "Avg Drop-off Rate",
            "14.8%",
            "↓ 1.2%",
        )

    st.divider()

    # -----------------------------
    # COURSE CHARTS
    # -----------------------------

    col1, col2 = st.columns(2)

    with col1:
        render_section_header(
            "Course Completion Comparison",
            "Completion rate across courses.",
        )

        st.info("Course completion chart will be added here.")

    with col2:
        render_section_header(
            "Course Engagement",
            "Student activity and engagement across courses.",
        )

        st.info("Course engagement chart will be added here.")

    st.divider()

    # -----------------------------
    # COURSE PERFORMANCE
    # -----------------------------

    render_section_header(
        "Course Performance Comparison",
        "Compare completion, quiz performance, and engagement.",
    )

    st.info(
        "Course performance comparison will be added here."
    )

    st.divider()

    # -----------------------------
    # KEY INSIGHTS
    # -----------------------------

    col1, col2 = st.columns([1.6, 1])

    with col1:
        render_section_header(
            "Course Insights",
            "Important patterns identified across courses.",
        )

        render_insight(
            "Strong Completion",
            "Courses with consistent weekly activity show higher completion rates.",
            "success",
        )

        render_insight(
            "Performance Gap",
            "Courses with lower quiz performance show increased drop-off.",
            "warning",
        )

    with col2:
        render_section_header("Top Performing Course")

        st.metric(
            "Python Fundamentals",
            "82.4%",
            "Completion Rate",
        )