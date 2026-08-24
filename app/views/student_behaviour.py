import pandas as pd
import plotly.express as px
import streamlit as st

from components.charts import render_chart
from components.filters import render_filters
from components.insight_card import render_insight
from components.kpi_card import render_kpi_card
from components.section_header import render_section_header
from services.analytics_service import ALL_STATUSES, AnalyticsService


@st.cache_data(show_spinner=False)
def _load_dashboard_data(data_path: str = "data/raw"):
    return AnalyticsService(data_path).load()


def render_student_behaviour():
    """Render Student Behaviour using the current analytics contract."""

    st.title("Student Behaviour")
    st.caption("Understand how students are engaging with their courses.")

    try:
        dashboard = _load_dashboard_data()
    except (FileNotFoundError, ValueError, KeyError) as exc:
        st.error("Unable to load learning analytics.")
        st.caption(str(exc))
        return

    service = AnalyticsService()

    course, _, _, status = render_filters(
        courses=service.course_options(dashboard),
        statuses=[
            ALL_STATUSES,
            "Completed",
            "In Progress",
            "Dropped",
        ],
        key_prefix="student_behaviour",
        show_date=False,
        show_segment=False,
    )

    filtered = service.filter_data(
        dashboard,
        course=course,
        status=status,
    )

    try:
        metrics = service.behaviour_summary(filtered)
        by_status = service.behaviour_by_status(filtered)
    except (ValueError, KeyError) as exc:
        st.error("Unable to calculate student behaviour metrics.")
        st.caption(str(exc))
        return

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_kpi_card(
            "Avg Study Time",
            f"{metrics['avg_study_time_hours']:.2f} hrs",
        )
    with col2:
        render_kpi_card("Avg Sessions", f"{metrics['avg_sessions']:.2f}")
    with col3:
        render_kpi_card(
            "Avg Quiz Attempts",
            f"{metrics['avg_quiz_attempts']:.2f}",
        )
    with col4:
        render_kpi_card(
            "Completion Rate",
            f"{metrics['completion_rate']:.1f}%",
        )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        render_section_header(
            "Quiz Score vs Completion",
            "Relationship between quiz performance and course completion.",
        )

        completion = filtered.raw["completion"]
        quiz = filtered.raw["quiz"]

        if completion.empty or quiz.empty:
            st.info("No data matches the selected filters.")
        else:
            quiz_summary = (
                quiz.groupby(["student_id", "course_id"], as_index=False)
                .agg(avg_quiz_score=("score_pct", "mean"))
            )

            chart_data = completion.merge(
                quiz_summary,
                on=["student_id", "course_id"],
                how="inner",
                validate="one_to_one",
            )

            if chart_data.empty:
                st.info("No matching quiz and completion records.")
            else:
                fig = px.scatter(
                    chart_data,
                    x="avg_quiz_score",
                    y="completion_pct",
                    hover_name="student_id",
                    hover_data=["course_id", "status"],
                    labels={
                        "avg_quiz_score": "Average quiz score (%)",
                        "completion_pct": "Completion (%)",
                    },
                )
                fig.update_layout(
                    height=360,
                    margin=dict(l=10, r=10, t=20, b=10),
                )
                render_chart(fig)

    with col2:
        render_section_header(
            "Behaviour by Status",
            "Comparison using metrics available in the current dataset.",
        )

        if by_status.empty:
            st.info("No behaviour data matches the selected filters.")
        else:
            display = by_status.rename(
                columns={
                    "status": "Status",
                    "learners": "Learners",
                    "avg_completion_pct": "Avg Completion %",
                    "avg_quiz_score": "Avg Quiz Score %",
                    "avg_quiz_attempts": "Avg Quiz Attempts",
                    "avg_study_hours": "Avg Study Hours",
                    "avg_sessions": "Avg Sessions",
                }
            )
            st.dataframe(
                display,
                hide_index=True,
                use_container_width=True,
            )

    st.divider()

    col1, col2 = st.columns([1.6, 1])

    with col1:
        render_section_header(
            "Study Hours by Course",
            "Total recorded study time from session-duration data.",
        )

        sessions = filtered.raw["sessions"]

        if sessions.empty:
            st.info("No session activity matches the selected filters.")
        else:
            activity = sessions.copy()
            activity["duration_minutes"] = pd.to_numeric(
                activity["duration_minutes"],
                errors="coerce",
            )
            activity = (
                activity.groupby("course_id", as_index=False)
                .agg(
                    sessions=("student_id", "size"),
                    total_minutes=("duration_minutes", "sum"),
                )
            )
            activity["study_hours"] = (
                activity["total_minutes"] / 60
            ).round(2)

            fig = px.bar(
                activity,
                x="course_id",
                y="study_hours",
                hover_data=["sessions"],
                labels={
                    "course_id": "Course",
                    "study_hours": "Study hours",
                },
            )
            fig.update_layout(
                height=340,
                margin=dict(l=10, r=10, t=20, b=10),
            )
            render_chart(fig)

    with col2:
        render_section_header("Key Insights")

        render_insight(
            "Completion Health",
            (
                f"{metrics['completion_rate']:.1f}% of selected "
                "learner-course records are completed."
            ),
            "success" if metrics["completion_rate"] >= 70 else "warning",
        )

        render_insight(
            "Quiz Participation",
            (
                f"Average quiz attempts are "
                f"{metrics['avg_quiz_attempts']:.2f} per learner-course."
            ),
            "info",
        )

        render_insight(
            "Study Activity",
            (
                f"Average study time per learner-course is "
                f"{metrics['avg_study_time_hours']:.2f} hours."
            ),
            "info",
        )

        st.caption(
            "Time-series metrics such as learning streaks, active days, and "
            "weekly activity require timestamped session/quiz events and are "
            "not inferred from the current MVP dataset."
        )
