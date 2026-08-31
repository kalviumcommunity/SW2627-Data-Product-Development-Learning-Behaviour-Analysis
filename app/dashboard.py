from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from components.sidebar import render_sidebar
from components.navbar import render_navbar
from views.overview import render_overview
from views.student_behaviour import render_student_behaviour
from views.course_performance import render_course_performance
from views.reports_insights import render_reports_insights


st.set_page_config(
    page_title="LearnLens AI - Insight Engine",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

selected_page = render_sidebar()
_ = render_navbar()

if selected_page == "Overview":
    render_overview()
elif selected_page == "Student Behaviour":
    render_student_behaviour()
elif selected_page == "Course Performance":
    render_course_performance()
elif selected_page == "Reports & Insights":
    render_reports_insights()
elif selected_page == "Settings":
    st.title("Settings")
    st.write("System configuration and user preferences.")
