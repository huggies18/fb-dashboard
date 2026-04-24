#!/bin/bash
# runall_cron.sh - รัน /runall แล้วอัพเดต cron state
# ถูกเรียกทุก X นาทีโดย cron

LOG_FILE="/root/.openclaw/workspace/facebook-scraper/cron.log"
STATE_FILE="/root/.openclaw/workspace/facebook-scraper/cron_state.json"

cd /root/.openclaw/workspace/facebook-scraper

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Cron Run Started ===" >> $LOG_FILE

# Run scrape
python3 scrape_all_posts.py >> $LOG_FILE 2>&1
if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Scrape OK" >> $LOG_FILE
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Scrape FAILED" >> $LOG_FILE
fi

# Run filter
python3 ai_filter_all.py >> $LOG_FILE 2>&1
if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Filter OK" >> $LOG_FILE
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Filter FAILED" >> $LOG_FILE
fi

# Update state
if [ -f $STATE_FILE ]; then
    # Update last_run and increment total_runs
    python3 -c "
import json
with open('$STATE_FILE', 'r') as f:
    state = json.load(f)
state['last_run'] = '$(date '+%Y-%m-%d %H:%M:%S')'
state['total_runs'] = state.get('total_runs', 0) + 1
with open('$STATE_FILE', 'w') as f:
    json.dump(state, f, indent=2)
"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] State updated" >> $LOG_FILE
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Cron Run Complete ===" >> $LOG_FILE
echo "" >> $LOG_FILE
