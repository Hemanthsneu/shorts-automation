"""
Topic History — Deduplication system to prevent repeating topics across pipeline runs.

Maintains a JSON file of all previously used topics/titles.
Before script generation, loads history and passes it to Gemini 
as a blocklist to avoid repeats.
"""

import json
from datetime import datetime
from pathlib import Path

HISTORY_FILE = Path(__file__).parent.parent / "output" / "topic_history.json"


def load_history() -> list[dict]:
    """Load topic history from disk."""
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text())
        except (json.JSONDecodeError, Exception):
            return []
    return []


def save_history(history: list[dict]):
    """Save topic history to disk."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(history, indent=2))


def add_topic(title: str, niche: str, headline: str = "", score: int = 0):
    """Add a new topic to history after successful script generation."""
    history = load_history()
    history.append({
        "title": title,
        "niche": niche,
        "headline": headline,
        "score": score,
        "used_at": datetime.now().isoformat(),
    })
    # Keep last 200 entries to avoid unbounded growth
    if len(history) > 200:
        history = history[-200:]
    save_history(history)


def get_used_titles(limit: int = 50) -> list[str]:
    """Get list of previously used titles (most recent first)."""
    history = load_history()
    return [h["title"] for h in history[-limit:]]


def get_used_headlines(limit: int = 50) -> list[str]:
    """Get list of previously used source headlines."""
    history = load_history()
    return [h.get("headline", "") for h in history[-limit:] if h.get("headline")]


def migrate_from_content_log():
    """One-time migration: import existing titles from content_log.json."""
    content_log = Path(__file__).parent.parent / "output" / "content_log.json"
    if not content_log.exists():
        return

    history = load_history()
    existing_titles = {h["title"] for h in history}

    try:
        entries = json.loads(content_log.read_text())
        for entry in entries:
            title = entry.get("title", "")
            if title and title not in existing_titles:
                history.append({
                    "title": title,
                    "niche": entry.get("niche", "unknown"),
                    "headline": "",
                    "score": 0,
                    "used_at": entry.get("generated_at", datetime.now().isoformat()),
                })
                existing_titles.add(title)
        save_history(history)
        print(f"  📋 Migrated {len(entries)} topics from content_log.json")
    except Exception as e:
        print(f"  ⚠️  Migration failed: {e}")
