# Shorts Factory

An automated pipeline that turns trending topics into YouTube Shorts. It generates scripts, voiceovers, visuals, and uploads — all from a single command.

## How It Works

```
Trending Topics ──> Script Generation ──> Virality Gate ──> Voiceover ──> Video Clips ──> Assembly ──> Upload
   (RSS + Trends)      (Gemini AI)        (score/improve)   (Edge TTS)    (Gemini/Veo)   (FFmpeg)    (YT API)
```

**Stage 1 — Scripts:** Pulls real headlines from Google Trends and RSS feeds. Gemini writes a 60-second script using a matched viral formula (exposé, countdown, myth-buster, etc.).

**Stage 2 — Virality Gate:** Each script is scored across 12 dimensions (hook power, shareability, comment bait, etc.). Weak scripts are auto-improved or killed before wasting production time.

**Stage 3 — Voiceover:** Edge TTS generates narration. Each video gets a unique voice, rate, and pitch so no two sound alike.

**Stage 4 — Video Clips:** Gemini generates images from the script's visual cues, then FFmpeg animates them with Ken Burns effects. Alternatively, you can use Veo 3 prompts for higher quality.

**Stage 5 — Assembly:** FFmpeg combines clips + voiceover + animated captions + sound effects + color grading + progress bar into a final 9:16 short.

**Stage 6 — Upload:** Uploads to YouTube with SEO metadata, optimal timing, and a pinned engagement comment.

**Stage 7 — Analytics:** Pulls view/engagement data from YouTube, identifies winning patterns, and feeds insights back into the content strategy.

## Prerequisites

- **Python 3.10+**
- **FFmpeg** installed and on PATH
- **Gemini API key** (free tier at [ai.google.dev](https://ai.google.dev))
- **YouTube OAuth credentials** (for uploading)

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/Hemanthsneu/shorts-automation.git
cd shorts-automation
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Or use the setup script (macOS/Linux):

```bash
chmod +x setup.sh && ./setup.sh
```

### 3. Install FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

### 4. Configure environment

```bash
cp .env.example .env
```

Open `.env` and set your Gemini API key:

```
GEMINI_API_KEY=your_key_here
```

### 5. Set up YouTube upload (optional)

Skip this step if you only want to generate videos locally.

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable **YouTube Data API v3**
4. Go to **Credentials** → Create **OAuth 2.0 Client ID** (Desktop Application)
5. Download the JSON and save it as `client_secret.json` in the project root
6. Run the auth flow:

```bash
python scripts/youtube_auth.py
```

This opens a browser window for authorization and creates `token.json`.

## Usage

### Full pipeline (one command)

```bash
python pipeline.py --count 3 --niche tech --fallback --auto-upload
```

This generates 3 tech shorts with AI-generated visuals and uploads them.

### Run without upload

```bash
python pipeline.py --count 2 --niche ai --fallback
```

Videos are saved to `output/assembled/`.

### Run a single stage

```bash
# Generate scripts only
python pipeline.py --stage scripts --count 5 --niche tech

# Score scripts for virality
python pipeline.py --stage score

# Generate voiceovers
python pipeline.py --stage voice

# Generate video clips
python pipeline.py --stage video --fallback

# Assemble final videos
python pipeline.py --stage assemble

# Upload to YouTube
python pipeline.py --stage upload --privacy public
```

### Skip the virality gate

```bash
python pipeline.py --count 3 --niche tech --fallback --no-gate
```

### Check pipeline status

```bash
python pipeline.py --status
```

### View analytics

```bash
python pipeline.py --analytics
```

### Generate content calendar

```bash
python pipeline.py --calendar 7
```

## Available Niches

`tech` `ai` `finance` `cinema` `sports` `science` `gaming` `history` `space` `popculture`

## Configuration

All settings are in `.env`. Key options:

| Setting | Default | Description |
|---------|---------|-------------|
| `GEMINI_API_KEY` | — | Required. Get from ai.google.dev |
| `DEFAULT_NICHE` | `tech` | Default content niche |
| `SHORTS_PER_RUN` | `3` | Videos per pipeline run |
| `VIRALITY_GATE` | `true` | Score and filter scripts before production |
| `VIRALITY_THRESHOLD` | `75` | Minimum score (0-100) to enter production |
| `SOUND_DESIGN` | `true` | Add SFX and ambient audio |
| `CAPTION_STYLE` | `tiktok_pop` | Caption style: `tiktok_pop`, `dramatic_reveal`, `news_ticker` |
| `AUTO_UPLOAD` | `false` | Upload automatically after assembly |
| `UPLOAD_PRIVACY` | `private` | YouTube privacy: `public`, `private`, `unlisted` |
| `VEO_MODE` | `manual` | Video mode: `manual` (AI images) or `vertex` (Veo API) |

See `.env.example` for the full list.

## Project Structure

```
shorts-automation/
├── pipeline.py                 # Main pipeline orchestrator
├── config.py                   # Configuration
├── .env.example                # Environment template
├── requirements.txt            # Python dependencies
├── setup.sh                    # Setup script (macOS/Linux)
├── cron_run.sh                 # Cron automation script
├── scripts/
│   ├── generate_scripts.py     # Stage 1: Script generation (Gemini)
│   ├── virality_score.py       # Stage 2: Virality scoring gate
│   ├── generate_voice.py       # Stage 3: Voiceover (Edge TTS)
│   ├── generate_video.py       # Stage 4: Video clips (Gemini images)
│   ├── assemble.py             # Stage 5: FFmpeg assembly
│   ├── upload.py               # Stage 6: YouTube upload
│   ├── analytics.py            # Stage 7: Performance analytics
│   ├── viral_engine.py         # Viral psychology patterns and formulas
│   ├── caption_engine.py       # Animated caption generation
│   ├── sound_design.py         # SFX and audio mixing
│   ├── channel_manager.py      # Multi-channel scheduling
│   ├── content_log.py          # Content tracking
│   ├── topic_history.py        # Topic deduplication
│   └── youtube_auth.py         # YouTube OAuth setup
├── .github/workflows/
│   └── shorts_pipeline.yml     # GitHub Actions (4x daily)
└── output/                     # Generated content (gitignored)
    ├── scripts/                # Script JSON files
    ├── audio/                  # Voiceover MP3 + SRT + ASS
    ├── video/                  # Video clips per script
    ├── assembled/              # Final shorts
    ├── analytics/              # Performance data
    └── sfx/                    # Generated sound effects
```

## Automation

### Cron (Linux/macOS)

```bash
crontab -e
```

Add lines to run at peak YouTube engagement hours:

```
0 6 * * * /path/to/shorts-automation/cron_run.sh >> /path/to/shorts-automation/output/cron.log 2>&1
0 12 * * * /path/to/shorts-automation/cron_run.sh >> /path/to/shorts-automation/output/cron.log 2>&1
0 18 * * * /path/to/shorts-automation/cron_run.sh >> /path/to/shorts-automation/output/cron.log 2>&1
```

### GitHub Actions

The included workflow (`.github/workflows/shorts_pipeline.yml`) runs 4 times daily. Add these secrets to your repo:

- `GEMINI_API_KEY`
- `CLIENT_SECRET_JSON` (contents of `client_secret.json`)
- `YOUTUBE_TOKEN_JSON` (contents of `token.json`)

## License

MIT
