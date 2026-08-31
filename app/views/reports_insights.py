"""Reports & Insights dashboard view."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from components.charts import render_chart
from components.executive_summary import render_executive_summary
from components.filters import render_filters
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


def _csv_bytes(frame: pd.DataFrame) -> bytes:
    """Serialize report data for download."""
    return frame.to_csv(index=False).encode("utf-8")


def render_reports_insights():
    """Render Reports & Insights from the shared analytics service."""

    st.title("Reports & Insights")
    st.caption(
        "Review learning performance and behavioural patterns "
        "from the current analytics dataset."
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
        key_prefix="reports_insights",
        show_date=False,
        show_segment=False,
    )

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
        st.info("No report data matches the selected filters.")
        return

    try:
        snapshot = service.report_snapshot(filtered)
        course_metrics = service.course_performance(filtered)
        status_data = service.status_distribution(filtered)
        export_data = service.report_export_data(filtered)
    except (ValueError, KeyError) as exc:
        st.error("Unable to calculate the selected report.")
        st.caption(str(exc))
        return

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_kpi_card(
            "Completion Rate",
            f"{snapshot['completion_rate']:.1f}%",
        )

    with col2:
        render_kpi_card(
            "Drop-off Rate",
            f"{snapshot['dropout_rate']:.1f}%",
        )

    with col3:
        render_kpi_card(
            "Avg Study Time",
            f"{snapshot['avg_study_time_hours']:.2f} hrs",
        )

    with col4:
        render_kpi_card(
            "Active Students",
            f"{snapshot['active_students']:,}",
        )

    st.divider()

    col1, col2 = st.columns([1.6, 0.8])

    with col1:
        render_section_header(
            "Completion Status Distribution",
            "Current learner-course population by completion status.",
        )

        if status_data.empty:
            st.info("No completion-status data is available.")
        else:
            fig = px.bar(
                status_data,
                x="status",
                y="learners",
                text="learners",
                labels={
                    "status": "Status",
                    "learners": "Learners",
                },
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                height=360,
                margin=dict(l=10, r=10, t=20, b=10),
            )
            render_chart(fig)

    with col2:
        render_section_header(
            "Report Snapshot",
            "Scope of the selected report.",
        )

        st.metric(
            "Learner-course records",
            f"{snapshot['records']:,}",
        )
        st.metric(
            "Courses",
            f"{snapshot['courses']:,}",
        )
        st.metric(
            "Average Quiz Score",
            f"{snapshot['average_quiz_score']:.1f}%",
        )

    st.divider()

    render_section_header(
        "Course Performance Snapshot",
        "Compare completion and engagement across courses.",
    )

    if course_metrics.empty:
        st.info("No course performance data is available.")
    else:
        fig = px.bar(
            course_metrics,
            x="course_id",
            y="completion_rate",
            text="completion_rate",
            hover_data=[
                "learners",
                "avg_quiz_score",
                "dropout_rate",
                "study_hours",
            ],
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
            height=380,
            margin=dict(l=10, r=10, t=20, b=10),
        )
        render_chart(fig)

        display = course_metrics[
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

        st.dataframe(
            display,
            hide_index=True,
            use_container_width=True,
        )

    st.divider()

    summary = [
        (
            f"Completion rate is {snapshot['completion_rate']:.1f}% "
            "for the selected population."
        ),
        (
            f"Drop-off rate is {snapshot['dropout_rate']:.1f}%. "
            "This is descriptive and does not establish causality."
        ),
        (
            f"Average study time is "
            f"{snapshot['avg_study_time_hours']:.2f} hours "
            "per learner-course."
        ),
    ]

    if not course_metrics.empty:
        leader = course_metrics.loc[
            course_metrics["completion_rate"].idxmax()
        ]
        summary.append(
            (
                f"{leader['course_id']} has the highest completion "
                f"rate at {leader['completion_rate']:.1f}%."
            )
        )

    col1, col2 = st.columns([1.6, 0.8])

    with col1:
        render_executive_summary(summary)

    with col2:
        render_section_header(
            "Export Report",
            "Download the filtered learner-course report.",
        )
        st.download_button(
            "📊 Download CSV",
            data=_csv_bytes(export_data),
            file_name="learnlens_reports_insights.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.caption(
        "The current MVP data contract does not provide timestamped "
        "events or a dedicated dropout-reason field. This report "
        "therefore does not invent time-series trends or causal "
        "dropout explanations."
    )
