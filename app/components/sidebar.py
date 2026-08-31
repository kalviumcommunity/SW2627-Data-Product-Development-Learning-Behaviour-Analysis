import streamlit as st


NAV_PAGES = (
    "Overview",
    "Student Behaviour",
    "Course Performance",
    "Reports & Insights",
    "Settings",
)


def _get_persisted_page() -> str:
    """Read and validate the page stored in the browser URL."""
    page = st.query_params.get("page", "Overview")
    return page if page in NAV_PAGES else "Overview"


def _set_page(page: str) -> None:
    """Persist the selected page and synchronize the current session."""
    if page not in NAV_PAGES:
        page = "Overview"

    st.session_state["current_page"] = page
    st.query_params["page"] = page


def render_sidebar():
    """Render the LearnLens sidebar and persist navigation across refreshes."""

    # Initialize from the URL first. A browser refresh creates a new
    # Streamlit session, so session_state alone cannot preserve navigation.
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = _get_persisted_page()

    # If an existing session has a valid page, keep the URL synchronized.
    current_page = st.session_state["current_page"]
    if current_page not in NAV_PAGES:
        current_page = "Overview"
        st.session_state["current_page"] = current_page

    if st.query_params.get("page") != current_page:
        st.query_params["page"] = current_page

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap');

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

        div[data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background-color: #4f46e5 !important;
            color: #ffffff !important;
            box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35) !important;
            border: 1px solid #4f46e5 !important;
        }

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
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-brand-title">LearnLens AI</div>
                <div class="sidebar-brand-sub">Insight Engine</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        nav_items = [
            {"name": "Overview", "icon": "⊞"},
            {"name": "Student Behaviour", "icon": "💡"},
            {"name": "Course Performance", "icon": "📈"},
            {"name": "Reports & Insights", "icon": "📊"},
        ]

        for item in nav_items:
            is_active = st.session_state["current_page"] == item["name"]
            button_label = f"{item['icon']}  {item['name']}"

            if st.button(
                button_label,
                key=f"nav_{item['name']}",
                type="primary" if is_active else "secondary",
                use_container_width=True,
            ):
                _set_page(item["name"])
                st.rerun()

        st.markdown(
            "<div style='height: 100px;'></div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div class='sidebar-footer'></div>",
            unsafe_allow_html=True,
        )

        if st.button(
            "⚙️  Settings",
            key="nav_settings",
            type="secondary",
            use_container_width=True,
        ):
            _set_page("Settings")
            st.rerun()

        st.markdown(
            "<div class='upload-btn-container'>",
            unsafe_allow_html=True,
        )

        if st.button(
            "📥  Upload Dataset",
            key="btn_upload_dataset",
            use_container_width=True,
        ):
            st.session_state["show_uploader"] = not st.session_state.get(
                "show_uploader",
                False,
            )
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.get("show_uploader", False):
            with st.expander(
                "📁 Upload New Dataset",
                expanded=True,
            ):
                uploaded_file = st.file_uploader(
                    "Choose a CSV file",
                    type=["csv"],
                    key="sidebar_file_uploader",
                    label_visibility="collapsed",
                )

                if uploaded_file is not None:
                    st.success(f"Loaded: {uploaded_file.name}")

    return st.session_state["current_page"]
