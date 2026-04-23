#!/bin/bash
# Run /fbuyer then /wbuyer every 5 minutes for 20 minutes
# Start: now, every 5 min x 4 times
# Usage: ./run_loop.sh

cd /root/.openclaw/workspace/facebook-scraper

echo "=========================================="
echo "🚀 STARTING LOOP: /fbuyer → /wbuyer"
echo "=========================================="
echo "Start time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Runs: 4 times (every 5 minutes)"
echo "=========================================="

LOG_FILE="/root/.openclaw/workspace/facebook-scraper/loop_fbuyer.log"

for i in 1 2 3 4; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "" >> $LOG_FILE
    echo "========== RUN $i: $TIMESTAMP ==========" >> $LOG_FILE
    
    echo "[$TIMESTAMP] === RUN $i: Running /fbuyer ==="
    echo "[$TIMESTAMP] === RUN $i: Running /fbuyer ===" >> $LOG_FILE
    python3 scraper_hybrid.py >> $LOG_FILE 2>&1
    
    echo "[$TIMESTAMP] === RUN $i: Running /wbuyer ==="
    echo "[$TIMESTAMP] === RUN $i: Running /wbuyer ===" >> $LOG_FILE
    python3 -c "import wbuyer_hybrid; wbuyer_hybrid.main()" >> $LOG_FILE 2>&1
    
    echo "[$TIMESTAMP] === RUN $i: COMPLETE ==="
    echo "[$TIMESTAMP] === RUN $i: COMPLETE ===" >> $LOG_FILE
    
    if [ $i -lt 4 ]; then
        echo "[$TIMESTAMP] Sleeping 5 minutes before next run..."
        echo "[$TIMESTAMP] Sleeping 5 minutes before next run..." >> $LOG_FILE
        sleep 300  # 5 minutes
    fi
done

echo ""
echo "=========================================="
echo "✅ ALL 4 RUNS COMPLETE!"
echo "End time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="