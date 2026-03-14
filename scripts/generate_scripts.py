"""
Stage 1: Generate short-form video scripts using Gemini API.
Outputs JSON files with script, metadata, and Veo 3 prompts.

Features:
- REAL real-time trending data from Google Trends + RSS news
- Gemini writes scripts based on verified current topics
- Viral-optimized prompts with subscriber CTAs
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

# ── Niche → RSS feeds mapping (expanded with high-quality sources) ──
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

# ── Niche → YouTube category IDs for upload metadata ──
NICHE_YT_CATEGORIES = {
    "tech": "28",        # Science & Technology
    "ai": "28",          # Science & Technology
    "finance": "25",     # News & Politics
    "cinema": "24",      # Entertainment
    "sports": "17",      # Sports
    "science": "28",     # Science & Technology
    "gaming": "20",      # Gaming
    "history": "27",     # Education
    "space": "28",       # Science & Technology
    "popculture": "24",  # Entertainment
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
                # Clean up Google News attribution (e.g. " - CNN")
                if " - " in title:
                    title = title.rsplit(" - ", 1)[0].strip()
                if title and len(title) > 15:
                    headlines.append(title)
        except Exception:
            continue

    # Deduplicate and shuffle
    headlines = list(set(headlines))
    random.shuffle(headlines)
    return headlines[:max_headlines]


def fetch_google_trends_rss(max_results: int = 15) -> list[str]:
    """Fetch currently trending searches from Google Trends RSS (free, no API key)."""
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
    """Secondary Gemini call to reject hallucinated/unverifiable topics.
    This is the critical gate that prevents zero-search-volume videos."""
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
    """Pull VERIFIED real trending data from Google Trends + RSS only.
    No AI-generated topics — those cause hallucinated fake events."""
    print(f"  🔍 Fetching VERIFIED trending data for '{niche}'...")

    # 0. Migrate topic history from content_log if first run
    migrate_from_content_log()

    # 1. Google Trends RSS — what people are ACTUALLY searching for right now
    google_trends = fetch_google_trends_rss(max_results=15)
    print(f"    📈 Found {len(google_trends)} Google Trends topics")

    # 2. RSS News — breaking news from last 24 hours (verified real headlines)
    rss_headlines = fetch_rss_headlines(niche, max_headlines=25)
    print(f"    📰 Found {len(rss_headlines)} verified news headlines")

    all_real_data = google_trends + rss_headlines

    if not all_real_data:
        print(f"  ⚠️  No real-time data found, falling back to curated pool")
        return None

    # 2.5. Filter out previously used topics (dedup)
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

    # 3. CONTROVERSY SCORING — Rate each headline for viral potential (threshold: 8+)
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    today = datetime.now().strftime("%B %d, %Y")

    # Include previously used titles so scorer can deprioritize similar angles
    used_context = ""
    if used_titles:
        recent_used = used_titles[-20:]  # last 20 titles
        used_context = f"\n\nALREADY USED TITLES (avoid similar topics):\n" + chr(10).join(f'- {t}' for t in recent_used)

    prompt = f"""Today is {today}. You are a YouTube Shorts viral strategist.

Score each headline below from 1-10 for VIRAL POTENTIAL as a 60-second YouTube Short.

SCORING CRITERIA (what gets 8-10):
- Controversy, scandal, or exposé involving a NAMED person/company
- Celebrity/public figure drama or secrets revealed
- Shocking statistics with SPECIFIC numbers that affect millions
- Breaking news that people are ACTIVELY searching for RIGHT NOW
- Stories that trigger strong emotions (outrage, shock, fear, amazement)
- Topics with a clear debate angle (viewers will want to comment)

WHAT SCORES LOW (1-5):
- Generic corporate news, quarterly earnings, routine stock movements
- Boring policy updates, routine announcements
- Stories without a NAMED person or company
- Old news or topics with no active debate
- Topics too niche for a general audience
- Any topic that does NOT have a clear emotional hook

CRITICAL: A headline MUST contain at least one recognizable NAMED entity (person, company, brand) to score above 7.
{used_context}

HEADLINES TO SCORE:
{chr(10).join(f'{i+1}. {h}' for i, h in enumerate(all_real_data))}

Return ONLY a JSON array of objects. No markdown, no code fences.
Format: [{{"headline": "exact headline text", "score": 8, "angle": "the viral angle in 10 words", "named_entity": "the main person/company mentioned"}}]

Return ALL headlines with their scores. I will filter by score >= 8."""

    try:
        print(f"  🔥 Running controversy scoring on {len(all_real_data)} headlines...")
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

        scored = json.loads(text)
        if isinstance(scored, list):
            # Filter for high-scoring headlines (8+ — strict threshold)
            hot_topics = [s for s in scored if isinstance(s, dict) and s.get("score", 0) >= 8]
            hot_topics.sort(key=lambda x: x.get("score", 0), reverse=True)

            if hot_topics:
                # Take more than needed, then fact-check
                candidates = hot_topics[:count * 2]
                for p in candidates:
                    print(f"    🔥 [{p.get('score', '?')}/10] {p.get('headline', '?')[:60]}...")
                    print(f"       Angle: {p.get('angle', 'N/A')} | Entity: {p.get('named_entity', 'N/A')}")
                
                # FACT-CHECK GATE — reject hallucinated topics
                candidate_headlines = [p["headline"] for p in candidates]
                verified = fact_check_topics(candidate_headlines, model)
                print(f"    ✅ Fact-check passed: {len(verified)}/{len(candidate_headlines)}")
                
                if verified:
                    return verified[:count]

            # Fallback: lower threshold to 7 but still fact-check
            print(f"  ⚠️  No headlines scored 8+, trying 7+ with fact-check...")
            ok_topics = [s for s in scored if isinstance(s, dict) and s.get("score", 0) >= 7]
            ok_topics.sort(key=lambda x: x.get("score", 0), reverse=True)
            if ok_topics:
                candidate_headlines = [p["headline"] for p in ok_topics[:count * 2]]
                verified = fact_check_topics(candidate_headlines, model)
                if verified:
                    return verified[:count]

            # Last resort: top scored regardless
            print(f"  ⚠️  No fact-checked topics available, picking top scored")
            scored.sort(key=lambda x: x.get("score", 0), reverse=True)
            picked = scored[:count]
            for p in picked:
                print(f"    📊 [{p.get('score', '?')}/10] {p.get('headline', '?')[:60]}...")
            return [p["headline"] for p in picked]
    except Exception as e:
        print(f"  ⚠️  Controversy scoring failed: {e}")

    # Fallback: just return raw headlines
    return random.sample(all_real_data, min(count, len(all_real_data)))


def generate_scripts(niche: str, count: int, batch_id: str) -> list[dict]:
    """Generate `count` scripts for the given niche. Returns list of script dicts."""
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    niche_cfg = config.NICHE_CONFIG[niche]

    # Try to discover trending topics first
    trending_topics = discover_trending_topics(niche, count)
    if trending_topics:
        topics = trending_topics
        trending_source = "real_time_trending"
    else:
        # Fallback to curated pool
        topics = random.sample(niche_cfg["topics_pool"], min(count, len(niche_cfg["topics_pool"])))
        trending_source = "curated_pool"

    today = datetime.now().strftime("%B %d, %Y")

    # Build dedup context for the prompt
    used_titles = get_used_titles(limit=30)
    dedup_context = ""
    if used_titles:
        dedup_context = f"\n\n🚫 ALREADY USED TITLES (DO NOT make videos about these same topics):\n" + chr(10).join(f'- {t}' for t in used_titles[-15:])

    # Select only 5-8 best hashtags per niche (over-tagging triggers suppression)
    niche_hashtags = niche_cfg['hashtags'][:6]

    prompt = f"""{niche_cfg['system_prompt']}

Today is {today}. Generate exactly {count} YouTube Shorts scripts.
Return ONLY valid JSON — no markdown, no code fences.

⚠️ ABSOLUTE RULE — DO NOT FABRICATE:
- You are given REAL news headlines below. Your script MUST be about ONE of these REAL stories.
- DO NOT invent events, people, companies, products, or scandals that don't exist.
- DO NOT create fictional names like "Dr. Ishikawa" or fake products like "OmniCreator" or "Project Chimera".
- If you are not 100% certain the event/person/company is REAL, do NOT write about it.
- Your script should ONLY contain facts that actually happened. No speculation presented as fact.
{dedup_context}

WHAT MAKES A SHORT GO VIRAL ON YOUTUBE (STUDY THESE PATTERNS):
Our TOP performing videos and WHY they worked:
1. "OpenAI's SHOCKING 'Sky' Voice Scandal EXPOSED" → 1,812 views (real scandal + named entity + active debate)
2. "Hidden 5,000-Year-Old City Shocks Archaeologists" → 1,026 views (specific number + extreme claim + real discovery)
3. "3 Insane Ways Cells Are Secretly Quantum Computers" → 937 views (number + mind-blowing science + curiosity gap)
4. "3 INSANE Shedeur Sanders SECRETS" → 903 views (named athlete + secrets framing + sports drama)

Our WORST performing videos (1-9 views) failed because:
- Topics nobody was searching for (zero search volume)
- No named person/company in the title
- Generic or obscure topics without emotional stakes

SEO-FIRST TITLE STRATEGY (THIS IS CRITICAL FOR YOUTUBE DISCOVERY):
- Title MUST contain a recognizable NAMED entity (person, company, brand) from the headline
- Format: "[Real Name] + [Shocking Verb] + [Specific Detail]"
- Good: "Sam Altman's OpenAI Deal with Department of War Explained" (131 views - named entity + context)
- Good: "Ryan Reynolds' Wrexham Vision: Shocking Global Impact" (273 views - celebrity + impact)
- BAD: Generic titles without names → 1-9 views every time
- Keep titles 50-70 chars, natural language, NOT ALL CAPS

PATTERN INTERRUPT HOOK (CRITICAL — first 3 seconds decide everything):
- The VERY FIRST WORD must be the most shocking element — a name, a number, or a superlative
- Examples: "Elon Musk just..." / "$47 billion..." / "Three scientists just proved..."
- NEVER start with setup phrases like "So" / "Did you know" / "What if I told you"
- The hook must make someone STOP scrolling in 1 second

PACING & DELIVERY MARKERS (CRITICAL FOR ENGAGING VOICE):
- Use SHORT sentences (5-12 words each). This creates a punchy, fast-paced feel.
- After the hook, add [PAUSE 0.5] to create a dramatic beat before the context.
- Before the key revelation, add [PAUSE 0.3] for anticipation.
- Use [EMPHASIS] before the single most shocking sentence to slow it down for impact.
- Use [SLOW] before statistics or numbers so the viewer can absorb them.
- Do NOT overuse markers — max 3-4 per script. They should feel natural, not robotic.
- Write like you're TALKING to someone, not reading an essay. Use contractions. Be direct.

HOW TO WRITE THE SCRIPT:
1. HOOK (first 3 seconds): Start with the MOST SHOCKING word — a name, number, or superlative. No setup.
2. CONTEXT (next 15 seconds): Who is involved? What exactly happened? Use real names, dates, numbers. SHORT sentences only.
3. THE REVEAL (next 20 seconds): [PAUSE 0.3] before this section. The detail most people don't know. Build outrage/amazement.
4. WHY IT MATTERS (next 15 seconds): Make it personal — "This affects YOUR [money/privacy/future]". [EMPHASIS] on the key line.
5. CLOSER (last 5 seconds): Pose a DIVISIVE question that forces a side: "Was this justified, or did they go too far?" / "Is this the future, or a disaster waiting to happen?" — NOT "What do you think?" or "Type YES."

Return a JSON array where each element has:
{{
  "id": "S001",
  "title": "SEO-searchable title with REAL named entity, 50-70 chars, natural language",
  "hook": "first 3 sec, START with the most shocking word — a name or number. 10-15 words max.",
  "body": "main content, 130-160 words. Based ONLY on real facts. Real names, dates, numbers. SHORT punchy sentences (5-12 words). Include [PAUSE 0.3] before the key revelation and [EMPHASIS] before the most shocking sentence. Build to emotional climax. Make it personal.",
  "outro": "divisive binary question: 'Was X justified or did they go too far?' style. 10-15 words. Forces the viewer to pick a side.",
  "description": "First line: main keyword phrase people would search (e.g. 'OpenAI Sky voice scandal explained'). Second line: 1-sentence summary. Third line: 'Follow for daily deep dives!' Then 5-7 relevant hashtags: #Shorts #[PersonName] {' '.join(niche_hashtags)}",
  "tags": ["#Shorts", "#[PersonOrCompanyName]", "#[TopicKeyword]", "#[NicheTag]", "#Trending", "#Explained"] + {json.dumps(niche_hashtags)},
  "pinned_comment": "a thoughtful, divisive question that sparks real debate in the comments",
  "source_headline": "the exact RSS headline this script is based on",
  "visual_cues": [
    {{"timestamp": "0-3s", "description": "SPECIFIC image: photorealistic [actual person name] at [actual real location/event]. Example: 'Elon Musk at Tesla factory, dramatic side lighting' NOT 'dramatic close-up of named entity'"}},
    {{"timestamp": "3-20s", "description": "SPECIFIC image: the actual place/building/setting. Example: 'Pentagon building exterior, overcast sky, news vans outside' NOT 'relevant setting'"}},
    {{"timestamp": "20-40s", "description": "SPECIFIC image: concrete visual of the revelation. Example: 'computer screen showing leaked financial data with red warning alerts' NOT 'key evidence'"}},
    {{"timestamp": "40-55s", "description": "SPECIFIC image: the real-world consequence. Example: 'crowd of protesters outside Apple HQ with smartphones' NOT 'dramatic conclusion'"}}
  ],
  "veo3_prompts": [
    "photorealistic portrait of [ACTUAL PERSON NAME] in [SPECIFIC REAL SETTING], 9:16 vertical, dramatic cinematic lighting, editorial photography style. Example: 'photorealistic portrait of Tim Cook in Apple Park boardroom, dramatic side lighting, dark background'",
    "photorealistic wide shot of [ACTUAL REAL LOCATION related to the story], 9:16 vertical, atmospheric, news photography style. Example: 'wide shot of Wall Street trading floor with screens showing red numbers, tense atmosphere'",
    "photorealistic detail shot showing [CONCRETE VISUAL EVIDENCE from the story], 9:16 vertical, sharp focus, investigative photography style. Example: 'close-up of smartphone showing viral tweet with millions of views, dark moody lighting'",
    "photorealistic scene of [REAL-WORLD IMPACT/CONSEQUENCE], 9:16 vertical, emotional weight, documentary photography style. Example: 'aerial view of massive data center at night, blue cooling towers glowing, industrial scale'"
  ]
}}

VERIFIED REAL HEADLINES to choose from (pick the most viral-worthy one):
{chr(10).join(f'{i+1}. {t}' for i, t in enumerate(topics))}

Visual style direction: {niche_cfg['visual_style']}

CRITICAL RULES:
- Total spoken words per script: 140-170 (equals 55-65 seconds). Pacing markers [PAUSE], [EMPHASIS], [SLOW] do NOT count as words.
- Script MUST be about ONE of the real headlines above — do NOT invent a new topic
- Title MUST contain a real, recognizable NAMED entity from the headline
- The hook MUST start with the most shocking word (a name, number, or superlative)
- The outro MUST be a divisive binary-choice question (not 'What do you think?')
- NO fabricated names, events, or companies — only real ones from the headlines
- Visual cues and veo3_prompts MUST use REAL specific names, locations, and objects — NOT placeholders like [named entity]
- Keep hashtags to 5-7 maximum (over-tagging triggers YouTube suppression)
- Use 3-4 pacing markers total: [PAUSE 0.3] before revelations, [EMPHASIS] on the key shocking line, [SLOW] before stats
- Return ONLY the JSON array, nothing else
"""

    print(f"  ⏳ Calling Gemini for {count} viral scripts...")
    response = model.generate_content(prompt)
    text = response.text.strip()

    # Clean up common Gemini response issues
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    scripts = json.loads(text)

    # Ensure scripts is a list of dicts
    if isinstance(scripts, dict):
        scripts = [scripts]
    # Filter out any non-dict entries (Gemini sometimes returns strings)
    scripts = [s for s in scripts if isinstance(s, dict)]
    if not scripts:
        raise ValueError("Gemini returned no valid script objects")

    # Assign proper IDs and save individually
    results = []
    for i, script in enumerate(scripts):
        script["id"] = f"{batch_id}_{i+1:03d}"
        script["niche"] = niche
        script["channel"] = niche_cfg["channel_name"]
        script["generated_at"] = datetime.now().isoformat()
        script["full_script"] = f"{script['hook']} {script['body']} {script['outro']}"
        script["trending_source"] = trending_source

        # Word count validation — strip pacing markers before counting
        import re as _re
        clean_text = _re.sub(r'\[PAUSE\s+[\d.]+\]', '', script["full_script"])
        clean_text = clean_text.replace('[EMPHASIS]', '').replace('[SLOW]', '')
        word_count = len(clean_text.split())
        script["word_count"] = word_count
        if word_count < 100 or word_count > 200:
            print(f"  ⚠️  Script {script['id']} has {word_count} words (target: 140-170)")

        # Save individual script JSON
        out_path = config.SCRIPTS_DIR / f"{script['id']}.json"
        out_path.write_text(json.dumps(script, indent=2))
        results.append(script)
        source_label = "🔥 LIVE trending" if trending_source == "real_time_trending" else "📋 curated"
        print(f"  ✅ Script {script['id']}: \"{script['title']}\" ({word_count} words) [{source_label}]")

        # Track topic in dedup history
        add_topic(
            title=script["title"],
            niche=niche,
            headline=script.get("source_headline", ""),
            score=0,
        )

    return results


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--niche", default=config.DEFAULT_NICHE)
    parser.add_argument("--count", type=int, default=config.SHORTS_PER_RUN)
    parser.add_argument("--batch-id", default=datetime.now().strftime("B%Y%m%d"))
    args = parser.parse_args()

    print(f"\n🎬 Stage 1: Generating {args.count} viral scripts for '{args.niche}' niche\n")
    scripts = generate_scripts(args.niche, args.count, args.batch_id)
    print(f"\n✅ Generated {len(scripts)} scripts → {config.SCRIPTS_DIR}/\n")
    return scripts


if __name__ == "__main__":
    main()
