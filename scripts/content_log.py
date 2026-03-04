"""
Content Log — Tracks all generated and uploaded content.
Appends to output/content_log.csv after each pipeline run.
"""

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

LOG_FILE = config.OUTPUT / "content_log.csv"
HEADERS = [
    "script_id", "title", "niche", "channel", "word_count",
    "trending_source", "generated_at", "audio_path", "assembled_path",
    "assembled_size_mb", "duration_sec", "youtube_id", "youtube_url",
    "upload_privacy", "uploaded_at", "status"
]


def _ensure_log():
    """Create log file with headers if it doesn't exist."""
    if not LOG_FILE.exists():
        with open(LOG_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS)
            writer.writeheader()


def log_script(script: dict):
    """Log a newly generated script."""
    _ensure_log()
    row = {
        "script_id": script.get("id", ""),
        "title": script.get("title", ""),
        "niche": script.get("niche", ""),
        "channel": script.get("channel", ""),
        "word_count": script.get("word_count", ""),
        "trending_source": script.get("trending_source", ""),
        "generated_at": script.get("generated_at", ""),
        "status": "script_generated",
    }
    _append_or_update(row)


def log_assembled(script: dict):
    """Update log after assembly."""
    row = {
        "script_id": script.get("id", ""),
        "assembled_path": script.get("assembled_path", ""),
        "assembled_size_mb": script.get("assembled_size_mb", ""),
        "duration_sec": script.get("assembled_duration", ""),
        "audio_path": script.get("audio_path", ""),
        "status": "assembled",
    }
    _append_or_update(row)


def log_uploaded(script: dict):
    """Update log after upload."""
    row = {
        "script_id": script.get("id", ""),
        "youtube_id": script.get("youtube_id", ""),
        "youtube_url": script.get("youtube_url", ""),
        "upload_privacy": script.get("upload_privacy", ""),
        "uploaded_at": script.get("uploaded_at", ""),
        "status": "uploaded",
    }
    _append_or_update(row)


def _append_or_update(row: dict):
    """Append a new row or update an existing row by script_id."""
    _ensure_log()
    rows = []
    found = False

    with open(LOG_FILE, "r", newline="") as f:
        reader = csv.DictReader(f)
        for existing in reader:
            if existing["script_id"] == row["script_id"]:
                # Merge: keep existing values, overwrite with new non-empty values
                for key, val in row.items():
                    if val:
                        existing[key] = val
                rows.append(existing)
                found = True
            else:
                rows.append(existing)

    if not found:
        full_row = {h: "" for h in HEADERS}
        full_row.update(row)
        rows.append(full_row)

    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def print_log():
    """Pretty-print the content log."""
    _ensure_log()
    with open(LOG_FILE, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("\n📭 No content logged yet.\n")
        return

    print(f"\n📊 Content Log — {len(rows)} entries\n")
    print(f"{'ID':<25} {'Title':<45} {'Status':<15} {'YouTube'}")
    print("─" * 100)
    for r in rows:
        title = r.get("title", "")[:42]
        status = r.get("status", "?")
        yt = r.get("youtube_url", "")
        print(f"{r['script_id']:<25} {title:<45} {status:<15} {yt}")
    print()


def main():
    print_log()


if __name__ == "__main__":
    main()
