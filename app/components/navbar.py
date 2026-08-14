import streamlit as st

def render_navbar():
    """
    Renders the top navigation bar with:
    - Row 1: LearnLens AI main website title (Golden Yellow) + Smaller Notification & Profile Icons (Right)
    - Row 2: Full-width Search input box positioned directly below the website name
    Fully compatible with both Light and Dark themes.
    """
    st.markdown(
        """
        <style>
        /* Import Google Font */
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap');

        /* Clean up top space in main content area */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 3rem !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
        }

        /* Top row title styling with Golden Yellow gradient */
        .navbar-main-title {
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            font-size: 2.5rem !important;
            font-weight: 800 !important;
            background: linear-gradient(135deg, #b45309 0%, #d97706 35%, #f59e0b 70%, #fbbf24 100%) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            color: #f59e0b !important;
            letter-spacing: -0.035em !important;
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1.1 !important;
            display: inline-block !important;
        }

        /* Right actions container */
        .nav-actions {
            display: flex !important;
            align-items: center !important;
            justify-content: flex-end !important;
            gap: 0.65rem !important;
            height: 100% !important;
            padding-top: 0.2rem !important;
        }

        /* Notification Icon */
        .notification-btn {
            position: relative !important;
            width: 34px !important;
            height: 34px !important;
            border-radius: 50% !important;
            background-color: var(--secondary-background-color, rgba(128, 128, 128, 0.08)) !important;
            border: 1px solid rgba(128, 128, 128, 0.2) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
            color: var(--text-color, #475569) !important;
        }

        .notification-btn:hover {
            background-color: rgba(128, 128, 128, 0.15) !important;
            border-color: rgba(128, 128, 128, 0.35) !important;
        }

        .notification-dot {
            position: absolute !important;
            top: 5px !important;
            right: 5px !important;
            width: 7px !important;
            height: 7px !important;
            background-color: #ef4444 !important;
            border: 1.5px solid var(--background-color, #ffffff) !important;
            border-radius: 50% !important;
        }

        /* User Profile Avatar */
        .profile-avatar {
            width: 34px !important;
            height: 34px !important;
            border-radius: 50% !important;
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(217, 119, 6, 0.25) 100%) !important;
            border: 1.5px solid #f59e0b !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
            color: #d97706 !important;
        }

        .profile-avatar:hover {
            transform: scale(1.05) !important;
            box-shadow: 0 3px 10px rgba(245, 158, 11, 0.35) !important;
        }

        /* Full-width Search input styling */
        div[data-testid="stTextInput"] {
            width: 100% !important;
        }

        div[data-testid="stTextInput"] input {
            width: 100% !important;
            background-color: var(--secondary-background-color, rgba(128, 128, 128, 0.08)) !important;
            border: 1.5px solid rgba(128, 128, 128, 0.2) !important;
            border-radius: 10px !important;
            padding: 0.65rem 1rem !important;
            font-size: 0.92rem !important;
            color: var(--text-color, #1e293b) !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            transition: all 0.2s ease !important;
        }

        div[data-testid="stTextInput"] input:focus {
            background-color: var(--background-color, #ffffff) !important;
            border-color: #f59e0b !important;
            box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.2) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ROW 1: Website Name (LearnLens AI in Golden Yellow) & Smaller Action Icons
    row1_title_col, row1_actions_col = st.columns([8, 1], vertical_alignment="center")

    with row1_title_col:
        st.markdown('<div class="navbar-main-title">LearnLens AI</div>', unsafe_allow_html=True)

    with row1_actions_col:
        st.markdown(
            """
            <div class="nav-actions">
                <div class="notification-btn" title="Notifications">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"></path>
                        <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"></path>
                    </svg>
                    <div class="notification-dot"></div>
                </div>
                <div class="profile-avatar" title="User Profile">
                    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                        <circle cx="12" cy="7" r="4"></circle>
                    </svg>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Space between Row 1 and Row 2
    st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

    # ROW 2: Full Width Search Bar
    search_query = st.text_input(
        "Search",
        placeholder="🔍  Search students, courses, or metrics...",
        label_visibility="collapsed",
        key="navbar_search_input",
    )

    # Horizontal divider separating navbar from main page body
    st.markdown(
        "<hr style='margin-top: 1rem; margin-bottom: 1.5rem; border: none; border-bottom: 1px solid rgba(128, 128, 128, 0.15);' />",
        unsafe_allow_html=True,
    )

    return search_query
