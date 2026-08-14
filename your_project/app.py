import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="YouTube Engagement Analytics",
    page_icon="▶️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# LOAD CSS
# --------------------------------------------------

css_file = Path("style.css")

if css_file.exists():
    st.markdown(
        f"<style>{css_file.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True
    )

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-logo">
            <div class="youtube-icon">▶</div>
            <div>
                <div class="youtube-title">YouTube</div>
                <div class="analytics-title">Analytics</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### 🔎 Search YouTube")

    search = st.text_input(
        "Search",
        placeholder="e.g. MrBeast, T-Series...",
        label_visibility="collapsed"
    )

    if st.button("🔍 Search Channel", use_container_width=True):
        if search:
            st.session_state["search"] = search

    st.markdown("---")

    st.markdown("### ⭐ Popular Searches")

    popular = [
        "MrBeast",
        "T-Series",
        "GamerFleet",
        "CarryMinati",
        "Technical Guruji",
        "PewDiePie"
    ]

    cols = st.columns(2)

    for i, name in enumerate(popular):

        with cols[i % 2]:

            if st.button(
                name,
                key=f"popular_{i}",
                use_container_width=True
            ):
                st.session_state["search"] = name

    st.markdown("---")

    st.markdown(
        """
        <div class="sidebar-info">
            Search any public YouTube channel and explore
            subscribers, views, videos, likes, comments
            and engagement.
        </div>
        """,
        unsafe_allow_html=True
    )


# --------------------------------------------------
# MAIN PAGE
# --------------------------------------------------

st.markdown(
    """
    <div class="hero">

        <div class="hero-left">

            <div class="hero-badge">
                📊 YOUTUBE DATA INTELLIGENCE
            </div>

            <h1>YouTube Engagement Analytics</h1>

            <p>
                Search any public YouTube channel and explore
                subscribers, views, videos, likes, comments
                and engagement performance through interactive
                analytics.
            </p>

            <div class="hero-pills">

                <span>🔎 Search</span>
                <span>📊 Analyze</span>
                <span>🎥 Videos</span>
                <span>👥 Audience</span>
                <span>🚀 Grow</span>

            </div>

        </div>

        <div class="hero-card">

            <div class="hero-card-title">
                YouTube Engagement Analytics
            </div>

            <div class="hero-card-text">
                Search for a YouTube channel to see
                performance and engagement insights.
            </div>

            <div class="hero-code">
                📊 Dashboard
            </div>

        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# SEARCH SECTION
# --------------------------------------------------

st.markdown(
    """
    <div class="section-header">
        <h2>🔎 Find a YouTube Channel</h2>
        <p>
            Search by channel name and select the channel you want to analyze.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

search_col, button_col = st.columns([5, 1])

with search_col:

    channel_name = st.text_input(
        "Channel name",
        value=st.session_state.get("search", ""),
        placeholder="Search any YouTube channel...",
        label_visibility="collapsed"
    )

with button_col:

    search_clicked = st.button(
        "🔍 Search",
        use_container_width=True
    )


# --------------------------------------------------
# API WARNING
# --------------------------------------------------

if search_clicked and not channel_name:

    st.warning(
        "Please enter a YouTube channel name."
    )


# --------------------------------------------------
# SAMPLE DASHBOARD
# --------------------------------------------------

st.markdown(
    """
    <div class="dashboard-section">

        <h2>📺 Channel Overview</h2>

        <p class="muted">
            Complete overview of the selected YouTube channel.
        </p>

    </div>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# CHANNEL CARD
# --------------------------------------------------

col1, col2 = st.columns([1, 5])

with col1:

    st.markdown(
        """
        <div class="channel-logo">
            ▶
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:

    st.markdown(
        """
        <div class="channel-information">

            <h1>Techno Gamerz</h1>

            <p>
                🎮 YouTube gaming and entertainment channel.
            </p>

            <p>
                Explore channel statistics, video performance,
                engagement and audience information.
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )


# --------------------------------------------------
# STATISTICS
# --------------------------------------------------

st.markdown("### 📊 Channel Statistics")

a, b, c, d = st.columns(4)

with a:
    st.metric(
        "Subscribers",
        "52.70M"
    )

with b:
    st.metric(
        "Total Views",
        "16.31B"
    )

with c:
    st.metric(
        "Videos",
        "1.19K"
    )

with d:
    st.metric(
        "Avg. Views / Video",
        "13.75M"
    )


# --------------------------------------------------
# ENGAGEMENT
# --------------------------------------------------

st.markdown("### 📈 Engagement Analysis")

a, b, c, d = st.columns(4)

with a:
    st.metric(
        "Engagement",
        "4.12%"
    )

with b:
    st.metric(
        "Views",
        "331.18M"
    )

with c:
    st.metric(
        "Likes",
        "13.05M"
    )

with d:
    st.metric(
        "Comments",
        "1.45M"
    )


# --------------------------------------------------
# VIDEOS
# --------------------------------------------------

st.markdown("### 🎬 Recent YouTube Videos")

videos = [
    {
        "title": "REMOVING WATER FROM THE MARKET",
        "views": "4.70M",
        "likes": "135.46K",
        "comments": "14.04K",
        "engagement": "3.18%"
    },
    {
        "title": "MY FIRST MISSION IN A 5 STAR HOTEL",
        "views": "4.83M",
        "likes": "183.20K",
        "comments": "13.37K",
        "engagement": "4.07%"
    },
    {
        "title": "MY FIRST DAY OF AGENT TRAINING",
        "views": "6.80M",
        "likes": "211.78K",
        "comments": "12.83K",
        "engagement": "3.30%"
    }
]

cols = st.columns(3)

for i, video in enumerate(videos):

    with cols[i]:

        st.markdown(
            f"""
            <div class="video-card">

                <div class="video-placeholder">
                    ▶
                </div>

                <h3>{video["title"]}</h3>

                <div class="video-stats">
                    👁 {video["views"]}<br>
                    ❤️ {video["likes"]}<br>
                    💬 {video["comments"]}<br>
                    📊 Engagement: {video["engagement"]}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )