#!/bin/bash
# ══════════════════════════════════════════════════════
# Shorts Factory v2.0 — Viral Intelligence Cron Runner
# ══════════════════════════════════════════════════════
# Posts viral shorts at YouTube peak engagement hours.
# Uses Viral Intelligence Engine for maximum reach.
#
# CRON SETUP (run: crontab -e, then paste):
#   0 6 * * * /path/to/shorts-automation/ngm/cron_run.sh >> /path/to/shorts-automation/ngm/output/cron.log 2>&1
#   0 12 * * * /path/to/shorts-automation/ngm/cron_run.sh >> /path/to/shorts-automation/ngm/output/cron.log 2>&1
#   0 18 * * * /path/to/shorts-automation/ngm/cron_run.sh >> /path/to/shorts-automation/ngm/output/cron.log 2>&1
#   0 22 * * * /path/to/shorts-automation/ngm/cron_run.sh >> /path/to/shorts-automation/ngm/output/cron.log 2>&1
#
# = 4 Shorts/day, virality-gated, analytics-driven
# ══════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

# Niche rotation weighted by past performance
HIGH_WEIGHT=(ai sports popculture ai sports ai popculture science)
MED_WEIGHT=(tech cinema history)
ALL_NICHES=("${HIGH_WEIGHT[@]}" "${MED_WEIGHT[@]}")

NICHE=$(python3 -c "import random; print(random.choice('${ALL_NICHES[*]}'.split()))")

HOUR=$(date '+%H')
case $HOUR in
  05|06|07) SLOT="Morning" ;;
  11|12|13) SLOT="Midday" ;;
  17|18|19) SLOT="Evening" ;;
  21|22|23) SLOT="Night" ;;
  *) SLOT="Manual" ;;
esac

echo ""
echo "════════════════════════════════════════════════"
echo "  VIRAL PIPELINE v2.0 — $SLOT Run"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "  Niche: ${NICHE}"
echo "════════════════════════════════════════════════"

# Generate 2 scripts, virality gate keeps the best 1
python3 pipeline.py --count 1 --niche "$NICHE" --fallback --auto-upload --privacy public

echo "Done at $(date '+%H:%M:%S')"
