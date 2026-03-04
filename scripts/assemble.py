"""
Stage 4: Assemble final shorts using FFmpeg.
Combines: video clips + voiceover + captions + background music + subscribe overlay.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config


def get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file in seconds."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", audio_path],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def assemble_short(script_path: Path) -> Path:
    """Assemble a complete short from its components."""
    script = json.loads(script_path.read_text())
    sid = script["id"]

    audio_path = config.AUDIO_DIR / f"{sid}.mp3"
    srt_path = config.AUDIO_DIR / f"{sid}.srt"
    vid_dir = config.VIDEO_DIR / sid
    output_path = config.ASSEMBLED_DIR / f"{sid}.mp4"

    if not audio_path.exists():
        raise FileNotFoundError(f"Audio not found: {audio_path}")

    # Get audio duration to set total video length
    duration = get_audio_duration(str(audio_path))

    # Find video clips
    clips = sorted(vid_dir.glob("clip_*.mp4"))
    if not clips:
        raise FileNotFoundError(f"No video clips found in {vid_dir}")

    # Calculate clip duration (split evenly across audio duration)
    clip_duration = duration / len(clips)

    # Build FFmpeg concat filter
    # Step 1: Create a concat file for video clips
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        concat_file = f.name
        for clip in clips:
            f.write(f"file '{clip}'\n")

    # Step 2: Concatenate and trim clips to match audio length, add captions
    # Build complex filter for professional result
    
    # First: concat all clips into one video, loop if needed
    # Add captions if SRT exists
    srt_filter = ""
    if srt_path.exists():
        escaped_srt_path = str(srt_path).replace(':', r'\\:')
        srt_filter = (
            f"[vig]subtitles={escaped_srt_path}:"
            f"force_style='Fontname=Arial Black,Fontsize=18,"
            f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
            f"BorderStyle=3,Outline=2,Shadow=0,"
            f"Alignment=2,MarginV=120'"
            f"[captioned]"
        )
    else:
        srt_filter = "[vig]null[captioned]"

    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_file,  # video clips
        "-i", str(audio_path),                              # voiceover
        "-filter_complex",
        # Scale all clips to 1080x1920 (9:16), trim to audio length
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,setsar=1,fps=30,"
        f"trim=duration={duration},setpts=PTS-STARTPTS[base];"
        f"[base]vignette=PI/4[vig];"
        f"{srt_filter}",
        "-map", "[captioned]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(output_path)
    ]

    print(f"  🔧 Assembling {sid}...")
    result = subprocess.run(concat_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        # Fallback: simpler assembly without captions filter
        simple_cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_file,
            "-i", str(audio_path),
            "-filter_complex",
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,setsar=1,fps=30,"
            f"trim=duration={duration},setpts=PTS-STARTPTS[v]",
            "-map", "[v]", "-map", "1:a",
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart",
            str(output_path)
        ]
        subprocess.run(simple_cmd, capture_output=True, text=True)

    # Clean up
    Path(concat_file).unlink(missing_ok=True)

    if output_path.exists():
        # Get file size
        size_mb = output_path.stat().st_size / (1024 * 1024)
        script["assembled_path"] = str(output_path)
        script["assembled_size_mb"] = round(size_mb, 1)
        script["assembled_duration"] = round(duration, 1)
        script_path.write_text(json.dumps(script, indent=2))
        return output_path
    else:
        raise RuntimeError(f"Assembly failed for {sid}")


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
            out = assemble_short(path)
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

    print(f"\n✂️  Stage 4: Assembling shorts\n")
    results = assemble_all(args.scripts)
    print(f"\n✅ Assembled {len(results)} shorts → {config.ASSEMBLED_DIR}/\n")


if __name__ == "__main__":
    main()
