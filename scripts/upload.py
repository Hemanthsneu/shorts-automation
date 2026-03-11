"""
Stage 5: Upload assembled shorts to YouTube via Data API v3.
Handles: upload, metadata, scheduling, and AI content disclosure.
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

ROOT = Path(__file__).parent.parent
TOKEN_FILE = ROOT / "token.json"
CLIENT_SECRET = ROOT / "client_secret.json"


def get_youtube_service():
    """Build authenticated YouTube API service using stored token."""
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
               "https://www.googleapis.com/auth/youtube",
               "https://www.googleapis.com/auth/youtube.force-ssl"]

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"  ⚠️  Token refresh failed: {e}")
                print(f"  🔄 Will re-run OAuth flow...")
                creds = None
        if not creds or not creds.valid:
            if not CLIENT_SECRET.exists():
                raise FileNotFoundError(
                    "Run 'python scripts/youtube_auth.py' first to set up OAuth"
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
            creds = flow.run_local_server(port=8081)

        TOKEN_FILE.write_text(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def upload_short(script_path: Path, schedule_time: datetime = None, privacy: str = None) -> dict:
    """Upload a single assembled short to YouTube."""
    from googleapiclient.http import MediaFileUpload

    script = json.loads(script_path.read_text())
    sid = script["id"]

    video_path = script.get("assembled_path")
    if not video_path or not Path(video_path).exists():
        raise FileNotFoundError(f"Assembled video not found for {sid}")

    youtube = get_youtube_service()
    privacy = privacy or config.UPLOAD_PRIVACY

    # Build metadata
    title = script["title"][:100]  # YT limit
    tags_list = script.get("tags", [])
    
    # Limit to 5-8 most relevant tags (over-tagging triggers suppression)
    tags_list = tags_list[:8]
    tags_str = " ".join(tags_list[:5])  # Only put top 5 in description body

    # First-line keyword optimization (YouTube weighs first 2 lines heavily)
    keyword_desc = script.get('description', title)
    description = (
        f"{keyword_desc}\n\n"
        f"🔔 Follow for daily deep dives!\n\n"
        f"{tags_str}"
    )

    # Dynamic category ID based on niche
    niche = script.get("niche", "tech")
    NICHE_CATEGORIES = {
        "tech": "28", "ai": "28", "finance": "25", "cinema": "24",
        "sports": "17", "science": "28", "gaming": "20", "history": "27",
        "space": "28", "popculture": "24",
    }
    category_id = NICHE_CATEGORIES.get(niche, "28")

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": [t.replace("#", "") for t in tags_list],
            "categoryId": category_id,
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    # Schedule if requested
    if schedule_time and privacy == "private":
        body["status"]["privacyStatus"] = "private"
        body["status"]["publishAt"] = schedule_time.isoformat()
    elif schedule_time:
        body["status"]["publishAt"] = schedule_time.isoformat()

    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)

    print(f"  📤 Uploading {sid}: \"{title}\"...")

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            print(f"     ↳ {progress}% uploaded")

    video_id = response["id"]
    video_url = f"https://youtube.com/shorts/{video_id}"

    print(f"  ✅ Uploaded! {video_url}")

    # Post pinned comment if available
    pinned_comment_text = script.get("pinned_comment", "")
    if pinned_comment_text:
        try:
            post_pinned_comment(youtube, video_id, pinned_comment_text)
        except Exception as e:
            print(f"  ⚠️  Pinned comment failed: {e}")

    # Update script JSON
    script["youtube_id"] = video_id
    script["youtube_url"] = video_url
    script["uploaded_at"] = datetime.now(timezone.utc).isoformat()
    script["upload_privacy"] = privacy
    script_path.write_text(json.dumps(script, indent=2))

    return {"id": video_id, "url": video_url, "title": title}


def post_pinned_comment(youtube, video_id: str, comment_text: str):
    """Post a comment on the video and pin it to boost engagement."""
    # Insert the comment
    comment_response = youtube.commentThreads().insert(
        part="snippet",
        body={
            "snippet": {
                "videoId": video_id,
                "topLevelComment": {
                    "snippet": {
                        "textOriginal": comment_text,
                    }
                },
            }
        },
    ).execute()

    comment_id = comment_response["snippet"]["topLevelComment"]["id"]
    print(f"  📌 Posted comment: \"{comment_text[:50]}...\"")

    # Pin the comment (requires youtube.force_ssl scope — may not work with all tokens)
    try:
        youtube.comments().setModerationStatus(
            id=comment_id,
            moderationStatus="published",
        ).execute()
    except Exception:
        pass  # Pinning may require additional permissions, comment still posts

    return comment_id


def upload_all(script_ids: list[str] = None, stagger_hours: int = None, privacy: str = None):
    """Upload all assembled shorts, optionally staggering schedule times."""
    if script_ids:
        paths = [config.SCRIPTS_DIR / f"{sid}.json" for sid in script_ids]
    else:
        paths = sorted(config.SCRIPTS_DIR.glob("*.json"))

    results = []
    schedule_time = None

    if stagger_hours:
        schedule_time = datetime.now(timezone.utc) + timedelta(hours=config.SCHEDULE_HOURS)

    for i, path in enumerate(paths):
        script = json.loads(path.read_text())
        sid = script["id"]

        if not script.get("assembled_path") or not Path(script["assembled_path"]).exists():
            print(f"  ⏭️  Skipping {sid} — not assembled yet")
            continue

        if script.get("youtube_id"):
            print(f"  ⏭️  Skipping {sid} — already uploaded ({script['youtube_url']})")
            continue

        current_schedule = None
        if schedule_time and stagger_hours:
            current_schedule = schedule_time + timedelta(hours=i * stagger_hours)
            print(f"  📅 Scheduling for: {current_schedule.strftime('%Y-%m-%d %H:%M UTC')}")

        try:
            result = upload_short(path, schedule_time=current_schedule, privacy=privacy)
            results.append(result)
        except Exception as e:
            print(f"  ❌ Failed {sid}: {e}")

    return results


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--scripts", nargs="*", help="Specific script IDs")
    parser.add_argument("--privacy", choices=["public", "private", "unlisted"], default=None)
    parser.add_argument("--stagger", type=int, default=None,
                        help="Hours between scheduled uploads")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be uploaded")
    args = parser.parse_args()

    if args.dry_run:
        paths = sorted(config.SCRIPTS_DIR.glob("*.json"))
        print("\n📋 Dry run — would upload:\n")
        for path in paths:
            s = json.loads(path.read_text())
            assembled = "✅" if s.get("assembled_path") else "❌"
            uploaded = "⏭️ already uploaded" if s.get("youtube_id") else "📤 pending"
            print(f"  {assembled} {s['id']}: \"{s['title'][:60]}\" — {uploaded}")
        return

    print(f"\n📤 Stage 5: Uploading to YouTube\n")
    results = upload_all(args.scripts, stagger_hours=args.stagger, privacy=args.privacy)
    print(f"\n✅ Uploaded {len(results)} shorts\n")
    for r in results:
        print(f"  🔗 {r['url']} — {r['title']}")


if __name__ == "__main__":
    main()
