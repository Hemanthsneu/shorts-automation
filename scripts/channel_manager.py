"""
Channel Manager — Multi-Channel Orchestration & Content Calendar

Manages multiple YouTube channels with:
- Per-channel content strategy and branding
- Optimal posting schedule based on analytics
- Content calendar with niche rotation
- Channel health monitoring
- Cross-channel performance comparison
- Posting frequency optimization
"""

import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

CALENDAR_DIR = config.OUTPUT / "calendar"
CALENDAR_DIR.mkdir(parents=True, exist_ok=True)
CHANNELS_FILE = CALENDAR_DIR / "channels.json"
SCHEDULE_FILE = CALENDAR_DIR / "schedule.json"

# Optimal posting windows by niche (UTC hours)
# Based on YouTube Shorts audience analysis
OPTIMAL_POSTING_WINDOWS = {
    "tech": {
        "peak_hours_utc": [14, 15, 16, 21, 22],  # 9-11 AM EST, 4-5 PM EST
        "best_days": ["Tuesday", "Wednesday", "Thursday"],
        "posts_per_day": 2,
        "spacing_hours": 6,
    },
    "ai": {
        "peak_hours_utc": [14, 15, 16, 17],
        "best_days": ["Monday", "Tuesday", "Wednesday", "Thursday"],
        "posts_per_day": 2,
        "spacing_hours": 6,
    },
    "finance": {
        "peak_hours_utc": [12, 13, 14, 21, 22],  # Market hours + evening
        "best_days": ["Monday", "Tuesday", "Wednesday"],
        "posts_per_day": 2,
        "spacing_hours": 8,
    },
    "cinema": {
        "peak_hours_utc": [17, 18, 19, 23, 0],  # Afternoon + evening
        "best_days": ["Thursday", "Friday", "Saturday"],
        "posts_per_day": 3,
        "spacing_hours": 5,
    },
    "sports": {
        "peak_hours_utc": [16, 17, 18, 22, 23],
        "best_days": ["Monday", "Friday", "Saturday", "Sunday"],
        "posts_per_day": 2,
        "spacing_hours": 6,
    },
    "science": {
        "peak_hours_utc": [14, 15, 16, 20, 21],
        "best_days": ["Tuesday", "Wednesday", "Thursday"],
        "posts_per_day": 1,
        "spacing_hours": 24,
    },
    "gaming": {
        "peak_hours_utc": [17, 18, 19, 22, 23, 0, 1],
        "best_days": ["Friday", "Saturday", "Sunday"],
        "posts_per_day": 3,
        "spacing_hours": 4,
    },
    "history": {
        "peak_hours_utc": [14, 15, 20, 21],
        "best_days": ["Monday", "Wednesday", "Friday"],
        "posts_per_day": 1,
        "spacing_hours": 24,
    },
    "space": {
        "peak_hours_utc": [15, 16, 21, 22],
        "best_days": ["Tuesday", "Thursday", "Saturday"],
        "posts_per_day": 1,
        "spacing_hours": 24,
    },
    "popculture": {
        "peak_hours_utc": [15, 16, 17, 21, 22, 23],
        "best_days": ["Thursday", "Friday", "Saturday", "Sunday"],
        "posts_per_day": 3,
        "spacing_hours": 4,
    },
}

# Channel archetypes with branding strategies
CHANNEL_ARCHETYPES = {
    "authority": {
        "description": "Deep expertise in one niche, builds trust and subscriber loyalty",
        "best_niches": ["tech", "ai", "finance", "science"],
        "tone": "Expert insider sharing exclusive knowledge",
        "posting_strategy": "quality > quantity, 1-2 per day",
        "growth_pattern": "Slow start, compounds exponentially once authority established",
    },
    "curator": {
        "description": "Finds and presents the most interesting content across a broad niche",
        "best_niches": ["cinema", "gaming", "popculture", "sports"],
        "tone": "Excited friend sharing cool discoveries",
        "posting_strategy": "Volume matters, 2-3 per day",
        "growth_pattern": "Faster initial growth, wider but shallower audience",
    },
    "investigator": {
        "description": "Uncovers hidden truths, exposes secrets, conspiracy-adjacent",
        "best_niches": ["history", "tech", "finance", "popculture"],
        "tone": "Detective uncovering what 'they' don't want you to know",
        "posting_strategy": "1-2 per day, each video must feel like an investigation",
        "growth_pattern": "Viral spikes from exposé content, loyal dedicated audience",
    },
}


def _load_channels() -> dict:
    if CHANNELS_FILE.exists():
        return json.loads(CHANNELS_FILE.read_text())
    return {"channels": {}}


def _save_channels(data: dict):
    CHANNELS_FILE.write_text(json.dumps(data, indent=2))


def register_channel(
    channel_id: str,
    channel_name: str,
    niches: list[str],
    archetype: str = "authority",
) -> dict:
    """Register a new YouTube channel for management."""
    data = _load_channels()

    channel = {
        "id": channel_id,
        "name": channel_name,
        "niches": niches,
        "archetype": archetype,
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "total_uploads": 0,
        "total_views": 0,
        "active": True,
    }

    data["channels"][channel_id] = channel
    _save_channels(data)

    print(f"  ✅ Registered channel: {channel_name}")
    print(f"     Niches: {', '.join(niches)}")
    print(f"     Archetype: {archetype} — {CHANNEL_ARCHETYPES.get(archetype, {}).get('description', '')}")

    return channel


def get_next_posting_slot(niche: str, from_time: datetime = None) -> datetime:
    """Calculate the next optimal posting time for a niche."""
    now = from_time or datetime.now(timezone.utc)
    schedule = OPTIMAL_POSTING_WINDOWS.get(niche, OPTIMAL_POSTING_WINDOWS["tech"])

    peak_hours = schedule["peak_hours_utc"]
    best_days = schedule["best_days"]

    # Start from now and find the next peak hour on a best day
    candidate = now + timedelta(minutes=15)

    for _ in range(7 * 24):  # Search up to a week
        day_name = candidate.strftime("%A")
        hour = candidate.hour

        if day_name in best_days and hour in peak_hours:
            return candidate.replace(minute=0, second=0, microsecond=0)

        # Also allow non-best-days but at peak hours (less strict)
        if hour in peak_hours and _ > 24:
            return candidate.replace(minute=0, second=0, microsecond=0)

        candidate += timedelta(hours=1)

    # Fallback: 2 hours from now
    return now + timedelta(hours=2)


def generate_content_calendar(days: int = 7, niches: list[str] = None) -> list[dict]:
    """Generate a content calendar for the next N days."""
    if not niches:
        niches = list(config.NICHE_CONFIG.keys())

    calendar = []
    current_time = datetime.now(timezone.utc)

    for day_offset in range(days):
        day = current_time + timedelta(days=day_offset)
        day_name = day.strftime("%A")
        date_str = day.strftime("%Y-%m-%d")

        for niche in niches:
            schedule = OPTIMAL_POSTING_WINDOWS.get(niche, OPTIMAL_POSTING_WINDOWS["tech"])
            posts_today = schedule["posts_per_day"]
            peak_hours = schedule["peak_hours_utc"]
            best_days = schedule["best_days"]

            # Reduce posts on non-optimal days
            if day_name not in best_days:
                posts_today = max(1, posts_today - 1)

            # Pick posting hours
            selected_hours = random.sample(
                peak_hours,
                min(posts_today, len(peak_hours)),
            )
            selected_hours.sort()

            for hour in selected_hours:
                slot_time = day.replace(hour=hour, minute=random.randint(0, 15), second=0, microsecond=0)
                if slot_time <= current_time:
                    continue

                calendar.append({
                    "date": date_str,
                    "day": day_name,
                    "time_utc": slot_time.isoformat(),
                    "niche": niche,
                    "is_peak_day": day_name in best_days,
                    "status": "planned",
                })

    # Sort by time
    calendar.sort(key=lambda x: x["time_utc"])

    # Save calendar
    SCHEDULE_FILE.write_text(json.dumps({
        "generated_at": current_time.isoformat(),
        "days": days,
        "total_slots": len(calendar),
        "calendar": calendar,
    }, indent=2))

    return calendar


def get_daily_production_plan(target_date: datetime = None) -> dict:
    """Get what needs to be produced today across all channels."""
    if not target_date:
        target_date = datetime.now(timezone.utc)

    date_str = target_date.strftime("%Y-%m-%d")

    # Load or generate calendar
    if SCHEDULE_FILE.exists():
        schedule = json.loads(SCHEDULE_FILE.read_text())
        calendar = schedule.get("calendar", [])
    else:
        calendar = generate_content_calendar()

    # Filter today's slots
    today_slots = [s for s in calendar if s["date"] == date_str and s["status"] == "planned"]

    # Group by niche
    by_niche = defaultdict(list)
    for slot in today_slots:
        by_niche[slot["niche"]].append(slot)

    plan = {
        "date": date_str,
        "total_shorts_needed": len(today_slots),
        "by_niche": {
            niche: {
                "count": len(slots),
                "posting_times": [s["time_utc"] for s in slots],
            }
            for niche, slots in by_niche.items()
        },
    }

    return plan


def print_calendar(days: int = 7, niches: list[str] = None):
    """Print a formatted content calendar."""
    calendar = generate_content_calendar(days, niches)

    print(f"\n{'='*60}")
    print(f"  📅 CONTENT CALENDAR — Next {days} Days")
    print(f"{'='*60}")

    current_date = ""
    for slot in calendar:
        if slot["date"] != current_date:
            current_date = slot["date"]
            peak = "🔥" if slot["is_peak_day"] else "  "
            print(f"\n  {peak} {slot['day']}, {slot['date']}")

        time_str = datetime.fromisoformat(slot["time_utc"]).strftime("%H:%M UTC")
        niche = slot["niche"]
        print(f"      {time_str}  [{niche:>12}]")

    # Summary
    by_niche = defaultdict(int)
    for slot in calendar:
        by_niche[slot["niche"]] += 1

    print(f"\n  📊 SUMMARY:")
    print(f"     Total slots: {len(calendar)}")
    for niche, count in sorted(by_niche.items(), key=lambda x: x[1], reverse=True):
        print(f"     {niche:>12}: {count} videos")
    print()


def get_niche_rotation(channel_niches: list[str], recent_niches: list[str] = None) -> str:
    """Pick the next niche to produce for, avoiding recent repeats."""
    if not recent_niches:
        return random.choice(channel_niches)

    # Prefer niches not recently used
    available = [n for n in channel_niches if n not in recent_niches[-2:]]
    if available:
        return random.choice(available)
    return random.choice(channel_niches)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Channel Manager & Content Calendar")
    parser.add_argument("--calendar", type=int, default=0, help="Generate calendar for N days")
    parser.add_argument("--niches", nargs="*", help="Filter niches")
    parser.add_argument("--plan", action="store_true", help="Get today's production plan")
    parser.add_argument("--register", nargs=3, metavar=("ID", "NAME", "ARCHETYPE"),
                        help="Register a channel: ID NAME ARCHETYPE")
    args = parser.parse_args()

    if args.calendar:
        print_calendar(args.calendar, args.niches)
    elif args.plan:
        plan = get_daily_production_plan()
        print(f"\n📋 Today's Production Plan: {plan['date']}")
        print(f"   Shorts needed: {plan['total_shorts_needed']}")
        for niche, data in plan["by_niche"].items():
            print(f"   {niche}: {data['count']} videos")
    elif args.register:
        niches = args.niches or ["tech"]
        register_channel(args.register[0], args.register[1], niches, args.register[2])
    else:
        print_calendar(7)


if __name__ == "__main__":
    main()
