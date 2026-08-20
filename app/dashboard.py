import streamlit as st

from components.sidebar import render_sidebar
from components.navbar import render_navbar
from views.overview import render_overview
from views.student_behaviour import render_student_behaviour
from views.course_performance import render_course_performance


st.set_page_config(
    page_title="LearnLens AI - Insight Engine",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 1. Render Sidebar (single persistent sidebar)
selected_page = render_sidebar()

# 2. Render Top Navbar
_ = render_navbar()

# 3. Route content based on selected sidebar item
if selected_page == "Overview":
    render_overview()
elif selected_page == "Student Behaviour":
    render_student_behaviour()
elif selected_page == "Course Performance":
    render_course_performance()
elif selected_page == "Reports & Insights":
    st.title("Reports & Insights")
    st.write("Comprehensive institutional reports and key findings.")
elif selected_page == "Settings":
    st.title("Settings")
    st.write("System configuration and user preferences.")