import streamlit as st


def render_student_segments(segments):
    """Render reusable student segment cards."""

    st.subheader("Student Segments")

    columns = st.columns(len(segments))

    for column, segment in zip(columns, segments):
        with column:
            with st.container(border=True):
                st.write(f"{segment['icon']}  {segment['badge']}")
                st.markdown(f"### {segment['name']}")
                st.caption(segment["description"])

                st.divider()

                col1, col2 = st.columns([4, 1])

                with col1:
                    st.caption(f"{segment['students']} Students")

                with col2:
                    st.write("→")