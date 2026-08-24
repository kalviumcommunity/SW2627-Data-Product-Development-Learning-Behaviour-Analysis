import streamlit as st

from components.filters import render_filters
from components.kpi_card import render_kpi_card
from components.section_header import render_section_header
from components.charts import render_chart
from components.executive_summary import render_executive_summary


def render_reports_insights():
    """Render the Reports & Insights dashboard."""

    st.title("Reports & Insights")

    st.caption(
        "Investigate performance metrics and engagement patterns."
    )

    # --------------------------------
    # FILTERS
    # --------------------------------

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
        key_prefix="reports_insights",
    )

    st.divider()

    # --------------------------------
    # PLACEHOLDER REPORT DATA
    # Replace with backend data later
    # --------------------------------

    report_data = {
        "completion_rate": "78%",
        "completion_delta": "6%",
        "dropout_rate": "12%",
        "dropout_delta": "-2%",
        "avg_study_time": "4.5h",
        "active_students": "2.4k",
    }

    # --------------------------------
    # KPI METRICS
    # --------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_kpi_card(
            "Completion Rate",
            report_data["completion_rate"],
            report_data["completion_delta"],
        )

    with col2:
        render_kpi_card(
            "Dropout Rate",
            report_data["dropout_rate"],
            report_data["dropout_delta"],
        )

    with col3:
        render_kpi_card(
            "Avg Study Time / Week",
            report_data["avg_study_time"],
            "No change",
        )

    with col4:
        render_kpi_card(
            "Active Students",
            report_data["active_students"],
        )

    st.divider()

    # --------------------------------
    # MAIN ANALYTICS
    # --------------------------------

    col1, col2 = st.columns([1.7, 0.8])

    # Monthly Completion Trend
    with col1:

        render_section_header(
            "Monthly Completion Trend",
            "Trailing 6 months",
        )

        st.info(
            "Monthly completion trend chart will be added here."
        )

    # Dropout Reasons
    with col2:

        render_section_header(
            "Dropout Reasons",
            "Main factors associated with student drop-off.",
        )

        st.info(
            "Dropout reasons chart will be added here."
        )

    st.divider()

    # --------------------------------
    # EXECUTIVE SUMMARY + EXPORT
    # --------------------------------

    col1, col2 = st.columns([1.7, 0.8])

    with col1:

        summary = [
            "Completion rate increased 6% quarter-over-quarter.",
            "Maintaining a 48hr quiz window is key to student retention.",
            "Highest drop-offs occur immediately before assignment submission.",
        ]

        render_executive_summary(summary)

    with col2:

        render_section_header(
            "Export Report",
            "Download the current report.",
        )

        st.download_button(
            "📄 PDF",
            data="LearnLens AI Report",
            file_name="learnlens_report.txt",
            mime="text/plain",
            use_container_width=True,
        )

        st.download_button(
            "📊 CSV",
            data="LearnLens AI Report Data",
            file_name="learnlens_report.csv",
            mime="text/csv",
            use_container_width=True,
        )