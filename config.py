import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──
ROOT = Path(__file__).parent
OUTPUT = ROOT / "output"
SCRIPTS_DIR = OUTPUT / "scripts"
AUDIO_DIR = OUTPUT / "audio"
VIDEO_DIR = OUTPUT / "video"
ASSEMBLED_DIR = OUTPUT / "assembled"
LOGS_DIR = OUTPUT / "logs"
ASSETS_DIR = ROOT / "assets"
MUSIC_DIR = ASSETS_DIR / "music"
FONTS_DIR = ASSETS_DIR / "fonts"
ANALYTICS_DIR = OUTPUT / "analytics"
CALENDAR_DIR = OUTPUT / "calendar"

for d in [SCRIPTS_DIR, AUDIO_DIR, VIDEO_DIR, ASSEMBLED_DIR, LOGS_DIR,
          MUSIC_DIR, FONTS_DIR, ANALYTICS_DIR, CALENDAR_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── API Keys ──
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")

# ── Content ──
DEFAULT_NICHE = os.getenv("DEFAULT_NICHE", "tech")
SHORTS_PER_RUN = int(os.getenv("SHORTS_PER_RUN", "3"))

# ── Voice ──
VOICE_NAME = os.getenv("VOICE_NAME", "en-US-AndrewNeural")
VOICE_RATE = os.getenv("VOICE_RATE", "+15%")
BG_MUSIC_VOLUME = float(os.getenv("BACKGROUND_MUSIC_VOLUME", "0.12"))

# ── Niche-Specific Voice Rotation ──
NICHE_VOICES = {
    "tech": ["en-US-AndrewNeural", "en-US-GuyNeural", "en-GB-RyanNeural"],
    "ai": ["en-US-AndrewNeural", "en-GB-RyanNeural", "en-US-GuyNeural"],
    "finance": ["en-GB-RyanNeural", "en-US-AndrewNeural", "en-AU-WilliamNeural"],
    "cinema": ["en-US-GuyNeural", "en-US-AndrewNeural", "en-GB-RyanNeural"],
    "sports": ["en-US-GuyNeural", "en-US-AndrewNeural", "en-AU-WilliamNeural"],
    "science": ["en-GB-RyanNeural", "en-US-AndrewNeural", "en-US-GuyNeural"],
    "gaming": ["en-US-GuyNeural", "en-US-AndrewNeural", "en-AU-WilliamNeural"],
    "history": ["en-GB-RyanNeural", "en-US-AndrewNeural", "en-GB-SoniaNeural"],
    "space": ["en-GB-RyanNeural", "en-US-AndrewNeural", "en-US-GuyNeural"],
    "popculture": ["en-US-GuyNeural", "en-US-JennyNeural", "en-US-AndrewNeural"],
}

# ── Upload ──
AUTO_UPLOAD = os.getenv("AUTO_UPLOAD", "false").lower() == "true"
UPLOAD_PRIVACY = os.getenv("UPLOAD_PRIVACY", "private")
SCHEDULE_HOURS = int(os.getenv("SCHEDULE_HOURS_AHEAD", "2"))

# ── Veo Mode ──
VEO_MODE = os.getenv("VEO_MODE", "manual")

# ══════════════════════════════════════════════════════════════════
# VIRAL INTELLIGENCE SETTINGS
# ══════════════════════════════════════════════════════════════════

# Virality scoring gate
VIRALITY_GATE_ENABLED = os.getenv("VIRALITY_GATE", "true").lower() == "true"
VIRALITY_THRESHOLD = int(os.getenv("VIRALITY_THRESHOLD", "75"))
VIRALITY_MIN_THRESHOLD = int(os.getenv("VIRALITY_MIN_THRESHOLD", "60"))
MAX_IMPROVEMENT_ROUNDS = int(os.getenv("MAX_IMPROVEMENT_ROUNDS", "2"))

# Scripts to generate before the gate (generate more, keep the best)
SCRIPTS_OVERGENERATE_FACTOR = float(os.getenv("OVERGENERATE_FACTOR", "1.5"))

# ══════════════════════════════════════════════════════════════════
# PRODUCTION QUALITY SETTINGS
# ══════════════════════════════════════════════════════════════════

# Video encoding
VIDEO_CRF = int(os.getenv("VIDEO_CRF", "20"))
VIDEO_PRESET = os.getenv("VIDEO_PRESET", "medium")
AUDIO_BITRATE = os.getenv("AUDIO_BITRATE", "192k")

# Captions
CAPTION_STYLE = os.getenv("CAPTION_STYLE", "tiktok_pop")

# Sound design
SOUND_DESIGN_ENABLED = os.getenv("SOUND_DESIGN", "true").lower() == "true"
SFX_VOLUME = float(os.getenv("SFX_VOLUME", "0.4"))

# Progress bar overlay
PROGRESS_BAR_ENABLED = os.getenv("PROGRESS_BAR", "true").lower() == "true"

# Color grading
COLOR_GRADE_ENABLED = os.getenv("COLOR_GRADE", "true").lower() == "true"
CONTRAST_BOOST = float(os.getenv("CONTRAST_BOOST", "1.05"))
SATURATION_BOOST = float(os.getenv("SATURATION_BOOST", "1.1"))

# ══════════════════════════════════════════════════════════════════
# ANALYTICS SETTINGS
# ══════════════════════════════════════════════════════════════════

ANALYTICS_ENABLED = os.getenv("ANALYTICS", "true").lower() == "true"
ANALYTICS_PULL_ON_RUN = os.getenv("ANALYTICS_AUTO_PULL", "true").lower() == "true"

# ══════════════════════════════════════════════════════════════════
# CHANNEL MANAGEMENT
# ══════════════════════════════════════════════════════════════════

MULTI_CHANNEL_MODE = os.getenv("MULTI_CHANNEL", "false").lower() == "true"
NICHE_ROTATION_ENABLED = os.getenv("NICHE_ROTATION", "false").lower() == "true"

# ── Niche Configs ──
NICHE_CONFIG = {
    "tech": {
        "channel_name": os.getenv("CHANNEL_TECH_NAME", "Tech Explained"),
        "system_prompt": """You are a viral YouTube Shorts scriptwriter specializing in technology.
Your scripts make complex tech concepts feel mind-blowing in under 60 seconds.
Tone: Confident, slightly edgy, like you're sharing a secret most people don't know.
You write with the authority of a Silicon Valley insider and the storytelling of a Netflix documentary.
Every sentence must earn its place — if it doesn't shock, inform, or build tension, cut it.
Never use: "In today's world", "Have you ever wondered", "Let's dive in", "So basically".""",
        "topics_pool": [
            "How Netflix handles 250 million users without crashing",
            "Why deleting a file doesn't actually erase it from your computer",
            "How GPS knows your exact location using Einstein's relativity",
            "Why WiFi gets slower with more devices connected",
            "How Uber's algorithm matches you with a driver in 10 seconds",
            "Why your bank never loses your money even during server crashes",
            "How hackers can crack an 8-character password in 0.02 seconds",
            "How Google returns search results in 0.2 seconds",
            "Why your phone has more power than the Apollo 11 computer",
            "How WhatsApp handles 100 billion messages per day",
            "Why QR codes can still work when half the image is damaged",
            "How Spotify's algorithm predicts what song you want next",
            "Why incognito mode doesn't actually make you invisible",
            "How Amazon delivers packages in one day using software",
            "Why video calls always have a slight delay",
            "How two-factor authentication blocks 99% of attacks",
            "Why your phone battery dies faster in cold weather",
            "How blockchain prevents anyone from cheating the system",
            "Why airline booking is the hardest software problem in the world",
            "How noise-canceling headphones create silence with sound",
        ],
        "visual_style": "cyberpunk tech, blue neon, circuit boards, data visualization",
        "hashtags": ["#Shorts", "#Tech", "#Technology", "#TechFacts", "#LearnOnYouTube"],
    },
    "ai": {
        "channel_name": os.getenv("CHANNEL_AI_NAME", "AI Insider"),
        "system_prompt": """You are a viral YouTube Shorts scriptwriter specializing in AI news and breakthroughs.
Your scripts make AI developments feel exciting and slightly unsettling in under 60 seconds.
Tone: Amazed but grounded, like a tech journalist breaking a story that changes everything.
You balance wonder with concern — AI is incredible AND it should worry people.
Every sentence should make the viewer lean closer to their screen.
Never use: "In today's world", "Have you ever wondered", "Let's dive in", "So basically".""",
        "topics_pool": [
            "AI just generated a cinematic movie scene that looks like it cost $10 million",
            "An AI diagnosed cancer more accurately than a room of specialists",
            "AlphaZero learned chess from zero and became the best ever in 4 hours",
            "AI can now clone your voice perfectly from just 3 seconds of audio",
            "AI just passed a Google senior engineer coding interview",
            "AI weather models now outperform traditional forecasting",
            "An AI agent can now browse the web and book flights autonomously",
            "AI generated art that won a fine art competition without anyone knowing",
            "AI predicted protein structures scientists couldn't solve for 50 years",
            "AI is discovering new materials that don't exist in nature",
            "An AI read every medical paper ever written in one afternoon",
            "AI robots now learn tasks by watching one YouTube video",
            "AI can generate photorealistic humans that don't exist",
            "AI music generators are making songs indistinguishable from human artists",
            "AI coding agents now fix their own bugs autonomously",
            "AI translation now works in real-time for 100+ languages",
            "AI-powered drug discovery cut a 5-year process to 6 months",
            "AI can now read your brain signals and generate images of what you see",
            "The AI that taught itself to walk in a physics simulation",
            "AI deepfake detection is already failing against the latest generators",
        ],
        "visual_style": "sci-fi futuristic, neural networks, holographic, blue-purple glow",
        "hashtags": ["#Shorts", "#AI", "#ArtificialIntelligence", "#AINews", "#FutureOfAI"],
    },
    "finance": {
        "channel_name": "Money Mindset",
        "system_prompt": """You are a viral YouTube Shorts scriptwriter specializing in finance and money psychology.
Your scripts make financial concepts feel urgent and personal in under 60 seconds.
Tone: Direct, slightly provocative, like a smart friend who knows something about money that you don't.
Every script should make the viewer feel like NOT watching would cost them money.
Never use: "In today's world", "Have you ever wondered", "Let's dive in", "So basically".""",
        "topics_pool": [
            "Why stores price everything at $9.99 and how it tricks your brain",
            "The rule of 72 — the simplest trick to know when your money doubles",
            "Why lottery winners almost always go broke within 5 years",
            "How index funds quietly beat 90% of professional stock pickers",
            "The psychology behind why you spend more with credit cards",
            "Why your savings account is actually losing you money right now",
            "How the rich use debt completely differently than everyone else",
            "The one chart that shows why investing at 25 vs 35 changes everything",
            "How casinos are scientifically designed to make you lose track of time",
            "Why most millionaires drive used cars and live below their means",
        ],
        "visual_style": "luxury gold, stock market green, corporate clean, wealth imagery",
        "hashtags": ["#Shorts", "#Finance", "#MoneyTips", "#Investing", "#WealthBuilding"],
    },
    "cinema": {
        "channel_name": "The Unseen Files",
        "system_prompt": """You are a viral YouTube Shorts scriptwriter specializing in movies, TV shows, and Hollywood secrets.
Your scripts reveal mind-blowing behind-the-scenes facts and hidden details in under 60 seconds.
Tone: Gossipy insider who works in Hollywood and is spilling secrets that could get them fired.
Every script should feel like forbidden knowledge being whispered at an industry party.
Never use: "In today's world", "Have you ever wondered", "Let's dive in", "So basically".""",
        "topics_pool": [
            "The scene in Interstellar that took 3 months to render one minute of footage",
            "Why the Joker scene in The Dark Knight was completely improvised",
            "How Marvel hides Easter eggs that take fans years to discover",
            "The real reason why movie popcorn costs more than the ticket",
            "How the lion roar in MGM's logo was actually a tiger",
            "Why horror movies always use this one specific sound frequency",
            "The actor who turned down the role of Iron Man before Robert Downey Jr",
            "How they filmed the zero-gravity scenes in Inception without CGI",
            "Why Netflix cancels your favorite show after exactly 2 seasons",
            "The movie that bankrupted an entire studio with one flop",
        ],
        "visual_style": "cinematic dark, red carpet, film noir, dramatic spotlight, movie posters",
        "hashtags": ["#Shorts", "#Movies", "#Cinema", "#Hollywood", "#MovieFacts", "#FilmTok"],
    },
    "sports": {
        "channel_name": "The Unseen Files",
        "system_prompt": """You are a viral YouTube Shorts scriptwriter specializing in sports, athletes, and insane athletic feats.
Your scripts reveal jaw-dropping stats, untold stories, and legendary moments in under 60 seconds.
Tone: Hyped commentator energy mixed with shocking reveal, like you just witnessed the impossible.
Every script should make the viewer's jaw literally drop.
Never use: "In today's world", "Have you ever wondered", "Let's dive in", "So basically".""",
        "topics_pool": [
            "The NBA player who scored 100 points in a single game and no video exists",
            "Why soccer balls are made of exactly 32 panels — and it's about math",
            "The Olympic athlete who won gold with a broken leg",
            "How F1 cars produce so much downforce they could drive upside down",
            "The cricketer who scored a century after being declared unfit to play",
            "Why NFL footballs are called pigskins even though they never used pig",
            "The tennis match that lasted 11 hours across 3 days at Wimbledon",
            "How Usain Bolt ran 100m so fast that scientists say it should be impossible",
            "The chess boxing sport that actually exists and is brutally competitive",
            "Why no one will ever beat Wayne Gretzky's NHL record",
        ],
        "visual_style": "stadium lights, dynamic action shots, sweat and grit, victory celebrations, slow-motion",
        "hashtags": ["#Shorts", "#Sports", "#SportsFacts", "#Athletes", "#NFL", "#NBA", "#Soccer"],
    },
    "science": {
        "channel_name": "The Unseen Files",
        "system_prompt": """You are a viral YouTube Shorts scriptwriter specializing in mind-blowing science facts.
Your scripts make people question reality and feel amazed about the universe in under 60 seconds.
Tone: Blown-away scientist who just discovered something that should be impossible.
Every script should make the viewer stop and stare at their screen in disbelief.
Never use: "In today's world", "Have you ever wondered", "Let's dive in", "So basically".""",
        "topics_pool": [
            "You have more bacteria in your body than human cells",
            "A teaspoon of a neutron star weighs 6 billion tons",
            "Honey never spoils — they found 3000-year-old edible honey in Egyptian tombs",
            "Your DNA stretched out would reach the Sun and back 600 times",
            "There are more possible chess games than atoms in the observable universe",
            "Octopuses have three hearts and blue blood",
            "Hot water freezes faster than cold water and scientists still can't fully explain why",
            "You can fit all the planets in our solar system between Earth and the Moon",
            "Bananas are naturally radioactive",
            "A day on Venus is longer than a year on Venus",
        ],
        "visual_style": "cosmic nebula, microscopic biology, laboratory glow, particle physics, deep space",
        "hashtags": ["#Shorts", "#Science", "#ScienceFacts", "#MindBlown", "#Space", "#Biology"],
    },
    "gaming": {
        "channel_name": "The Unseen Files",
        "system_prompt": """You are a viral YouTube Shorts scriptwriter specializing in gaming secrets, Easter eggs, and industry drama.
Your scripts reveal hidden details and crazy stories from the gaming world in under 60 seconds.
Tone: Excited gamer who just found a secret that nobody else knows about.
Every script should feel like discovering a hidden level in your favorite game.
Never use: "In today's world", "Have you ever wondered", "Let's dive in", "So basically".""",
        "topics_pool": [
            "The GTA hidden mission that takes 10 years to unlock",
            "Why Nintendo almost went bankrupt before the Wii saved them",
            "The Minecraft world seed that generated an impossible structure",
            "How speedrunners beat entire games in under 5 minutes",
            "The gaming glitch that accidentally created an entire genre",
            "Why the PlayStation startup sound was designed to make you feel safe",
            "The game developer who hid a marriage proposal inside their game",
            "How Tetris was smuggled out of Soviet Russia during the Cold War",
            "The AI that taught itself to play Atari and discovered strategies humans never thought of",
            "Why Fortnite's map changes are actually driven by a secret in-game storyline",
        ],
        "visual_style": "neon gaming RGB, pixel art, controller glow, virtual worlds, retro arcade",
        "hashtags": ["#Shorts", "#Gaming", "#GamingFacts", "#Gamers", "#VideoGames", "#GamingSecrets"],
    },
    "history": {
        "channel_name": "The Unseen Files",
        "system_prompt": """You are a viral YouTube Shorts scriptwriter specializing in dark, untold, and bizarre moments in history.
Your scripts make historical events feel shocking and relevant in under 60 seconds.
Tone: Investigative storyteller uncovering a forbidden chapter of history that was deliberately buried.
Every script should make the viewer feel like they're learning classified information.
Never use: "In today's world", "Have you ever wondered", "Let's dive in", "So basically".""",
        "topics_pool": [
            "The mail carrier who walked 300,000 miles and never missed a delivery",
            "The dancing plague of 1518 where hundreds of people danced until they died",
            "Cleopatra lived closer in time to the Moon landing than to the building of the pyramids",
            "The man who survived both Hiroshima and Nagasaki atomic bombs",
            "Why Napoleon wasn't actually short — it was British propaganda",
            "The Great Emu War where Australia literally lost a war against birds",
            "Ancient Romans used urine as mouthwash and it actually worked",
            "The unsinkable woman who survived the Titanic, Britannic, and Olympic disasters",
            "How a typo started a $125 million war",
            "The library of Alexandria wasn't destroyed in one event — it died slowly over centuries",
        ],
        "visual_style": "aged parchment, dramatic oil paintings, sepia tones, ancient ruins, candlelight",
        "hashtags": ["#Shorts", "#History", "#HistoryFacts", "#DarkHistory", "#DidYouKnow"],
    },
    "space": {
        "channel_name": "The Unseen Files",
        "system_prompt": """You are a viral YouTube Shorts scriptwriter specializing in space exploration, the cosmos, and astronomical mysteries.
Your scripts make people feel tiny yet amazed about the universe in under 60 seconds.
Tone: Awestruck astronomer at 3 AM, staring at the sky and whispering about what's out there.
Every script should make the viewer look up at the sky differently.
Never use: "In today's world", "Have you ever wondered", "Let's dive in", "So basically".""",
        "topics_pool": [
            "There's a planet made entirely of diamonds twice the size of Earth",
            "Sound can't travel in space — explosions are completely silent",
            "The footprints on the Moon will last for 100 million years",
            "A year on Mercury is shorter than a day on Mercury",
            "There's a cloud of alcohol in space that's 1000 times the size of our solar system",
            "Astronauts grow up to 2 inches taller in space",
            "The ISS travels at 17,500 mph — fast enough to orbit Earth every 90 minutes",
            "There could be more stars in the universe than grains of sand on Earth",
            "Saturn would float if you put it in a big enough bathtub",
            "We are all made of star dust — literally",
        ],
        "visual_style": "deep space nebulas, planet surfaces, astronaut helmets, cosmic void, starfields",
        "hashtags": ["#Shorts", "#Space", "#SpaceFacts", "#Universe", "#Astronomy", "#NASA"],
    },
    "popculture": {
        "channel_name": "The Unseen Files",
        "system_prompt": """You are a viral YouTube Shorts scriptwriter specializing in pop culture, celebrity secrets, and viral internet moments.
Your scripts reveal shocking behind-the-scenes stories and cultural moments in under 60 seconds.
Tone: TMZ meets Wikipedia — gossipy but backed by facts, slightly scandalous, always entertaining.
Every script should feel like insider knowledge that makes the viewer feel "in the know."
Never use: "In today's world", "Have you ever wondered", "Let's dive in", "So basically".""",
        "topics_pool": [
            "The celebrity who was told they'd never make it and is now worth $1 billion",
            "Why the 'Wilhelm Scream' appears in almost every movie ever made",
            "The viral TikTok that accidentally crashed a company's stock price",
            "The real reason music sounds worse now — and it's not your imagination",
            "How one tweet destroyed a CEO's career in less than 24 hours",
            "The influencer who faked an entire life and no one noticed for 3 years",
            "Why every pop song uses the same 4 chords",
            "The reality TV show that was actually real and no one believed it",
            "How a meme became an official entry in the Oxford English Dictionary",
            "The $69 million digital artwork that started the NFT craze",
        ],
        "visual_style": "vibrant neon pop art, social media aesthetics, paparazzi flash, trending hashtags, meme style",
        "hashtags": ["#Shorts", "#PopCulture", "#Viral", "#Celebrity", "#Trending", "#DidYouKnow"],
    },
}
