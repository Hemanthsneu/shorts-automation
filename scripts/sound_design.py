"""
Sound Design Engine — Cinematic Audio Layering for Viral Shorts

Generates and layers sound effects using FFmpeg to create a professional
audio experience that matches the emotional arc of each video.

Features:
- Generated sound effects via FFmpeg audio synthesis (no external files needed)
- Emotional arc-based music/SFX timing
- Strategic silence for dramatic pauses
- Bass drops on revelations
- Whoosh transitions between scenes
- Notification/alert sounds for urgency
- Background ambience matching niche
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

# Sound effect durations and FFmpeg generation commands
SFX_LIBRARY = {
    "whoosh": {
        "description": "Quick whoosh transition sound",
        "duration": 0.5,
        "generate_cmd": (
            'anoisesrc=d=0.5:c=pink:r=44100:a=0.3,'
            'afade=t=in:ss=0:d=0.1,'
            'afade=t=out:st=0.3:d=0.2,'
            'highpass=f=2000,lowpass=f=8000,'
            'aecho=0.8:0.7:6:0.5'
        ),
    },
    "bass_drop": {
        "description": "Deep bass drop for revelations",
        "duration": 1.0,
        "generate_cmd": (
            'sine=frequency=60:duration=1:sample_rate=44100,'
            'afade=t=in:ss=0:d=0.05,'
            'afade=t=out:st=0.3:d=0.7,'
            'volume=0.5'
        ),
    },
    "impact": {
        "description": "Sharp impact hit for shocking moments",
        "duration": 0.3,
        "generate_cmd": (
            'anoisesrc=d=0.3:c=white:r=44100:a=0.5,'
            'afade=t=in:ss=0:d=0.01,'
            'afade=t=out:st=0.05:d=0.25,'
            'lowpass=f=200,'
            'volume=0.6'
        ),
    },
    "tension_rise": {
        "description": "Rising tension sound for building suspense",
        "duration": 3.0,
        "generate_cmd": (
            'sine=frequency=200:duration=3:sample_rate=44100,'
            'afade=t=in:ss=0:d=2.5,'
            'afade=t=out:st=2.8:d=0.2,'
            'vibrato=f=5:d=0.5,'
            'volume=0.15'
        ),
    },
    "reveal_sting": {
        "description": "Musical sting for the big reveal moment",
        "duration": 1.5,
        "generate_cmd": (
            'sine=frequency=440:duration=0.3:sample_rate=44100,'
            'afade=t=out:st=0.1:d=0.2[a1];'
            'sine=frequency=554:duration=0.3:sample_rate=44100,'
            'afade=t=out:st=0.1:d=0.2[a2];'
            'sine=frequency=659:duration=0.8:sample_rate=44100,'
            'afade=t=out:st=0.2:d=0.6[a3];'
            '[a1][a2][a3]concat=n=3:v=0:a=1,'
            'volume=0.3'
        ),
    },
    "notification": {
        "description": "Alert/notification sound for urgency",
        "duration": 0.4,
        "generate_cmd": (
            'sine=frequency=880:duration=0.2:sample_rate=44100,'
            'afade=t=out:st=0.1:d=0.1[n1];'
            'sine=frequency=1100:duration=0.2:sample_rate=44100,'
            'afade=t=out:st=0.1:d=0.1[n2];'
            '[n1][n2]concat=n=2:v=0:a=1,'
            'volume=0.25'
        ),
    },
    "dark_ambience": {
        "description": "Low dark ambient pad for serious topics",
        "duration": 10.0,
        "generate_cmd": (
            'sine=frequency=80:duration=10:sample_rate=44100,'
            'tremolo=f=0.5:d=0.3,'
            'afade=t=in:ss=0:d=2,'
            'afade=t=out:st=8:d=2,'
            'volume=0.08'
        ),
    },
    "tech_pulse": {
        "description": "Rhythmic tech pulse for tech/AI content",
        "duration": 10.0,
        "generate_cmd": (
            'sine=frequency=120:duration=10:sample_rate=44100,'
            'tremolo=f=2:d=0.8,'
            'afade=t=in:ss=0:d=1,'
            'afade=t=out:st=8:d=2,'
            'volume=0.06'
        ),
    },
}

# Niche-specific background ambience
NICHE_AMBIENCE = {
    "tech": "tech_pulse",
    "ai": "tech_pulse",
    "finance": "dark_ambience",
    "cinema": "dark_ambience",
    "sports": "tech_pulse",
    "science": "dark_ambience",
    "gaming": "tech_pulse",
    "history": "dark_ambience",
    "space": "dark_ambience",
    "popculture": "tech_pulse",
}


def generate_sfx(sfx_key: str, output_path: Path) -> bool:
    """Generate a sound effect file using FFmpeg audio synthesis."""
    sfx = SFX_LIBRARY.get(sfx_key)
    if not sfx:
        return False

    gen_cmd = sfx["generate_cmd"]

    # Check if it's a complex filter (contains [labels]) or simple
    if '[' in gen_cmd and ']' in gen_cmd:
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", gen_cmd.split('[')[0].split(';')[0].strip(),
        ]
        # For complex multi-source commands, use filter_complex
        parts = gen_cmd.split(';')
        if len(parts) > 1:
            # Multi-source: need multiple inputs
            inputs = []
            filter_parts = []
            input_idx = 0
            for part in parts:
                part = part.strip()
                if part and not part.startswith('['):
                    if any(part.startswith(src) for src in ['sine=', 'anoisesrc=']):
                        inputs.extend(["-f", "lavfi", "-i", part.split('[')[0].strip()])
                        input_idx += 1
                    filter_parts.append(part)
                else:
                    filter_parts.append(part)

            cmd = ["ffmpeg", "-y"] + inputs
            full_filter = ";".join(filter_parts)
            cmd.extend(["-filter_complex", full_filter, "-t", str(sfx["duration"]), str(output_path)])
        else:
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", gen_cmd,
                "-t", str(sfx["duration"]),
                str(output_path),
            ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", gen_cmd,
            "-t", str(sfx["duration"]),
            str(output_path),
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def generate_sfx_simple(sfx_key: str, output_path: Path) -> bool:
    """Simplified SFX generation that avoids complex filter issues."""
    sfx = SFX_LIBRARY.get(sfx_key)
    if not sfx:
        return False

    dur = sfx["duration"]

    generators = {
        "whoosh": f"anoisesrc=d={dur}:c=pink:r=44100:a=0.3,afade=t=in:ss=0:d=0.1,afade=t=out:st={dur-0.2}:d=0.2,highpass=f=2000,lowpass=f=8000",
        "bass_drop": f"sine=frequency=60:duration={dur}:sample_rate=44100,afade=t=in:ss=0:d=0.05,afade=t=out:st=0.3:d=0.7,volume=0.5",
        "impact": f"anoisesrc=d={dur}:c=white:r=44100:a=0.5,afade=t=in:ss=0:d=0.01,afade=t=out:st=0.05:d=0.25,lowpass=f=200,volume=0.6",
        "tension_rise": f"sine=frequency=200:duration={dur}:sample_rate=44100,afade=t=in:ss=0:d=2.5,afade=t=out:st={dur-0.2}:d=0.2,volume=0.15",
        "reveal_sting": f"sine=frequency=523:duration={dur}:sample_rate=44100,afade=t=out:st=0.5:d=1.0,volume=0.3",
        "notification": f"sine=frequency=880:duration={dur}:sample_rate=44100,afade=t=out:st=0.2:d=0.2,volume=0.25",
        "dark_ambience": f"sine=frequency=80:duration={dur}:sample_rate=44100,tremolo=f=0.5:d=0.3,afade=t=in:ss=0:d=2,afade=t=out:st={dur-2}:d=2,volume=0.08",
        "tech_pulse": f"sine=frequency=120:duration={dur}:sample_rate=44100,tremolo=f=2:d=0.8,afade=t=in:ss=0:d=1,afade=t=out:st={dur-2}:d=2,volume=0.06",
    }

    gen_filter = generators.get(sfx_key)
    if not gen_filter:
        return False

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", gen_filter,
        "-t", str(dur),
        "-ar", "44100",
        "-ac", "1",
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def build_sound_design_timeline(script: dict, audio_duration: float) -> list[dict]:
    """Build a timeline of sound effects based on the script's emotional arc."""
    formula_key = script.get("viral_formula_used", "expose")
    niche = script.get("niche", "tech")

    timeline = []

    # 1. Opening impact (0s) — stops the scroll with audio too
    timeline.append({
        "sfx": "impact",
        "time": 0.0,
        "purpose": "scroll_stopper",
    })

    # 2. Whoosh transition at ~3s (hook → build transition)
    timeline.append({
        "sfx": "whoosh",
        "time": 3.0,
        "purpose": "scene_transition",
    })

    # 3. Tension rise before revelation (~18s, builds to ~21s)
    if audio_duration > 25:
        reveal_time = audio_duration * 0.35
        timeline.append({
            "sfx": "tension_rise",
            "time": max(reveal_time - 3, 10),
            "purpose": "build_tension",
        })

    # 4. Bass drop at revelation moment (~20-25s)
    if audio_duration > 25:
        timeline.append({
            "sfx": "bass_drop",
            "time": reveal_time,
            "purpose": "revelation_impact",
        })

    # 5. Whoosh for personal stake transition (~35s)
    if audio_duration > 40:
        timeline.append({
            "sfx": "whoosh",
            "time": audio_duration * 0.65,
            "purpose": "scene_transition",
        })

    # 6. Notification sound for urgency-type formulas
    if formula_key in ["time_bomb", "expose"] and audio_duration > 45:
        timeline.append({
            "sfx": "notification",
            "time": audio_duration * 0.75,
            "purpose": "urgency_alert",
        })

    # 7. Final impact at closer
    if audio_duration > 50:
        timeline.append({
            "sfx": "impact",
            "time": audio_duration - 3,
            "purpose": "closer_emphasis",
        })

    # Sort by time
    timeline.sort(key=lambda x: x["time"])

    return timeline


def render_sound_design(
    script: dict,
    voiceover_path: Path,
    output_path: Path,
    audio_duration: float,
) -> Path:
    """Render the full sound design: voiceover + SFX + ambient background."""
    sid = script["id"]
    niche = script.get("niche", "tech")
    sfx_dir = config.OUTPUT / "sfx"
    sfx_dir.mkdir(exist_ok=True)

    # Build the SFX timeline
    timeline = build_sound_design_timeline(script, audio_duration)
    print(f"    🎵 Sound design: {len(timeline)} SFX events planned")

    # Generate all needed SFX files
    sfx_files = {}
    for event in timeline:
        sfx_key = event["sfx"]
        if sfx_key not in sfx_files:
            sfx_path = sfx_dir / f"{sfx_key}.wav"
            if not sfx_path.exists():
                print(f"    🔊 Generating SFX: {sfx_key}")
                generate_sfx_simple(sfx_key, sfx_path)
            sfx_files[sfx_key] = sfx_path

    # Generate ambient background
    ambience_key = NICHE_AMBIENCE.get(niche, "dark_ambience")
    ambience_path = sfx_dir / f"{ambience_key}_bg.wav"
    if not ambience_path.exists():
        print(f"    🎵 Generating ambient background: {ambience_key}")
        generate_sfx_simple(ambience_key, ambience_path)

    # Build FFmpeg complex filter to mix everything
    inputs = ["-i", str(voiceover_path)]
    input_idx = 1

    # Add ambience as loop
    if ambience_path.exists():
        inputs.extend(["-stream_loop", "-1", "-i", str(ambience_path)])
        ambience_idx = input_idx
        input_idx += 1
    else:
        ambience_idx = None

    # Add each SFX file
    sfx_input_map = {}
    for event in timeline:
        sfx_path = sfx_files.get(event["sfx"])
        if sfx_path and sfx_path.exists():
            if str(sfx_path) not in sfx_input_map:
                inputs.extend(["-i", str(sfx_path)])
                sfx_input_map[str(sfx_path)] = input_idx
                input_idx += 1

    # Build the filter_complex string
    filter_parts = []

    # Voiceover is input [0] — normalize volume
    filter_parts.append(f"[0:a]volume=1.0[voice]")

    # Mix voice with ambience
    if ambience_idx is not None:
        filter_parts.append(f"[{ambience_idx}:a]volume=0.08,atrim=0:{audio_duration + 1}[amb]")
        filter_parts.append(f"[voice][amb]amix=inputs=2:duration=shortest:dropout_transition=2[voiced]")
    else:
        filter_parts.append(f"[voice]acopy[voiced]")

    # Apply each SFX at its timestamp
    current_mix = "voiced"
    for i, event in enumerate(timeline):
        sfx_path = sfx_files.get(event["sfx"])
        if not sfx_path or str(sfx_path) not in sfx_input_map:
            continue

        sfx_idx = sfx_input_map[str(sfx_path)]
        delay_ms = int(event["time"] * 1000)

        filter_parts.append(
            f"[{sfx_idx}:a]adelay={delay_ms}|{delay_ms},volume=0.4[sfx{i}]"
        )
        next_mix = f"mix{i}"
        filter_parts.append(
            f"[{current_mix}][sfx{i}]amix=inputs=2:duration=first:dropout_transition=0[{next_mix}]"
        )
        current_mix = next_mix

    # Final normalization
    filter_parts.append(f"[{current_mix}]loudnorm=I=-14:TP=-1:LRA=11[final]")

    filter_complex = ";\n".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[final]",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-t", str(audio_duration + 0.5),
        str(output_path),
    ]

    print(f"    🎬 Rendering sound design mix...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"    ⚠️  Sound design mix failed, falling back to voiceover only")
        if result.stderr:
            print(f"    FFmpeg: {result.stderr[-200:]}")
        # Fallback: just copy voiceover
        import shutil
        shutil.copy2(str(voiceover_path), str(output_path))

    return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate sound design for scripts")
    parser.add_argument("--scripts", nargs="*", help="Specific script IDs")
    parser.add_argument("--generate-library", action="store_true", help="Pre-generate all SFX")
    args = parser.parse_args()

    if args.generate_library:
        sfx_dir = config.OUTPUT / "sfx"
        sfx_dir.mkdir(exist_ok=True)
        print(f"\n🔊 Generating SFX Library\n")
        for sfx_key in SFX_LIBRARY:
            path = sfx_dir / f"{sfx_key}.wav"
            print(f"  Generating: {sfx_key}...")
            success = generate_sfx_simple(sfx_key, path)
            print(f"  {'✅' if success else '❌'} {sfx_key} → {path.name}")
        return

    if args.scripts:
        paths = [config.SCRIPTS_DIR / f"{sid}.json" for sid in args.scripts]
    else:
        paths = sorted(config.SCRIPTS_DIR.glob("*.json"))

    for path in paths:
        script = json.loads(path.read_text())
        sid = script["id"]
        voice_path = config.AUDIO_DIR / f"{sid}.mp3"
        if not voice_path.exists():
            print(f"  ⏭️  Skipping {sid} — no voiceover")
            continue

        output = config.AUDIO_DIR / f"{sid}_designed.m4a"
        print(f"  🎵 Sound designing {sid}...")
        render_sound_design(script, voice_path, output, 60.0)


if __name__ == "__main__":
    main()
