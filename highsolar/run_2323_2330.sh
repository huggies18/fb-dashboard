#!/bin/bash
# Run scraper from 23:23 to 23:30 Thai time, report every minute
# Thai time = UTC + 7

THAI_HOUR=23
THAI_MIN=23

cd /root/.openclaw/workspace/facebook-scraper

echo "=== Starting at $(date) UTC ==="
echo "Will run until Thai time 23:30 (UTC 16:30)"

# Calculate seconds until Thai time 23:23
# Thai 23:23 = UTC 16:23, but we need to check if we passed it
TARGET_HOUR=16
TARGET_MIN=23

for i in {1..8}; do
    echo "=== Run $i at $(date) UTC ==="
    
    # Get count before
    BEFORE=$(python3 -c "import sqlite3; conn=sqlite3.connect('comments.db'); print(conn.execute('SELECT COUNT(*)').fetchone()[0])" 2>/dev/null || echo "0")
    
    # Run scraper
    python3 scraper_v3.py >> bot.log 2>&1
    
    # Get count after
    AFTER=$(python3 -c "import sqlite3; conn=sqlite3.connect('comments.db'); print(conn.execute('SELECT COUNT(*)').fetchone()[0])" 2>/dev/null || echo "0")
    
    NEW=$((AFTER - BEFORE))
    
    echo "New posts: $NEW | Total: $AFTER"
    
    # Sleep 1 minute
    sleep 60
done

echo "=== Done at $(date) UTC ==="