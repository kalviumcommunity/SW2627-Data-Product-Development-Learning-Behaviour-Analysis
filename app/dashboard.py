import streamlit as st
import sys
from pathlib import Path

# Add project root and app dir to path for imports
app_dir = Path(__file__).resolve().parent
if str(app_dir) not in sys.path:
    sys.path.append(str(app_dir))

from components.sidebar import render_sidebar
from components.navbar import render_navbar
from components.overview import render_overview

st.set_page_config(
    page_title="LearnLens AI - Insight Engine",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 1. Render Sidebar (single persistent sidebar)
selected_page = render_sidebar()

# 2. Render Top Navbar
search_query = render_navbar()

# 3. Route content based on selected sidebar item
if selected_page == "Overview":
    render_overview()
elif selected_page == "Student Behaviour":
    st.title("Student Behaviour")
    st.write("Detailed behavioural analysis and patterns.")
elif selected_page == "Course Performance":
    st.title("Course Performance")
    st.write("Course completion metrics and performance KPIs.")
elif selected_page == "Reports & Insights":
    st.title("Reports & Insights")
    st.write("Comprehensive institutional reports and key findings.")
elif selected_page == "Settings":
    st.title("Settings")
    st.write("System configuration and user preferences.")