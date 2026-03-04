"""
Stage 3: Video clip preparation — AUTOMATED MODE.

Uses Gemini image generation to create visuals from script visual cues,
then animates them with FFmpeg Ken Burns effects (zoom/pan) to produce
professional-looking video clips. No manual Veo 3 step needed.

Fallback chain:
  1. Gemini image generation → Ken Burns animation (primary)
  2. Solid-color placeholder clips (last resort)
"""

import json
import subprocess
import sys
import time
import random
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

# ---------------------------------------------------------------------------
# Ken Burns animation presets for variety
# ---------------------------------------------------------------------------
BURNS_EFFECTS = [
    # Slow zoom in from center
    "scale=8000:-1,zoompan=z='min(zoom+0.0015,1.5)':d=150:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
    # Slow zoom out
    "scale=8000:-1,zoompan=z='if(lte(zoom,1.0),1.5,max(1.001,zoom-0.0015))':d=150:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
    # Pan left to right
    "scale=8000:-1,zoompan=z='1.3':d=150:x='if(lte(on,1),0,min(x+3,iw-iw/zoom))':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
    # Pan right to left
    "scale=8000:-1,zoompan=z='1.3':d=150:x='if(lte(on,1),iw,max(0,x-3))':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
]


def generate_image_gemini(prompt: str, output_path: Path) -> bool:
    """Generate a single image using Gemini's image generation model."""
    try:
        from google import genai

        client = genai.Client(api_key=config.GEMINI_API_KEY)

        full_prompt = (
            f"Generate a stunning, cinematic image for a YouTube Short: {prompt}. "
            f"Vertical 9:16 aspect ratio, photorealistic, dramatic lighting, "
            f"vivid colors, high detail, 4K quality."
        )

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=full_prompt,
            config=genai.types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            ),
        )

        # Extract image from response
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                output_path.write_bytes(part.inline_data.data)
                return True

        return False

    except Exception as e:
        print(f"    ⚠️  Image generation error: {e}")
        return False


def image_to_video_clip(image_path: Path, output_path: Path, duration: float = 5.0, effect_idx: int = 0) -> bool:
    """Convert a still image to an animated video clip using Ken Burns effect."""
    effect = BURNS_EFFECTS[effect_idx % len(BURNS_EFFECTS)]
    frames = int(duration * 30)
    effect = effect.replace("d=150", f"d={frames}")

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-vf", effect,
        "-t", str(duration),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def generate_clips_auto(script_path: Path) -> list[Path]:
    """Generate video clips automatically using Gemini image gen + Ken Burns."""
    script = json.loads(script_path.read_text())
    sid = script["id"]
    vid_dir = config.VIDEO_DIR / sid
    vid_dir.mkdir(exist_ok=True)

    # Get visual prompts from the script
    veo_prompts = script.get("veo3_prompts", [])
    if not veo_prompts:
        # Fallback to visual cues
        for cue in script.get("visual_cues", []):
            veo_prompts.append(cue.get("description", "abstract tech background"))

    clips = []
    for j, prompt in enumerate(veo_prompts):
        clip_path = vid_dir / f"clip_{j+1:02d}.mp4"
        img_path = vid_dir / f"img_{j+1:02d}.png"

        # Skip if clip already exists and is a real clip (not a tiny placeholder)
        if clip_path.exists() and clip_path.stat().st_size > 50000:
            print(f"    ✅ Clip {j+1} already exists, skipping")
            clips.append(clip_path)
            continue

        # Step 1: Generate image from prompt
        print(f"    🎨 Generating image {j+1}/{len(veo_prompts)}: {prompt[:60]}...")
        success = generate_image_gemini(prompt, img_path)

        if success and img_path.exists():
            # Step 2: Animate the image with Ken Burns effect
            print(f"    🎬 Animating clip {j+1} with Ken Burns effect...")
            if image_to_video_clip(img_path, clip_path, duration=15.0, effect_idx=j):
                size_kb = clip_path.stat().st_size / 1024
                print(f"    ✅ Clip {j+1}: {clip_path.name} ({size_kb:.0f} KB)")
                clips.append(clip_path)
            else:
                print(f"    ❌ FFmpeg animation failed for clip {j+1}, using fallback")
                _generate_solid_fallback(clip_path, j)
                clips.append(clip_path)
        else:
            print(f"    ⚠️  Image gen failed for clip {j+1}, using fallback")
            _generate_solid_fallback(clip_path, j)
            clips.append(clip_path)

        # Small delay between API calls to respect rate limits
        if j < len(veo_prompts) - 1:
            time.sleep(1)

    return clips


def _generate_solid_fallback(clip_path: Path, idx: int):
    """Generate a solid-color fallback clip."""
    colors = ["0x1a1a2e", "0x16213e", "0x0f3460", "0x533483", "0x1a1a2e"]
    color = colors[idx % len(colors)]
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"color=c={color}:s=1080x1920:d=5:r=30",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(clip_path),
    ]
    subprocess.run(cmd, capture_output=True)


def generate_veo_prompt_sheet(script_ids: list[str] = None) -> Path:
    """Generate a markdown file with all Veo 3 prompts ready to copy-paste."""
    if script_ids:
        paths = [config.SCRIPTS_DIR / f"{sid}.json" for sid in script_ids]
    else:
        paths = sorted(config.SCRIPTS_DIR.glob("*.json"))

    lines = [
        "# 🎬 Veo 3 Prompt Sheet",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Instructions",
        "1. Open Veo 3 in your Google AI Ultra account (work account)",
        "2. For each script below, generate the 4 video clips using the prompts",
        "3. Download each clip and place in: `output/video/{SCRIPT_ID}/clip_01.mp4` etc.",
        "4. Once all clips are in place, run: `python pipeline.py --stage assemble`",
        "",
        "---",
        "",
    ]

    for path in paths:
        script = json.loads(path.read_text())
        sid = script["id"]

        # Create video output folder
        vid_dir = config.VIDEO_DIR / sid
        vid_dir.mkdir(exist_ok=True)

        lines.append(f"## {sid}: {script['title']}")
        lines.append(f"**Channel:** {script.get('channel', 'N/A')}")
        lines.append(f"**Hook:** {script['hook']}")
        lines.append("")

        veo_prompts = script.get("veo3_prompts", [])
        if not veo_prompts:
            for cue in script.get("visual_cues", []):
                veo_prompts.append(
                    f"Cinematic {cue['description']}, smooth camera movement, "
                    f"dramatic lighting, photorealistic, 4K, 9:16 vertical format"
                )

        for j, prompt in enumerate(veo_prompts, 1):
            lines.append(f"### Clip {j}")
            lines.append(f"**Save as:** `output/video/{sid}/clip_{j:02d}.mp4`")
            lines.append("")
            lines.append("```")
            lines.append(prompt)
            lines.append("```")
            lines.append("")

        lines.append("---")
        lines.append("")

        # Update script with expected video paths
        script["video_dir"] = str(vid_dir)
        script["expected_clips"] = [
            str(vid_dir / f"clip_{j+1:02d}.mp4") for j in range(len(veo_prompts))
        ]
        path.write_text(json.dumps(script, indent=2))

    output_path = config.OUTPUT / "veo3_prompts.md"
    output_path.write_text("\n".join(lines))
    return output_path


def generate_all_clips(script_ids: list[str] = None, auto: bool = True) -> list[Path]:
    """Generate video clips for all scripts."""
    if script_ids:
        paths = [config.SCRIPTS_DIR / f"{sid}.json" for sid in script_ids]
    else:
        paths = sorted(config.SCRIPTS_DIR.glob("*.json"))

    all_clips = []
    for path in paths:
        script = json.loads(path.read_text())
        sid = script["id"]
        print(f"  🎬 Processing {sid}: \"{script['title'][:50]}...\"")

        if auto:
            clips = generate_clips_auto(path)
        else:
            # Manual mode: just generate prompt sheet
            generate_veo_prompt_sheet([sid])
            clips = []

        all_clips.extend(clips)

    return all_clips


def check_video_readiness(script_ids: list[str] = None) -> dict:
    """Check which scripts have their video clips ready."""
    if script_ids:
        paths = [config.SCRIPTS_DIR / f"{sid}.json" for sid in script_ids]
    else:
        paths = sorted(config.SCRIPTS_DIR.glob("*.json"))

    status = {"ready": [], "missing": [], "partial": []}

    for path in paths:
        script = json.loads(path.read_text())
        sid = script["id"]
        vid_dir = config.VIDEO_DIR / sid

        if not vid_dir.exists():
            status["missing"].append(sid)
            continue

        clips = sorted(vid_dir.glob("clip_*.mp4"))
        expected = len(script.get("veo3_prompts", script.get("visual_cues", [{}] * 4)))

        if len(clips) >= expected:
            status["ready"].append(sid)
        elif len(clips) > 0:
            status["partial"].append({"id": sid, "have": len(clips), "need": expected})
        else:
            status["missing"].append(sid)

    return status


def generate_fallback_clips(script_ids: list[str] = None):
    """
    Generate solid-color placeholder clips using FFmpeg so pipeline never stalls.
    These are temporary — replace with real Veo 3 clips for quality.
    """
    if script_ids:
        paths = [config.SCRIPTS_DIR / f"{sid}.json" for sid in script_ids]
    else:
        paths = sorted(config.SCRIPTS_DIR.glob("*.json"))

    for path in paths:
        script = json.loads(path.read_text())
        sid = script["id"]
        vid_dir = config.VIDEO_DIR / sid
        vid_dir.mkdir(exist_ok=True)

        num_clips = len(script.get("veo3_prompts", [None] * 4))
        colors = ["0x1a1a2e", "0x16213e", "0x0f3460", "0x533483", "0x1a1a2e"]

        for j in range(num_clips):
            clip_path = vid_dir / f"clip_{j+1:02d}.mp4"
            if clip_path.exists():
                continue

            color = colors[j % len(colors)]
            cmd = [
                "ffmpeg", "-y", "-f", "lavfi",
                "-i", f"color=c={color}:s=1080x1920:d=15:r=30",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                str(clip_path),
            ]
            subprocess.run(cmd, capture_output=True)
            print(f"  📦 Placeholder: {clip_path.name}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--scripts", nargs="*", help="Specific script IDs")
    parser.add_argument("--check", action="store_true", help="Check clip readiness")
    parser.add_argument("--fallback", action="store_true", help="Generate placeholder clips")
    parser.add_argument("--auto", action="store_true", help="Auto-generate with Gemini images")
    args = parser.parse_args()

    if args.check:
        status = check_video_readiness(args.scripts)
        print(f"\n📊 Video Clip Status:")
        print(f"  ✅ Ready:   {len(status['ready'])} — {status['ready']}")
        print(f"  ⚠️  Partial: {len(status['partial'])} — {status['partial']}")
        print(f"  ❌ Missing: {len(status['missing'])} — {status['missing']}")
        return status

    if args.fallback:
        print(f"\n📦 Generating placeholder clips (replace with Veo 3 later)\n")
        generate_fallback_clips(args.scripts)
        return

    if args.auto:
        print(f"\n🎬 Stage 3: Auto-generating video clips with Gemini AI\n")
        clips = generate_all_clips(args.scripts, auto=True)
        print(f"\n✅ Generated {len(clips)} clips\n")
        return clips

    print(f"\n🎬 Stage 3: Generating Veo 3 prompt sheet\n")
    prompt_sheet = generate_veo_prompt_sheet(args.scripts)
    print(f"  ✅ Prompt sheet saved: {prompt_sheet}")
    print(f"\n📋 Next steps:")
    print(f"  1. Open {prompt_sheet} and paste prompts into Veo 3")
    print(f"  2. Download clips to output/video/{{script_id}}/")
    print(f"  3. Run: python pipeline.py --stage assemble")
    print(f"\n  Or use --auto for AI-generated clips\n")

    return prompt_sheet


if __name__ == "__main__":
    main()
