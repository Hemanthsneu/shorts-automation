"""
Pro Caption Engine — TikTok-Style Word-by-Word Animated Captions

Generates dynamic ASS (Advanced SubStation Alpha) subtitle files that create
the animated word-by-word caption effect seen in viral TikTok/Shorts content.

Features:
- Word-by-word pop-in animation
- Key word highlighting in accent color
- Multiple style presets (pop, dramatic, news ticker)
- Emotion-based color shifts
- Strategic emphasis on power words
- Clean, readable formatting optimized for 9:16
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from scripts.viral_engine import HOOK_POWER_WORDS, CAPTION_STYLES


# Power words that should be highlighted in accent color
HIGHLIGHT_WORDS = set()
for category_words in HOOK_POWER_WORDS.values():
    HIGHLIGHT_WORDS.update(w.lower() for w in category_words)

# Additional highlight triggers
HIGHLIGHT_WORDS.update([
    "million", "billion", "trillion", "thousand", "hundred",
    "never", "always", "every", "nobody", "everyone",
    "secret", "hidden", "banned", "leaked", "exposed",
    "dead", "killed", "destroyed", "crashed", "fired",
    "impossible", "insane", "shocking", "terrifying",
    "money", "dollars", "profit", "loss", "scam", "fraud",
])

# Number pattern — any token with digits gets highlighted
NUMBER_PATTERN = re.compile(r'\d')

ASS_HEADER_TEMPLATE = """[Script Info]
Title: Viral Shorts Captions
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{fontsize},{primary_color},&H000000FF,{outline_color},{back_color},-1,0,0,0,100,100,0,0,{border_style},{outline},{shadow},{alignment},40,40,{margin_v},1
Style: Highlight,{font},{fontsize},{highlight_color},&H000000FF,{highlight_outline},{back_color},-1,0,0,0,100,100,0,0,{border_style},{outline},{shadow},{alignment},40,40,{margin_v},1
Style: Emphasis,{font},{emphasis_size},{emphasis_color},&H000000FF,{outline_color},{back_color},-1,0,0,0,100,100,0,0,{border_style},{outline},{shadow},{alignment},40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _format_ass_time(seconds: float) -> str:
    """Convert seconds to ASS timestamp format (H:MM:SS.CC)."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _should_highlight(word: str) -> bool:
    """Determine if a word should be highlighted (accent color)."""
    clean = word.lower().strip(".,!?;:'\"()-")
    if clean in HIGHLIGHT_WORDS:
        return True
    if NUMBER_PATTERN.search(word):
        return True
    if word.isupper() and len(word) > 2:
        return True
    return False


def _should_emphasize(word: str) -> bool:
    """Determine if a word should get extra emphasis (larger size)."""
    clean = word.lower().strip(".,!?;:'\"()-")
    strong_emphasis = {"exposed", "leaked", "destroyed", "killed", "banned",
                       "impossible", "insane", "shocking", "terrifying", "scam",
                       "fraud", "never", "dead", "secret"}
    return clean in strong_emphasis


def parse_srt_to_word_timings(srt_path: Path) -> list[dict]:
    """Parse SRT file and extract word-level timings from Edge TTS output."""
    if not srt_path.exists():
        return []

    content = srt_path.read_text(encoding="utf-8")
    entries = []

    blocks = content.strip().split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue

        time_line = lines[1]
        text = " ".join(lines[2:])

        match = re.match(r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})', time_line)
        if not match:
            continue

        start_s = int(match.group(1)) * 3600 + int(match.group(2)) * 60 + int(match.group(3)) + int(match.group(4)) / 1000
        end_s = int(match.group(5)) * 3600 + int(match.group(6)) * 60 + int(match.group(7)) + int(match.group(8)) / 1000

        words = text.split()
        if not words:
            continue

        word_duration = (end_s - start_s) / len(words)
        for i, word in enumerate(words):
            entries.append({
                "word": word,
                "start": start_s + (i * word_duration),
                "end": start_s + ((i + 1) * word_duration),
            })

    return entries


def generate_word_timings_from_script(script: dict, total_duration: float) -> list[dict]:
    """Generate approximate word timings from the script text when SRT isn't available."""
    full_text = script.get("full_script", "")
    words = full_text.split()
    if not words:
        return []

    # Estimate timing based on ~2.5 words per second (natural speech with emphasis)
    avg_word_duration = total_duration / len(words)

    entries = []
    current_time = 0.1
    for word in words:
        duration = avg_word_duration
        # Slightly longer pause after sentence-ending punctuation
        if word.endswith(('.', '!', '?')):
            duration *= 1.3
        # Slightly longer for emphasized words
        if _should_emphasize(word):
            duration *= 1.2

        entries.append({
            "word": word,
            "start": current_time,
            "end": current_time + duration,
        })
        current_time += duration

    return entries


def generate_ass_captions(
    script: dict,
    srt_path: Path,
    output_path: Path,
    style_key: str = "tiktok_pop",
    total_duration: float = 60.0,
) -> Path:
    """Generate ASS subtitle file with animated word-by-word captions."""

    style = CAPTION_STYLES.get(style_key, CAPTION_STYLES["tiktok_pop"])

    # Get word timings
    word_timings = parse_srt_to_word_timings(srt_path)
    if not word_timings:
        word_timings = generate_word_timings_from_script(script, total_duration)

    if not word_timings:
        print(f"    ⚠️  No word timings available for captions")
        return None

    # Style configuration
    font = style.get("font", "Montserrat-ExtraBold")
    font_map = {
        "Montserrat-ExtraBold": "Montserrat ExtraBold",
        "Arial-Black": "Arial Black",
        "Impact": "Impact",
    }
    font_name = font_map.get(font, font)

    words_per_group = style.get("words_per_frame", 2)
    position = style.get("position", "center")

    alignment = 5 if position == "center" else 2
    margin_v = 850 if position == "center" else 180

    fontsize = 72
    emphasis_size = 84
    if position == "bottom":
        fontsize = 56
        emphasis_size = 64

    primary_color = style.get("primary_color", "&H00FFFFFF")
    highlight_color = style.get("highlight_color", "&H0000FFFF")
    outline_color = "&H00000000"
    back_color = "&H80000000"
    highlight_outline = "&H00000000"
    emphasis_color = highlight_color

    header = ASS_HEADER_TEMPLATE.format(
        font=font_name,
        fontsize=fontsize,
        emphasis_size=emphasis_size,
        primary_color=primary_color,
        highlight_color=highlight_color,
        emphasis_color=emphasis_color,
        outline_color=outline_color,
        back_color=back_color,
        highlight_outline=highlight_outline,
        border_style=3,
        outline=3,
        shadow=1,
        alignment=alignment,
        margin_v=margin_v,
    )

    events = []

    # Group words for display
    groups = []
    current_group = []
    for wt in word_timings:
        current_group.append(wt)
        is_sentence_end = wt["word"].rstrip().endswith(('.', '!', '?'))

        if len(current_group) >= words_per_group or is_sentence_end:
            groups.append(current_group)
            current_group = []

    if current_group:
        groups.append(current_group)

    for group in groups:
        start_time = group[0]["start"]
        end_time = group[-1]["end"]

        # Build styled text for the group
        styled_parts = []
        for wt in group:
            word = wt["word"]
            if _should_emphasize(word):
                styled_parts.append(f"{{\\rEmphasis}}{word}{{\\rDefault}}")
            elif _should_highlight(word):
                styled_parts.append(f"{{\\rHighlight}}{word}{{\\rDefault}}")
            else:
                styled_parts.append(word)

        display_text = " ".join(styled_parts)

        # Add pop-in animation effect
        anim_style = style.get("animation", "pop_in")
        if anim_style == "pop_in":
            fade_ms = 80
            display_text = f"{{\\fad({fade_ms},0)\\fscx120\\fscy120\\t(0,{fade_ms},\\fscx100\\fscy100)}}" + display_text
        elif anim_style == "fade_in":
            display_text = f"{{\\fad(150,50)}}" + display_text
        elif anim_style == "slide_in":
            display_text = f"{{\\fad(100,0)\\move(0,20,0,0,0,100)}}" + display_text

        start_str = _format_ass_time(start_time)
        end_str = _format_ass_time(end_time)

        events.append(
            f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{display_text}"
        )

    ass_content = header + "\n".join(events) + "\n"
    output_path.write_text(ass_content, encoding="utf-8")

    print(f"    ✅ Generated {len(events)} caption groups → {output_path.name}")
    return output_path


def generate_captions_for_script(script_id: str) -> Path:
    """Generate pro captions for a single script."""
    script_path = config.SCRIPTS_DIR / f"{script_id}.json"
    if not script_path.exists():
        return None

    script = json.loads(script_path.read_text())
    srt_path = config.AUDIO_DIR / f"{script_id}.srt"
    ass_path = config.AUDIO_DIR / f"{script_id}.ass"

    # Get caption style from script (set by viral engine) or default
    caption_config = script.get("caption_config", {})
    style_key = caption_config.get("style_key", "tiktok_pop")

    duration = script.get("assembled_duration", 60.0)

    return generate_ass_captions(script, srt_path, ass_path, style_key, duration)


def generate_all_captions(script_ids: list[str] = None) -> list[Path]:
    """Generate pro captions for all scripts."""
    if script_ids:
        paths = [config.SCRIPTS_DIR / f"{sid}.json" for sid in script_ids]
    else:
        paths = sorted(config.SCRIPTS_DIR.glob("*.json"))

    results = []
    for path in paths:
        script = json.loads(path.read_text())
        sid = script["id"]
        print(f"  📝 Generating pro captions for {sid}...")
        ass_path = generate_captions_for_script(sid)
        if ass_path:
            results.append(ass_path)

    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate pro animated captions")
    parser.add_argument("--scripts", nargs="*", help="Specific script IDs")
    args = parser.parse_args()

    print(f"\n📝 Generating Pro Captions\n")
    results = generate_all_captions(args.scripts)
    print(f"\n✅ Generated {len(results)} caption files\n")


if __name__ == "__main__":
    main()
