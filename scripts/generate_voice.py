"""
Stage 2: Generate voiceover audio from scripts using Edge TTS.
Edge TTS is free, high-quality, and requires no API key.
Outputs MP3 files with timing metadata.
"""

import asyncio
import json
import sys
from pathlib import Path

import edge_tts

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

# High-quality voices ranked by naturalness for shorts
VOICE_OPTIONS = {
    "male_us": "en-US-AndrewNeural",        # Clear, authoritative — best for tech
    "male_us_casual": "en-US-GuyNeural",     # Casual, friendly
    "female_us": "en-US-JennyNeural",        # Clear, professional
    "male_uk": "en-GB-RyanNeural",           # British accent — good for finance
    "female_uk": "en-GB-SoniaNeural",        # British female
    "male_aus": "en-AU-WilliamNeural",       # Australian — stands out
}


async def generate_voice(script_path: Path) -> Path:
    """Generate voiceover MP3 from a script JSON file."""
    script = json.loads(script_path.read_text())
    script_id = script["id"]
    full_text = script["full_script"]

    output_mp3 = config.AUDIO_DIR / f"{script_id}.mp3"
    output_srt = config.AUDIO_DIR / f"{script_id}.srt"

    # Use SubMaker for word-level timing (useful for captions)
    communicate = edge_tts.Communicate(
        text=full_text,
        voice=config.VOICE_NAME,
        rate=config.VOICE_RATE,
        pitch="+0Hz",
    )

    submaker = edge_tts.SubMaker()

    with open(output_mp3, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.feed(chunk)

    # Save SRT subtitles (backup — FFmpeg will also generate captions)
    srt_content = submaker.get_srt()
    output_srt.write_text(srt_content)

    # Update script JSON with audio path
    script["audio_path"] = str(output_mp3)
    script["srt_path"] = str(output_srt)
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
        print(f"  🎙️  Generating voice for {script['id']}: \"{script['title'][:50]}...\"")
        mp3_path = await generate_voice(path)
        print(f"  ✅ Audio saved: {mp3_path.name}")
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

    print(f"\n🎙️  Stage 2: Generating voiceovers (voice: {config.VOICE_NAME})\n")
    results = asyncio.run(generate_all_voices(args.scripts))
    print(f"\n✅ Generated {len(results)} audio files → {config.AUDIO_DIR}/\n")


if __name__ == "__main__":
    main()
