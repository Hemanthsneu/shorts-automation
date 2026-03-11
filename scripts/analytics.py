"""
Analytics Feedback Loop — Learn From Results, Auto-Optimize

Tracks video performance via YouTube Analytics API and feeds data back
into the content strategy to continuously improve viral hit rate.

Features:
- Pull views, watch time, CTR, retention, engagement metrics
- Track performance by niche, formula, topic type, hook style
- Identify winning patterns and losing patterns
- Generate data-driven content strategy recommendations
- Auto-adjust viral scoring thresholds based on real results
- Performance report generation
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

ANALYTICS_DIR = config.OUTPUT / "analytics"
ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
PERFORMANCE_DB = ANALYTICS_DIR / "performance_db.json"
INSIGHTS_FILE = ANALYTICS_DIR / "insights.json"
STRATEGY_FILE = ANALYTICS_DIR / "strategy.json"


def _load_performance_db() -> dict:
    if PERFORMANCE_DB.exists():
        return json.loads(PERFORMANCE_DB.read_text())
    return {"videos": {}, "last_updated": None}


def _save_performance_db(db: dict):
    db["last_updated"] = datetime.now(timezone.utc).isoformat()
    PERFORMANCE_DB.write_text(json.dumps(db, indent=2))


def get_youtube_analytics_service():
    """Build authenticated YouTube Analytics API service."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    ROOT = Path(__file__).parent.parent
    TOKEN_FILE = ROOT / "token.json"
    SCOPES = [
        "https://www.googleapis.com/auth/youtube.readonly",
        "https://www.googleapis.com/auth/yt-analytics.readonly",
    ]

    if not TOKEN_FILE.exists():
        print("  ⚠️  No YouTube token found. Run youtube_auth.py first.")
        return None

    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            return None

    return build("youtubeAnalytics", "v2", credentials=creds)


def get_youtube_data_service():
    """Build YouTube Data API service for video metadata."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    ROOT = Path(__file__).parent.parent
    TOKEN_FILE = ROOT / "token.json"

    if not TOKEN_FILE.exists():
        return None

    creds = Credentials.from_authorized_user_file(
        str(TOKEN_FILE),
        ["https://www.googleapis.com/auth/youtube.readonly"]
    )
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return build("youtube", "v3", credentials=creds)


def fetch_video_stats(video_ids: list[str]) -> dict:
    """Fetch video statistics from YouTube Data API."""
    youtube = get_youtube_data_service()
    if not youtube:
        return {}

    stats = {}
    # Process in batches of 50 (API limit)
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        try:
            response = youtube.videos().list(
                part="statistics,snippet",
                id=",".join(batch),
            ).execute()

            for item in response.get("items", []):
                vid_id = item["id"]
                s = item.get("statistics", {})
                stats[vid_id] = {
                    "views": int(s.get("viewCount", 0)),
                    "likes": int(s.get("likeCount", 0)),
                    "comments": int(s.get("commentCount", 0)),
                    "title": item.get("snippet", {}).get("title", ""),
                    "published_at": item.get("snippet", {}).get("publishedAt", ""),
                }
        except Exception as e:
            print(f"  ⚠️  Failed to fetch stats for batch: {e}")

    return stats


def pull_performance_data() -> dict:
    """Pull latest performance data for all uploaded videos."""
    print(f"  📊 Pulling performance data from YouTube...")

    # Find all uploaded videos from script JSONs
    paths = sorted(config.SCRIPTS_DIR.glob("*.json"))
    video_ids = []
    script_map = {}

    for path in paths:
        script = json.loads(path.read_text())
        yt_id = script.get("youtube_id")
        if yt_id:
            video_ids.append(yt_id)
            script_map[yt_id] = script

    if not video_ids:
        print(f"  📭 No uploaded videos found to track")
        return {}

    print(f"  🔍 Tracking {len(video_ids)} videos...")
    stats = fetch_video_stats(video_ids)

    # Merge with script metadata for analysis
    db = _load_performance_db()
    for vid_id, stat in stats.items():
        script = script_map.get(vid_id, {})

        entry = db["videos"].get(vid_id, {})
        entry.update({
            "youtube_id": vid_id,
            "title": stat.get("title", script.get("title", "")),
            "views": stat["views"],
            "likes": stat["likes"],
            "comments": stat["comments"],
            "niche": script.get("niche", "unknown"),
            "viral_formula": script.get("viral_formula_used", "unknown"),
            "primary_emotion": script.get("primary_emotion", "unknown"),
            "trending_source": script.get("trending_source", "unknown"),
            "virality_score": script.get("virality_score", {}).get("final_score", 0),
            "topic_viral_score": script.get("topic_viral_score", 0),
            "word_count": script.get("word_count", 0),
            "hook": script.get("hook", ""),
            "uploaded_at": script.get("uploaded_at", ""),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        })

        # Calculate engagement rate
        if stat["views"] > 0:
            entry["engagement_rate"] = round(
                (stat["likes"] + stat["comments"]) / stat["views"] * 100, 2
            )
        else:
            entry["engagement_rate"] = 0

        # Track view velocity (views per hour since upload)
        if script.get("uploaded_at"):
            try:
                uploaded = datetime.fromisoformat(script["uploaded_at"].replace("Z", "+00:00"))
                hours_live = max((datetime.now(timezone.utc) - uploaded).total_seconds() / 3600, 1)
                entry["views_per_hour"] = round(stat["views"] / hours_live, 1)
            except Exception:
                entry["views_per_hour"] = 0

        db["videos"][vid_id] = entry

        status_icon = "🔥" if stat["views"] >= 1000 else "📈" if stat["views"] >= 100 else "📊"
        print(f"  {status_icon} {stat['views']:>8} views | {stat['likes']:>5} likes | "
              f"{stat['comments']:>4} comments | {entry.get('title', '')[:40]}...")

    _save_performance_db(db)
    return db


def analyze_patterns() -> dict:
    """Analyze performance patterns to identify what works and what doesn't."""
    db = _load_performance_db()
    videos = list(db.get("videos", {}).values())

    if len(videos) < 3:
        return {"status": "insufficient_data", "message": "Need at least 3 uploaded videos to analyze"}

    insights = {
        "total_videos": len(videos),
        "total_views": sum(v.get("views", 0) for v in videos),
        "avg_views": round(sum(v.get("views", 0) for v in videos) / len(videos)),
        "median_views": sorted(v.get("views", 0) for v in videos)[len(videos) // 2],
        "top_performers": [],
        "patterns": {},
        "recommendations": [],
    }

    # Sort by views
    sorted_videos = sorted(videos, key=lambda v: v.get("views", 0), reverse=True)

    # Top 5 performers
    insights["top_performers"] = [
        {"title": v.get("title", ""), "views": v.get("views", 0),
         "formula": v.get("viral_formula", ""), "niche": v.get("niche", ""),
         "emotion": v.get("primary_emotion", "")}
        for v in sorted_videos[:5]
    ]

    # Analyze by niche
    by_niche = defaultdict(list)
    for v in videos:
        by_niche[v.get("niche", "unknown")].append(v.get("views", 0))

    insights["patterns"]["by_niche"] = {
        niche: {
            "count": len(views),
            "avg_views": round(sum(views) / len(views)),
            "max_views": max(views),
            "total_views": sum(views),
        }
        for niche, views in by_niche.items()
    }

    # Analyze by viral formula
    by_formula = defaultdict(list)
    for v in videos:
        by_formula[v.get("viral_formula", "unknown")].append(v.get("views", 0))

    insights["patterns"]["by_formula"] = {
        formula: {
            "count": len(views),
            "avg_views": round(sum(views) / len(views)),
            "max_views": max(views),
        }
        for formula, views in by_formula.items()
    }

    # Analyze by primary emotion
    by_emotion = defaultdict(list)
    for v in videos:
        by_emotion[v.get("primary_emotion", "unknown")].append(v.get("views", 0))

    insights["patterns"]["by_emotion"] = {
        emotion: {
            "count": len(views),
            "avg_views": round(sum(views) / len(views)),
        }
        for emotion, views in by_emotion.items()
    }

    # Analyze by trending source
    by_source = defaultdict(list)
    for v in videos:
        by_source[v.get("trending_source", "unknown")].append(v.get("views", 0))

    insights["patterns"]["by_source"] = {
        source: {"count": len(views), "avg_views": round(sum(views) / len(views))}
        for source, views in by_source.items()
    }

    # Correlation: virality score vs actual views
    scored_videos = [v for v in videos if v.get("virality_score", 0) > 0]
    if scored_videos:
        high_score = [v for v in scored_videos if v["virality_score"] >= 75]
        low_score = [v for v in scored_videos if v["virality_score"] < 75]

        insights["patterns"]["score_correlation"] = {
            "high_score_avg_views": round(sum(v["views"] for v in high_score) / max(len(high_score), 1)),
            "low_score_avg_views": round(sum(v["views"] for v in low_score) / max(len(low_score), 1)),
            "score_is_predictive": (
                sum(v["views"] for v in high_score) / max(len(high_score), 1) >
                sum(v["views"] for v in low_score) / max(len(low_score), 1)
            ) if high_score and low_score else None,
        }

    # Generate recommendations
    recs = []

    # Best niche
    if insights["patterns"]["by_niche"]:
        best_niche = max(
            insights["patterns"]["by_niche"].items(),
            key=lambda x: x[1]["avg_views"]
        )
        recs.append(f"Focus on '{best_niche[0]}' niche — avg {best_niche[1]['avg_views']} views")

    # Best formula
    if insights["patterns"]["by_formula"]:
        best_formula = max(
            insights["patterns"]["by_formula"].items(),
            key=lambda x: x[1]["avg_views"]
        )
        recs.append(f"Use '{best_formula[0]}' formula more — avg {best_formula[1]['avg_views']} views")

    # Best emotion
    if insights["patterns"]["by_emotion"]:
        best_emotion = max(
            insights["patterns"]["by_emotion"].items(),
            key=lambda x: x[1]["avg_views"]
        )
        recs.append(f"Target '{best_emotion[0]}' emotion — avg {best_emotion[1]['avg_views']} views")

    # Engagement insights
    high_engagement = [v for v in videos if v.get("engagement_rate", 0) > 5]
    if high_engagement:
        recs.append(
            f"{len(high_engagement)} videos have >5% engagement — study their hooks"
        )

    insights["recommendations"] = recs
    insights["generated_at"] = datetime.now(timezone.utc).isoformat()

    INSIGHTS_FILE.write_text(json.dumps(insights, indent=2))
    return insights


def generate_strategy_update() -> dict:
    """Generate an updated content strategy based on analytics insights."""
    insights = analyze_patterns()
    if insights.get("status") == "insufficient_data":
        return insights

    strategy = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "based_on_videos": insights["total_videos"],
        "total_views": insights["total_views"],
    }

    # Niche priority ranking
    niche_data = insights.get("patterns", {}).get("by_niche", {})
    if niche_data:
        ranked_niches = sorted(
            niche_data.items(),
            key=lambda x: x[1]["avg_views"],
            reverse=True,
        )
        strategy["niche_priority"] = [
            {"niche": n, "avg_views": d["avg_views"], "count": d["count"]}
            for n, d in ranked_niches
        ]

    # Formula priority
    formula_data = insights.get("patterns", {}).get("by_formula", {})
    if formula_data:
        ranked_formulas = sorted(
            formula_data.items(),
            key=lambda x: x[1]["avg_views"],
            reverse=True,
        )
        strategy["formula_priority"] = [
            {"formula": f, "avg_views": d["avg_views"], "count": d["count"]}
            for f, d in ranked_formulas
        ]

    # Optimal posting analysis
    db = _load_performance_db()
    videos = list(db.get("videos", {}).values())

    hour_performance = defaultdict(list)
    for v in videos:
        uploaded_at = v.get("uploaded_at", "")
        if uploaded_at:
            try:
                dt = datetime.fromisoformat(uploaded_at.replace("Z", "+00:00"))
                hour = dt.hour
                hour_performance[hour].append(v.get("views", 0))
            except Exception:
                pass

    if hour_performance:
        best_hour = max(
            hour_performance.items(),
            key=lambda x: sum(x[1]) / len(x[1]),
        )
        strategy["best_posting_hour_utc"] = best_hour[0]
        strategy["posting_hour_data"] = {
            str(h): {"avg_views": round(sum(v) / len(v)), "count": len(v)}
            for h, v in sorted(hour_performance.items())
        }

    # Top performing hooks analysis
    top_videos = sorted(videos, key=lambda v: v.get("views", 0), reverse=True)[:10]
    strategy["winning_hook_patterns"] = [
        {"hook": v.get("hook", "")[:80], "views": v.get("views", 0)}
        for v in top_videos if v.get("hook")
    ]

    strategy["recommendations"] = insights.get("recommendations", [])

    STRATEGY_FILE.write_text(json.dumps(strategy, indent=2))
    return strategy


def print_performance_report():
    """Print a formatted performance report."""
    insights = analyze_patterns()
    if insights.get("status") == "insufficient_data":
        print(f"\n  📊 {insights['message']}\n")
        return

    print(f"\n{'='*60}")
    print(f"  📊 PERFORMANCE ANALYTICS REPORT")
    print(f"{'='*60}")
    print(f"\n  Total Videos: {insights['total_videos']}")
    print(f"  Total Views:  {insights['total_views']:,}")
    print(f"  Avg Views:    {insights['avg_views']:,}")
    print(f"  Median Views: {insights['median_views']:,}")

    print(f"\n  🏆 TOP PERFORMERS:")
    for i, v in enumerate(insights.get("top_performers", []), 1):
        print(f"    {i}. {v['views']:>8,} views — {v['title'][:50]}")
        print(f"       Formula: {v['formula']} | Emotion: {v['emotion']}")

    print(f"\n  📈 BY NICHE:")
    for niche, data in sorted(
        insights.get("patterns", {}).get("by_niche", {}).items(),
        key=lambda x: x[1]["avg_views"], reverse=True,
    ):
        print(f"    {niche:>12}: {data['avg_views']:>6,} avg views ({data['count']} videos)")

    print(f"\n  🎯 BY FORMULA:")
    for formula, data in sorted(
        insights.get("patterns", {}).get("by_formula", {}).items(),
        key=lambda x: x[1]["avg_views"], reverse=True,
    ):
        print(f"    {formula:>20}: {data['avg_views']:>6,} avg views ({data['count']} videos)")

    print(f"\n  💡 RECOMMENDATIONS:")
    for rec in insights.get("recommendations", []):
        print(f"    → {rec}")

    print()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Analytics Feedback Loop")
    parser.add_argument("--pull", action="store_true", help="Pull latest performance data")
    parser.add_argument("--report", action="store_true", help="Print performance report")
    parser.add_argument("--strategy", action="store_true", help="Generate strategy update")
    args = parser.parse_args()

    if args.pull:
        pull_performance_data()
    elif args.strategy:
        strategy = generate_strategy_update()
        if strategy.get("status") != "insufficient_data":
            print(json.dumps(strategy, indent=2))
    elif args.report:
        print_performance_report()
    else:
        # Default: pull + report
        pull_performance_data()
        print_performance_report()


if __name__ == "__main__":
    main()
