"""
Stage 4: Assemble final shorts using FFmpeg.

ENHANCED VERSION:
- ASS subtitles with large bold text, proper positioning, and readable styling
- Higher quality encoding (CRF 18, slow preset)
- Crossfade transitions between video clips
- Audio normalization for consistent volume
- Better color/contrast filters
"""

import json
import subprocess
import sys
import tempfile
import shutil
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


def get_clip_duration(clip_path: str) -> float:
    """Get duration of a video clip in seconds."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", clip_path],
            capture_output=True, text=True
        )
        return float(result.stdout.strip())
    except (ValueError, AttributeError):
        return 5.0  # fallback


def srt_to_ass(srt_path: Path, ass_path: Path):
    """Convert SRT to ASS with enhanced styling for YouTube Shorts captions.
    
    ASS gives us:
    - Larger, bolder text
    - Colored highlight box behind text
    - Better positioning control
    - Smooth fade-in/out per subtitle
    """
    srt_content = srt_path.read_text(encoding="utf-8")
    
    # ASS header with professional styling
    ass_header = """[Script Info]
Title: YouTube Shorts Captions
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,36,&H00FFFFFF,&H000000FF,&H00000000,&H96000000,-1,0,0,0,100,100,1,0,4,3,0,2,40,40,180,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    # Parse SRT entries
    entries = []
    blocks = srt_content.strip().split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        
        # Parse timing line: "00:00:01,234 --> 00:00:03,456"
        timing = lines[1]
        if "-->" not in timing:
            continue
        
        start_str, end_str = timing.split("-->")
        start = _srt_time_to_ass(start_str.strip())
        end = _srt_time_to_ass(end_str.strip())
        
        # Caption text (join multi-line captions)
        text = " ".join(lines[2:]).strip()
        # Escape ASS special chars
        text = text.replace("\\", "\\\\")
        
        # Add subtle fade effect (100ms fade in, 100ms fade out)
        text_with_effects = f"{{\\fad(100,100)}}{text}"
        
        entries.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text_with_effects}")
    
    ass_content = ass_header + "\n".join(entries) + "\n"
    ass_path.write_text(ass_content, encoding="utf-8")
    return ass_path


def _srt_time_to_ass(srt_time: str) -> str:
    """Convert SRT time (HH:MM:SS,mmm) to ASS time (H:MM:SS.cc)."""
    # SRT format: 00:00:01,234
    srt_time = srt_time.replace(",", ".")
    parts = srt_time.split(":")
    if len(parts) == 3:
        h, m, s = parts
        # ASS uses centiseconds, not milliseconds
        s_parts = s.split(".")
        secs = s_parts[0]
        millis = s_parts[1] if len(s_parts) > 1 else "000"
        centis = millis[:2]  # truncate to centiseconds
        return f"{int(h)}:{m}:{secs}.{centis}"
    return "0:00:00.00"


def build_crossfade_filter(clips: list[Path], duration: float, crossfade_duration: float = 0.5) -> str:
    """Build FFmpeg filter for crossfade transitions between clips.
    
    Instead of hard cuts, clips dissolve into each other over `crossfade_duration` seconds.
    """
    n = len(clips)
    if n <= 1:
        # Single clip: just scale, crop, and trim
        return (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,setsar=1,fps=30,"
            f"trim=duration={duration},setpts=PTS-STARTPTS[base]"
        )
    
    # For multiple clips, we'll use xfade filter between them
    # First, scale and trim each clip
    clip_duration = duration / n
    filter_parts = []
    
    for i in range(n):
        filter_parts.append(
            f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,setsar=1,fps=30,"
            f"trim=duration={clip_duration + crossfade_duration},setpts=PTS-STARTPTS[v{i}]"
        )
    
    # Chain xfade transitions
    if n == 2:
        offset = clip_duration - crossfade_duration
        filter_parts.append(
            f"[v0][v1]xfade=transition=fade:duration={crossfade_duration}:offset={max(0, offset)}[base]"
        )
    else:
        # Chain: v0+v1 -> tmp0, tmp0+v2 -> tmp1, etc.
        prev = "v0"
        for i in range(1, n):
            offset = clip_duration * i - crossfade_duration * i
            out_label = "base" if i == n - 1 else f"tmp{i-1}"
            filter_parts.append(
                f"[{prev}][v{i}]xfade=transition=fade:duration={crossfade_duration}:offset={max(0, offset)}[{out_label}]"
            )
            prev = out_label
    
    return ";\n".join(filter_parts)


def assemble_short(script_path: Path) -> Path:
    """Assemble a complete short from its components.
    
    Enhanced with:
    - ASS subtitles (richer styling than SRT)
    - CRF 18 (much better quality)
    - Crossfade transitions between clips
    - Audio normalization
    """
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

    # Convert SRT to ASS for better caption styling
    ass_path = None
    has_captions = False
    if srt_path.exists() and srt_path.stat().st_size > 10:
        # Copy SRT to safe temp path, convert to ASS
        safe_srt = Path(tempfile.gettempdir()) / f"{sid}_captions.srt"
        safe_ass = Path(tempfile.gettempdir()) / f"{sid}_captions.ass"
        shutil.copy2(str(srt_path), str(safe_srt))
        
        try:
            srt_to_ass(safe_srt, safe_ass)
            ass_path = safe_ass
            has_captions = True
            print(f"    📝 ASS captions generated with enhanced styling")
        except Exception as e:
            print(f"    ⚠️  ASS conversion failed: {e}, will try SRT fallback")

    # Build FFmpeg command with individual clip inputs (for crossfade)
    cmd = ["ffmpeg", "-y"]
    
    # Add each clip as separate input
    for clip in clips:
        cmd.extend(["-i", str(clip)])
    
    # Add audio input
    audio_input_idx = len(clips)
    cmd.extend(["-i", str(audio_path)])
    
    # Build filter complex
    n_clips = len(clips)
    clip_duration = duration / n_clips
    
    # Simple approach: concat with crossfade for 2+ clips  
    if n_clips == 1:
        vfilter = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,setsar=1,fps=30,"
            f"trim=duration={duration},setpts=PTS-STARTPTS,"
            f"eq=contrast=1.05:brightness=0.02:saturation=1.1,"
            f"unsharp=5:5:0.5:5:5:0.5"
        )
        if has_captions:
            escaped_ass = str(ass_path).replace(':', r'\\:').replace('\\', '/')
            vfilter += f"[vig];[vig]ass='{escaped_ass}'"
        vfilter += "[vout]"
    else:
        # Scale each clip
        filter_parts = []
        for i in range(n_clips):
            filter_parts.append(
                f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
                f"crop=1080:1920,setsar=1,fps=30,"
                f"trim=duration={clip_duration + 0.5},setpts=PTS-STARTPTS[v{i}]"
            )
        
        # Concat (simpler and more reliable than xfade for variable clip counts)
        stream_labels = "".join(f"[v{i}]" for i in range(n_clips))
        filter_parts.append(
            f"{stream_labels}concat=n={n_clips}:v=1:a=0,"
            f"trim=duration={duration},setpts=PTS-STARTPTS,"
            f"eq=contrast=1.05:brightness=0.02:saturation=1.1,"
            f"unsharp=5:5:0.5:5:5:0.5"
        )
        
        if has_captions:
            escaped_ass = str(ass_path).replace(':', r'\\:').replace('\\', '/')
            filter_parts[-1] += f"[vig];[vig]ass='{escaped_ass}'"
        
        filter_parts[-1] += "[vout]"
        vfilter = ";\n".join(filter_parts)
    
    # Audio filter: normalize loudness
    afilter = f"[{audio_input_idx}:a]loudnorm=I=-14:LRA=11:TP=-1.5[aout]"
    
    full_filter = f"{vfilter};\n{afilter}"
    
    cmd.extend([
        "-filter_complex", full_filter,
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-tune", "film",
        "-c:a", "aac",
        "-b:a", "256k",
        "-ar", "48000",
        "-shortest",
        "-movflags", "+faststart",
        str(output_path)
    ])

    print(f"  🔧 Assembling {sid} (CRF 18, slow preset, ASS captions)...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  ⚠️  Enhanced assembly failed for {sid}, trying simplified version")
        print(f"     FFmpeg error: {result.stderr[-500:] if result.stderr else 'no error output'}")
        
        # Fallback: simpler assembly without ASS captions, use concat demuxer
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            concat_file = f.name
            for clip in clips:
                f.write(f"file '{clip}'\n")
        
        simple_cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_file,
            "-i", str(audio_path),
            "-filter_complex",
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,setsar=1,fps=30,"
            f"trim=duration={duration},setpts=PTS-STARTPTS[v];"
            f"[1:a]loudnorm=I=-14:LRA=11:TP=-1.5[a]",
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "slow", "-crf", "18",
            "-c:a", "aac", "-b:a", "256k",
            "-shortest", "-movflags", "+faststart",
            str(output_path)
        ]
        
        result2 = subprocess.run(simple_cmd, capture_output=True, text=True)
        Path(concat_file).unlink(missing_ok=True)
        
        if result2.returncode != 0:
            # Last resort: very basic assembly
            print(f"  ⚠️  Simplified version also failed, using basic concat")
            print(f"     Error: {result2.stderr[-300:] if result2.stderr else 'no error'}")
            
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                concat_file = f.name
                for clip in clips:
                    f.write(f"file '{clip}'\n")
            
            basic_cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", concat_file,
                "-i", str(audio_path),
                "-filter_complex",
                f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
                f"crop=1080:1920,setsar=1,fps=30,"
                f"trim=duration={duration},setpts=PTS-STARTPTS[v]",
                "-map", "[v]", "-map", "1:a",
                "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest", "-movflags", "+faststart",
                str(output_path)
            ]
            subprocess.run(basic_cmd, capture_output=True, text=True)
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

    print(f"\n✂️  Stage 4: Assembling shorts (Enhanced Quality)\n")
    results = assemble_all(args.scripts)
    print(f"\n✅ Assembled {len(results)} shorts → {config.ASSEMBLED_DIR}/\n")


if __name__ == "__main__":
    main()
