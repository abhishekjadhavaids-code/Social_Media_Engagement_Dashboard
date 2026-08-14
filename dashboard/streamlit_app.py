import os
import sys
import io
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from dotenv import load_dotenv

# Setup Paths
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BASE_DIR / ".env")

from youtube_api_v3 import analyze_youtube_channel

# Page Configuration
st.set_page_config(
    page_title="YouTube Engagement Analytics Studio (Power BI & Tableau)",
    page_icon="▶️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling
st.markdown("""
<style>
    .stApp {
        background-color: #060913;
        color: #f8fafc;
    }
    .metric-card {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(51, 65, 85, 0.8);
        border-radius: 1rem;
        padding: 1.25rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }
    .score-badge {
        font-size: 2.5rem;
        font-weight: 800;
        color: #ef4444;
    }
</style>
""", unsafe_allow_html=True)

st.title("▶️ YouTube Engagement Analytics Studio")
st.caption("Powered by YouTube Data API v3 &bull; Power BI & Tableau Workspace Integration")

# Sidebar Search & Settings
st.sidebar.header("Channel Search Studio")
query_input = st.sidebar.text_input("Enter Channel Name, @Handle, URL, or ID", "@MrBeast")
search_button = st.sidebar.button("🔍 Search & Analyze Channel", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.subheader("Quick Presets")
col_p1, col_p2 = st.sidebar.columns(2)
if col_p1.button("@MrBeast"):
    query_input = "@MrBeast"
    search_button = True
if col_p2.button("@mkbhd"):
    query_input = "@mkbhd"
    search_button = True
if col_p1.button("@veritasium"):
    query_input = "@veritasium"
    search_button = True
if col_p2.button("@fireship"):
    query_input = "@fireship"
    search_button = True

if search_button or "data" not in st.session_state or st.session_state.get("last_query") != query_input:
    with st.spinner(f"Fetching YouTube API data for '{query_input}'..."):
        try:
            st.session_state["data"] = analyze_youtube_channel(query_input, max_videos=50)
            st.session_state["last_query"] = query_input
        except Exception as e:
            st.error(f"Error fetching channel: {e}")

if "data" in st.session_state:
    data = st.session_state["data"]
    ch = data["channel_info"]
    scores = data["scores"]
    metrics = data["metrics_summary"]
    ai = data["ai_recommendations"]

    # Header Card
    col_av, col_info, col_score = st.columns([1, 3, 2])
    with col_av:
        if ch["avatar_url"]:
            st.image(ch["avatar_url"], width=120)
    with col_info:
        st.subheader(f"{ch['title']} ({ch['handle']})")
        st.write(f"🌍 **Country**: {ch['country']} | 📅 **Created**: {ch['published_at'][:10] if ch['published_at'] else 'N/A'}")
        st.write(f"🔗 [Open on YouTube](https://www.youtube.com/{ch['handle']})")
    with col_score:
        st.markdown(f"""
        <div class="metric-card" style="text-align: center;">
            <p style="margin:0; font-size: 0.8rem; text-transform: uppercase; color: #94a3b8;">Overall Channel Score</p>
            <div class="score-badge">{scores['overall_score']} <span style="font-size: 1rem; color: #94a3b8;">/ 100</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Navigation Tabs
    tab_overview, tab_strategy, tab_pbi, tab_tableau, tab_vault, tab_export = st.tabs([
        "📊 Overview & Scores", "🧠 AI Strategy & Heatmaps", "🟡 Power BI Workspace", "🔵 Tableau Studio", "🎬 Video Vault", "📥 Export Studio"
    ])

    # Tab 1: Overview
    with tab_overview:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Subscribers", ch["subscriber_count_formatted"])
        c2.metric("Total Views", ch["view_count_formatted"])
        c3.metric("Avg Views / Video", metrics["avg_views_formatted"])
        c4.metric("Avg Engagement Rate", f"{metrics['avg_engagement_rate']}%")

        col_radar, col_bar = st.columns([1, 1])
        with col_radar:
            st.subheader("5 Core Channel Scores")
            df_scores = pd.DataFrame({
                "Metric": ["Performance", "Engagement", "Growth", "Consistency", "Quality"],
                "Score": [scores["performance_score"], scores["engagement_score"], scores["growth_score"], scores["consistency_score"], scores["quality_score"]]
            })
            fig_radar = px.line_polar(df_scores, r="Score", theta="Metric", line_close=True, range_r=[0, 100])
            fig_radar.update_traces(fill='toself', fillcolor="rgba(239, 68, 68, 0.3)", line_color="#ef4444")
            fig_radar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#cbd5e1")
            st.plotly_chart(fig_radar, use_container_width=True)

        with col_bar:
            st.subheader("Views & Engagement Timeline")
            if data["videos"]:
                df_vids = pd.DataFrame(data["videos"])
                fig_line = px.line(df_vids, x="publish_date", y="views", hover_data=["title", "engagement_rate"], title="Video Views over Time")
                fig_line.update_traces(line_color="#3b82f6")
                fig_line.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#cbd5e1")
                st.plotly_chart(fig_line, use_container_width=True)

    # Tab 2: AI Strategy & Heatmaps
    with tab_strategy:
        sc1, sc2, sc3 = st.columns(3)
        sc1.success(f"🗓️ **Best Day**: {ai['best_day']['day']}s ({ai['best_day']['avg_engagement']}% ER)")
        sc2.warning(f"⏰ **Best Hour**: {ai['best_hour']['hour_label']} UTC")
        sc3.info(f"⏱️ **Optimal Duration**: {ai['best_duration']['name']}")

        st.subheader("🗓️ 7x24 Upload Heatmap Matrix (Day vs Hour)")
        if ai["heatmap_matrix"]:
            heatmap_rows = []
            for r in ai["heatmap_matrix"]:
                heatmap_rows.append(r["hours"])
            df_hm = pd.DataFrame(heatmap_rows, index=[r["day"] for r in ai["heatmap_matrix"]], columns=[f"{h}:00" for h in range(24)])
            fig_hm = px.imshow(df_hm, labels=dict(x="Hour of Day", y="Day of Week", color="Engagement Rate (%)"), color_continuous_scale="Viridis")
            fig_hm.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#cbd5e1")
            st.plotly_chart(fig_hm, use_container_width=True)

    # Tab 3: Power BI Workspace
    with tab_pbi:
        st.subheader("🟡 Power BI Interactive Workspace Simulation")
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Subs KPI", ch["subscriber_count_formatted"])
        p2.metric("Total Views KPI", ch["view_count_formatted"])
        p3.metric("Performance Score", f"{scores['performance_score']}/100")
        p4.metric("Engagement Score", f"{scores['engagement_score']}/100")
        
        if data["videos"]:
            df_pbi = pd.DataFrame(data["videos"])
            fig_pbi = px.bar(df_pbi, x="title", y="views", color="engagement_rate", title="Power BI Executive Video Matrix")
            fig_pbi.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#cbd5e1")
            st.plotly_chart(fig_pbi, use_container_width=True)

    # Tab 4: Tableau Studio
    with tab_tableau:
        st.subheader("🔵 Tableau Visual Studio")
        if data["videos"]:
            df_tab = pd.DataFrame(data["videos"])
            fig_scatter = px.scatter(df_tab, x="duration_seconds", y="views", size="likes", color="engagement_rate", hover_name="title", title="Scatter Plot: Duration vs Views vs Engagement")
            fig_scatter.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#cbd5e1")
            st.plotly_chart(fig_scatter, use_container_width=True)

    # Tab 5: Video Vault
    with tab_vault:
        st.subheader("🎬 Channel Video Vault")
        if data["videos"]:
            df_vids = pd.DataFrame(data["videos"])
            st.dataframe(df_vids[["title", "publish_date", "duration_formatted", "views", "likes", "comments", "engagement_rate", "category_name"]], use_container_width=True)

    # Tab 6: Export Studio
    with tab_export:
        st.subheader("📥 Download Datasets")
        ex1, ex2, ex3 = st.columns(3)
        if data["videos"]:
            df_export = pd.DataFrame(data["videos"])
            
            csv_buf = io.StringIO()
            df_export.to_csv(csv_buf, index=False)
            
            ex1.download_button("📥 Download Power BI CSV", data=csv_buf.getvalue(), file_name=f"{ch['title']}_PowerBI_Dataset.csv", mime="text/csv")
            ex2.download_button("📥 Download Tableau CSV", data=csv_buf.getvalue(), file_name=f"{ch['title']}_Tableau_Dataset.csv", mime="text/csv")
            ex3.download_button("📥 Download Raw Video CSV", data=csv_buf.getvalue(), file_name=f"{ch['title']}_Raw_Videos.csv", mime="text/csv")