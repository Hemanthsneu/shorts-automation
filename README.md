# 🎬 Shorts Factory — Fully Automated Pipeline

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  1. SCRIPT   │───▶│  2. VOICE   │───▶│  3. VIDEO   │───▶│  4. ASSEMBLE │───▶│  5. UPLOAD  │
│  (Gemini)    │    │  (Edge TTS) │    │  (Veo 3 *)  │    │  (FFmpeg)    │    │  (YT API)   │
└─────────────┘    └─────────────┘    └─────────────┘    └──────────────┘    └─────────────┘
       │                  │                  │                   │                   │
       ▼                  ▼                  ▼                   ▼                   ▼
  scripts/*.json    audio/*.mp3       video/*.mp4        assembled/*.mp4     ✅ Published
```

**\* Veo 3 Note:** Veo 3 API is available via Vertex AI. If you prefer manual Veo 3 generation
through the Gemini app, the pipeline supports a "semi-auto" mode — it generates all scripts
and prompts, you paste prompts into Veo 3, drop clips into the folder, and automation handles
the rest.

## Quick Start

```bash
# 1. Clone to your machine
cp -r shorts-automation ~/shorts-automation
cd ~/shorts-automation

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up config
cp .env.example .env
# Edit .env with your API keys

# 4. One-time YouTube OAuth setup
python scripts/youtube_auth.py

# 5. Run the full pipeline (content → YouTube in one go)
python pipeline.py --count 5 --niche tech --fallback --auto-upload --privacy public --stagger 8

# 6. Or use the one-click script (Windows)
.\run_full_pipeline.ps1 -Niche tech -Count 2 -Upload -Stagger 8

# 7. Daily automation: cron (Linux/Mac) or Task Scheduler (Windows)
# Linux/Mac: crontab -e → 0 6 * * * cd ~/shorts-automation && python pipeline.py --count 2 --niche tech --fallback --auto-upload --privacy public --stagger 8
# Windows: see docs/WINDOWS_SCHEDULER.md
```

## Setup Guide

### API Keys Needed

| Service | How to Get | Cost |
|---------|-----------|------|
| Gemini API | ai.google.dev → Get API Key (free tier: 60 RPM) | Free with your Ultra sub |
| YouTube Data API | console.cloud.google.com → Enable YouTube Data API v3 | Free |
| Edge TTS | No key needed — it's free and runs locally | Free |

### YouTube OAuth Setup (One-Time)

1. Go to [Google Cloud Console](https://console.cloud.google.com/) — **use your PERSONAL Google account**
2. Create new project: "Shorts Factory"
3. Enable **YouTube Data API v3**
4. Create OAuth 2.0 credentials (Desktop Application)
5. Download `client_secret.json` → place in project root
6. Run `python scripts/youtube_auth.py` → authorize in browser
7. This creates `token.json` — pipeline uses this for uploads

## End-to-end automation (content → YouTube)

The **full automation pipeline** runs all five stages in one go: script → voice → video (AI) → assemble → upload.

| What you want | Command |
|---------------|--------|
| One-shot full run (recommended) | `python pipeline.py --count 2 --niche tech --fallback --auto-upload --privacy public --stagger 8` |
| Windows one-click | `.\run_full_pipeline.ps1` or double-click `run_full_pipeline.bat` |
| Upload as private first (review before public) | `python pipeline.py --count 2 --niche tech --fallback --auto-upload --privacy private` |
| Daily on a schedule | **Windows:** [docs/WINDOWS_SCHEDULER.md](docs/WINDOWS_SCHEDULER.md) • **Linux/Mac:** cron (see COMMANDS.md) |

**Strategy and stages:** See [PIPELINE_STRATEGY.md](PIPELINE_STRATEGY.md) for the full strategy (what each stage does and how to run stages individually).

### Folder Structure
```
shorts-automation/
├── pipeline.py              # Main orchestrator
├── config.py                # Configuration & settings
├── PIPELINE_STRATEGY.md      # Full strategy: content → YouTube
├── run_full_pipeline.ps1    # One-click full pipeline (Windows)
├── run_full_pipeline.bat     # One-click full pipeline (Windows, double-click)
├── .env                     # API keys (never commit)
├── .env.example             # Template
├── requirements.txt         # Python deps
├── client_secret.json       # YouTube OAuth (you provide)
├── token.json               # YouTube auth token (auto-generated)
├── docs/
│   └── WINDOWS_SCHEDULER.md # Schedule daily runs on Windows
├── scripts/
│   ├── generate_scripts.py  # Stage 1: Gemini script generation
│   ├── generate_voice.py    # Stage 2: Edge TTS voiceover
│   ├── generate_video.py    # Stage 3: Veo 3 prompt generator + Vertex AI
│   ├── assemble.py          # Stage 4: FFmpeg video assembly
│   ├── upload.py            # Stage 5: YouTube upload
│   └── youtube_auth.py      # One-time OAuth setup
├── n8n/
│   └── workflow.json        # n8n workflow (alternative to cron)
├── output/
│   ├── scripts/             # Generated scripts + metadata
│   ├── audio/               # Voiceover MP3s
│   ├── video/               # Veo 3 clips (manual or API)
│   ├── assembled/           # Final shorts ready to upload
│   └── logs/                # Pipeline run logs
└── assets/
    ├── fonts/               # Caption fonts
    ├── music/               # Background music tracks
    └── overlays/            # Subscribe buttons, logos
```
