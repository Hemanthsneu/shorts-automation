"""
Stage 4: Pro Video Assembly — Cinematic Multi-Layer Composition

Combines all production elements into a final viral-ready short:
- Video clips with intelligent scene transitions
- Sound-designed audio (voiceover + SFX + ambient)
- Pro animated captions (word-by-word TikTok style via ASS)
- Color grading and vignette
- Progress bar overlay (retention booster)
- Optimized encoding for YouTube Shorts

The assembly pipeline is the production quality differentiator.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from scripts.caption_engine import generate_captions_for_script
from scripts.sound_design import render_sound_design


def get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file in seconds."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", audio_path],
        capture_output=True, text=True
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 60.0


def _build_concat_file(clips: list[Path]) -> str:
    """Create a temporary concat file for FFmpeg."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    for clip in clips:
        f.write(f"file '{clip}'\n")
    f.close()
    return f.name


def assemble_short_pro(script_path: Path) -> Path:
    """Assemble a complete short with all pro production elements."""
    script = json.loads(script_path.read_text())
    sid = script["id"]
    niche = script.get("niche", "tech")

    audio_path = config.AUDIO_DIR / f"{sid}.mp3"
    srt_path = config.AUDIO_DIR / f"{sid}.srt"
    vid_dir = config.VIDEO_DIR / sid
    output_path = config.ASSEMBLED_DIR / f"{sid}.mp4"

    if not audio_path.exists():
        raise FileNotFoundError(f"Audio not found: {audio_path}")

    duration = get_audio_duration(str(audio_path))

    # Find video clips
    clips = sorted(vid_dir.glob("clip_*.mp4"))
    if not clips:
        raise FileNotFoundError(f"No video clips found in {vid_dir}")

    # ═══════════════════════════════════════════════════════════════
    # STEP 1: Generate Pro Captions (ASS format with animations)
    # ═══════════════════════════════════════════════════════════════
    print(f"  📝 Generating pro captions for {sid}...")
    ass_path = generate_captions_for_script(sid)

    # ═══════════════════════════════════════════════════════════════
    # STEP 2: Sound Design (voiceover + SFX + ambient)
    # ═══════════════════════════════════════════════════════════════
    designed_audio_path = config.AUDIO_DIR / f"{sid}_designed.m4a"
    if not designed_audio_path.exists():
        print(f"  🎵 Rendering sound design for {sid}...")
        render_sound_design(script, audio_path, designed_audio_path, duration)

    final_audio = designed_audio_path if designed_audio_path.exists() else audio_path

    # ═══════════════════════════════════════════════════════════════
    # STEP 3: Video Assembly with FFmpeg
    # ═══════════════════════════════════════════════════════════════
    concat_file = _build_concat_file(clips)

    # Build the video filter chain
    video_filters = []

    # Base: scale, crop, framerate
    video_filters.append(
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,setsar=1,fps=30,"
        f"trim=duration={duration},setpts=PTS-STARTPTS"
    )

    # Color grading: slight contrast boost + saturation for cinematic look
    video_filters.append(
        "eq=contrast=1.05:brightness=0.02:saturation=1.1"
    )

    # Vignette for cinematic depth
    video_filters.append("vignette=PI/4")

    # Progress bar (thin line at bottom that fills over duration — retention booster)
    progress_bar = (
        f"drawbox=x=0:y=ih-6:w='(t/{duration})*iw':h=6:"
        f"color=white@0.7:t=fill"
    )
    video_filters.append(progress_bar)

    video_filter_str = ",".join(video_filters)

    # Try assembly with ASS captions first
    if ass_path and ass_path.exists():
        safe_ass = Path(tempfile.gettempdir()) / f"{sid}_captions.ass"
        shutil.copy2(str(ass_path), str(safe_ass))
        escaped_ass = str(safe_ass).replace(':', r'\\:').replace('\\', '/')

        full_filter = (
            f"[0:v]{video_filter_str}[styled];"
            f"[styled]ass={escaped_ass}[final]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_file,
            "-i", str(final_audio),
            "-filter_complex", full_filter,
            "-map", "[final]",
            "-map", "1:a",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "20",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            "-metadata", f"title={script.get('title', '')}",
            str(output_path),
        ]

        print(f"  🔧 Assembling {sid} (pro mode: captions + sound design + color grade)...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and output_path.exists():
            Path(concat_file).unlink(missing_ok=True)
            _finalize(script, script_path, output_path, duration)
            return output_path

        print(f"  ⚠️  ASS caption render failed, trying SRT fallback...")

    # Fallback: try with SRT captions
    if srt_path.exists():
        safe_srt = Path(tempfile.gettempdir()) / f"{sid}_captions.srt"
        shutil.copy2(str(srt_path), str(safe_srt))
        escaped_srt = str(safe_srt).replace(':', r'\\:').replace('\\', '/')

        srt_style = (
            f"Fontname=Arial Black,Fontsize=24,"
            f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
            f"BackColour=&H80000000,"
            f"BorderStyle=4,Outline=0,Shadow=0,"
            f"Alignment=2,MarginV=100,Bold=1"
        )

        full_filter = (
            f"[0:v]{video_filter_str}[styled];"
            f"[styled]subtitles={escaped_srt}:force_style='{srt_style}'[final]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_file,
            "-i", str(final_audio),
            "-filter_complex", full_filter,
            "-map", "[final]",
            "-map", "1:a",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "20",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            str(output_path),
        ]

        print(f"  🔧 Assembling {sid} (SRT caption fallback)...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and output_path.exists():
            Path(concat_file).unlink(missing_ok=True)
            _finalize(script, script_path, output_path, duration)
            return output_path

        print(f"  ⚠️  SRT render also failed, assembling without captions...")

    # Last resort: no captions
    simple_filter = f"[0:v]{video_filter_str}[final]"

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_file,
        "-i", str(final_audio),
        "-filter_complex", simple_filter,
        "-map", "[final]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(output_path),
    ]

    print(f"  🔧 Assembling {sid} (no-caption fallback)...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    Path(concat_file).unlink(missing_ok=True)

    if output_path.exists():
        _finalize(script, script_path, output_path, duration)
        return output_path
    else:
        stderr_tail = result.stderr[-300:] if result.stderr else "no output"
        raise RuntimeError(f"Assembly failed for {sid}: {stderr_tail}")


def _finalize(script: dict, script_path: Path, output_path: Path, duration: float):
    """Update script JSON with assembly metadata."""
    size_mb = output_path.stat().st_size / (1024 * 1024)
    script["assembled_path"] = str(output_path)
    script["assembled_size_mb"] = round(size_mb, 1)
    script["assembled_duration"] = round(duration, 1)
    script["assembly_mode"] = "pro"
    script_path.write_text(json.dumps(script, indent=2))


def assemble_all(script_ids: list[str] = None) -> list[Path]:
    """Assemble all scripts with available video clips."""
    if script_ids:
        paths = [config.SCRIPTS_DIR / f"{sid}.json" for sid in script_ids]
    else:
        paths = sorted(config.SCRIPTS_DIR.glob("*.json"))

    results = []
    for path in paths:
        script = json.loads(path.read_text())
        sid = script["id"]
        vid_dir = config.VIDEO_DIR / sid

        if not vid_dir.exists() or not list(vid_dir.glob("clip_*.mp4")):
            print(f"  ⏭️  Skipping {sid} — no video clips yet")
            continue

        try:
            out = assemble_short_pro(path)
            size = json.loads(path.read_text()).get("assembled_size_mb", "?")
            print(f"  ✅ Assembled {sid}: {out.name} ({size} MB)")
            results.append(out)
        except Exception as e:
            print(f"  ❌ Failed {sid}: {e}")

    return results


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--scripts", nargs="*", help="Specific script IDs")
    args = parser.parse_args()

    print(f"\n✂️  Stage 4: Pro Video Assembly\n")
    results = assemble_all(args.scripts)
    print(f"\n✅ Assembled {len(results)} shorts → {config.ASSEMBLED_DIR}/\n")


if __name__ == "__main__":
    main()
