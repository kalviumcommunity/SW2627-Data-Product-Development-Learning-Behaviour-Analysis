"""Behaviour Insights Streamlit view."""
from __future__ import annotations

import streamlit as st
from app.services.behaviour_analytics_service import BehaviourAnalyticsService


def render_behaviour_insights() -> None:
    st.title("Behaviour Insights")
    st.caption("Learner behaviour analysis powered by the existing analytics layer.")

    service = BehaviourAnalyticsService()
    try:
        dashboard = service.load()
        features = service.build_features(dashboard)
    except (KeyError, ValueError) as exc:
        st.error(f"Behaviour analytics could not be loaded: {exc}")
        return

    if features.empty:
        st.info("No learner-course behavioural records are available.")
        return

    segments = service.segments(features)
    segment_stats = service.segment_summary(features)
    relationships = service.relationships(features)
    roots = service.root_causes(features)
    root_stats = service.root_cause_summary(features)
    recommendations = service.recommendations(features)
    recommendation_stats = service.recommendation_summary(features)
    insights = service.insights(features)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Learner-course records", f"{len(features):,}")
    c2.metric("Average completion", f"{features['completion_pct'].mean():.1f}%")
    c3.metric("At-risk records", f"{(segments['segment'] == 'at_risk').sum():,}")
    c4.metric("High-priority actions", f"{(recommendations['priority'] == 'high').sum():,}")

    tab1, tab2, tab3 = st.tabs(
        ["Learner Segments", "Behaviour Drivers", "Recommendations & Insights"]
    )

    with tab1:
        st.subheader("Learner segment distribution")
        if segment_stats.empty:
            st.info("No segmentation results are available.")
        else:
            st.bar_chart(segment_stats.set_index("segment")["student_count"])
            st.dataframe(segment_stats, width="stretch", hide_index=True)
        st.subheader("Learner segments")
        st.dataframe(segments, width="stretch", hide_index=True)

    with tab2:
        st.subheader("Behaviour-to-completion relationships")
        if relationships.empty:
            st.info("There is not enough valid data for relationship analysis.")
        else:
            st.dataframe(relationships, width="stretch", hide_index=True)
            matrix = service.correlation_matrix(features)
            if not matrix.empty:
                st.subheader("Correlation matrix")
                st.dataframe(matrix, width="stretch")

        st.subheader("Root-cause signals")
        st.caption("These are observable behavioural signals, not causal attribution.")
        if root_stats.empty:
            st.info("No root-cause signals are available.")
        else:
            st.dataframe(root_stats, width="stretch", hide_index=True)
            st.dataframe(roots, width="stretch", hide_index=True)

    with tab3:
        st.subheader("Recommended actions")
        if recommendation_stats.empty:
            st.info("No recommendations are available.")
        else:
            st.dataframe(recommendation_stats, width="stretch", hide_index=True)
            st.dataframe(recommendations, width="stretch", hide_index=True)

        st.subheader("Learner insights")
        st.dataframe(insights, width="stretch", hide_index=True)
        st.download_button(
            "Download learner insights CSV",
            data=insights.to_csv(index=False).encode("utf-8"),
            file_name="learner_insights.csv",
            mime="text/csv",
            width="stretch",
        )
