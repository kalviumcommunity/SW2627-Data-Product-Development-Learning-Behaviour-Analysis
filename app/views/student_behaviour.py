import streamlit as st

from components.filters import render_filters
from components.kpi_card import render_kpi_card
from components.insight_card import render_insight
from components.section_header import render_section_header


def render_student_behaviour():

    st.title("Student Behaviour")

    st.caption(
        "Understand how students are engaging with their courses."
    )

    # Filters
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
        key_prefix="student_behaviour",
    )

    st.divider()

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_kpi_card(
            "Avg Study Time",
            "5.2 hrs",
            "4.2%",
        )

    with col2:
        render_kpi_card(
            "Weekly Sessions",
            "4",
            "2.1%",
        )

    with col3:
        render_kpi_card(
            "Quiz Attempts",
            "1.8",
            "3.4%",
        )

    with col4:
        render_kpi_card(
            "Assignment Completion",
            "74%",
            "5.2%",
        )

    st.divider()

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        render_section_header(
            "Quiz Score vs Completion",
            "Relationship between quiz performance and course completion.",
        )

        st.info("Scatter chart will be added here.")

    with col2:
        render_section_header(
            "Weekly Learning Activity",
            "Student learning activity over time.",
        )

        st.info("Line chart will be added here.")

    st.divider()

    # Bottom section
    col1, col2 = st.columns([1.6, 1])

    with col1:
        render_section_header(
            "Behaviour Comparison",
            "Comparison between completed and dropped students.",
        )

        st.info("Behaviour comparison table will be added here.")

    with col2:
        render_section_header("Key Insights")

        render_insight(
            "Optimal Engagement",
            "Most successful students study between 5–7 hours per week.",
            "success",
        )

        render_insight(
            "Predictive Metric",
            "Consistent quiz participation strongly predicts final completion rates.",
            "warning",
        )