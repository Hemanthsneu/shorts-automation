#!/bin/bash
# ──────────────────────────────────────────────────
# 🚀 Shorts Factory — MONETIZATION SPRINT
# ──────────────────────────────────────────────────
# Posts 3 Shorts/day at YouTube peak engagement hours.
# Uses controversy-scored trending topics for max reach.
#
# CRON SETUP (run: crontab -e, then paste these 3 lines):
#
#   0 6 * * * /Users/hemanth/Downloads/files\ \(3\)/shorts-automation/cron_run.sh >> /Users/hemanth/Downloads/files\ \(3\)/shorts-automation/output/cron.log 2>&1
#   0 12 * * * /Users/hemanth/Downloads/files\ \(3\)/shorts-automation/cron_run.sh >> /Users/hemanth/Downloads/files\ \(3\)/shorts-automation/output/cron.log 2>&1
#   0 18 * * * /Users/hemanth/Downloads/files\ \(3\)/shorts-automation/cron_run.sh >> /Users/hemanth/Downloads/files\ \(3\)/shorts-automation/output/cron.log 2>&1
#
# = 3 Shorts/day × 14 days = 42 viral Shorts
# ──────────────────────────────────────────────────

cd "/Users/hemanth/Downloads/files (3)/shorts-automation"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

# High-viral-potential niches (weighted by past performance)
# AI + Sports + PopCulture = highest engagement historically
HIGH_WEIGHT=(ai sports popculture ai sports popculture tech cinema)
MED_WEIGHT=(finance science gaming space history)
ALL_NICHES=("${HIGH_WEIGHT[@]}" "${MED_WEIGHT[@]}")

# Pick 1 random niche (weighted toward high performers)
NICHE=$(python3 -c "import random; print(random.choice('${ALL_NICHES[*]}'.split()))")

HOUR=$(date '+%H')
case $HOUR in
  05|06|07) SLOT="🌅 Morning" ;;
  11|12|13) SLOT="☀️ Midday" ;;
  17|18|19) SLOT="🌆 Evening" ;;
  *) SLOT="⏰ Manual" ;;
esac

echo ""
echo "════════════════════════════════════════════════"
echo "  🚀 MONETIZATION SPRINT — $SLOT Run"
echo "  📅 $(date '+%Y-%m-%d %H:%M:%S')"
echo "  🎯 Niche: ${NICHE}"  
echo "════════════════════════════════════════════════"

python3 pipeline.py --count 1 --niche "$NICHE" --fallback --auto-upload --privacy public

echo "✅ Done at $(date '+%H:%M:%S')"
