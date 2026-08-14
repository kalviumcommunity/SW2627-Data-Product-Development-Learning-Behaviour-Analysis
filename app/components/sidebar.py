import streamlit as st

def render_sidebar():
    """
    Renders the custom LearnLens AI sidebar with seamless Light & Dark mode support.
    Returns the selected navigation page name.
    """
    # Initialize session state for navigation
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Overview"

    # Inject theme-adaptive CSS for Sidebar
    st.markdown(
        """
        <style>
        /* Import Google Font */
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap');

        /* Sidebar container styling */
        section[data-testid="stSidebar"] {
            border-right: 1px solid rgba(128, 128, 128, 0.15) !important;
            padding-top: 1.5rem !important;
            width: 280px !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
        }

        section[data-testid="stSidebar"] .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
            padding-left: 1.25rem !important;
            padding-right: 1.25rem !important;
        }

        /* Brand styling in sidebar */
        .sidebar-brand {
            padding: 0 0.5rem 1.5rem 0.5rem !important;
        }
        .sidebar-brand-title {
            font-size: 0.90rem !important;
            font-weight: 800 !important;
            background: linear-gradient(135deg, #d97706 0%, #f59e0b 60%, #fbbf24 100%) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            color: #f59e0b !important;
            letter-spacing: -0.01em !important;
            line-height: 1.2 !important;
            margin: 0 !important;
            display: inline-block !important;
        }
        .sidebar-brand-sub {
            font-size: 0.68rem !important;
            font-weight: 600 !important;
            color: rgba(128, 128, 128, 0.85) !important;
            margin-top: 0.15rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.04em !important;
        }

        /* Navigation Buttons */
        div[data-testid="stSidebar"] .stButton > button {
            width: 100% !important;
            border-radius: 10px !important;
            padding: 0.65rem 1rem !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            border: 1px solid transparent !important;
            text-align: left !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
            gap: 0.75rem !important;
            transition: all 0.2s ease-in-out !important;
            background-color: transparent !important;
            color: var(--text-color, #334155) !important;
            margin-bottom: 0.35rem !important;
            box-shadow: none !important;
        }

        div[data-testid="stSidebar"] .stButton > button:hover {
            background-color: rgba(128, 128, 128, 0.1) !important;
            color: var(--text-color, #1e1b4b) !important;
            border-color: rgba(128, 128, 128, 0.2) !important;
        }

        /* Active Nav Button */
        div[data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background-color: #4f46e5 !important;
            color: #ffffff !important;
            box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35) !important;
            border: 1px solid #4f46e5 !important;
        }

        /* Bottom section buttons */
        .sidebar-footer {
            margin-top: 2rem !important;
            padding-top: 1rem !important;
            border-top: 1px solid rgba(128, 128, 128, 0.15) !important;
        }

        .upload-btn-container button {
            border: 1.5px solid #4f46e5 !important;
            color: #4f46e5 !important;
            background-color: transparent !important;
            font-weight: 600 !important;
            border-radius: 10px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 0.5rem !important;
        }
        .upload-btn-container button:hover {
            background-color: rgba(79, 70, 229, 0.1) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        # Brand / Logo Header with Golden Yellow color
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-brand-title">LearnLens AI</div>
                <div class="sidebar-brand-sub">Insight Engine</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Navigation Options List
        nav_items = [
            {"name": "Overview", "icon": "⊞"},
            {"name": "Student Behaviour", "icon": "💡"},
            {"name": "Course Performance", "icon": "📈"},
            {"name": "Reports & Insights", "icon": "📊"},
        ]

        for item in nav_items:
            is_active = st.session_state["current_page"] == item["name"]
            button_label = f"{item['icon']}  {item['name']}"
            btn_type = "primary" if is_active else "secondary"

            if st.button(
                button_label,
                key=f"nav_{item['name']}",
                type=btn_type,
                use_container_width=True,
            ):
                st.session_state["current_page"] = item["name"]
                st.rerun()

        # Vertical Spacer
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)

        # Footer Actions
        st.markdown("<div class='sidebar-footer'></div>", unsafe_allow_html=True)

        # Settings link/button
        if st.button("⚙️  Settings", key="nav_settings", type="secondary", use_container_width=True):
            st.session_state["current_page"] = "Settings"
            st.rerun()

        # Upload Dataset Button
        st.markdown("<div class='upload-btn-container'>", unsafe_allow_html=True)
        if st.button("📥  Upload Dataset", key="btn_upload_dataset", use_container_width=True):
            st.session_state["show_uploader"] = not st.session_state.get("show_uploader", False)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # Optional file uploader drawer if clicked
        if st.session_state.get("show_uploader", False):
            with st.expander("📁 Upload New Dataset", expanded=True):
                uploaded_file = st.file_uploader(
                    "Choose a CSV file",
                    type=["csv"],
                    key="sidebar_file_uploader",
                    label_visibility="collapsed",
                )
                if uploaded_file is not None:
                    st.success(f"Loaded: {uploaded_file.name}")

    return st.session_state["current_page"]
