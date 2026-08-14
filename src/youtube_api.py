import os
import re
import requests
import pandas as pd
from dotenv import load_dotenv


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")

if not API_KEY:
    raise ValueError(
        "YOUTUBE_API_KEY not found. Check your .env file."
    )

BASE_URL = "https://www.googleapis.com/youtube/v3"

OUTPUT_FILE = "data/raw/youtube_videos.csv"

# Search topics for our Social Media Engagement project
SEARCH_QUERIES = [
    "data analytics",
    "python data analysis",
    "Power BI",
    "machine learning"
]

VIDEOS_PER_QUERY = 25


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def iso_duration_to_seconds(duration):
    """
    Convert YouTube ISO 8601 duration into seconds.

    Example:
    PT10M30S -> 630
    """

    if not duration:
        return 0

    pattern = re.compile(
        r"PT"
        r"(?:(\d+)H)?"
        r"(?:(\d+)M)?"
        r"(?:(\d+)S)?"
    )

    match = pattern.match(duration)

    if not match:
        return 0

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    return hours * 3600 + minutes * 60 + seconds


def get_video_ids(query, max_results=25):
    """
    Search YouTube and return video IDs.
    """

    url = f"{BASE_URL}/search"

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "order": "relevance",
        "maxResults": max_results,
        "key": API_KEY
    }

    response = requests.get(url, params=params, timeout=30)

    if response.status_code != 200:
        raise RuntimeError(
            f"YouTube search failed: "
            f"{response.status_code}\n{response.text}"
        )

    data = response.json()

    results = []

    for item in data.get("items", []):
        video_id = item.get("id", {}).get("videoId")

        if video_id:
            results.append({
                "video_id": video_id,
                "search_query": query
            })

    return results


def get_video_details(video_ids):
    """
    Retrieve detailed information and statistics
    for a list of video IDs.
    """

    url = f"{BASE_URL}/videos"

    params = {
        "part": "snippet,contentDetails,statistics",
        "id": ",".join(video_ids),
        "key": API_KEY
    }

    response = requests.get(url, params=params, timeout=30)

    if response.status_code != 200:
        raise RuntimeError(
            f"YouTube video details failed: "
            f"{response.status_code}\n{response.text}"
        )

    return response.json().get("items", [])


# ============================================================
# MAIN DATA COLLECTION
# ============================================================

def main():

    print("=" * 60)
    print("SOCIAL MEDIA ENGAGEMENT DASHBOARD")
    print("YouTube Data Collection")
    print("=" * 60)

    all_search_results = []

    # --------------------------------------------------------
    # STEP 1: Search videos
    # --------------------------------------------------------

    for query in SEARCH_QUERIES:

        print(f"\nSearching YouTube for: {query}")

        results = get_video_ids(
            query,
            VIDEOS_PER_QUERY
        )

        print(f"Videos found: {len(results)}")

        all_search_results.extend(results)

    # --------------------------------------------------------
    # STEP 2: Remove duplicate videos
    # --------------------------------------------------------

    unique_videos = {}

    for item in all_search_results:

        video_id = item["video_id"]

        if video_id not in unique_videos:
            unique_videos[video_id] = item

    print("\nUnique videos:", len(unique_videos))

    # --------------------------------------------------------
    # STEP 3: Get detailed video information
    # --------------------------------------------------------

    video_ids = list(unique_videos.keys())

    # YouTube allows multiple IDs in one request.
    # Process in groups of 50.

    detailed_videos = []

    for i in range(0, len(video_ids), 50):

        batch = video_ids[i:i + 50]

        print(
            f"Fetching details for videos "
            f"{i + 1} to {i + len(batch)}..."
        )

        details = get_video_details(batch)

        detailed_videos.extend(details)

    # --------------------------------------------------------
    # STEP 4: Build dataset
    # --------------------------------------------------------

    records = []

    for video in detailed_videos:

        snippet = video.get("snippet", {})
        statistics = video.get("statistics", {})
        content = video.get("contentDetails", {})

        video_id = video.get("id")

        search_query = unique_videos.get(
            video_id,
            {}
        ).get(
            "search_query",
            ""
        )

        published_at = snippet.get(
            "publishedAt"
        )

        duration_iso = content.get(
            "duration",
            ""
        )

        duration_seconds = iso_duration_to_seconds(
            duration_iso
        )

        records.append({

            "video_id": video_id,

            "title": snippet.get(
                "title",
                ""
            ),

            "channel": snippet.get(
                "channelTitle",
                ""
            ),

            "channel_id": snippet.get(
                "channelId",
                ""
            ),

            "published_at": published_at,

            "description": snippet.get(
                "description",
                ""
            ),

            "category_id": snippet.get(
                "categoryId",
                ""
            ),

            "duration": duration_iso,

            "duration_seconds": duration_seconds,

            "views": int(
                statistics.get(
                    "viewCount",
                    0
                )
            ),

            "likes": int(
                statistics.get(
                    "likeCount",
                    0
                )
            ),

            "comments": int(
                statistics.get(
                    "commentCount",
                    0
                )
            ),

            "search_query": search_query
        })

    # --------------------------------------------------------
    # STEP 5: Create DataFrame
    # --------------------------------------------------------

    df = pd.DataFrame(records)

    # --------------------------------------------------------
    # STEP 6: Convert date
    # --------------------------------------------------------

    df["published_at"] = pd.to_datetime(
        df["published_at"],
        errors="coerce",
        utc=True
    )

    # --------------------------------------------------------
    # STEP 7: Add analytical columns
    # --------------------------------------------------------

    df["publish_date"] = (
        df["published_at"]
        .dt.date
    )

    df["publish_day"] = (
        df["published_at"]
        .dt.day_name()
    )

    df["publish_hour"] = (
        df["published_at"]
        .dt.hour
    )

    # Engagement rate based on available public metrics
    #
    # Formula:
    # (Likes + Comments) / Views * 100

    df["engagement_rate"] = (
        (
            df["likes"] +
            df["comments"]
        )
        / df["views"].replace(0, pd.NA)
        * 100
    )

    # --------------------------------------------------------
    # STEP 8: Sort
    # --------------------------------------------------------

    df = df.sort_values(
        by="views",
        ascending=False
    )

    # --------------------------------------------------------
    # STEP 9: Save CSV
    # --------------------------------------------------------

    os.makedirs(
        "data/raw",
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------------
    # STEP 10: Display summary
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("DATA COLLECTION COMPLETED")
    print("=" * 60)

    print(f"Total videos: {len(df)}")

    print(
        f"Saved to: {OUTPUT_FILE}"
    )

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nTop 5 videos by views:")

    print(
        df[
            [
                "title",
                "channel",
                "views",
                "likes",
                "comments",
                "engagement_rate"
            ]
        ].head(5).to_string(index=False)
    )


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":
    main()