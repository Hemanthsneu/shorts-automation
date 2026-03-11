#!/usr/bin/env python3
"""
Shorts Factory v2.0 — Viral Intelligence Pipeline

The pipeline that turns trending topics into 1M+ view YouTube Shorts.

Pipeline stages:
  1. SCRIPTS     — Generate viral scripts powered by Viral Intelligence Engine
  2. SCORE       — Virality pre-score gate (kill weak scripts before production)
  3. VOICE       — Generate cinematic voiceovers with niche-matched voices
  4. VIDEO       — Generate visual clips (Gemini AI + Ken Burns / Veo 3)
  5. ASSEMBLE    — Pro assembly (captions + sound design + color grade + progress bar)
  6. UPLOAD      — YouTube upload with optimal timing from Channel Manager
  7. ANALYTICS   — Pull performance data and feed back into strategy

Usage:
  # Full viral pipeline (generates, scores, produces, uploads)
  python pipeline.py --count 5 --niche tech --auto-upload

  # Generate and score only (quality check before production)
  python pipeline.py --stage scripts --count 10 --niche ai

  # Run specific stages
  python pipeline.py --stage score
  python pipeline.py --stage voice
  python pipeline.py --stage video --fallback
  python pipeline.py --stage assemble
  python pipeline.py --stage upload --privacy public --stagger 6

  # Analytics and strategy
  python pipeline.py --stage analytics
  python pipeline.py --analytics

  # Content calendar
  python pipeline.py --calendar 7

  # Full status
  python pipeline.py --status
"""

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path

import config
from scripts.generate_scripts import generate_scripts
from scripts.generate_voice import generate_all_voices
from scripts.generate_video import (
    generate_veo_prompt_sheet, generate_fallback_clips,
    generate_all_clips, check_video_readiness,
)
from scripts.assemble import assemble_all
from scripts.upload import upload_all
from scripts.content_log import log_script, log_assembled, log_uploaded, print_log
from scripts.virality_score import gate_and_improve, score_batch
from scripts.analytics import pull_performance_data, print_performance_report, generate_strategy_update
from scripts.channel_manager import (
    generate_content_calendar, get_next_posting_slot,
    get_daily_production_plan, print_calendar,
)


def run_pipeline(args):
    """Run the full viral pipeline or a specific stage."""
    batch_id = datetime.now().strftime("B%Y%m%d_%H%M")
    script_ids = args.scripts if hasattr(args, "scripts") and args.scripts else None

    stages = {
        "scripts": lambda: run_stage_scripts(args, batch_id),
        "score": lambda: run_stage_score(script_ids),
        "voice": lambda: run_stage_voice(script_ids),
        "video": lambda: run_stage_video(script_ids, args.fallback if hasattr(args, "fallback") else False),
        "assemble": lambda: run_stage_assemble(script_ids),
        "upload": lambda: run_stage_upload(script_ids, args),
        "analytics": lambda: run_stage_analytics(),
    }

    if args.stage:
        print(f"\n{'='*60}")
        print(f"  Running Stage: {args.stage.upper()}")
        print(f"{'='*60}")
        stages[args.stage]()
        return

    # ═══════════════════════════════════════════════════════════════
    # FULL VIRAL PIPELINE
    # ═══════════════════════════════════════════════════════════════
    print(f"\n{'='*60}")
    print(f"  SHORTS FACTORY v2.0 — Viral Intelligence Pipeline")
    print(f"  {'─'*56}")
    print(f"  Batch:   {batch_id}")
    print(f"  Niche:   {args.niche} | Target: {args.count} shorts")
    print(f"  Veo:     {config.VEO_MODE}")
    print(f"  Gate:    {'ON (threshold: ' + str(config.VIRALITY_THRESHOLD) + ')' if config.VIRALITY_GATE_ENABLED else 'OFF'}")
    print(f"  Sound:   {'ON' if config.SOUND_DESIGN_ENABLED else 'OFF'}")
    print(f"  Caption: {config.CAPTION_STYLE}")
    print(f"{'='*60}\n")

    # Step 0: Pull analytics (if enabled) to inform content strategy
    if config.ANALYTICS_ENABLED and config.ANALYTICS_PULL_ON_RUN:
        run_stage_analytics_brief()

    # Stage 1: Generate scripts (overgenerate for quality gate)
    generate_count = args.count
    if config.VIRALITY_GATE_ENABLED:
        generate_count = max(args.count, math.ceil(args.count * config.SCRIPTS_OVERGENERATE_FACTOR))
        print(f"  Overgenerate: Producing {generate_count} scripts to keep best {args.count}")

    generated = run_stage_scripts(args, batch_id, override_count=generate_count)
    if not generated:
        print("  Script generation failed. Aborting.")
        return

    # Stage 2: Virality scoring gate
    if config.VIRALITY_GATE_ENABLED:
        scored = run_stage_score_inline(generated, args.count)
        if not scored:
            print("  No scripts passed the virality gate. Aborting.")
            return
        new_ids = [s["id"] for s in scored]
    else:
        new_ids = [s["id"] for s in generated]

    # Stage 3: Generate voiceovers
    run_stage_voice(new_ids)

    # Stage 4: Video clips
    use_fallback = getattr(args, "fallback", False)
    use_auto_video = getattr(args, "auto_video", False) or use_fallback
    run_stage_video(new_ids, use_fallback, use_auto_video)

    if config.VEO_MODE == "manual" and not use_fallback and not use_auto_video:
        print(f"\n{'='*60}")
        print(f"  Pipeline paused — Manual Veo 3 step required")
        print(f"{'='*60}")
        print(f"\n  1. Open output/veo3_prompts.md")
        print(f"  2. Generate clips in Veo 3")
        print(f"  3. Save clips to output/video/{{script_id}}/clip_XX.mp4")
        print(f"  4. Resume: python pipeline.py --stage assemble")
        print(f"  5. Then:   python pipeline.py --stage upload\n")
        return

    # Stage 5: Pro assembly (captions + sound design + color grade)
    run_stage_assemble(new_ids)

    # Stage 6: Upload (if auto-upload)
    if getattr(args, "auto_upload", False) or config.AUTO_UPLOAD:
        run_stage_upload(new_ids, args)
    else:
        print(f"\n  Auto-upload is OFF. Run manually:")
        print(f"     python pipeline.py --stage upload --privacy public\n")

    # Summary
    print_status()


def run_stage_scripts(args, batch_id, override_count=None):
    count = override_count or args.count
    print(f"\n  STAGE 1: Script Generation (Viral Intelligence Engine)")
    print(f"  {'─'*50}")
    try:
        scripts = generate_scripts(args.niche, count, batch_id)
        for s in (scripts or []):
            log_script(s)
        return scripts
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_stage_score(script_ids=None):
    """Score existing scripts through the virality gate."""
    print(f"\n  STAGE 2: Virality Pre-Score Gate")
    print(f"  {'─'*50}")

    if script_ids:
        paths = [config.SCRIPTS_DIR / f"{sid}.json" for sid in script_ids]
    else:
        paths = sorted(config.SCRIPTS_DIR.glob("*.json"))

    scripts = []
    for p in paths:
        if p.exists():
            scripts.append(json.loads(p.read_text()))

    if not scripts:
        print("  No scripts to score.")
        return []

    passed = gate_and_improve(scripts, config.MAX_IMPROVEMENT_ROUNDS)

    for script in passed:
        out_path = config.SCRIPTS_DIR / f"{script['id']}.json"
        out_path.write_text(json.dumps(script, indent=2))

    return passed


def run_stage_score_inline(scripts: list[dict], keep_count: int) -> list[dict]:
    """Score and filter scripts inline during pipeline run."""
    print(f"\n  STAGE 2: Virality Pre-Score Gate")
    print(f"  {'─'*50}")

    passed = gate_and_improve(scripts, config.MAX_IMPROVEMENT_ROUNDS)

    # Sort by score and keep the top N
    passed.sort(
        key=lambda s: s.get("virality_score", {}).get("final_score", 0),
        reverse=True,
    )
    kept = passed[:keep_count]

    if len(kept) < keep_count:
        print(f"  Warning: Only {len(kept)}/{keep_count} scripts passed the gate")

    # Save updated scripts
    for script in kept:
        out_path = config.SCRIPTS_DIR / f"{script['id']}.json"
        out_path.write_text(json.dumps(script, indent=2))

    # Remove killed scripts' JSON files
    killed_ids = set(s["id"] for s in scripts) - set(s["id"] for s in kept)
    for sid in killed_ids:
        kill_path = config.SCRIPTS_DIR / f"{sid}.json"
        if kill_path.exists():
            kill_path.unlink()
            print(f"  Removed killed script: {sid}")

    return kept


def run_stage_voice(script_ids):
    import asyncio
    print(f"\n  STAGE 3: Voiceover Generation")
    print(f"  {'─'*50}")
    try:
        return asyncio.run(generate_all_voices(script_ids))
    except Exception as e:
        print(f"  Error: {e}")
        return []


def run_stage_video(script_ids, use_fallback=False, use_auto_video=False):
    print(f"\n  STAGE 4: Video Preparation")
    print(f"  {'─'*50}")

    if use_auto_video:
        print(f"  Auto-generating video clips with Gemini AI...")
        generate_all_clips(script_ids, auto=True)
    else:
        prompt_sheet = generate_veo_prompt_sheet(script_ids)
        print(f"  Veo 3 prompts: {prompt_sheet}")

        if use_fallback:
            print(f"  Generating fallback placeholder clips...")
            generate_fallback_clips(script_ids)


def run_stage_assemble(script_ids):
    print(f"\n  STAGE 5: Pro Video Assembly")
    print(f"  {'─'*50}")
    try:
        results = assemble_all(script_ids)
        for path in (results or []):
            try:
                script = json.loads((config.SCRIPTS_DIR / f"{path.stem}.json").read_text())
                log_assembled(script)
            except Exception:
                pass
        return results
    except Exception as e:
        print(f"  Error: {e}")
        return []


def run_stage_upload(script_ids, args):
    print(f"\n  STAGE 6: YouTube Upload")
    print(f"  {'─'*50}")
    privacy = getattr(args, "privacy", None) or config.UPLOAD_PRIVACY
    stagger = getattr(args, "stagger", None)
    try:
        return upload_all(script_ids, stagger_hours=stagger, privacy=privacy)
    except Exception as e:
        print(f"  Error: {e}")
        return []


def run_stage_analytics():
    """Full analytics: pull data + generate report + update strategy."""
    print(f"\n  STAGE 7: Analytics & Strategy")
    print(f"  {'─'*50}")
    try:
        pull_performance_data()
        print_performance_report()
        strategy = generate_strategy_update()
        if strategy and strategy.get("status") != "insufficient_data":
            print(f"\n  Strategy updated → output/analytics/strategy.json")
            recs = strategy.get("recommendations", [])
            if recs:
                print(f"\n  KEY RECOMMENDATIONS:")
                for r in recs:
                    print(f"    -> {r}")
    except Exception as e:
        print(f"  Analytics error: {e}")


def run_stage_analytics_brief():
    """Quick analytics pull without full report (used at pipeline start)."""
    try:
        print(f"  Pulling latest analytics...")
        pull_performance_data()
    except Exception:
        pass


def print_status():
    """Print status of all scripts in the pipeline."""
    paths = sorted(config.SCRIPTS_DIR.glob("*.json"))
    if not paths:
        print("\n  No scripts in pipeline yet.\n")
        return

    print(f"\n{'='*60}")
    print(f"  Pipeline Status — {len(paths)} scripts")
    print(f"{'='*60}\n")

    counts = {"script": 0, "scored": 0, "audio": 0, "video": 0, "assembled": 0, "uploaded": 0}

    for path in paths:
        s = json.loads(path.read_text())
        sid = s["id"]
        flags = []

        flags.append("S")
        counts["script"] += 1

        has_score = bool(s.get("virality_score"))
        v_score = s.get("virality_score", {}).get("final_score", 0)
        flags.append(f"V:{v_score:.0f}" if has_score else "V:--")
        counts["scored"] += int(has_score)

        has_audio = Path(s.get("audio_path", "")).exists() if s.get("audio_path") else False
        flags.append("A" if has_audio else "-")
        counts["audio"] += int(has_audio)

        vid_dir = config.VIDEO_DIR / sid
        has_video = vid_dir.exists() and list(vid_dir.glob("clip_*.mp4"))
        flags.append("V" if has_video else "-")
        counts["video"] += int(bool(has_video))

        has_assembled = Path(s.get("assembled_path", "")).exists() if s.get("assembled_path") else False
        flags.append("F" if has_assembled else "-")
        counts["assembled"] += int(has_assembled)

        has_uploaded = bool(s.get("youtube_id"))
        flags.append("U" if has_uploaded else "-")
        counts["uploaded"] += int(has_uploaded)

        status = " ".join(flags)
        title = s.get("title", "Untitled")[:45]
        formula = s.get("viral_formula_used", "-")[:12]
        url = s.get("youtube_url", "")
        views = ""
        if url:
            views = f" | {url}"
        print(f"  [{status}] {sid}: {title} [{formula}]{views}")

    print(f"\n  Legend: S=Script V=ViralScore A=Audio V=Video F=Final U=Uploaded")
    total = len(paths)
    print(f"\n  Progress: {counts['script']}/{total} -> "
          f"scored:{counts['scored']}/{total} -> "
          f"audio:{counts['audio']}/{total} -> "
          f"video:{counts['video']}/{total} -> "
          f"assembled:{counts['assembled']}/{total} -> "
          f"uploaded:{counts['uploaded']}/{total}\n")


def main():
    parser = argparse.ArgumentParser(description="Shorts Factory v2.0 — Viral Intelligence Pipeline")
    parser.add_argument("--stage",
                        choices=["scripts", "score", "voice", "video", "assemble", "upload", "analytics"],
                        help="Run a specific stage only")
    parser.add_argument("--niche", default=config.DEFAULT_NICHE,
                        choices=list(config.NICHE_CONFIG.keys()))
    parser.add_argument("--count", type=int, default=config.SHORTS_PER_RUN)
    parser.add_argument("--scripts", nargs="*", help="Specific script IDs to process")
    parser.add_argument("--fallback", action="store_true",
                        help="Auto-generate video clips with Gemini AI + Ken Burns")
    parser.add_argument("--auto-video", action="store_true",
                        help="Auto-generate video clips with Gemini AI + Ken Burns")
    parser.add_argument("--auto-upload", action="store_true",
                        help="Automatically upload after assembly")
    parser.add_argument("--privacy", choices=["public", "private", "unlisted"])
    parser.add_argument("--stagger", type=int,
                        help="Hours between scheduled uploads")
    parser.add_argument("--status", action="store_true", help="Show pipeline status")
    parser.add_argument("--log", action="store_true", help="Show content log")
    parser.add_argument("--analytics", action="store_true", help="Run analytics report")
    parser.add_argument("--calendar", type=int, default=0, help="Show content calendar for N days")
    parser.add_argument("--no-gate", action="store_true", help="Skip virality scoring gate")
    parser.add_argument("--no-sound", action="store_true", help="Skip sound design")
    args = parser.parse_args()

    # Override settings from CLI flags
    if args.no_gate:
        config.VIRALITY_GATE_ENABLED = False
    if args.no_sound:
        config.SOUND_DESIGN_ENABLED = False

    if args.log:
        print_log()
        return

    if args.status:
        print_status()
        return

    if args.analytics:
        run_stage_analytics()
        return

    if args.calendar:
        print_calendar(args.calendar)
        return

    run_pipeline(args)


if __name__ == "__main__":
    main()
