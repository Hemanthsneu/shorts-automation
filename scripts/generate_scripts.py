"""
Stage 1: Generate Viral Short-Form Scripts Using Gemini + Viral Intelligence Engine

This is the brain of the pipeline. It combines:
- Real-time trending data (Google Trends + RSS)
- Viral psychology patterns (from viral_engine.py)
- Proven hook formulas and emotional arc structures
- Virality pre-scoring and automatic improvement
- SEO-first title strategy with named entity requirement

The goal: Every script that exits this stage has a realistic shot at 100K+ views.
"""

import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path

import google.generativeai as genai

sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from scripts.topic_history import load_history, add_topic, get_used_titles, get_used_headlines, migrate_from_content_log
from scripts.viral_engine import (
    VIRAL_FORMULAS,
    HOOK_POWER_WORDS,
    TITLE_FORMULAS,
    POWER_ADJECTIVES,
    POWER_VERBS,
    ENGAGEMENT_DRIVERS,
    RETENTION_STRATEGIES,
    build_viral_prompt_context,
    select_viral_formula,
    get_caption_style,
)

# ── Niche → RSS feeds mapping ──
NICHE_RSS_FEEDS = {
    "tech": [
        "https://news.google.com/rss/search?q=technology+trending+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://www.theverge.com/rss/index.xml",
        "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "https://news.google.com/rss/search?q=Apple+OR+Google+OR+Microsoft+OR+Samsung+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
    "ai": [
        "https://news.google.com/rss/search?q=artificial+intelligence+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=ChatGPT+OR+OpenAI+OR+Gemini+AI+OR+Claude+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=AI+scandal+OR+AI+danger+OR+AI+breakthrough+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
    "finance": [
        "https://news.google.com/rss/search?q=stock+market+crash+OR+cryptocurrency+scandal+OR+economy+crisis+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=Bitcoin+OR+Tesla+stock+OR+Wall+Street+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
    "cinema": [
        "https://news.google.com/rss/search?q=movies+box+office+OR+Hollywood+scandal+OR+Netflix+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=celebrity+drama+OR+actor+controversy+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
    "sports": [
        "https://news.google.com/rss/search?q=NFL+OR+NBA+OR+UFC+OR+soccer+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=sports+controversy+OR+athlete+scandal+OR+trade+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=LeBron+OR+Messi+OR+Mahomes+OR+boxing+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
    "science": [
        "https://news.google.com/rss/search?q=science+discovery+OR+breakthrough+OR+shocking+study+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
    "gaming": [
        "https://news.google.com/rss/search?q=gaming+news+OR+PlayStation+OR+Xbox+OR+Nintendo+controversy+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=GTA+OR+Fortnite+OR+gaming+scandal+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
    "history": [
        "https://news.google.com/rss/search?q=history+discovery+OR+archaeological+find+OR+ancient+secret+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
    "space": [
        "https://news.google.com/rss/search?q=NASA+OR+SpaceX+OR+space+discovery+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
    "popculture": [
        "https://news.google.com/rss/search?q=viral+celebrity+OR+influencer+drama+OR+trending+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=TikTok+OR+Instagram+OR+YouTube+drama+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
}

NICHE_YT_CATEGORIES = {
    "tech": "28", "ai": "28", "finance": "25", "cinema": "24",
    "sports": "17", "science": "28", "gaming": "20", "history": "27",
    "space": "28", "popculture": "24",
}


def fetch_rss_headlines(niche: str, max_headlines: int = 20) -> list[str]:
    """Fetch real headlines from RSS news feeds for the given niche."""
    import feedparser

    feeds = NICHE_RSS_FEEDS.get(niche, [
        f"https://news.google.com/rss/search?q={niche}+trending+when:1d&hl=en-US&gl=US&ceid=US:en",
    ])

    headlines = []
    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                title = entry.get("title", "").strip()
                if " - " in title:
                    title = title.rsplit(" - ", 1)[0].strip()
                if title and len(title) > 15:
                    headlines.append(title)
        except Exception:
            continue

    headlines = list(set(headlines))
    random.shuffle(headlines)
    return headlines[:max_headlines]


def fetch_google_trends_rss(max_results: int = 15) -> list[str]:
    """Fetch currently trending searches from Google Trends RSS."""
    import feedparser

    try:
        url = "https://trends.google.com/trending/rss?geo=US"
        feed = feedparser.parse(url)

        topics = []
        for entry in feed.entries[:max_results]:
            title = entry.get("title", "").strip()
            if title and len(title) > 2:
                topics.append(title)
        return topics
    except Exception as e:
        print(f"    ⚠️  Google Trends RSS failed: {e}")
        return []


def fact_check_topics(topics: list[str], model) -> list[str]:
    """Reject hallucinated/unverifiable topics — critical quality gate."""
    if not topics:
        return topics

    prompt = f"""You are a strict fact-checker. For each headline below, determine if it describes
a REAL, VERIFIABLE event, person, or company that actually exists.

Rules:
- If the headline mentions a real person, company, or event you can confirm → KEEP
- If the headline seems plausible but you are NOT 100% certain it really happened → REJECT
- If the headline uses names/products/projects you've never heard of → REJECT
- If it's about a real ongoing trend or debate → KEEP

HEADLINES:
{chr(10).join(f'{i+1}. {h}' for i, h in enumerate(topics))}

Return ONLY a JSON array of objects. No markdown, no code fences.
Format: [{{"headline": "exact headline text", "verdict": "KEEP" or "REJECT", "reason": "brief reason"}}]"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

        results = json.loads(text)
        kept = []
        for r in results:
            if isinstance(r, dict) and r.get("verdict", "").upper() == "KEEP":
                kept.append(r["headline"])
            else:
                reason = r.get("reason", "unknown") if isinstance(r, dict) else "parse error"
                headline = r.get("headline", "?") if isinstance(r, dict) else "?"
                print(f"    🚫 REJECTED: {headline[:50]}... — {reason}")
        return kept
    except Exception as e:
        print(f"    ⚠️  Fact-check gate failed: {e} — passing all topics through")
        return topics


def discover_trending_topics(niche: str, count: int) -> list[str]:
    """Pull VERIFIED real trending data from Google Trends + RSS only."""
    print(f"  🔍 Fetching VERIFIED trending data for '{niche}'...")

    migrate_from_content_log()

    google_trends = fetch_google_trends_rss(max_results=15)
    print(f"    📈 Found {len(google_trends)} Google Trends topics")

    rss_headlines = fetch_rss_headlines(niche, max_headlines=25)
    print(f"    📰 Found {len(rss_headlines)} verified news headlines")

    all_real_data = google_trends + rss_headlines

    if not all_real_data:
        print(f"  ⚠️  No real-time data found, falling back to curated pool")
        return None

    used_titles = get_used_titles(limit=100)
    used_headlines = get_used_headlines(limit=100)
    used_set = set(t.lower() for t in used_titles + used_headlines)

    before_count = len(all_real_data)
    all_real_data = [h for h in all_real_data if h.lower() not in used_set]
    deduped = before_count - len(all_real_data)
    if deduped > 0:
        print(f"    🔄 Deduped {deduped} previously used topics")

    if not all_real_data:
        print(f"  ⚠️  All topics were duplicates, falling back to curated pool")
        return None

    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    today = datetime.now().strftime("%B %d, %Y")

    used_context = ""
    if used_titles:
        recent_used = used_titles[-20:]
        used_context = f"\n\nALREADY USED TITLES (avoid similar topics):\n" + chr(10).join(f'- {t}' for t in recent_used)

    prompt = f"""Today is {today}. You are a YouTube Shorts viral strategist specializing in predicting
which topics will explode on short-form video.

Score each headline below from 1-10 for VIRAL POTENTIAL as a 60-second YouTube Short.

SCORING CRITERIA (what gets 8-10):
- Controversy, scandal, or exposé involving a NAMED person/company
- Celebrity/public figure drama or secrets revealed
- Shocking statistics with SPECIFIC numbers that affect millions
- Breaking news that people are ACTIVELY searching for RIGHT NOW
- Stories that trigger strong emotions (outrage, shock, fear, amazement)
- Topics with a clear debate angle (viewers will want to comment)
- Content that makes someone stop scrolling in 0.5 seconds
- Stories where the viewer thinks "I NEED to share this"

WHAT SCORES LOW (1-5):
- Generic corporate news, quarterly earnings, routine stock movements
- Boring policy updates, routine announcements
- Stories without a NAMED person or company
- Old news or topics with no active debate
- Topics too niche for a general audience
- Any topic that does NOT have a clear emotional hook

VIRAL FORMULA MATCH — Also identify which viral formula works best:
- EXPOSÉ: Revealing hidden truth about well-known entity
- IMPOSSIBLE_FACT: A fact so shocking it seems impossible
- TIME_BOMB: Something happening NOW that affects everyone
- CONSPIRACY: Real facts that imply something bigger
- UNDERDOG: Against-all-odds success story
- VS_BATTLE: Two sides, clear winner
- MYTH_BUSTER: Destroying a common belief
- COUNTDOWN: Multiple shocking reveals

CRITICAL: A headline MUST contain at least one recognizable NAMED entity to score above 7.
{used_context}

HEADLINES TO SCORE:
{chr(10).join(f'{i+1}. {h}' for i, h in enumerate(all_real_data))}

Return ONLY a JSON array of objects. No markdown, no code fences.
Format: [{{"headline": "exact headline text", "score": 8, "angle": "the viral angle in 10 words", "named_entity": "the main person/company", "best_formula": "expose|impossible_fact|time_bomb|conspiracy|underdog|vs_battle|myth_buster|countdown", "emotional_hook": "the primary emotion this triggers"}}]

Return ALL headlines with their scores. I will filter by score >= 8."""

    try:
        print(f"  🔥 Running viral potential scoring on {len(all_real_data)} headlines...")
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

        scored = json.loads(text)
        if isinstance(scored, list):
            hot_topics = [s for s in scored if isinstance(s, dict) and s.get("score", 0) >= 8]
            hot_topics.sort(key=lambda x: x.get("score", 0), reverse=True)

            if hot_topics:
                candidates = hot_topics[:count * 2]
                for p in candidates:
                    print(f"    🔥 [{p.get('score', '?')}/10] {p.get('headline', '?')[:60]}...")
                    print(f"       Formula: {p.get('best_formula', 'N/A')} | Emotion: {p.get('emotional_hook', 'N/A')}")

                candidate_headlines = [p["headline"] for p in candidates]
                verified = fact_check_topics(candidate_headlines, model)
                print(f"    ✅ Fact-check passed: {len(verified)}/{len(candidate_headlines)}")

                if verified:
                    # Return with metadata for viral engine
                    result_topics = []
                    for headline in verified[:count]:
                        metadata = next((s for s in candidates if s["headline"] == headline), {})
                        result_topics.append({
                            "headline": headline,
                            "score": metadata.get("score", 8),
                            "formula": metadata.get("best_formula", "expose"),
                            "emotion": metadata.get("emotional_hook", "shock"),
                            "entity": metadata.get("named_entity", ""),
                            "angle": metadata.get("angle", ""),
                        })
                    return result_topics

            # Fallback to 7+ threshold
            print(f"  ⚠️  No headlines scored 8+, trying 7+...")
            ok_topics = [s for s in scored if isinstance(s, dict) and s.get("score", 0) >= 7]
            ok_topics.sort(key=lambda x: x.get("score", 0), reverse=True)
            if ok_topics:
                candidate_headlines = [p["headline"] for p in ok_topics[:count * 2]]
                verified = fact_check_topics(candidate_headlines, model)
                if verified:
                    result_topics = []
                    for headline in verified[:count]:
                        metadata = next((s for s in ok_topics if s["headline"] == headline), {})
                        result_topics.append({
                            "headline": headline,
                            "score": metadata.get("score", 7),
                            "formula": metadata.get("best_formula", "expose"),
                            "emotion": metadata.get("emotional_hook", "curiosity"),
                            "entity": metadata.get("named_entity", ""),
                            "angle": metadata.get("angle", ""),
                        })
                    return result_topics

            # Last resort
            print(f"  ⚠️  No fact-checked topics, picking top scored")
            scored.sort(key=lambda x: x.get("score", 0), reverse=True)
            picked = scored[:count]
            return [{"headline": p.get("headline", ""), "score": p.get("score", 5),
                      "formula": p.get("best_formula", "expose"), "emotion": "curiosity",
                      "entity": p.get("named_entity", ""), "angle": p.get("angle", "")}
                     for p in picked]
    except Exception as e:
        print(f"  ⚠️  Controversy scoring failed: {e}")

    # Fallback: raw headlines without metadata
    sample = random.sample(all_real_data, min(count, len(all_real_data)))
    return [{"headline": h, "score": 5, "formula": "expose", "emotion": "curiosity",
             "entity": "", "angle": ""} for h in sample]


def generate_scripts(niche: str, count: int, batch_id: str) -> list[dict]:
    """Generate viral scripts powered by the Viral Intelligence Engine."""
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    niche_cfg = config.NICHE_CONFIG[niche]

    # Discover trending topics with viral metadata
    trending_data = discover_trending_topics(niche, count)
    if trending_data and isinstance(trending_data, list) and isinstance(trending_data[0], dict):
        topics_with_meta = trending_data
        trending_source = "real_time_trending"
    elif trending_data and isinstance(trending_data, list):
        topics_with_meta = [{"headline": t, "score": 5, "formula": "expose",
                             "emotion": "curiosity", "entity": "", "angle": ""}
                            for t in trending_data]
        trending_source = "real_time_trending"
    else:
        raw_topics = random.sample(niche_cfg["topics_pool"], min(count, len(niche_cfg["topics_pool"])))
        topics_with_meta = [{"headline": t, "score": 5, "formula": "impossible_fact",
                             "emotion": "amazement", "entity": "", "angle": ""}
                            for t in raw_topics]
        trending_source = "curated_pool"

    today = datetime.now().strftime("%B %d, %Y")
    used_titles = get_used_titles(limit=30)
    dedup_context = ""
    if used_titles:
        dedup_context = f"\n\n🚫 ALREADY USED TITLES (DO NOT repeat these):\n" + chr(10).join(f'- {t}' for t in used_titles[-15:])

    niche_hashtags = niche_cfg['hashtags'][:6]

    # Build per-headline viral context
    headlines_with_context = []
    for tm in topics_with_meta:
        viral_ctx = build_viral_prompt_context(niche, tm["headline"])
        formula = viral_ctx["formula"]
        arc = viral_ctx["emotional_arc"]

        headlines_with_context.append({
            "headline": tm["headline"],
            "recommended_formula": formula["name"],
            "formula_key": formula["formula_key"],
            "structure": formula["structure"],
            "hook_templates": formula["hook_templates"][:2],
            "emotional_arc": arc["description"],
            "intensity_curve": arc["intensity_curve"],
            "voice_modulation": arc.get("voice_modulation", []),
            "named_entity": tm.get("entity", ""),
            "viral_angle": tm.get("angle", ""),
            "primary_emotion": tm.get("emotion", "shock"),
        })

    # Build the mega-prompt with viral intelligence
    headlines_block = json.dumps(headlines_with_context, indent=2)

    retention_guide = "\n".join([
        f"  {ts}: {strat['goal']} — {strat['tactics'][0]}"
        for ts, strat in RETENTION_STRATEGIES.items()
    ])

    engagement_comment_triggers = ", ".join(ENGAGEMENT_DRIVERS["comment_triggers"][:4])
    engagement_share_triggers = ", ".join(ENGAGEMENT_DRIVERS["share_triggers"][:3])

    title_formula_examples = "\n".join(f"  - {f}" for f in random.sample(TITLE_FORMULAS, 4))
    power_adj = ", ".join(random.sample(POWER_ADJECTIVES, 6))
    power_vrb = ", ".join(random.sample(POWER_VERBS, 6))

    prompt = f"""{niche_cfg['system_prompt']}

Today is {today}. Generate exactly {count} YouTube Shorts scripts that are ENGINEERED to go viral.
Return ONLY valid JSON — no markdown, no code fences.

═══════════════════════════════════════════════
VIRAL INTELLIGENCE BRIEFING (Study this carefully)
═══════════════════════════════════════════════

HEADLINES WITH VIRAL FORMULAS (use the recommended formula for each):
{headlines_block}

For each headline, a viral formula has been pre-selected. Follow its structure:
- Each formula has a specific 5-part structure (see "structure" field)
- Follow the emotional arc's intensity curve for pacing
- Use the voice_modulation hints for tone shifts

═══════════════════════════════════════════════
RETENTION OPTIMIZATION (prevent viewer drop-off)
═══════════════════════════════════════════════
{retention_guide}

═══════════════════════════════════════════════
ENGAGEMENT ENGINEERING
═══════════════════════════════════════════════
COMMENT TRIGGERS to use: {engagement_comment_triggers}
SHARE TRIGGERS to use: {engagement_share_triggers}
The outro MUST use one of these comment trigger patterns:
- DIVISIVE QUESTION: "Was {'{entity}'} justified, or did they go too far?"
- HOT TAKE: Make a bold claim that forces agreement/disagreement
- PREDICTION: "I think {'{X}'} will happen within {'{time}'}. Prove me wrong."

═══════════════════════════════════════════════
TITLE ENGINEERING (CTR is the #1 factor)
═══════════════════════════════════════════════
Title formulas that get high CTR:
{title_formula_examples}

Power adjectives: {power_adj}
Power verbs: {power_vrb}
- Title MUST contain a recognizable named entity from the headline
- 50-70 characters, natural language, NOT ALL CAPS
- The title should make someone think "I NEED to click this"

═══════════════════════════════════════════════
SCRIPT STRUCTURE (follow this EXACTLY)
═══════════════════════════════════════════════

PART 1 — THE HOOK (0-3 seconds, 10-15 words):
- First word MUST be the most shocking element (name, number, superlative)
- Create an information gap that's impossible to resist
- The viewer should think "wait, WHAT?" within 1 second
- NEVER start with: "So", "Did you know", "What if I told you", "In today's world"
- Pattern interrupt examples: "Elon Musk just..." / "$47 billion..." / "Three scientists proved..."

PART 2 — THE BUILD (3-20 seconds, 40-50 words):
- Establish credibility with specific numbers, dates, names
- Each sentence must add NEW information (no repetition)
- Use short, punchy sentences (5-10 words each)
- Voice should be measured, building tension

PART 3 — THE REVELATION (20-40 seconds, 50-60 words):
- The "holy shit" moment — the detail most people don't know
- This is where the emotional peak hits
- Use strategic pauses before the big reveal
- Connect multiple pieces of evidence for maximum impact

PART 4 — THE PERSONAL STAKE (40-50 seconds, 25-30 words):
- Make it about the VIEWER directly
- Use "you", "your", "everyone who..."
- Show why this matters to THEIR life/money/future

PART 5 — THE CLOSER (50-60 seconds, 10-15 words):
- Divisive binary question that forces a side
- Must be impossible to scroll past without having an opinion
- NOT: "What do you think?" / "Type YES" / "Comment below"
- YES: "Was this justified or pure corporate greed?" / "Is this the future, or the end?"
{dedup_context}

⚠️ ABSOLUTE RULES — VIOLATION = SCRIPT REJECTED:
- DO NOT fabricate events, people, companies, or products
- Script MUST be about ONE of the real headlines provided
- Title MUST contain a real, recognizable named entity
- Hook MUST start with the most shocking word
- Outro MUST be a divisive binary-choice question
- Total spoken words: 140-170 (equals 55-65 seconds)
- NO fabricated statistics — only use real numbers you're certain about
- Hashtags limited to 5-7 (over-tagging triggers YouTube suppression)

Return a JSON array where each element has:
{{
  "id": "S001",
  "title": "SEO title with REAL named entity, 50-70 chars",
  "hook": "first 3 sec hook, START with name/number/superlative, 10-15 words",
  "body": "main content 130-160 words. Follow the viral formula structure. Real names, dates, numbers. Short punchy sentences. Build emotional arc per the intensity curve.",
  "outro": "divisive binary question 10-15 words. Forces viewer to pick a side.",
  "description": "First line: keyword phrase people search. Second line: 1-sentence summary. Third: 'Follow for daily deep dives!' Then 5-7 hashtags.",
  "tags": ["#Shorts", "#[PersonOrCompanyName]", "#[NicheTag]", "#Trending"] + {json.dumps(niche_hashtags)},
  "pinned_comment": "a thoughtful divisive question that sparks real debate",
  "source_headline": "the exact RSS headline this is based on",
  "viral_formula_used": "formula key from the briefing",
  "primary_emotion": "the main emotion this script triggers",
  "retention_hooks": [
    {{"timestamp": "0-3s", "hook": "what keeps them watching at this point"}},
    {{"timestamp": "15s", "hook": "mid-video retention hook"}},
    {{"timestamp": "30s", "hook": "the revelation that prevents drop-off"}},
    {{"timestamp": "45s", "hook": "the personal stake that drives to the end"}}
  ],
  "visual_cues": [
    {{"timestamp": "0-1s", "description": "SCROLL STOPPER: extreme close-up or dramatic visual that stops the thumb", "motion": "fast_zoom_in"}},
    {{"timestamp": "1-3s", "description": "HOOK VISUAL: reinforces the shocking opening statement", "motion": "slow_pan"}},
    {{"timestamp": "3-15s", "description": "CONTEXT: setting, evidence, establishing shots — change every 3 seconds", "motion": "ken_burns"}},
    {{"timestamp": "15-30s", "description": "REVELATION: the key evidence or proof, dramatically lit", "motion": "dramatic_zoom"}},
    {{"timestamp": "30-45s", "description": "PERSONAL: viewer-focused, relatable imagery", "motion": "slow_zoom_out"}},
    {{"timestamp": "45-60s", "description": "CLOSER: divisive visual, split-screen or binary choice", "motion": "static_dramatic"}}
  ],
  "veo3_prompts": [
    "cinematic 9:16 [specific scene], photorealistic, dramatic lighting, 4K",
    "cinematic 9:16 [specific scene], photorealistic, tense atmosphere",
    "cinematic 9:16 [key evidence/revelation], photorealistic, sharp focus",
    "cinematic 9:16 [dramatic conclusion], photorealistic, emotional weight"
  ],
  "caption_style": "tiktok_pop",
  "voice_pacing": {{
    "hook": "fast_intense",
    "build": "measured_building",
    "revelation": "dramatic_pause_then_punch",
    "personal": "sincere_direct",
    "closer": "emphatic_slow"
  }}
}}

VERIFIED HEADLINES (use ONLY these):
{chr(10).join(f'{i+1}. {tm["headline"]}' for i, tm in enumerate(topics_with_meta))}

Visual style: {niche_cfg['visual_style']}
"""

    print(f"  ⏳ Calling Gemini with Viral Intelligence Engine for {count} scripts...")
    response = model.generate_content(prompt)
    text = response.text.strip()

    if text.startswith("```"):
        text = text.split("\n", 1)[1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    scripts = json.loads(text)

    if isinstance(scripts, dict):
        scripts = [scripts]
    scripts = [s for s in scripts if isinstance(s, dict)]
    if not scripts:
        raise ValueError("Gemini returned no valid script objects")

    results = []
    for i, script in enumerate(scripts):
        script["id"] = f"{batch_id}_{i+1:03d}"
        script["niche"] = niche
        script["channel"] = niche_cfg["channel_name"]
        script["generated_at"] = datetime.now().isoformat()
        script["full_script"] = f"{script.get('hook', '')} {script.get('body', '')} {script.get('outro', '')}"
        script["trending_source"] = trending_source

        # Attach viral metadata
        if i < len(topics_with_meta):
            topic_meta = topics_with_meta[i]
            script["topic_viral_score"] = topic_meta.get("score", 0)
            script["recommended_formula"] = topic_meta.get("formula", "")
            script["primary_emotion"] = topic_meta.get("emotion", script.get("primary_emotion", ""))

        # Attach caption style from viral engine
        formula_key = script.get("viral_formula_used", "expose")
        script["caption_config"] = get_caption_style(formula_key)

        word_count = len(script["full_script"].split())
        script["word_count"] = word_count
        if word_count < 100 or word_count > 200:
            print(f"  ⚠️  Script {script['id']} has {word_count} words (target: 140-170)")

        # Save script JSON
        out_path = config.SCRIPTS_DIR / f"{script['id']}.json"
        out_path.write_text(json.dumps(script, indent=2))
        results.append(script)
        source_label = "🔥 LIVE" if trending_source == "real_time_trending" else "📋 curated"
        formula_label = script.get("viral_formula_used", "auto")
        print(f"  ✅ {script['id']}: \"{script['title']}\" ({word_count}w) [{source_label}] [Formula: {formula_label}]")

        add_topic(
            title=script["title"],
            niche=niche,
            headline=script.get("source_headline", ""),
            score=script.get("topic_viral_score", 0),
        )

    return results


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--niche", default=config.DEFAULT_NICHE)
    parser.add_argument("--count", type=int, default=config.SHORTS_PER_RUN)
    parser.add_argument("--batch-id", default=datetime.now().strftime("B%Y%m%d"))
    args = parser.parse_args()

    print(f"\n🎬 Stage 1: Generating {args.count} viral scripts for '{args.niche}'\n")
    scripts = generate_scripts(args.niche, args.count, args.batch_id)
    print(f"\n✅ Generated {len(scripts)} scripts → {config.SCRIPTS_DIR}/\n")
    return scripts


if __name__ == "__main__":
    main()
