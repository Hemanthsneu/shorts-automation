# 🎬 Shorts Factory — Command Cheat Sheet

## Daily Commands

```bash
# Generate 3 tech shorts (full pipeline, stops at Veo 3 step)
python pipeline.py --count 3 --niche tech

# Generate 3 AI shorts
python pipeline.py --count 3 --niche ai

# Full auto with placeholder videos (for testing)
python pipeline.py --count 3 --niche tech --fallback --auto-upload

# Check status of everything in pipeline
python pipeline.py --status
```

## Stage-by-Stage

```bash
# Stage 1: Scripts only
python pipeline.py --stage scripts --count 10 --niche tech

# Stage 2: Voice only (processes all unvoiced scripts)
python pipeline.py --stage voice

# Stage 3: Generate Veo 3 prompt sheet
python pipeline.py --stage video

# Stage 3b: Use placeholder clips instead of Veo 3
python pipeline.py --stage video --fallback

# Stage 4: Assemble all ready shorts
python pipeline.py --stage assemble

# Stage 5: Upload — private (for review)
python pipeline.py --stage upload --privacy private

# Stage 5: Upload — public with 8hr stagger
python pipeline.py --stage upload --privacy public --stagger 8

# Stage 5: Upload specific scripts only
python pipeline.py --stage upload --scripts B20260302_001 B20260302_002

# Dry run (see what would upload)
python pipeline.py --stage upload --dry-run
```

## Cron Automation

```bash
# Edit crontab
crontab -e

# Daily at 6 AM: 2 tech shorts, auto-upload, stagger 8 hrs apart
0 6 * * * cd ~/shorts-automation && python pipeline.py --count 2 --niche tech --fallback --auto-upload --privacy public --stagger 8 >> output/logs/cron.log 2>&1

# Daily at 7 AM: 2 AI shorts
0 7 * * * cd ~/shorts-automation && python pipeline.py --count 2 --niche ai --fallback --auto-upload --privacy public --stagger 8 >> output/logs/cron.log 2>&1

# Weekly Sunday batch: 10 scripts for the week
0 10 * * 0 cd ~/shorts-automation && python pipeline.py --stage scripts --count 10 --niche tech >> output/logs/cron.log 2>&1
```

## Semi-Auto Workflow (Recommended for Quality)

```bash
# Sunday: Batch generate scripts + voice for the whole week
python pipeline.py --stage scripts --count 14 --niche tech
python pipeline.py --stage voice

# Sunday: Get Veo 3 prompt sheet
python pipeline.py --stage video
# → Open output/veo3_prompts.md
# → Paste prompts into Veo 3 (work account)
# → Download clips to output/video/{script_id}/

# Wednesday: Check what's ready, assemble, schedule uploads
python pipeline.py --status
python pipeline.py --stage assemble
python pipeline.py --stage upload --privacy public --stagger 12
```

## Useful Voice Options

```bash
# List available voices
python scripts/generate_voice.py --list-voices

# Override voice for a batch
python scripts/generate_voice.py --voice en-GB-RyanNeural
python scripts/generate_voice.py --voice en-US-JennyNeural
```
