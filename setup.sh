#!/bin/bash
# 🎬 Shorts Factory — One-Command Setup
# Run: chmod +x setup.sh && ./setup.sh

set -e

echo ""
echo "============================================"
echo "  🎬 Shorts Factory — Setup"
echo "============================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Install it first."
    exit 1
fi
echo "✅ Python 3 found: $(python3 --version)"

# Check FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg not found. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install ffmpeg
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update && sudo apt-get install -y ffmpeg
    else
        echo "❌ Please install FFmpeg manually: https://ffmpeg.org/download.html"
        exit 1
    fi
fi
echo "✅ FFmpeg found: $(ffmpeg -version 2>&1 | head -1)"

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt --quiet

# Create .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "📝 Created .env from template — edit it with your API keys"
else
    echo "✅ .env already exists"
fi

# Create directory structure
echo ""
echo "📁 Creating directory structure..."
mkdir -p output/{scripts,audio,video,assembled,logs}
mkdir -p assets/{fonts,music,overlays}

# Download a free background music track placeholder
echo "🎵 Note: Add royalty-free music to assets/music/"
echo "   Recommended: YouTube Audio Library (free)"
echo "   https://studio.youtube.com/channel/UC/music"

echo ""
echo "============================================"
echo "  ✅ Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo ""
echo "  1. Edit .env with your Gemini API key:"
echo "     nano .env"
echo ""
echo "  2. Set up YouTube OAuth (one-time):"
echo "     python scripts/youtube_auth.py"
echo ""
echo "  3. Test the pipeline:"
echo "     python pipeline.py --count 1 --niche tech --fallback"
echo ""
echo "  4. For daily automation, add to crontab:"
echo "     crontab -e"
echo "     0 6 * * * cd $(pwd) && python pipeline.py --count 2 --niche tech --fallback --auto-upload --privacy public >> output/logs/cron.log 2>&1"
echo ""
echo "  Or import n8n/workflow.json into n8n for visual automation."
echo ""
