#!/bin/bash
# Cronjob Script - Run /fbuyer repeatedly then /wbuyer
# Usage: ./cron_fbuyer.sh <X.Y>
# X.Y = X hours Y minutes
# Example: ./cron_fbuyer.sh 0.10 (10 minutes)
#          ./cron_fbuyer.sh 1.0  (1 hour)
#          ./cron_fbuyer.sh 2.30 (2 hours 30 minutes)

if [ -z "$1" ]; then
    echo "Usage: ./cron_fbuyer.sh <X.Y>"
    echo "Example: ./cron_fbuyer.sh 0.10 (10 minutes)"
    echo "         ./cron_fbuyer.sh 0.50 (50 minutes)"
    echo "         ./cron_fbuyer.sh 1.0  (1 hour)"
    echo "         ./cron_fbuyer.sh 2.30 (2 hours 30 minutes)"
    exit 1
fi

INPUT=$1
cd /root/.openclaw/workspace/facebook-scraper

# ==================== PARSE X.Y FORMAT ====================
# X.Y = X hours Y minutes
# Y must be 2 digits for minutes (e.g., 10, 30, 43)
# Example: 1.54 = 1 hour 54 minutes

# Split into hours and minutes
HOURS=$(echo $INPUT | cut -d'.' -f1)
MINUTES=$(echo $INPUT | cut -d'.' -f2)

# Ensure MINUTES is 2 digits (pad if necessary)
if [ ${#MINUTES} -eq 1 ]; then
    MINUTES="0${MINUTES}"
fi

# Convert to integer
HOURS=$((10#$HOURS))
MINUTES=$((10#$MINUTES))

# Calculate total minutes
TOTAL_MINUTES=$((HOURS * 60 + MINUTES))

# Validation
if [ $TOTAL_MINUTES -eq 0 ]; then
    echo "Error: Total minutes must be greater than 0"
    exit 1
fi

# ==================== CONFIG ====================
INTERVAL=5  # minutes between /fbuyer runs

LOG_FILE="/root/.openclaw/workspace/facebook-scraper/cron_fbuyer.log"

# ==================== START ====================
echo "=========================================="
echo "🚀 CRONJOB STARTED"
echo "=========================================="
echo "Time: $(date '+%Y-%m-%d %H:%M:%S' -d '+7 hours')"
echo "Duration: $INPUT"
echo "Hours: $HOURS, Minutes: $MINUTES"
echo "Total: $TOTAL_MINUTES minutes"
echo "Interval: every $INTERVAL minutes"
echo "=========================================="

# Calculate number of runs
RUNS=$((TOTAL_MINUTES / INTERVAL))
if [ $((TOTAL_MINUTES % INTERVAL)) -gt 0 ]; then
    RUNS=$((RUNS + 1))
fi

echo "Expected runs: $RUNS"
echo "=========================================="

# ==================== MAIN LOOP ====================
for i in $(seq 1 $RUNS); do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S' -d '+7 hours')
    ELAPSED=$((i * INTERVAL))
    
    echo "" >> $LOG_FILE
    echo "========== RUN $i: $TIMESTAMP (${ELAPSED}/${TOTAL_MINUTES} min) ==========" >> $LOG_FILE
    
    echo "[$i] Running /fbuyer at $TIMESTAMP (${ELAPSED}/${TOTAL_MINUTES} min)..."
    python3 scraper_hybrid.py >> $LOG_FILE 2>&1
    
    if [ $i -lt $RUNS ]; then
        echo "[$i] Waiting $INTERVAL minutes before next run..."
        sleep ${INTERVAL}m
    fi
done

# ==================== FINAL /wbuyer ====================
echo "" >> $LOG_FILE
echo "========== FINAL: $(date '+%Y-%m-%d %H:%M:%S' -d '+7 hours') ==========" >> $LOG_FILE
echo "Running /wbuyer to export..." >> $LOG_FILE

echo ""
echo "=========================================="
echo "⏰ Duration complete! Running /wbuyer..."
echo "=========================================="

python3 wbuyer_hybrid.py >> $LOG_FILE 2>&1

echo "" >> $LOG_FILE
echo "========== COMPLETED: $(date '+%Y-%m-%d %H:%M:%S' -d '+7 hours') ==========" >> $LOG_FILE
echo "=========================================="
echo "✅ CRONJOB COMPLETED!"
echo "=========================================="
echo "Log file: $LOG_FILE"
