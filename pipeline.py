#!/usr/bin/env python3
"""
🎬 Shorts Factory — Main Pipeline Orchestrator

Usage:
  # Full pipeline (stops at video stage if manual mode)
  python pipeline.py --count 5 --niche tech

  # Run specific stage
  python pipeline.py --stage scripts --count 10 --niche ai
  python pipeline.py --stage voice
  python pipeline.py --stage video --fallback
  python pipeline.py --stage assemble
  python pipeline.py --stage upload --privacy unlisted --stagger 6

  # Full auto (with fallback videos for testing)
  python pipeline.py --count 3 --niche tech --fallback --auto-upload

  # Daily cron job
  python pipeline.py --count 2 --niche tech --fallback --auto-upload --privacy public --stagger 8

  # Check status of all scripts in pipeline
  python pipeline.py --status
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import config
from scripts.generate_scripts import generate_scripts
from scripts.generate_voice import generate_all_voices
from scripts.generate_video import generate_veo_prompt_sheet, generate_fallback_clips, generate_all_clips, check_video_readiness
from scripts.assemble import assemble_all
from scripts.upload import upload_all
from scripts.content_log import log_script, log_assembled, log_uploaded, print_log


def run_pipeline(args):
    """Run the full pipeline or a specific stage."""
    batch_id = datetime.now().strftime("B%Y%m%d_%H%M")
    script_ids = args.scripts if hasattr(args, "scripts") and args.scripts else None

    stages = {
        "scripts": lambda: run_stage_scripts(args, batch_id),
        "voice": lambda: run_stage_voice(script_ids),
        "video": lambda: run_stage_video(script_ids, args.fallback if hasattr(args, "fallback") else False),
        "assemble": lambda: run_stage_assemble(script_ids),
        "upload": lambda: run_stage_upload(script_ids, args),
    }

    if args.stage:
        # Run single stage
        print(f"\n{'='*60}")
        print(f"  🎬 Running Stage: {args.stage}")
        print(f"{'='*60}")
        stages[args.stage]()
        return

    # Run full pipeline
    print(f"\n{'='*60}")
    print(f"  🎬 SHORTS FACTORY — Full Pipeline Run")
    print(f"  📅 Batch: {batch_id}")
    print(f"  🎯 Niche: {args.niche} | Count: {args.count}")
    print(f"  🎥 Veo Mode: {config.VEO_MODE}")
    print(f"{'='*60}\n")

    # Stage 1: Generate scripts
    generated = run_stage_scripts(args, batch_id)
    if not generated:
        print("❌ Script generation failed. Aborting.")
        return

    new_ids = [s["id"] for s in generated]

    # Stage 2: Generate voiceovers
    run_stage_voice(new_ids)

    # Stage 3: Video clips
    use_fallback = getattr(args, "fallback", False)
    use_auto_video = getattr(args, "auto_video", False) or use_fallback
    run_stage_video(new_ids, use_fallback, use_auto_video)

    if config.VEO_MODE == "manual" and not use_fallback and not use_auto_video:
        print(f"\n{'='*60}")
        print(f"  ⏸️  Pipeline paused — Manual Veo 3 step required")
        print(f"{'='*60}")
        print(f"\n  1. Open output/veo3_prompts.md")
        print(f"  2. Generate clips in Veo 3 (work account)")
        print(f"  3. Save clips to output/video/{{script_id}}/clip_XX.mp4")
        print(f"  4. Resume: python pipeline.py --stage assemble")
        print(f"  5. Then:   python pipeline.py --stage upload\n")
        return

    # Stage 4: Assemble
    run_stage_assemble(new_ids)

    # Stage 5: Upload (if auto-upload enabled)
    if getattr(args, "auto_upload", False) or config.AUTO_UPLOAD:
        run_stage_upload(new_ids, args)
    else:
        print(f"\n  📤 Auto-upload is OFF. Run manually:")
        print(f"     python pipeline.py --stage upload --privacy public\n")

    # Summary
    print_status()
    print_log()


def run_stage_scripts(args, batch_id):
    print(f"\n📝 STAGE 1: Script Generation")
    print(f"{'─'*40}")
    try:
        scripts = generate_scripts(args.niche, args.count, batch_id)
        for s in (scripts or []):
            log_script(s)
        return scripts
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None


def run_stage_voice(script_ids):
    import asyncio
    print(f"\n🎙️  STAGE 2: Voiceover Generation")
    print(f"{'─'*40}")
    try:
        return asyncio.run(generate_all_voices(script_ids))
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return []


def run_stage_video(script_ids, use_fallback=False, use_auto_video=False):
    print(f"\n🎬 STAGE 3: Video Preparation")
    print(f"{'─'*40}")

    if use_auto_video:
        print(f"  🤖 Auto-generating video clips with Gemini AI...")
        generate_all_clips(script_ids, auto=True)
    else:
        prompt_sheet = generate_veo_prompt_sheet(script_ids)
        print(f"  📋 Veo 3 prompts: {prompt_sheet}")

        if use_fallback:
            print(f"  📦 Generating fallback placeholder clips...")
            generate_fallback_clips(script_ids)


def run_stage_assemble(script_ids):
    print(f"\n✂️  STAGE 4: Video Assembly")
    print(f"{'─'*40}")
    try:
        results = assemble_all(script_ids)
        # Log assembled videos
        for path in (results or []):
            try:
                script = json.loads((config.SCRIPTS_DIR / f"{path.stem}.json").read_text())
                log_assembled(script)
            except Exception:
                pass
        return results
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return []


def run_stage_upload(script_ids, args):
    print(f"\n📤 STAGE 5: YouTube Upload")
    print(f"{'─'*40}")
    privacy = getattr(args, "privacy", None) or config.UPLOAD_PRIVACY
    stagger = getattr(args, "stagger", None)
    try:
        return upload_all(script_ids, stagger_hours=stagger, privacy=privacy)
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return []


def print_status():
    """Print status of all scripts in the pipeline."""
    paths = sorted(config.SCRIPTS_DIR.glob("*.json"))
    if not paths:
        print("\n📭 No scripts in pipeline yet.\n")
        return

    print(f"\n{'='*60}")
    print(f"  📊 Pipeline Status — {len(paths)} scripts")
    print(f"{'='*60}\n")

    counts = {"script": 0, "audio": 0, "video": 0, "assembled": 0, "uploaded": 0}

    for path in paths:
        s = json.loads(path.read_text())
        sid = s["id"]
        flags = []

        flags.append("📝" if path.exists() else "  ")
        counts["script"] += 1

        has_audio = Path(s.get("audio_path", "")).exists() if s.get("audio_path") else False
        flags.append("🎙️" if has_audio else "  ")
        counts["audio"] += int(has_audio)

        vid_dir = config.VIDEO_DIR / sid
        has_video = vid_dir.exists() and list(vid_dir.glob("clip_*.mp4"))
        flags.append("🎬" if has_video else "  ")
        counts["video"] += int(bool(has_video))

        has_assembled = Path(s.get("assembled_path", "")).exists() if s.get("assembled_path") else False
        flags.append("✂️" if has_assembled else "  ")
        counts["assembled"] += int(has_assembled)

        has_uploaded = bool(s.get("youtube_id"))
        flags.append("📤" if has_uploaded else "  ")
        counts["uploaded"] += int(has_uploaded)

        status = " ".join(flags)
        title = s.get("title", "Untitled")[:50]
        url = s.get("youtube_url", "")
        print(f"  {status}  {sid}: {title} {url}")

    print(f"\n  Legend: 📝Script  🎙️Audio  🎬Video  ✂️Assembled  📤Uploaded")
    total = len(paths)
    print(f"\n  Progress: {counts['script']}/{total} → {counts['audio']}/{total} → "
          f"{counts['video']}/{total} → {counts['assembled']}/{total} → {counts['uploaded']}/{total}\n")


def main():
    parser = argparse.ArgumentParser(description="🎬 Shorts Factory Pipeline")
    parser.add_argument("--stage", choices=["scripts", "voice", "video", "assemble", "upload"],
                        help="Run a specific stage only")
    parser.add_argument("--niche", default=config.DEFAULT_NICHE,
                        choices=list(config.NICHE_CONFIG.keys()))
    parser.add_argument("--count", type=int, default=config.SHORTS_PER_RUN)
    parser.add_argument("--scripts", nargs="*", help="Specific script IDs to process")
    parser.add_argument("--fallback", action="store_true",
                        help="Auto-generate video clips with Gemini AI + Ken Burns animation")
    parser.add_argument("--auto-video", action="store_true",
                        help="Auto-generate video clips with Gemini AI + Ken Burns animation")
    parser.add_argument("--auto-upload", action="store_true",
                        help="Automatically upload after assembly")
    parser.add_argument("--privacy", choices=["public", "private", "unlisted"])
    parser.add_argument("--stagger", type=int,
                        help="Hours between scheduled uploads")
    parser.add_argument("--status", action="store_true",
                        help="Show pipeline status for all scripts")
    parser.add_argument("--log", action="store_true",
                        help="Show content log")
    args = parser.parse_args()

    if args.log:
        print_log()
        return

    if args.status:
        print_status()
        return

    run_pipeline(args)


if __name__ == "__main__":
    main()
