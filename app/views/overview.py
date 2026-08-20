import streamlit as st

from components.kpi_card import render_kpi_card
from components.insight_card import render_insight
from components.student_segments import render_student_segments
from components.section_header import render_section_header

def render_overview():
    """Renders the overview page content."""
    st.title("Monitor Overview")

    st.caption(
        "Real-time pulse of institutional learning performance."
    )

    st.divider()

    # -----------------------------
    # KPI CARDS
    # -----------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_kpi_card(
            "Total Students",
            "12,450",
            "4.2% vs last month",
        )

    with col2:
        render_kpi_card(
            "Completion Rate",
            "68.2%",
            "1.5% vs last month",
        )

    with col3:
        render_kpi_card(
            "Dropout Rate",
            "14.8%",
            "0.8% vs last month",
        )

    with col4:
        render_kpi_card(
            "Avg Quiz Score",
            "76.4%",
            "0%",
        )

    st.divider()

    # -----------------------------
    # MAIN ANALYTICS SECTION
    # -----------------------------

    col1, col2 = st.columns(2)

    with col1:
        render_section_header(
            "Learning Behaviour Correlation",
            "Activity metrics vs Completion",
        )

        st.info("Chart will be added here.")

    with col2:
        render_section_header(
            "Course Completion Funnel",
            "Milestone drop-off rates",
        )

        st.info("Chart will be added here.")

    st.divider()

    # -----------------------------
    # STUDENT SEGMENTS DATA
    # -----------------------------

    segments = [
        {
            "name": "High Achievers",
            "badge": "Top 15%",
            "description": (
                "Consistently score >90%, highly engaged "
                "in forums, complete early."
            ),
            "students": "1,867",
            "icon": "🏆",
        },
        {
            "name": "Consistent Learners",
            "badge": "Core 60%",
            "description": (
                "Steady progress, average scores 70–89%, "
                "meets standard deadlines."
            ),
            "students": "7,470",
            "icon": "🏃",
        },
        {
            "name": "Silent At-Risk",
            "badge": "Bottom 10%",
            "description": (
                "Low platform time, missed >1 assignment, "
                "passive viewing only."
            ),
            "students": "1,245",
            "icon": "🚫",
        },
    ]

    # -----------------------------
    # KEY INSIGHTS + STUDENT SEGMENTS
    # -----------------------------

    col1, col2 = st.columns([1, 1.6])

    with col1:
        st.subheader("Key Insights")

        render_insight(
            "Engagement Decline",
            "Weekly student activity has decreased over the recent period.",
            "warning",
        )

        render_insight(
            "Completion Health",
            "Overall completion performance is currently above the baseline.",
            "success",
        )

        render_insight(
            "Quiz Performance",
            "Students with stronger quiz performance show better completion behaviour.",
            "info",
        )

    with col2:
        render_student_segments(segments)