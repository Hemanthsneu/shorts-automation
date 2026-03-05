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

# ── Niche → Reddit subreddits for hot posts ──
NICHE_SUBREDDITS = {
    "tech": ["technology", "gadgets", "tech"],
    "ai": ["artificial", "MachineLearning", "ChatGPT", "OpenAI"],
    "finance": ["wallstreetbets", "CryptoCurrency", "stocks", "economics"],
    "cinema": ["movies", "entertainment", "netflix", "television"],
    "sports": ["sports", "nba", "nfl", "soccer", "MMA"],
    "science": ["science", "Futurology", "space"],
    "gaming": ["gaming", "pcgaming", "PS5", "XboxSeriesX"],
    "history": ["history", "Archaeology", "todayilearned"],
    "space": ["space", "SpaceXLounge", "nasa", "Astronomy"],
    "popculture": ["entertainment", "popculturechat", "Celebs"],
}

# ── Niche → YouTube Trending category IDs ──
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


def fetch_youtube_trending(niche: str, max_results: int = 10) -> list[str]:
    """Fetch currently trending YouTube videos for the niche category."""
    import requests
    
    try:
        # Use YouTube Data API v3 — key is same as GEMINI_API_KEY for Google Cloud
        api_key = config.GEMINI_API_KEY
        category_id = NICHE_YT_CATEGORIES.get(niche, "0")
        
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "part": "snippet,statistics",
            "chart": "mostPopular",
            "regionCode": "US",
            "videoCategoryId": category_id,
            "maxResults": max_results,
            "key": api_key,
        }
        
        r = requests.get(url, params=params)
        if r.status_code == 200:
            data = r.json()
            titles = []
            for item in data.get("items", []):
                title = item.get("snippet", {}).get("channelTitle", "") + ": " + item.get("snippet", {}).get("title", "")
                view_count = int(item.get("statistics", {}).get("viewCount", "0"))
                # Only include videos with significant traction
                if view_count > 50000:
                    titles.append(item.get("snippet", {}).get("title", ""))
            return titles
        else:
            print(f"    ⚠️  YouTube API: {r.status_code}")
            return []
    except Exception as e:
        print(f"    ⚠️  YouTube Trending fetch failed: {e}")
        return []


def fetch_reddit_hot(niche: str, max_posts: int = 10) -> list[str]:
    """Fetch hot posts from relevant Reddit subreddits."""
    import requests
    
    subreddits = NICHE_SUBREDDITS.get(niche, [niche])
    headlines = []
    
    headers = {"User-Agent": "ShortsFactory/1.0"}
    
    for sub in subreddits[:2]:  # Limit to 2 subreddits to avoid rate limits
        try:
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit=10"
            r = requests.get(url, headers=headers, timeout=5)
            if r.status_code == 200:
                data = r.json()
                for post in data.get("data", {}).get("children", []):
                    post_data = post.get("data", {})
                    title = post_data.get("title", "")
                    score = post_data.get("score", 0)
                    # Only include posts with good engagement
                    if score > 100 and len(title) > 15 and not post_data.get("stickied"):
                        headlines.append(title)
        except Exception:
            continue
    
    return headlines[:max_posts]


def discover_trending_topics(niche: str, count: int) -> list[str]:
    """Pull REAL trending data from YouTube Trending + Reddit + RSS, then use Gemini
    controversy scoring to pick only the most viral-worthy topics (8+/10)."""
    print(f"  🔍 Fetching REAL trending data for '{niche}'...")

    # 1. YouTube Trending — what's actually going viral on YouTube RIGHT NOW
    yt_trending = fetch_youtube_trending(niche, max_results=10)
    print(f"    🎬 Found {len(yt_trending)} YouTube trending videos")

    # 2. Reddit Hot — engagement-validated topics people are actively discussing
    reddit_hot = fetch_reddit_hot(niche, max_posts=10)
    print(f"    🔥 Found {len(reddit_hot)} Reddit hot posts")

    # 3. RSS News — breaking news from last 24 hours
    rss_headlines = fetch_rss_headlines(niche, max_headlines=20)
    print(f"    📰 Found {len(rss_headlines)} news headlines")

    all_real_data = yt_trending + reddit_hot + rss_headlines

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

Today is {today}. Generate exactly {count} YouTube Shorts scripts about topics that are CURRENTLY trending.
Return ONLY valid JSON — no markdown, no code fences.

WHAT MAKES A SHORT GO VIRAL (follow this EXACTLY):
Our top performing video "OpenAI's SHOCKING 'Sky' Voice Scandal EXPOSED" hit 2,000+ views because:
1. It NAMED a specific company/person (OpenAI, Scarlett Johansson)
2. It had an EXPOSE angle ("caught", "exposed", "scandal")
3. The hook was a SPECIFIC claim, not generic clickbait
4. It felt like BREAKING NEWS the viewer hadn't heard yet
5. It created OUTRAGE — viewers felt compelled to comment

YOU MUST FOLLOW THIS FORMULA:
- ALWAYS name specific people, companies, or organizations in the title
- Frame as an EXPOSE: someone got caught, a secret leaked, the truth came out
- The hook must make a SPECIFIC shocking claim (never vague)
- Body must include REAL details: dates, numbers, quotes, specifics
- Create a VILLAIN vs VICTIM narrative — viewers love taking sides
- End with an UNRESOLVED question that forces viewers to comment
- The title MUST read like a news alert someone would screenshot and share

TITLE FORMULAS THAT WORK (pick one):
- "[Famous Name] Just Got CAUGHT Doing [Shocking Thing]" 
- "[Company] Has Been LYING About [Topic]... Here's Proof"
- "The [Industry] Secret They Don't Want You to Know"
- "[Breaking Event]: What Nobody Is Telling You"
- "[Person] EXPOSED: The [Number] Things They're Hiding"

Return a JSON array where each element has:
{{
  "id": "S001",
  "title": "MUST name a specific person/company + use EXPOSED/CAUGHT/SHOCKING — under 70 chars",
  "hook": "first 2-3 sec, a SPECIFIC shocking claim with a named entity, 10-15 words, must trigger outrage or disbelief",
  "body": "main content, 130-160 words. Start with context (who/what). Then the revelation (what happened). Then WHY it matters (how it affects viewers). Use specific numbers, dates, and names. Short punchy sentences. Build tension to a climax.",
  "outro": "end with a provocative question or unresolved cliffhanger that FORCES comments, 10-15 words",
  "description": "First line: exact topic keyword phrase. Second line: 1-sentence summary. Third line: 'Follow for daily exposés and breaking stories!' Then 15+ hashtags: #Shorts #Viral #Trending #Exposed #Breaking #[TopicSpecific] {' '.join(niche_cfg['hashtags'])}",
  "tags": ["#Shorts", "#Viral", "#Trending", "#MustWatch", "#Exposed", "#Breaking", "#DidYouKnow", "#Facts"] + {json.dumps(niche_cfg['hashtags'])},
  "pinned_comment": "a POLARIZING question that forces people to pick a side, e.g. 'Do you think [person] should be held accountable? YES or NO 👇'",
  "visual_cues": [
    {{"timestamp": "0-3s", "description": "dramatic close-up or headline-style visual — immediately signals THIS IS IMPORTANT"}},
    {{"timestamp": "3-20s", "description": "visual of the person/company/event being discussed — establishes WHO"}},
    {{"timestamp": "20-40s", "description": "visual showing the evidence/revelation — the PROOF"}},
    {{"timestamp": "40-55s", "description": "dramatic visual showing impact/consequences — WHY IT MATTERS"}}
  ],
  "veo3_prompts": [
    "cinematic 9:16 dramatic close-up related to the topic, photorealistic, breaking-news energy, red/dark tones",
    "cinematic 9:16 wide shot establishing the scene/person, photorealistic, dramatic lighting",
    "cinematic 9:16 the key evidence or revelation moment, photorealistic, intense atmosphere",
    "cinematic 9:16 dramatic conclusion shot, photorealistic, somber or powerful mood"
  ]
}}

Topics to cover (one script per topic — make these VIRAL EXPOSÉS):
{chr(10).join(f'{i+1}. {t}' for i, t in enumerate(topics))}

Visual style direction: {niche_cfg['visual_style']}

CRITICAL RULES:
- Total spoken words per script: 140-170 (equals 55-65 seconds)
- EVERY title MUST name a specific person, company, or organization
- NEVER use generic titles like "3 Shocking Facts" — always tie to a NAMED entity
- Scripts MUST reference CURRENT events happening TODAY — NO old news
- The viewer should feel like they're getting INSIDER information
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
