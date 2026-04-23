#!/bin/bash
# Run scraper from 23:20 to 23:30, report every minute

START_TIME=$(date -d "23:20" +%s)
END_TIME=$(date -d "23:30" +%s)
NOW=$(date +%s)

# If it's already past 23:20 today, schedule for tomorrow
if [ $NOW -gt $START_TIME ]; then
    START_TIME=$((START_TIME + 86400))
    END_TIME=$((END_TIME + 86400))
fi

echo "Will start at $(date -d @$START_TIME)"

# Wait until start time
sleep $((START_TIME - NOW))

echo "=== Started at $(date) ==="

cd /root/.openclaw/workspace/facebook-scraper

# Run for 10 minutes (until 23:30)
for i in {1..10}; do
    echo "=== Run $i at $(date) ==="
    
    # Get count before
    BEFORE=$(python3 -c "import sqlite3; conn=sqlite3.connect('comments.db'); print(conn.execute('SELECT COUNT(*)').fetchone()[0])" 2>/dev/null || echo "0")
    
    # Run scraper
    python3 scraper_v3.py >> bot.log 2>&1
    
    # Get count after
    AFTER=$(python3 -c "import sqlite3; conn=sqlite3.connect('comments.db'); print(conn.execute('SELECT COUNT(*)').fetchone()[0])" 2>/dev/null || echo "0")
    
    NEW=$((AFTER - BEFORE))
    
    echo "New posts this run: $NEW (Total: $AFTER)"
    
    # Sleep 1 minute
    sleep 60
done

echo "=== Stopped at $(date) ==="
pkill -f "run_every_2min" 2>/dev/null
echo "All stopped"