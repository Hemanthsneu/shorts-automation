"""
Stage 3: Generate voiceover audio from scripts using Edge TTS.

Each video gets a unique voice configuration — voice, rate, and pitch
are deterministically varied per script so no two videos sound alike.
This prevents YouTube's algorithm from fingerprinting the channel as
"same-sounding automated content."

Edge TTS is free, high-quality, and requires no API key.
"""

import asyncio
import hashlib
import json
import sys
from pathlib import Path

import edge_tts

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

VOICE_OPTIONS = {
    "male_us": "en-US-AndrewNeural",
    "male_us_casual": "en-US-GuyNeural",
    "female_us": "en-US-JennyNeural",
    "male_uk": "en-GB-RyanNeural",
    "female_uk": "en-GB-SoniaNeural",
    "male_aus": "en-AU-WilliamNeural",
}

# Rate and pitch variations to make each video sound distinct
RATE_VARIATIONS = ["+5%", "+8%", "+10%", "+12%", "+15%", "+18%", "+6%", "+14%"]
PITCH_VARIATIONS = ["+0Hz", "+1Hz", "-1Hz", "+2Hz", "-2Hz", "+0Hz", "+3Hz", "-3Hz"]


def _get_voice_config(script: dict) -> dict:
    """Deterministically pick a unique voice + rate + pitch per script.

    Uses a hash of the script ID so the same script always gets the same
    voice (reproducible), but different scripts get different voices.
    """
    sid = script.get("id", "default")
    niche = script.get("niche", "tech")
    voice_pool = config.NICHE_VOICES.get(niche, [config.VOICE_NAME])

    digest = int(hashlib.md5(sid.encode()).hexdigest(), 16)

    voice = voice_pool[digest % len(voice_pool)]
    rate = RATE_VARIATIONS[digest % len(RATE_VARIATIONS)]
    pitch = PITCH_VARIATIONS[(digest >> 4) % len(PITCH_VARIATIONS)]

    return {"voice": voice, "rate": rate, "pitch": pitch}


async def generate_voice(script_path: Path) -> Path:
    """Generate voiceover MP3 from a script JSON file."""
    script = json.loads(script_path.read_text())
    script_id = script["id"]
    full_text = script["full_script"]

    output_mp3 = config.AUDIO_DIR / f"{script_id}.mp3"
    output_srt = config.AUDIO_DIR / f"{script_id}.srt"

    voice_cfg = _get_voice_config(script)

    communicate = edge_tts.Communicate(
        text=full_text,
        voice=voice_cfg["voice"],
        rate=voice_cfg["rate"],
        pitch=voice_cfg["pitch"],
    )
    print(f"    Voice: {voice_cfg['voice']}  Rate: {voice_cfg['rate']}  Pitch: {voice_cfg['pitch']}")

    submaker = edge_tts.SubMaker()

    with open(output_mp3, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.feed(chunk)

    srt_content = submaker.get_srt()
    output_srt.write_text(srt_content)

    script["audio_path"] = str(output_mp3)
    script["srt_path"] = str(output_srt)
    script["voice_config"] = voice_cfg
    script_path.write_text(json.dumps(script, indent=2))

    return output_mp3


async def generate_all_voices(script_ids: list[str] = None) -> list[Path]:
    """Generate voice for all scripts or specific IDs."""
    if script_ids:
        paths = [config.SCRIPTS_DIR / f"{sid}.json" for sid in script_ids]
    else:
        paths = sorted(config.SCRIPTS_DIR.glob("*.json"))

    results = []
    for path in paths:
        script = json.loads(path.read_text())
        print(f"  Generating voice for {script['id']}: \"{script['title'][:50]}...\"")
        mp3_path = await generate_voice(path)
        print(f"  Saved: {mp3_path.name}")
        results.append(mp3_path)

    return results


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--scripts", nargs="*", help="Specific script IDs (default: all)")
    parser.add_argument("--voice", default=None, help="Override voice name")
    parser.add_argument("--list-voices", action="store_true")
    args = parser.parse_args()

    if args.list_voices:
        print("\nAvailable voices:")
        for key, voice in VOICE_OPTIONS.items():
            print(f"  {key}: {voice}")
        return

    if args.voice:
        config.VOICE_NAME = args.voice

    print(f"\nStage 3: Generating voiceovers\n")
    results = asyncio.run(generate_all_voices(args.scripts))
    print(f"\nGenerated {len(results)} audio files -> {config.AUDIO_DIR}/\n")


if __name__ == "__main__":
    main()
