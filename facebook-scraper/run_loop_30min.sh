#!/bin/bash
# Run /fbuyer every 5 minutes for 30 minutes (6 runs)
# Start: now, every 5 min x 6 times

cd /root/.openclaw/workspace/facebook-scraper

echo "=========================================="
echo "🚀 STARTING LOOP: /fbuyer"
echo "=========================================="
echo "Start time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Runs: 6 times (every 5 minutes = 30 min)"
echo "=========================================="

LOG_FILE="/root/.openclaw/workspace/facebook-scraper/loop_fbuyer_30min.log"

for i in 1 2 3 4 5 6; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "" >> $LOG_FILE
    echo "========== RUN $i: $TIMESTAMP ==========" >> $LOG_FILE
    
    echo "[$i] Running /fbuyer at $TIMESTAMP..."
    python3 scraper_hybrid.py >> $LOG_FILE 2>&1
    
    if [ $i -lt 6 ]; then
        echo "[$i] Waiting 5 minutes before next run..."
        sleep 300
    fi
done

echo "" >> $LOG_FILE
echo "========== COMPLETED: $(date '+%Y-%m-%d %H:%M:%S') ==========" >> $LOG_FILE
echo "=========================================="
echo "✅ LOOP COMPLETED! (6 runs)"
echo "=========================================="
echo "Log file: $LOG_FILE"
