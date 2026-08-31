"""Course Performance dashboard view."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from components.charts import render_chart
from components.filters import render_filters
from components.insight_card import render_insight
from components.kpi_card import render_kpi_card
from components.section_header import render_section_header
from services.analytics_service import (
    ALL_SEGMENTS,
    ALL_STATUSES,
    AnalyticsService,
)


@st.cache_data(show_spinner=False)
def _load_dashboard_data(data_path: str | None = None):
    """Load and cache cleaned dashboard data."""
    return AnalyticsService(data_path).load()


def render_course_performance():
    """Render course-level performance from the analytics service."""

    st.title("Course Performance")
    st.caption(
        "Compare course completion, engagement, and learning performance."
    )

    try:
        dashboard = _load_dashboard_data()
    except (FileNotFoundError, ValueError, KeyError) as exc:
        st.error("Unable to load learning analytics.")
        st.caption(str(exc))
        return

    service = AnalyticsService()

    course, _, _, status = render_filters(
        courses=service.course_options(dashboard),
        segments=[ALL_SEGMENTS],
        statuses=[
            ALL_STATUSES,
            "Completed",
            "In Progress",
            "Dropped",
        ],
        key_prefix="course_performance",
        show_date=False,
        show_segment=False,
    )

    # UI labels use spaces; backend status values use underscores.
    status_value = (
        status
        if status == ALL_STATUSES
        else status.strip().lower().replace(" ", "_")
    )

    filtered = service.filter_data(
        dashboard,
        course=course,
        status=status_value,
    )

    if filtered.raw["completion"].empty:
        st.info("No course data matches the selected filters.")
        return

    try:
        metrics = service.course_performance(filtered)
    except (ValueError, KeyError) as exc:
        st.error("Unable to calculate course performance.")
        st.caption(str(exc))
        return

    if metrics.empty:
        st.info("No course performance data is available.")
        return

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_kpi_card(
            "Total Courses",
            f"{metrics['course_id'].nunique():,}",
        )

    with col2:
        render_kpi_card(
            "Avg Completion Rate",
            f"{metrics['completion_rate'].mean():.1f}%",
        )

    with col3:
        render_kpi_card(
            "Avg Quiz Score",
            f"{metrics['avg_quiz_score'].mean():.1f}%",
        )

    with col4:
        render_kpi_card(
            "Avg Drop-off Rate",
            f"{metrics['dropout_rate'].mean():.1f}%",
        )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        render_section_header(
            "Course Completion Comparison",
            "Completion rate across the selected course population.",
        )

        fig = px.bar(
            metrics,
            x="course_id",
            y="completion_rate",
            text="completion_rate",
            labels={
                "course_id": "Course",
                "completion_rate": "Completion rate (%)",
            },
        )
        fig.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside",
        )
        fig.update_layout(
            height=360,
            margin=dict(l=10, r=10, t=20, b=10),
        )
        render_chart(fig)

    with col2:
        render_section_header(
            "Course Engagement",
            "Recorded study hours and sessions by course.",
        )

        fig = px.bar(
            metrics,
            x="course_id",
            y="study_hours",
            hover_data=[
                "sessions",
                "active_students",
            ],
            labels={
                "course_id": "Course",
                "study_hours": "Study hours",
                "sessions": "Sessions",
                "active_students": "Active students",
            },
        )
        fig.update_layout(
            height=360,
            margin=dict(l=10, r=10, t=20, b=10),
        )
        render_chart(fig)

    st.divider()

    render_section_header(
        "Course Performance Comparison",
        "Compare completion, quiz performance, drop-off, and study effort.",
    )

    display = metrics[
        [
            "course_id",
            "learners",
            "completion_rate",
            "avg_quiz_score",
            "dropout_rate",
            "study_hours",
        ]
    ].rename(
        columns={
            "course_id": "Course",
            "learners": "Learners",
            "completion_rate": "Completion %",
            "avg_quiz_score": "Avg Quiz %",
            "dropout_rate": "Drop-off %",
            "study_hours": "Study Hours",
        }
    )

    # Compatible with the existing Streamlit API used in this repository.
    st.dataframe(
        display,
        hide_index=True,
        use_container_width=True,
    )

    st.divider()

    completion_leader = metrics.loc[
        metrics["completion_rate"].idxmax()
    ]
    quiz_leader = metrics.loc[
        metrics["avg_quiz_score"].idxmax()
    ]
    study_leader = metrics.loc[
        metrics["study_hours"].idxmax()
    ]

    col1, col2 = st.columns([1.6, 1])

    with col1:
        render_section_header(
            "Course Insights",
            "Patterns derived from the current course-level data.",
        )

        render_insight(
            "Completion Leader",
            (
                f"{completion_leader['course_id']} has the highest "
                f"completion rate at "
                f"{completion_leader['completion_rate']:.1f}%."
            ),
            "success",
        )

        render_insight(
            "Quiz Performance",
            (
                f"{quiz_leader['course_id']} has the highest average "
                f"quiz score at "
                f"{quiz_leader['avg_quiz_score']:.1f}%."
            ),
            "info",
        )

        render_insight(
            "Study Activity",
            (
                f"{study_leader['course_id']} has the highest recorded "
                f"study time at "
                f"{study_leader['study_hours']:.1f} hours."
            ),
            "info",
        )

    with col2:
        render_section_header("Top Performing Course")
        st.metric(
            "Completion Rate",
            f"{completion_leader['completion_rate']:.1f}%",
        )
        st.caption(str(completion_leader["course_id"]))
