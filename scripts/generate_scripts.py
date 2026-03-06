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


def discover_trending_topics(niche: str, count: int) -> list[str]:
    """Pull VERIFIED real trending data from Google Trends + RSS only.
    No AI-generated topics — those cause hallucinated fake events."""
    print(f"  🔍 Fetching VERIFIED trending data for '{niche}'...")

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

    # 3. CONTROVERSY SCORING — Rate each headline for viral potential
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    today = datetime.now().strftime("%B %d, %Y")

    prompt = f"""Today is {today}. You are a YouTube Shorts viral strategist.

Score each headline below from 1-10 for VIRAL POTENTIAL as a 60-second YouTube Short.

SCORING CRITERIA (what gets 8-10):
- Controversy, scandal, or exposé (e.g. "Company CAUGHT doing X")
- Celebrity/public figure drama or secrets revealed
- Shocking statistics or "you won't believe" revelations  
- Breaking news that affects millions of people
- Stories that trigger strong emotions (outrage, shock, fear, amazement)
- Topics people are actively debating RIGHT NOW

WHAT SCORES LOW (1-4):
- Generic corporate news, quarterly earnings, stock movements
- Boring policy updates, routine announcements
- Stories without a clear emotional hook
- Old news or topics no one is actively discussing

HEADLINES TO SCORE:
{chr(10).join(f'{i+1}. {h}' for i, h in enumerate(all_real_data))}

Return ONLY a JSON array of objects. No markdown, no code fences.
Format: [{{"headline": "exact headline text", "score": 8, "angle": "the viral angle in 10 words"}}]

Return ALL headlines with their scores. I will filter by score >= 7."""

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
            # Filter for high-scoring headlines (7+)
            hot_topics = [s for s in scored if isinstance(s, dict) and s.get("score", 0) >= 7]
            hot_topics.sort(key=lambda x: x.get("score", 0), reverse=True)

            if hot_topics:
                picked = hot_topics[:count]
                for p in picked:
                    print(f"    🔥 [{p.get('score', '?')}/10] {p.get('headline', '?')[:60]}...")
                    print(f"       Angle: {p.get('angle', 'N/A')}")
                return [p["headline"] for p in picked]
            else:
                print(f"  ⚠️  No headlines scored 7+, picking top scored anyway")
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

    prompt = f"""{niche_cfg['system_prompt']}

Today is {today}. Generate exactly {count} YouTube Shorts scripts.
Return ONLY valid JSON — no markdown, no code fences.

⚠️ ABSOLUTE RULE — DO NOT FABRICATE:
- You are given REAL news headlines below. Your script MUST be about ONE of these REAL stories.
- DO NOT invent events, people, companies, products, or scandals that don't exist.
- DO NOT create fictional names like "Dr. Ishikawa" or fake products like "OmniCreator" or "Project Chimera".
- If you are not 100% certain the event/person/company is REAL, do NOT write about it.
- Your script should ONLY contain facts that actually happened. No speculation presented as fact.

WHAT MAKES A SHORT GO VIRAL ON YOUTUBE:
Our best video "OpenAI's SHOCKING 'Sky' Voice Scandal EXPOSED" hit 2,000 views because:
1. It was about a REAL event people were actively googling (OpenAI + Scarlett Johansson)
2. The title contained SEARCH KEYWORDS people actually type into YouTube
3. It explained a real story with real details viewers hadn't heard yet
4. It created genuine debate — viewers felt compelled to comment

SEO-FIRST TITLE STRATEGY (THIS IS CRITICAL FOR YOUTUBE DISCOVERY):
- Your title MUST contain keywords people actually search on YouTube
- Use the REAL names of people/companies/events from the headline
- Format: "[Real Person/Company] + [What Happened] + [Hook Word]"
- Good examples: "Why Tesla Just Fired 10,000 Workers", "The Real Reason LeBron Is Leaving"
- BAD examples: "Person X CAUGHT doing Y!!!" (too clickbaity, YouTube suppresses these)
- Keep titles natural and searchable, not ALL CAPS clickbait

HOW TO WRITE THE SCRIPT:
1. HOOK (first 3 seconds): State the shocking REAL fact. Use the actual name from the headline.
2. CONTEXT (next 15 seconds): Explain the real backstory briefly. Who is involved? What happened?
3. THE REVEAL (next 20 seconds): The key detail most people don't know. Use real facts, numbers, dates.
4. WHY IT MATTERS (next 15 seconds): How this affects the viewer or the world.
5. CLOSER (last 5 seconds): Ask a genuine question to drive comments. NOT "Type YES or NO"

Return a JSON array where each element has:
{{
  "id": "S001",
  "title": "SEO-searchable title with real names, under 70 chars, NOT all caps clickbait",
  "hook": "first 3 sec, state the shocking real fact with a real name, 10-15 words",
  "body": "main content, 130-160 words. Based ONLY on real facts from the headline. Include real names, real dates, real numbers. Short punchy sentences. Build to a climax.",
  "outro": "genuine question that drives real discussion, 10-15 words, NOT 'Type YES or NO'",
  "description": "First line: main keyword phrase people would search. Second line: 1-sentence summary of the real story. Third line: 'Follow for daily deep dives!' Then 10+ relevant hashtags: #Shorts #[TopicKeyword] #[PersonName] {' '.join(niche_cfg['hashtags'])}",
  "tags": ["#Shorts", "#[PersonOrCompanyName]", "#[TopicKeyword]", "#[NicheTag]", "#Trending", "#Explained", "#News"] + {json.dumps(niche_cfg['hashtags'])},
  "pinned_comment": "a thoughtful question related to the topic that sparks real discussion",
  "visual_cues": [
    {{"timestamp": "0-3s", "description": "dramatic photorealistic image of the person or event — immediately recognizable"}},
    {{"timestamp": "3-20s", "description": "visual context: the setting, company, or situation being discussed"}},
    {{"timestamp": "20-40s", "description": "visual showing the key revelation or evidence"}},
    {{"timestamp": "40-55s", "description": "powerful conclusion visual — the aftermath or consequences"}}
  ],
  "veo3_prompts": [
    "cinematic 9:16 dramatic close-up related to the topic, photorealistic, breaking-news energy",
    "cinematic 9:16 wide shot establishing the scene, photorealistic, dramatic lighting",
    "cinematic 9:16 the key evidence or revelation moment, photorealistic, intense atmosphere",
    "cinematic 9:16 dramatic conclusion shot, photorealistic, powerful mood"
  ]
}}

VERIFIED REAL HEADLINES to choose from (pick the most viral-worthy one):
{chr(10).join(f'{i+1}. {t}' for i, t in enumerate(topics))}

Visual style direction: {niche_cfg['visual_style']}

CRITICAL RULES:
- Total spoken words per script: 140-170 (equals 55-65 seconds)
- Script MUST be about ONE of the real headlines above — do NOT invent a new topic
- The title must be SEARCHABLE — use keywords people actually type into YouTube
- NO fabricated names, events, or companies — only real ones from the headlines
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

        # Word count validation
        word_count = len(script["full_script"].split())
        script["word_count"] = word_count
        if word_count < 100 or word_count > 200:
            print(f"  ⚠️  Script {script['id']} has {word_count} words (target: 140-170)")

        # Save individual script JSON
        out_path = config.SCRIPTS_DIR / f"{script['id']}.json"
        out_path.write_text(json.dumps(script, indent=2))
        results.append(script)
        source_label = "🔥 LIVE trending" if trending_source == "real_time_trending" else "📋 curated"
        print(f"  ✅ Script {script['id']}: \"{script['title']}\" ({word_count} words) [{source_label}]")

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
