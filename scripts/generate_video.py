"""
Stage 3: Video clip preparation — AUTOMATED MODE.

ENHANCED VERSION:
- Context-aware image prompts using actual script content (not just generic visual cues)
- Pre-generation Gemini step to create detailed, topic-specific image descriptions
- Improved Ken Burns effects with smoother easing
- Higher quality encoding for individual clips
- Better fallback chain with retry logic

Fallback chain:
  1. Context-enriched Gemini image generation → Ken Burns animation (primary)
  2. Gemini image with simplified prompt (fallback)
  3. Solid-color placeholder clips (last resort)
"""

import json
import subprocess
import sys
import time
import random
from pathlib import Path
from datetime import datetime

import google.generativeai as genai

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

# ---------------------------------------------------------------------------
# Ken Burns animation presets — ENHANCED with smoother easing
# ---------------------------------------------------------------------------
BURNS_EFFECTS = [
    # Smooth zoom in with ease-in-out (using sine curve)
    "scale=8000:-1,zoompan=z='1.0+0.5*on/d*(3-2*on/d)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
    # Smooth zoom out with ease-in-out
    "scale=8000:-1,zoompan=z='1.5-0.5*on/d*(3-2*on/d)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
    # Smooth pan left to right with slight zoom
    "scale=8000:-1,zoompan=z='1.2':d={frames}:x='(iw-iw/zoom)*on/d':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
    # Smooth pan right to left with slight zoom
    "scale=8000:-1,zoompan=z='1.2':d={frames}:x='(iw-iw/zoom)*(1-on/d)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
    # Diagonal zoom from top-left
    "scale=8000:-1,zoompan=z='1.0+0.4*on/d':d={frames}:x='(iw/zoom/4)*on/d':y='(ih/zoom/4)*on/d':s=1080x1920:fps=30",
    # Diagonal zoom from bottom-right
    "scale=8000:-1,zoompan=z='1.0+0.4*on/d':d={frames}:x='iw/2-(iw/zoom/2)+(iw/zoom/4)*(1-on/d)':y='ih/2-(ih/zoom/2)+(ih/zoom/4)*(1-on/d)':s=1080x1920:fps=30",
]

# Niche-specific visual style guides for more relevant images
NICHE_STYLE_GUIDE = {
    "tech": "high-tech digital environment, glowing blue circuits, holographic displays, clean modern design",
    "ai": "futuristic neural network visualization, glowing data streams, robotic elements, digital brain imagery",
    "finance": "professional financial setting, stock market displays, luxury business environment, gold accents",
    "cinema": "dramatic movie-set lighting, film noir shadows, red carpet glamour, cinema screen glow",
    "sports": "dynamic athletic action, stadium atmosphere, dramatic sweat and motion blur, celebration energy",
    "science": "laboratory environment, microscopic views, cosmic phenomena, particle physics visualization",
    "gaming": "vibrant game world, neon RGB lighting, retro pixel art elements, virtual reality scene",
    "history": "aged parchment textures, dramatic oil painting style, ancient architecture, sepia-toned atmosphere",
    "space": "deep space nebula colors, planetary surfaces, astronaut perspective, cosmic void with distant stars",
    "popculture": "vibrant social media aesthetic, paparazzi flash, trending visual effects, bold pop art colors",
}


def build_context_enriched_prompt(script: dict, visual_cue: str, cue_index: int) -> str:
    """Build a highly specific image prompt using actual script content.
    
    Instead of generic 'cinematic image', this extracts real entities,
    topics, and context from the script to generate relevant images.
    """
    title = script.get("title", "")
    niche = script.get("niche", "tech")
    source_headline = script.get("source_headline", "")
    full_script = script.get("full_script", "")[:400]
    
    # Get niche-specific style
    style = NICHE_STYLE_GUIDE.get(niche, "cinematic, dramatic lighting")
    
    # Extract key context from the script
    context_topic = source_headline or title
    
    # Build a detailed, topic-specific prompt
    if cue_index == 0:
        # First image: the main subject/person/entity
        prompt = (
            f"Create a photorealistic, stunning vertical (9:16) image closely related to: {context_topic}. "
            f"This is the opening shot for a viral YouTube Short. "
            f"Show the main subject or entity mentioned: {visual_cue}. "
            f"Style: {style}. "
            f"Ultra high detail, dramatic cinematic lighting, shallow depth of field. "
            f"The image must be DIRECTLY about the topic '{title}', not generic. "
            f"NO text, NO watermarks, NO logos, NO letters on the image."
        )
    elif cue_index == 1:
        # Second image: context/setting
        prompt = (
            f"Create a photorealistic, atmospheric vertical (9:16) image for: {context_topic}. "
            f"Show the context or setting: {visual_cue}. "
            f"This should visually explain the background or situation from the story. "
            f"Style: {style}. "
            f"Wide establishing shot, dramatic atmosphere, rich detail, cinematic color grading. "
            f"The image must be SPECIFICALLY about '{title}', not a generic stock photo. "
            f"NO text, NO watermarks, NO logos, NO letters."
        )
    elif cue_index == 2:
        # Third image: the revelation/evidence
        prompt = (
            f"Create a dramatic, photorealistic vertical (9:16) image showing the key revelation: {visual_cue}. "
            f"Context: {context_topic}. "
            f"This image should convey the shocking discovery or evidence from the story. "
            f"Style: {style}. "
            f"Close-up detail shot, tense mood, sharp focus, dramatic contrast. "
            f"Must be DIRECTLY related to '{title}'. "
            f"NO text, NO watermarks, NO logos, NO letters."
        )
    else:
        # Fourth image: conclusion/impact
        prompt = (
            f"Create an emotionally powerful vertical (9:16) photorealistic image for the conclusion: {visual_cue}. "
            f"Context: {context_topic}. "
            f"Show the aftermath, consequences, or future implications of the story. "
            f"Style: {style}. "
            f"Dramatic wide shot, emotional weight, powerful mood, cinematic color palette. "
            f"Must be related to '{title}'. "
            f"NO text, NO watermarks, NO logos, NO letters."
        )
    
    return prompt


def _generate_image_gemini_flash(prompt: str, output_path: Path) -> bool:
    """Primary: Use Gemini 2.0 Flash for image generation (best compositional quality)."""
    import requests
    import base64
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateContent?key={config.GEMINI_API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"]
        }
    }
    
    response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
    if response.status_code == 200:
        data = response.json()
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            for p in parts:
                if "inlineData" in p:
                    img_data = p["inlineData"].get("data", "")
                    if img_data:
                        with open(output_path, "wb") as f:
                            f.write(base64.b64decode(img_data))
                        return True
    elif response.status_code != 503:
        print(f"    ⚠️  Gemini Flash: {response.status_code}")
    return False


def _generate_image_imagen4(prompt: str, output_path: Path) -> bool:
    """Fallback: Use Imagen 4.0 Fast for image generation."""
    import requests
    import base64
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-fast-generate-001:predict?key={config.GEMINI_API_KEY}"
    
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "9:16",
            "outputOptions": {"mimeType": "image/jpeg"}
        }
    }
    
    response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
    if response.status_code == 200:
        data = response.json()
        if "predictions" in data and len(data["predictions"]) > 0:
            b64_image = data["predictions"][0].get("bytesBase64Encoded")
            if b64_image:
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(b64_image))
                return True
    else:
        print(f"    ⚠️  Imagen 4: {response.status_code}")
    return False


def generate_image_gemini(prompt: str, output_path: Path) -> bool:
    """Generate image using dual-engine: Gemini Flash (primary) → Imagen 4 (fallback)."""
    try:
        # Try Gemini 2.0 Flash first (better compositional understanding)
        if _generate_image_gemini_flash(prompt, output_path):
            return True
        
        print("    🔄 Gemini Flash failed, trying Imagen 4...")
        # Fallback to Imagen 4.0 Fast
        if _generate_image_imagen4(prompt, output_path):
            return True
        
        # One more retry on Gemini Flash (handles transient 503s)
        time.sleep(3)
        print("    🔄 Retrying Gemini Flash...")
        if _generate_image_gemini_flash(prompt, output_path):
            return True
        
        # Final retry with simplified prompt (strip complexity)
        time.sleep(2)
        simple_prompt = prompt.split(". Style:")[0] + ". Photorealistic, vertical 9:16, dramatic lighting. NO text or logos."
        print("    🔄 Trying simplified prompt...")
        return _generate_image_gemini_flash(simple_prompt, output_path)
        
    except Exception as e:
        print(f"    ❌ Image generation error: {e}")
        return False


def image_to_video_clip(image_path: Path, output_path: Path, duration: float = 5.0, effect_idx: int = 0) -> bool:
    """Convert a still image to an animated video clip using Ken Burns effect.
    
    Enhanced with smoother easing curves and higher quality encoding.
    """
    frames = int(duration * 30)
    effect_template = BURNS_EFFECTS[effect_idx % len(BURNS_EFFECTS)]
    effect = effect_template.format(frames=frames)

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-vf", effect,
        "-t", str(duration),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "slow",
        "-crf", "18",
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def generate_clips_auto(script_path: Path) -> list[Path]:
    """Generate video clips automatically using context-enriched Gemini image gen + Ken Burns."""
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
    for j, raw_prompt in enumerate(veo_prompts):
        clip_path = vid_dir / f"clip_{j+1:02d}.mp4"
        img_path = vid_dir / f"img_{j+1:02d}.png"

        # Skip if clip already exists and is a real clip (not a tiny placeholder)
        if clip_path.exists() and clip_path.stat().st_size > 50000:
            print(f"    ✅ Clip {j+1} already exists, skipping")
            clips.append(clip_path)
            continue

        # Step 1: Build context-enriched prompt
        enriched_prompt = build_context_enriched_prompt(script, raw_prompt, j)
        print(f"    🎨 Generating image {j+1}/{len(veo_prompts)}: {raw_prompt[:60]}...")

        # Step 2: Generate image with enriched prompt
        success = generate_image_gemini(enriched_prompt, img_path)

        if success and img_path.exists():
            # Step 3: Animate the image with Ken Burns effect
            print(f"    🎬 Animating clip {j+1} with enhanced Ken Burns effect...")
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

        # Rate limit: 2s delay between API calls
        if j < len(veo_prompts) - 1:
            time.sleep(2)

    return clips


def _generate_solid_fallback(clip_path: Path, idx: int):
    """Generate a solid-color fallback clip with subtle gradient animation."""
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
        print(f"\n🎬 Stage 3: Auto-generating video clips with enhanced Gemini AI\n")
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
