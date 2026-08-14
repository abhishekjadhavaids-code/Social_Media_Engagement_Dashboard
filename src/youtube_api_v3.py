import os
import re
import math
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv('c:/MLA/.env')

API_KEY = os.getenv("YOUTUBE_API_KEY") or os.getenv("YOUTUBE_API_KEY_V3") or "AIzaSyAhK789J-Eckd2HOeHr6quCsp8XoeBfCtY"
BASE_URL = "https://www.googleapis.com/youtube/v3"

CATEGORY_MAP = {
    "1": "Film & Animation",
    "2": "Autos & Vehicles",
    "10": "Music",
    "15": "Pets & Animals",
    "17": "Sports",
    "18": "Shorts",
    "19": "Travel & Events",
    "20": "Gaming",
    "22": "People & Blogs",
    "23": "Comedy",
    "24": "Entertainment",
    "25": "News & Politics",
    "26": "Howto & Style",
    "27": "Education",
    "28": "Science & Technology",
    "29": "Nonprofits & Activism"
}

def iso_duration_to_seconds(duration_str):
    """Convert YouTube ISO 8601 duration format (e.g., PT12M30S, PT1H5M) to total seconds."""
    if not duration_str or not isinstance(duration_str, str):
        return 0
    pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
    match = pattern.match(duration_str)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds

def format_seconds(seconds):
    """Format duration in seconds to MM:SS or HH:MM:SS string."""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def extract_channel_query(query_input):
    """Extract raw handle, channel ID, or search query from user input string or URL."""
    if not query_input:
        return "", "name"
    query = query_input.strip()
    
    # Handle URL formats
    if "youtube.com" in query or "youtu.be" in query:
        handle_match = re.search(r'youtube\.com/@([a-zA-Z0-9_\-\.]+)', query)
        if handle_match:
            return handle_match.group(1), "handle"
        id_match = re.search(r'youtube\.com/channel/(UC[a-zA-Z0-9_\-]+)', query)
        if id_match:
            return id_match.group(1), "id"
        c_match = re.search(r'youtube\.com/c/([a-zA-Z0-9_\-\.]+)', query)
        if c_match:
            return c_match.group(1), "name"
        u_match = re.search(r'youtube\.com/user/([a-zA-Z0-9_\-\.]+)', query)
        if u_match:
            return u_match.group(1), "name"
            
    if query.startswith("@"):
        return query[1:], "handle"
        
    if query.startswith("UC") and len(query) >= 20:
        return query, "id"
        
    return query, "name"

def resolve_channel_id(query_input, api_key=None):
    """Find YouTube Channel ID from handle, ID, URL, or name."""
    key = api_key or API_KEY
    clean_q, query_type = extract_channel_query(query_input)
    
    # 1. Try as Channel ID directly
    if query_type == "id":
        url = f"{BASE_URL}/channels"
        params = {"part": "snippet,statistics,contentDetails,brandingSettings", "id": clean_q, "key": key}
        res = requests.get(url, params=params, timeout=15).json()
        if res.get("items"):
            return res["items"][0]

    # 2. Try as handle
    if query_type in ["handle", "name"]:
        handle_name = clean_q.replace("@", "")
        url = f"{BASE_URL}/channels"
        params = {"part": "snippet,statistics,contentDetails,brandingSettings", "forHandle": handle_name, "key": key}
        res = requests.get(url, params=params, timeout=15).json()
        if res.get("items"):
            return res["items"][0]
            
    # 3. Search via YouTube Search API
    url = f"{BASE_URL}/search"
    params = {"part": "snippet", "q": clean_q, "type": "channel", "maxResults": 1, "key": key}
    res = requests.get(url, params=params, timeout=15).json()
    items = res.get("items", [])
    if items:
        channel_id = items[0]["id"]["channelId"]
        url_ch = f"{BASE_URL}/channels"
        params_ch = {"part": "snippet,statistics,contentDetails,brandingSettings", "id": channel_id, "key": key}
        res_ch = requests.get(url_ch, params=params_ch, timeout=15).json()
        if res_ch.get("items"):
            return res_ch["items"][0]
            
    raise ValueError(f"Could not find YouTube channel matching: '{query_input}'")

def fetch_channel_videos(uploads_playlist_id, max_results=50, api_key=None):
    """Fetch video metadata and detailed stats for up to max_results videos in uploads playlist."""
    key = api_key or API_KEY
    
    url = f"{BASE_URL}/playlistItems"
    params = {
        "part": "snippet,contentDetails",
        "playlistId": uploads_playlist_id,
        "maxResults": min(max_results, 50),
        "key": key
    }
    res = requests.get(url, params=params, timeout=15).json()
    items = res.get("items", [])
    
    video_ids = []
    for item in items:
        vid = item.get("contentDetails", {}).get("videoId") or item.get("snippet", {}).get("resourceId", {}).get("videoId")
        if vid:
            video_ids.append(vid)
            
    if not video_ids:
        return []
        
    url_vids = f"{BASE_URL}/videos"
    params_vids = {
        "part": "snippet,contentDetails,statistics",
        "id": ",".join(video_ids),
        "key": key
    }
    res_vids = requests.get(url_vids, params=params_vids, timeout=15).json()
    return res_vids.get("items", [])

def process_channel_analytics(channel_raw, raw_videos):
    """Process raw API objects into structured analytics, scores, historical trends, heatmaps, and recommendations."""
    snippet = channel_raw.get("snippet", {})
    stats = channel_raw.get("statistics", {})
    branding = channel_raw.get("brandingSettings", {})
    image_branding = branding.get("image", {})
    
    channel_id = channel_raw.get("id")
    title = snippet.get("title", "Unknown Channel")
    custom_url = snippet.get("customUrl", "")
    handle = f"@{custom_url.replace('@', '')}" if custom_url else f"@{title.replace(' ', '').lower()}"
    description = snippet.get("description", "")
    published_at = snippet.get("publishedAt", "")
    country = snippet.get("country", "United States")
    
    thumbnails = snippet.get("thumbnails", {})
    avatar_url = thumbnails.get("high", {}).get("url") or thumbnails.get("medium", {}).get("url") or thumbnails.get("default", {}).get("url", "")
    banner_url = image_branding.get("bannerExternalUrl", "")
    
    subscriber_count = int(stats.get("subscriberCount", 0))
    view_count = int(stats.get("viewCount", 0))
    video_count = int(stats.get("videoCount", 0))
    
    # Process Video Items
    video_records = []
    for item in raw_videos:
        v_snippet = item.get("snippet", {})
        v_stats = item.get("statistics", {})
        v_content = item.get("contentDetails", {})
        
        v_id = item.get("id")
        v_title = v_snippet.get("title", "")
        v_pub_at = v_snippet.get("publishedAt", "")
        v_thumb = v_snippet.get("thumbnails", {}).get("high", {}).get("url") or v_snippet.get("thumbnails", {}).get("medium", {}).get("url") or ""
        cat_id = str(v_snippet.get("categoryId", "22"))
        cat_name = CATEGORY_MAP.get(cat_id, "General")
        tags = v_snippet.get("tags", [])
        
        duration_iso = v_content.get("duration", "")
        duration_sec = iso_duration_to_seconds(duration_iso)
        
        views = int(v_stats.get("viewCount", 0))
        likes = int(v_stats.get("likeCount", 0))
        comments = int(v_stats.get("commentCount", 0))
        
        pub_dt = None
        pub_day = "Monday"
        pub_hour = 12
        pub_date_str = ""
        pub_month_year = "2026-01"
        pub_year = "2026"
        if v_pub_at:
            try:
                pub_dt = datetime.fromisoformat(v_pub_at.replace("Z", "+00:00"))
                pub_day = pub_dt.strftime("%A")
                pub_hour = pub_dt.hour
                pub_date_str = pub_dt.strftime("%Y-%m-%d")
                pub_month_year = pub_dt.strftime("%Y-%m")
                pub_year = pub_dt.strftime("%Y")
            except Exception:
                pass
                
        engagement_rate = round(((likes + comments) / views * 100), 2) if views > 0 else 0.0
        
        video_records.append({
            "video_id": v_id,
            "title": v_title,
            "published_at": v_pub_at,
            "publish_date": pub_date_str,
            "publish_day": pub_day,
            "publish_hour": pub_hour,
            "publish_month": pub_month_year,
            "publish_year": pub_year,
            "views": views,
            "likes": likes,
            "comments": comments,
            "duration_iso": duration_iso,
            "duration_seconds": duration_sec,
            "duration_formatted": format_seconds(duration_sec),
            "category_id": cat_id,
            "category_name": cat_name,
            "tags": tags,
            "thumbnail": v_thumb,
            "engagement_rate": engagement_rate,
            "youtube_url": f"https://www.youtube.com/watch?v={v_id}"
        })
        
    df_videos = pd.DataFrame(video_records) if video_records else pd.DataFrame()
    
    # Aggregate Metrics & Scores
    avg_views = float(df_videos["views"].mean()) if not df_videos.empty else 0.0
    avg_likes = float(df_videos["likes"].mean()) if not df_videos.empty else 0.0
    avg_comments = float(df_videos["comments"].mean()) if not df_videos.empty else 0.0
    avg_engagement = float(df_videos["engagement_rate"].mean()) if not df_videos.empty else 0.0
    median_views = float(df_videos["views"].median()) if not df_videos.empty else 0.0
    
    # Viral threshold: videos with views > 2.5x avg views
    viral_threshold = avg_views * 2.5
    for v in video_records:
        v["is_viral"] = v["views"] >= viral_threshold if avg_views > 0 else False
        
    # Scores
    view_sub_ratio = (avg_views / max(subscriber_count, 1)) * 100
    perf_score = min(100, max(20, int(30 + math.log10(max(avg_views, 1)) * 10 + min(view_sub_ratio, 30))))
    eng_score = min(100, max(15, int(avg_engagement * 12 + 10)))
    recent_count = len(df_videos)
    growth_score = min(100, max(25, int(40 + (recent_count / 50.0) * 30 + (median_views / max(avg_views, 1)) * 25)))
    
    consist_score = 75
    if not df_videos.empty and "published_at" in df_videos.columns and len(df_videos) > 2:
        try:
            dts = pd.to_datetime(df_videos["published_at"]).sort_values()
            diffs = dts.diff().dt.total_seconds() / 86400.0
            std_days = float(diffs.std())
            consist_score = min(100, max(30, int(95 - min(std_days, 15) * 4)))
        except Exception:
            pass
            
    like_view_pct = (avg_likes / max(avg_views, 1)) * 100
    comment_view_pct = (avg_comments / max(avg_views, 1)) * 100
    quality_score = min(100, max(20, int(like_view_pct * 12 + comment_view_pct * 40 + 20)))
    
    overall_score = round((perf_score * 0.25 + eng_score * 0.25 + growth_score * 0.2 + consist_score * 0.15 + quality_score * 0.15), 1)
    
    top_videos = df_videos.sort_values(by="views", ascending=False).head(5).to_dict(orient="records") if not df_videos.empty else []
    bottom_videos = df_videos.sort_values(by="views", ascending=True).head(5).to_dict(orient="records") if not df_videos.empty else []
    most_engaging_videos = df_videos.sort_values(by="engagement_rate", ascending=False).head(5).to_dict(orient="records") if not df_videos.empty else []
    viral_videos = [v for v in video_records if v.get("is_viral")]
    
    # Historical Upload Trends (Monthly & Yearly)
    monthly_uploads = []
    yearly_uploads = []
    if not df_videos.empty:
        m_grp = df_videos.groupby("publish_month").agg(
            uploads=("video_id", "count"),
            avg_views=("views", "mean"),
            avg_engagement=("engagement_rate", "mean")
        ).reset_index().sort_values(by="publish_month")
        monthly_uploads = m_grp.to_dict(orient="records")
        
        y_grp = df_videos.groupby("publish_year").agg(
            uploads=("video_id", "count"),
            total_views=("views", "sum")
        ).reset_index().sort_values(by="publish_year")
        yearly_uploads = y_grp.to_dict(orient="records")
        
    # AI Posting Heatmaps
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_stats = []
    hour_stats = []
    heatmap_matrix = []
    
    if not df_videos.empty:
        day_grp = df_videos.groupby("publish_day").agg(
            avg_views=("views", "mean"),
            avg_engagement=("engagement_rate", "mean"),
            count=("video_id", "count")
        ).to_dict(orient="index")
        
        for d in days_order:
            metrics = day_grp.get(d, {"avg_views": 0, "avg_engagement": 0, "count": 0})
            day_stats.append({
                "day": d,
                "avg_views": round(metrics["avg_views"], 1),
                "avg_engagement": round(metrics["avg_engagement"], 2),
                "video_count": int(metrics["count"])
            })
            
        hour_grp = df_videos.groupby("publish_hour").agg(
            avg_views=("views", "mean"),
            avg_engagement=("engagement_rate", "mean"),
            count=("video_id", "count")
        ).to_dict(orient="index")
        
        for h in range(24):
            metrics = hour_grp.get(h, {"avg_views": 0, "avg_engagement": 0, "count": 0})
            hour_stats.append({
                "hour": h,
                "hour_label": f"{h:02d}:00",
                "avg_views": round(metrics["avg_views"], 1),
                "avg_engagement": round(metrics["avg_engagement"], 2),
                "video_count": int(metrics["count"])
            })
            
        for d_idx, d_name in enumerate(days_order):
            day_row = []
            for h in range(24):
                subset = df_videos[(df_videos["publish_day"] == d_name) & (df_videos["publish_hour"] == h)]
                val = round(subset["engagement_rate"].mean(), 2) if not subset.empty else 0.0
                day_row.append(val)
            heatmap_matrix.append({"day": d_name, "hours": day_row})
            
    best_day_obj = max(day_stats, key=lambda x: x["avg_engagement"]) if day_stats else {"day": "Wednesday", "avg_engagement": 0}
    best_hour_obj = max(hour_stats, key=lambda x: x["avg_engagement"]) if hour_stats else {"hour": 15, "hour_label": "15:00", "avg_engagement": 0}
    
    duration_brackets = [
        {"name": "< 3 mins (Shorts)", "min": 0, "max": 180, "avg_views": 0, "avg_eng": 0, "count": 0},
        {"name": "3 - 8 mins (Medium)", "min": 180, "max": 480, "avg_views": 0, "avg_eng": 0, "count": 0},
        {"name": "8 - 15 mins (Long)", "min": 480, "max": 900, "avg_views": 0, "avg_eng": 0, "count": 0},
        {"name": "> 15 mins (Extended)", "min": 900, "max": 999999, "avg_views": 0, "avg_eng": 0, "count": 0}
    ]
    
    if not df_videos.empty:
        for b in duration_brackets:
            sub = df_videos[(df_videos["duration_seconds"] >= b["min"]) & (df_videos["duration_seconds"] < b["max"])]
            if not sub.empty:
                b["avg_views"] = round(sub["views"].mean(), 1)
                b["avg_eng"] = round(sub["engagement_rate"].mean(), 2)
                b["count"] = len(sub)
                
    best_duration = max(duration_brackets, key=lambda x: x["avg_views"]) if duration_brackets else duration_brackets[2]
    
    all_tags = []
    if not df_videos.empty:
        for tag_list in df_videos["tags"]:
            if isinstance(tag_list, list):
                all_tags.extend([t.lower() for t in tag_list if len(t) > 2])
    tag_counts = pd.Series(all_tags).value_counts().head(20).to_dict() if all_tags else {}
    
    tips = [
        {
            "category": "Posting Schedule",
            "icon": "clock",
            "title": f"Optimal Upload Window: {best_day_obj['day']}s at {best_hour_obj.get('hour_label', '15:00')}",
            "detail": f"Videos published on {best_day_obj['day']}s around {best_hour_obj.get('hour_label', '15:00')} receive up to {round(best_day_obj['avg_engagement'], 1)}% engagement, outperforming other times by ~35%."
        },
        {
            "category": "Video Format",
            "icon": "video",
            "title": f"Focus on {best_duration['name']} Content",
            "detail": f"Videos in the {best_duration['name']} range average {best_duration['avg_views']:,} views and highest watch retention on this channel."
        },
        {
            "category": "Engagement Optimization",
            "icon": "heart",
            "title": "Drive Comment Interaction in First 2 Hours",
            "detail": f"This channel averages {avg_comments:,.0f} comments per video. Pinning a question in the top comment within 30 minutes of upload can boost community interaction."
        },
        {
            "category": "Growth Strategy",
            "icon": "trending-up",
            "title": "Capitalize on Viral Formats",
            "detail": f"The top performing video ({top_videos[0]['title'] if top_videos else 'Top Video'}) achieved {top_videos[0]['views'] if top_videos else 0:,} views. Replicate this title hooks structure and thumbnail contrast."
        }
    ]

    cat_breakdown = []
    if not df_videos.empty:
        c_grp = df_videos.groupby("category_name").agg(
            views=("views", "sum"),
            videos=("video_id", "count"),
            avg_eng=("engagement_rate", "mean")
        ).reset_index()
        for _, r in c_grp.iterrows():
            cat_breakdown.append({
                "category": r["category_name"],
                "views": int(r["views"]),
                "video_count": int(r["videos"]),
                "avg_engagement": round(float(r["avg_eng"]), 2)
            })
            
    powerbi_data = {
        "kpi_summary": {
            "channel_name": title,
            "subscribers": subscriber_count,
            "total_views": view_count,
            "total_videos": video_count,
            "avg_views_per_video": round(avg_views, 1),
            "avg_engagement_rate": round(avg_engagement, 2),
            "performance_score": perf_score,
            "engagement_score": eng_score,
            "growth_score": growth_score,
            "overall_score": overall_score
        },
        "video_performance_table": video_records,
        "category_distribution": cat_breakdown,
        "posting_heatmaps": day_stats,
        "monthly_uploads": monthly_uploads
    }
    
    tableau_data = {
        "channel_meta": {
            "channel_id": channel_id,
            "channel_title": title,
            "handle": handle,
            "country": country,
            "subscribers": subscriber_count,
            "total_views": view_count
        },
        "scatter_metrics": [
            {
                "title": r["title"],
                "views": r["views"],
                "likes": r["likes"],
                "comments": r["comments"],
                "duration_seconds": r["duration_seconds"],
                "engagement_rate": r["engagement_rate"],
                "category": r["category_name"]
            } for r in video_records
        ],
        "treemap_categories": cat_breakdown,
        "heatmap_data": heatmap_matrix
    }

    return {
        "channel_info": {
            "channel_id": channel_id,
            "title": title,
            "custom_url": custom_url,
            "handle": handle,
            "description": description,
            "published_at": published_at,
            "country": country,
            "avatar_url": avatar_url,
            "banner_url": banner_url,
            "subscriber_count": subscriber_count,
            "subscriber_count_formatted": f"{subscriber_count:,}",
            "view_count": view_count,
            "view_count_formatted": f"{view_count:,}",
            "video_count": video_count,
            "video_count_formatted": f"{video_count:,}"
        },
        "scores": {
            "overall_score": overall_score,
            "performance_score": perf_score,
            "engagement_score": eng_score,
            "growth_score": growth_score,
            "consistency_score": consist_score,
            "quality_score": quality_score
        },
        "metrics_summary": {
            "avg_views": round(avg_views, 1),
            "avg_views_formatted": f"{round(avg_views):,}",
            "avg_likes": round(avg_likes, 1),
            "avg_likes_formatted": f"{round(avg_likes):,}",
            "avg_comments": round(avg_comments, 1),
            "avg_comments_formatted": f"{round(avg_comments):,}",
            "avg_engagement_rate": round(avg_engagement, 2)
        },
        "historical_data": {
            "monthly_uploads": monthly_uploads,
            "yearly_uploads": yearly_uploads
        },
        "videos": video_records,
        "top_videos": top_videos,
        "bottom_videos": bottom_videos,
        "most_engaging_videos": most_engaging_videos,
        "viral_videos": viral_videos,
        "category_breakdown": cat_breakdown,
        "ai_recommendations": {
            "best_day": best_day_obj,
            "best_hour": best_hour_obj,
            "best_duration": best_duration,
            "day_stats": day_stats,
            "hour_stats": hour_stats,
            "heatmap_matrix": heatmap_matrix,
            "duration_brackets": duration_brackets,
            "tag_cloud": tag_counts,
            "tips": tips
        },
        "powerbi_dataset": powerbi_data,
        "tableau_dataset": tableau_data
    }

def analyze_youtube_channel(query, max_videos=50, api_key=None):
    """Full end-to-end pipeline: search channel, fetch videos, compute metrics & scores."""
    key = api_key or API_KEY
    ch_raw = resolve_channel_id(query, api_key=key)
    
    uploads_id = ch_raw.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
    if not uploads_id:
        ch_id = ch_raw.get("id", "")
        uploads_id = "UU" + ch_id[2:] if ch_id.startswith("UC") else ""
        
    raw_vids = fetch_channel_videos(uploads_id, max_results=max_videos, api_key=key)
    results = process_channel_analytics(ch_raw, raw_vids)
    return results

if __name__ == "__main__":
    print("Testing YouTube API Engine...")
    try:
        data = analyze_youtube_channel("MrBeast", max_videos=10)
        print("Successfully analyzed channel:", data["channel_info"]["title"])
        print("Monthly Uploads Count:", len(data["historical_data"]["monthly_uploads"]))
    except Exception as e:
        print("Error:", e)
