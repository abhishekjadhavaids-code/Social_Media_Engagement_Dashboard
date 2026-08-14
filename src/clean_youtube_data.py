import os
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "data/raw/youtube_videos.csv"
OUTPUT_FILE = "data/processed/youtube_engagement_cleaned.csv"


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 60)
print("YOUTUBE DATA CLEANING & PREPROCESSING")
print("=" * 60)

df = pd.read_csv(INPUT_FILE)

print(f"\nOriginal rows: {len(df)}")
print(f"Original columns: {len(df.columns)}")


# ============================================================
# 1. REMOVE DUPLICATE VIDEOS
# ============================================================

duplicates = df["video_id"].duplicated().sum()

print(f"\nDuplicate videos found: {duplicates}")

df = df.drop_duplicates(
    subset="video_id",
    keep="first"
)

print(f"Rows after duplicate removal: {len(df)}")


# ============================================================
# 2. CLEAN TEXT COLUMNS
# ============================================================

text_columns = [
    "title",
    "channel",
    "description",
    "search_query"
]

for column in text_columns:

    if column in df.columns:

        df[column] = (
            df[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )


# ============================================================
# 3. CONVERT NUMERIC COLUMNS
# ============================================================

numeric_columns = [
    "views",
    "likes",
    "comments",
    "duration_seconds",
    "publish_hour",
    "engagement_rate"
]

for column in numeric_columns:

    if column in df.columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )


# ============================================================
# 4. HANDLE MISSING NUMERIC VALUES
# ============================================================

for column in numeric_columns:

    if column in df.columns:

        missing = df[column].isna().sum()

        if missing > 0:

            print(
                f"Missing values in {column}: {missing}"
            )

            df[column] = df[column].fillna(0)


# ============================================================
# 5. REMOVE IMPOSSIBLE NEGATIVE VALUES
# ============================================================

non_negative_columns = [
    "views",
    "likes",
    "comments",
    "duration_seconds"
]

for column in non_negative_columns:

    if column in df.columns:

        negative_count = (
            df[column] < 0
        ).sum()

        if negative_count > 0:

            print(
                f"Negative values removed from "
                f"{column}: {negative_count}"
            )

            df.loc[
                df[column] < 0,
                column
            ] = 0


# ============================================================
# 6. CONVERT PUBLISHED DATE
# ============================================================

df["published_at"] = pd.to_datetime(
    df["published_at"],
    errors="coerce",
    utc=True
)


# ============================================================
# 7. REMOVE ROWS WITH INVALID DATES
# ============================================================

invalid_dates = df["published_at"].isna().sum()

print(
    f"\nInvalid publication dates: {invalid_dates}"
)

df = df.dropna(
    subset=["published_at"]
)


# ============================================================
# 8. CREATE DATE FEATURES
# ============================================================

df["publish_date"] = (
    df["published_at"].dt.date
)

df["publish_day"] = (
    df["published_at"].dt.day_name()
)

df["publish_day_number"] = (
    df["published_at"].dt.dayofweek
)

df["publish_hour"] = (
    df["published_at"].dt.hour
)

df["publish_month"] = (
    df["published_at"].dt.month
)

df["publish_month_name"] = (
    df["published_at"].dt.month_name()
)

df["publish_year"] = (
    df["published_at"].dt.year
)


# ============================================================
# 9. CONTENT LENGTH
# ============================================================

df["title_length"] = (
    df["title"]
    .str.len()
)

df["description_length"] = (
    df["description"]
    .str.len()
)


# ============================================================
# 10. ENGAGEMENT METRICS
# ============================================================

# Like rate
df["like_rate"] = np.where(
    df["views"] > 0,
    (df["likes"] / df["views"]) * 100,
    0
)

# Comment rate
df["comment_rate"] = np.where(
    df["views"] > 0,
    (df["comments"] / df["views"]) * 100,
    0
)

# Overall engagement rate
df["engagement_rate"] = np.where(
    df["views"] > 0,
    (
        (df["likes"] + df["comments"])
        / df["views"]
    ) * 100,
    0
)


# ============================================================
# 11. VIDEO LENGTH CATEGORY
# ============================================================

def classify_video_length(seconds):

    if seconds < 60:
        return "Short"

    elif seconds < 300:
        return "Medium"

    elif seconds < 900:
        return "Long"

    else:
        return "Very Long"


df["video_length_category"] = (
    df["duration_seconds"]
    .apply(classify_video_length)
)


# ============================================================
# 12. PERFORMANCE CATEGORY
# ============================================================

view_75 = df["views"].quantile(0.75)
view_50 = df["views"].quantile(0.50)
view_25 = df["views"].quantile(0.25)


def classify_performance(views):

    if views >= view_75:
        return "High"

    elif views >= view_50:
        return "Medium"

    elif views >= view_25:
        return "Low"

    else:
        return "Very Low"


df["performance_category"] = (
    df["views"]
    .apply(classify_performance)
)


# ============================================================
# 13. SORT DATA
# ============================================================

df = df.sort_values(
    by="engagement_rate",
    ascending=False
)


# ============================================================
# 14. FINAL COLUMN ORDER
# ============================================================

preferred_columns = [
    "video_id",
    "title",
    "channel",
    "search_query",
    "published_at",
    "publish_date",
    "publish_day",
    "publish_day_number",
    "publish_hour",
    "publish_month",
    "publish_month_name",
    "publish_year",
    "duration",
    "duration_seconds",
    "video_length_category",
    "views",
    "likes",
    "comments",
    "like_rate",
    "comment_rate",
    "engagement_rate",
    "performance_category",
    "title_length",
    "description_length",
    "category_id",
    "channel_id",
    "description"
]

existing_columns = [
    column
    for column in preferred_columns
    if column in df.columns
]

df = df[existing_columns]


# ============================================================
# 15. SAVE CLEAN DATA
# ============================================================

os.makedirs(
    "data/processed",
    exist_ok=True
)

df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# FINAL REPORT
# ============================================================

print("\n" + "=" * 60)
print("DATA CLEANING COMPLETED")
print("=" * 60)

print(f"\nFinal rows: {len(df)}")
print(f"Final columns: {len(df.columns)}")

print(
    f"\nClean dataset saved to:"
    f"\n{OUTPUT_FILE}"
)

print("\nMissing values:")
print(
    df.isna()
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

print("\nPerformance distribution:")
print(
    df["performance_category"]
    .value_counts()
)

print("\nVideo length distribution:")
print(
    df["video_length_category"]
    .value_counts()
)

print("\nTop 5 videos by engagement rate:")

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
    ]
    .head(5)
    .to_string(index=False)
)

print("\n" + "=" * 60)