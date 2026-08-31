import plotly.express as px
import streamlit as st

from components.charts import render_chart
from components.filters import render_filters
from components.insight_card import render_insight
from components.kpi_card import render_kpi_card
from components.section_header import render_section_header
from services.analytics_service import ALL_SEGMENTS, ALL_STATUSES, AnalyticsService


@st.cache_data(show_spinner=False)
def _load_dashboard_data(data_path: str | None = None):
    return AnalyticsService(data_path).load()


def render_overview():
    """Render Overview using the current analytics contract."""

    st.title("Monitor Overview")
    st.caption("Real-time pulse of institutional learning performance.")

    try:
        dashboard = _load_dashboard_data()
    except (FileNotFoundError, ValueError, KeyError) as exc:
        st.error("Unable to load learning analytics.")
        st.caption(str(exc))
        return

    service = AnalyticsService()

    # Date and Segment are hidden until the backend supports those filters.
    course, _, _, status = render_filters(
        courses=service.course_options(dashboard),
        segments=[ALL_SEGMENTS],
        statuses=[ALL_STATUSES, "Completed", "In Progress", "Dropped"],
        key_prefix="overview",
        show_date=False,
        show_segment=False,
    )

    filtered = service.filter_data(dashboard, course=course, status=status)

    try:
        kpis = service.kpis(filtered)
    except (ValueError, KeyError) as exc:
        st.error("The selected filters cannot be applied.")
        st.caption(str(exc))
        return

    st.divider()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_kpi_card("Active Students", f"{kpis['active_students']:,}")
    with col2:
        render_kpi_card("Completion Rate", f"{kpis['completion_rate']:.1f}%")
    with col3:
        render_kpi_card("Dropout Rate", f"{kpis['dropoff_rate']:.1f}%")
    with col4:
        render_kpi_card(
            "Avg Quiz Score", f"{kpis['average_quiz_score']:.1f}%"
        )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        render_section_header(
            "Quiz Performance vs Completion",
            "Available behavioural relationship in the current dataset",
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
                    height=360, margin=dict(l=10, r=10, t=20, b=10)
                )
                render_chart(fig)

    with col2:
        render_section_header(
            "Course Completion Funnel",
            "Learners retained at each completion milestone",
        )
        try:
            funnel = service.funnel(filtered)
        except (ValueError, KeyError) as exc:
            st.warning("Completion funnel is unavailable.")
            st.caption(str(exc))
        else:
            if funnel.empty:
                st.info("No completion data matches the selected filters.")
            else:
                labels = {
                    "enrolled": "Enrolled",
                    "started": "Started",
                    "25_percent": "25%",
                    "50_percent": "50%",
                    "75_percent": "75%",
                    "completed": "Completed",
                }
                funnel = funnel.copy()
                funnel["label"] = funnel["stage"].map(labels)
                fig = px.funnel(
                    funnel,
                    y="label",
                    x="student_count",
                    labels={"student_count": "Learners", "label": ""},
                )
                fig.update_layout(
                    height=360, margin=dict(l=10, r=10, t=20, b=10)
                )
                render_chart(fig)

    st.divider()

    col1, col2 = st.columns([1, 1.6])
    with col1:
        st.subheader("Key Insights")
        completion_rate = kpis["completion_rate"]
        dropout_rate = kpis["dropoff_rate"]
        quiz_score = kpis["average_quiz_score"]

        render_insight(
            "Completion Health",
            f"Current completion rate is {completion_rate:.1f}%.",
            "success" if completion_rate >= 70 else "warning",
        )
        render_insight(
            "Drop-off Risk",
            f"Current drop-off rate is {dropout_rate:.1f}%.",
            "warning" if dropout_rate >= 15 else "info",
        )
        render_insight(
            "Quiz Performance",
            f"Average quiz performance is {quiz_score:.1f}%.",
            "success" if quiz_score >= 75 else "info",
        )

    with col2:
        render_section_header(
            "Data Integration Status",
            "Current backend fields used by the dashboard",
        )
        st.success(
            "Overview is connected to the existing pipeline and analytics layer."
        )
        st.caption(
            "Course IDs are shown directly because the current backend does "
            "not yet provide course display names. Date and Segment filters "
            "will be added when the backend provides the required fields."
        )
