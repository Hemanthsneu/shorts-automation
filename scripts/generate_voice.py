"""
Stage 2: Generate voiceover audio from scripts using Edge TTS.

ENHANCED VERSION:
- Sentence-by-sentence generation for precise gap control (no more 1-2s pauses)
- Word-level timing capture for synced captions
- Configurable inter-sentence gaps (default 150ms vs TTS default ~1000ms)
- SSML prosody control for more natural, engaging delivery
"""

import asyncio
import io
import json
import re
import sys
import tempfile
from pathlib import Path

import edge_tts
from pydub import AudioSegment

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


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences, preserving short rhetorical fragments.
    
    Handles edge cases like abbreviations (Dr., Mr., etc.) and numbers ($9.99).
    """
    # Protect common abbreviations from splitting
    protected = text
    abbreviations = ['Dr.', 'Mr.', 'Mrs.', 'Ms.', 'Jr.', 'Sr.', 'vs.', 'etc.', 'U.S.', 'U.K.']
    for abbr in abbreviations:
        protected = protected.replace(abbr, abbr.replace('.', '<DOT>'))
    
    # Protect decimal numbers (e.g., $9.99, 3.5)
    protected = re.sub(r'(\d)\.(\d)', r'\1<DOT>\2', protected)
    
    # Split on sentence-ending punctuation followed by space or end
    parts = re.split(r'(?<=[.!?])\s+', protected)
    
    # Restore protected dots
    sentences = []
    for part in parts:
        restored = part.replace('<DOT>', '.').strip()
        if restored:
            sentences.append(restored)
    
    return sentences


def parse_pacing_markers(sentence: str) -> tuple[str, dict]:
    """Parse [PAUSE X.X] and [EMPHASIS] markers from script text.
    
    Returns clean text and a dict of pacing instructions.
    """
    pacing = {"pause_after_ms": 0, "emphasis": False, "slow": False}
    
    # Extract [PAUSE X.X] markers
    pause_match = re.search(r'\[PAUSE\s+([\d.]+)\]', sentence)
    if pause_match:
        pacing["pause_after_ms"] = int(float(pause_match.group(1)) * 1000)
        sentence = re.sub(r'\[PAUSE\s+[\d.]+\]', '', sentence)
    
    # Extract [EMPHASIS] markers
    if '[EMPHASIS]' in sentence:
        pacing["emphasis"] = True
        sentence = sentence.replace('[EMPHASIS]', '')
    
    # Extract [SLOW] markers
    if '[SLOW]' in sentence:
        pacing["slow"] = True
        sentence = sentence.replace('[SLOW]', '')
    
    return sentence.strip(), pacing


async def generate_sentence_audio(
    text: str, 
    voice: str, 
    rate: str, 
    pitch: str,
    pacing: dict = None
) -> tuple[AudioSegment, list[dict]]:
    """Generate audio for a single sentence and capture word-level timing.
    
    Returns (AudioSegment, list of word timing events).
    """
    # Adjust rate/pitch based on pacing markers
    effective_rate = rate
    effective_pitch = pitch
    if pacing:
        if pacing.get("emphasis"):
            # Slightly slower and deeper for emphasis
            effective_rate = "+10%"
            effective_pitch = "+0Hz"
        elif pacing.get("slow"):
            effective_rate = "+5%"
    
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=effective_rate,
        pitch=effective_pitch,
    )
    
    submaker = edge_tts.SubMaker()
    audio_bytes = io.BytesIO()
    word_events = []
    
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes.write(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            submaker.feed(chunk)
            word_events.append({
                "text": chunk.get("text", ""),
                "offset": chunk.get("offset", 0),
                "duration": chunk.get("duration", 0),
            })
    
    audio_bytes.seek(0)
    
    # Load as pydub AudioSegment
    try:
        segment = AudioSegment.from_mp3(audio_bytes)
    except Exception:
        # Fallback: save to temp file and load
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(audio_bytes.getvalue())
            tmp_path = tmp.name
        segment = AudioSegment.from_mp3(tmp_path)
        Path(tmp_path).unlink(missing_ok=True)
    
    return segment, word_events


def build_word_synced_srt(all_word_events: list[dict], words_per_group: int = 4) -> str:
    """Build SRT with consistent word groups using actual word timing data.
    
    Groups words into chunks of `words_per_group` for readable captions
    that stay on screen long enough to read but don't linger.
    """
    if not all_word_events:
        return ""
    
    srt_entries = []
    entry_num = 1
    
    for i in range(0, len(all_word_events), words_per_group):
        group = all_word_events[i:i + words_per_group]
        if not group:
            continue
        
        start_ms = group[0]["abs_offset_ms"]
        # End time = last word start + its duration + small buffer
        end_ms = group[-1]["abs_offset_ms"] + group[-1]["duration_ms"] + 100
        
        text = " ".join(w["text"] for w in group if w.get("text"))
        if not text.strip():
            continue
        
        srt_entries.append(
            f"{entry_num}\n"
            f"{_ms_to_srt_time(start_ms)} --> {_ms_to_srt_time(end_ms)}\n"
            f"{text}"
        )
        entry_num += 1
    
    return "\n\n".join(srt_entries) + "\n"


def _ms_to_srt_time(ms: int) -> str:
    """Convert milliseconds to SRT timestamp format (HH:MM:SS,mmm)."""
    if ms < 0:
        ms = 0
    hours = ms // 3_600_000
    ms %= 3_600_000
    minutes = ms // 60_000
    ms %= 60_000
    seconds = ms // 1_000
    millis = ms % 1_000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


async def generate_voice(script_path: Path) -> Path:
    """Generate voiceover MP3 from a script JSON file.
    
    Enhanced: generates per-sentence audio with controlled gaps,
    captures word-level timing for synced captions.
    """
    import random

    script = json.loads(script_path.read_text())
    script_id = script["id"]
    full_text = script["full_script"]

    output_mp3 = config.AUDIO_DIR / f"{script_id}.mp3"
    output_srt = config.AUDIO_DIR / f"{script_id}.srt"
    output_timing = config.AUDIO_DIR / f"{script_id}_timing.json"

    # Pick a niche-specific voice (rotate to avoid algorithm fingerprinting)
    niche = script.get("niche", "tech")
    voice_pool = config.NICHE_VOICES.get(niche, [config.VOICE_NAME])
    selected_voice = random.choice(voice_pool)
    
    print(f"    🗣️  Voice: {selected_voice} (from {niche} pool)")
    print(f"    ⚡ Rate: {config.VOICE_RATE} | Pitch: {config.VOICE_PITCH} | Gap: {config.INTER_SENTENCE_GAP_MS}ms")

    # Split into sentences
    sentences = split_into_sentences(full_text)
    print(f"    📝 Split into {len(sentences)} sentences for precise gap control")

    # Generate audio for each sentence
    combined_audio = AudioSegment.empty()
    all_word_events = []
    current_offset_ms = 0
    
    for idx, raw_sentence in enumerate(sentences):
        # Parse pacing markers
        clean_sentence, pacing = parse_pacing_markers(raw_sentence)
        if not clean_sentence:
            continue
        
        # Generate audio for this sentence
        segment, word_events = await generate_sentence_audio(
            clean_sentence, 
            selected_voice, 
            config.VOICE_RATE, 
            config.VOICE_PITCH,
            pacing
        )
        
        # Adjust word timing to absolute position in the combined audio
        if word_events:
            for we in word_events:
                # Edge TTS offsets are in 100-nanosecond units (ticks)
                raw_offset = we["offset"]
                raw_duration = we["duration"]
                word_offset_ms = raw_offset // 10_000 if raw_offset > 10_000 else raw_offset
                word_duration_ms = raw_duration // 10_000 if raw_duration > 10_000 else raw_duration
                
                all_word_events.append({
                    "text": we["text"],
                    "abs_offset_ms": current_offset_ms + word_offset_ms,
                    "duration_ms": max(word_duration_ms, 100),
                    "sentence_idx": idx,
                })
        else:
            # Fallback: estimate word timing from audio duration
            words = clean_sentence.split()
            if words:
                segment_ms = len(segment)
                ms_per_word = segment_ms / len(words)
                for w_idx, word in enumerate(words):
                    all_word_events.append({
                        "text": word,
                        "abs_offset_ms": current_offset_ms + int(w_idx * ms_per_word),
                        "duration_ms": max(int(ms_per_word * 0.9), 100),
                        "sentence_idx": idx,
                    })
        
        # Append audio segment
        combined_audio += segment
        current_offset_ms += len(segment)
        
        # Add controlled gap between sentences (not after the last one)
        if idx < len(sentences) - 1:
            # Use pacing marker pause if specified, otherwise default gap
            pause_ms = pacing.get("pause_after_ms", 0) or config.INTER_SENTENCE_GAP_MS
            combined_audio += AudioSegment.silent(duration=pause_ms)
            current_offset_ms += pause_ms

    # Export combined audio
    combined_audio.export(str(output_mp3), format="mp3", bitrate="192k")
    
    # Build word-synced SRT captions
    srt_content = build_word_synced_srt(
        all_word_events, 
        words_per_group=config.WORDS_PER_CAPTION_GROUP
    )
    output_srt.write_text(srt_content, encoding="utf-8")
    
    # Save word timing data for assembly stage
    output_timing.write_text(json.dumps(all_word_events, indent=2))

    # Update script JSON with audio path
    script["audio_path"] = str(output_mp3)
    script["srt_path"] = str(output_srt)
    script["word_timing_path"] = str(output_timing)
    script["audio_duration_ms"] = len(combined_audio)
    script["sentence_count"] = len(sentences)
    script_path.write_text(json.dumps(script, indent=2))
    
    duration_sec = len(combined_audio) / 1000
    print(f"    ✅ Audio: {duration_sec:.1f}s | {len(all_word_events)} words tracked | {len(sentences)} sentences")

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
