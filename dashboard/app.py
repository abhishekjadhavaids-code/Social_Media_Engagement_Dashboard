import os
import sys
import io
import json
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file, Response

# Add parent directory and src to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from youtube_api_v3 import analyze_youtube_channel

TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)


# Memory Cache for recent analysis
ANALYSIS_CACHE = {}
LAST_ANALYZED_DATA = None

PRESET_CHANNELS = [
    {"name": "MrBeast", "handle": "@MrBeast", "query": "@MrBeast", "category": "Entertainment", "avatar": "https://yt3.googleusercontent.com/fxGntNnZlFuHGwBHfM-7VUvgnbTXwfyYx4x7CRq-qKdS4phB1v9P82sD71fdp5Ob18n2gmXA=s176-c-k-c0x00ffffff-no-rj"},
    {"name": "Marques Brownlee", "handle": "@mkbhd", "query": "@mkbhd", "category": "Tech & Gadgets", "avatar": "https://yt3.googleusercontent.com/lkH37D712tiAjh0a8XxThB5ppEOoPxfgZf9bb3LuTFUKYuKSUhko4kSYDh-Dnyb0170y9jG7=s176-c-k-c0x00ffffff-no-rj"},
    {"name": "Veritasium", "handle": "@veritasium", "query": "@veritasium", "category": "Science & Ed", "avatar": "https://yt3.googleusercontent.com/ytc/AIdro_kM-Qz3f3K8hZ539Jg6dK_vA00Q-5Q0L7R_9nK90tWf9g=s176-c-k-c0x00ffffff-no-rj"},
    {"name": "Fireship", "handle": "@fireship", "query": "@fireship", "category": "Coding & Tech", "avatar": "https://yt3.googleusercontent.com/ytc/AIdro_n_T7EwJ3QJ53f86eN00nE-0l-M9-9n-0n-0n-0n=s176-c-k-c0x00ffffff-no-rj"},
    {"name": "TED", "handle": "@TED", "query": "@TED", "category": "Talks & Ideas", "avatar": "https://yt3.googleusercontent.com/ytc/AIdro_n0nE-0l-M9-9n-0n-0n-0n=s176-c-k-c0x00ffffff-no-rj"},
    {"name": "PewDiePie", "handle": "@PewDiePie", "query": "@PewDiePie", "category": "Gaming & Vlogs", "avatar": "https://yt3.googleusercontent.com/5o-s6H555555=s176-c-k-c0x00ffffff-no-rj"}
]

@app.route("/")
def index():
    """Render the main SaaS Dashboard SPA."""
    return render_template("index.html")

@app.route("/api/presets", methods=["GET"])
def get_presets():
    """Return list of quick-search preset channels."""
    return jsonify({"presets": PRESET_CHANNELS})

@app.route("/api/analyze", methods=["POST"])
def analyze_channel():
    """Analyze requested YouTube channel."""
    global LAST_ANALYZED_DATA
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    
    if not query:
        return jsonify({"error": "Please enter a channel name, URL, ID, or @handle."}), 400
        
    # Check cache
    cache_key = query.lower()
    if cache_key in ANALYSIS_CACHE:
        LAST_ANALYZED_DATA = ANALYSIS_CACHE[cache_key]
        return jsonify({"status": "success", "data": ANALYSIS_CACHE[cache_key]})
        
    try:
        results = analyze_youtube_channel(query, max_videos=50)
        ANALYSIS_CACHE[cache_key] = results
        LAST_ANALYZED_DATA = results
        
        # Save local dataset copies in data/processed
        save_local_datasets(results)
        
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def save_local_datasets(data):
    """Automatically save exported datasets into data/processed for offline access."""
    try:
        proc_dir = os.path.join(PROJECT_ROOT, "data", "processed")
        os.makedirs(proc_dir, exist_ok=True)
        
        ch_name = data["channel_info"]["title"].replace(" ", "_")
        
        # 1. JSON Export
        with open(os.path.join(proc_dir, f"{ch_name}_analytics.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            
        # 2. Power BI CSV Export
        if data.get("videos"):
            df_pbi = pd.DataFrame(data["videos"])
            df_pbi["Channel_Name"] = data["channel_info"]["title"]
            df_pbi["Overall_Score"] = data["scores"]["overall_score"]
            df_pbi.to_csv(os.path.join(proc_dir, f"PowerBI_{ch_name}_Dataset.csv"), index=False, encoding="utf-8-sig")
            df_pbi.to_csv(os.path.join(proc_dir, "powerbi_latest.csv"), index=False, encoding="utf-8-sig")
            
        # 3. Tableau CSV Export
        if data.get("videos"):
            df_tab = pd.DataFrame(data["videos"])
            df_tab["Channel_ID"] = data["channel_info"]["channel_id"]
            df_tab.to_csv(os.path.join(proc_dir, f"Tableau_{ch_name}_Dataset.csv"), index=False, encoding="utf-8-sig")
            df_tab.to_csv(os.path.join(proc_dir, "tableau_latest.csv"), index=False, encoding="utf-8-sig")
            
        # 4. Multi-sheet Excel Export
        excel_path = os.path.join(proc_dir, f"{ch_name}_Analytics_Report.xlsx")
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            pd.DataFrame([data["channel_info"]]).to_excel(writer, sheet_name="Channel Info", index=False)
            pd.DataFrame([data["scores"]]).to_excel(writer, sheet_name="Scores", index=False)
            if data.get("videos"):
                pd.DataFrame(data["videos"]).to_excel(writer, sheet_name="Video Details", index=False)
            if data.get("category_breakdown"):
                pd.DataFrame(data["category_breakdown"]).to_excel(writer, sheet_name="Category Analytics", index=False)
    except Exception as err:
        print("Error auto-saving local datasets:", err)


@app.route("/api/export/csv", methods=["GET"])
def export_csv():
    """Export video analytics dataset as CSV (compatible with Power BI and Tableau)."""
    global LAST_ANALYZED_DATA
    if not LAST_ANALYZED_DATA or "videos" not in LAST_ANALYZED_DATA:
        return jsonify({"error": "No channel data analyzed yet. Please search a channel first."}), 400
        
    df = pd.DataFrame(LAST_ANALYZED_DATA["videos"])
    ch_name = LAST_ANALYZED_DATA["channel_info"]["title"].replace(" ", "_")
    
    output = io.StringIO()
    df.to_csv(output, index=False, encoding="utf-8-sig")
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={ch_name}_youtube_analytics.csv"}
    )

@app.route("/api/export/powerbi", methods=["GET"])
def export_powerbi():
    """Export structured Power BI dataset format."""
    global LAST_ANALYZED_DATA
    if not LAST_ANALYZED_DATA:
        return jsonify({"error": "No channel data analyzed yet."}), 400
        
    df = pd.DataFrame(LAST_ANALYZED_DATA["videos"])
    # Add KPI summary metadata columns for Power BI slicers
    ch = LAST_ANALYZED_DATA["channel_info"]
    scores = LAST_ANALYZED_DATA["scores"]
    
    df["Channel_Name"] = ch["title"]
    df["Channel_Handle"] = ch["handle"]
    df["Subscriber_Count"] = ch["subscriber_count"]
    df["Total_Views"] = ch["view_count"]
    df["Performance_Score"] = scores["performance_score"]
    df["Engagement_Score"] = scores["engagement_score"]
    df["Growth_Score"] = scores["growth_score"]
    df["Consistency_Score"] = scores["consistency_score"]
    df["Overall_Score"] = scores["overall_score"]
    
    ch_name = ch["title"].replace(" ", "_")
    output = io.StringIO()
    df.to_csv(output, index=False, encoding="utf-8-sig")
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=PowerBI_{ch_name}_Dataset.csv"}
    )

@app.route("/api/export/tableau", methods=["GET"])
def export_tableau():
    """Export Tableau-optimized dataset format."""
    global LAST_ANALYZED_DATA
    if not LAST_ANALYZED_DATA:
        return jsonify({"error": "No channel data analyzed yet."}), 400
        
    df = pd.DataFrame(LAST_ANALYZED_DATA["videos"])
    ch = LAST_ANALYZED_DATA["channel_info"]
    scores = LAST_ANALYZED_DATA["scores"]
    
    df["Channel_ID"] = ch["channel_id"]
    df["Channel_Title"] = ch["title"]
    df["Channel_Country"] = ch["country"]
    df["Overall_Channel_Score"] = scores["overall_score"]
    
    ch_name = ch["title"].replace(" ", "_")
    output = io.StringIO()
    df.to_csv(output, index=False, encoding="utf-8-sig")
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=Tableau_{ch_name}_Dataset.csv"}
    )

@app.route("/api/export/excel", methods=["GET"])
def export_excel():
    """Export comprehensive multi-sheet Excel file (.xlsx)."""
    global LAST_ANALYZED_DATA
    if not LAST_ANALYZED_DATA:
        return jsonify({"error": "No channel data analyzed yet."}), 400
        
    ch_info = LAST_ANALYZED_DATA["channel_info"]
    scores = LAST_ANALYZED_DATA["scores"]
    metrics = LAST_ANALYZED_DATA["metrics_summary"]
    videos = LAST_ANALYZED_DATA["videos"]
    categories = LAST_ANALYZED_DATA["category_breakdown"]
    days = LAST_ANALYZED_DATA["ai_recommendations"]["day_stats"]
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Sheet 1: Channel Overview & Scores
        df_overview = pd.DataFrame([
            {"Metric": "Channel Title", "Value": ch_info["title"]},
            {"Metric": "Handle", "Value": ch_info["handle"]},
            {"Metric": "Subscribers", "Value": ch_info["subscriber_count"]},
            {"Metric": "Total Views", "Value": ch_info["view_count"]},
            {"Metric": "Total Videos", "Value": ch_info["video_count"]},
            {"Metric": "Country", "Value": ch_info["country"]},
            {"Metric": "Overall Score", "Value": scores["overall_score"]},
            {"Metric": "Performance Score", "Value": scores["performance_score"]},
            {"Metric": "Engagement Score", "Value": scores["engagement_score"]},
            {"Metric": "Growth Score", "Value": scores["growth_score"]},
            {"Metric": "Consistency Score", "Value": scores["consistency_score"]},
            {"Metric": "Quality Score", "Value": scores["quality_score"]},
            {"Metric": "Avg Views / Video", "Value": metrics["avg_views"]},
            {"Metric": "Avg Likes / Video", "Value": metrics["avg_likes"]},
            {"Metric": "Avg Comments / Video", "Value": metrics["avg_comments"]},
            {"Metric": "Avg Engagement Rate (%)", "Value": metrics["avg_engagement_rate"]}
        ])
        df_overview.to_excel(writer, sheet_name="Channel Overview", index=False)
        
        # Sheet 2: Video Details
        if videos:
            df_vids = pd.DataFrame(videos)
            cols = ["title", "publish_date", "publish_day", "publish_hour", "views", "likes", "comments", "engagement_rate", "duration_formatted", "category_name", "youtube_url"]
            df_vids[cols].to_excel(writer, sheet_name="Video Details", index=False)
            
        # Sheet 3: Category Breakdown
        if categories:
            pd.DataFrame(categories).to_excel(writer, sheet_name="Category Analytics", index=False)
            
        # Sheet 4: Posting Time Heatmap
        if days:
            pd.DataFrame(days).to_excel(writer, sheet_name="Posting Schedule", index=False)

    output.seek(0)
    ch_name = ch_info["title"].replace(" ", "_")
    return Response(
        output.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={ch_name}_Full_Analytics_Report.xlsx"}
    )

if __name__ == "__main__":
    import sys
    # Detect if executed via Streamlit CLI or Streamlit Cloud
    if any("streamlit" in arg for arg in sys.argv) or "STREAMLIT_SERVER_PORT" in os.environ:
        import streamlit as st
        st.error("⚠️ **Incorrect Main File Path Detected**\n\nYou are running the Flask application (`dashboard/app.py`).\n\nPlease update your **Main file path** in Streamlit Cloud settings to `streamlit_app.py` (or `dashboard/streamlit_app.py`).")
    else:
        from waitress import serve
        port = int(os.environ.get("PORT", 5000))
        print(f"Starting YouTube Engagement Analytics Production WSGI Server on port {port}")
        serve(app, host="0.0.0.0", port=port)



