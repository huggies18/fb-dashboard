#!/bin/bash
# Run /runall every 5 minutes for 10 minutes total (2 runs)

cd /root/.openclaw/workspace/facebook-scraper

echo "[$(date)] Starting /runall loop - 2 runs, 5 min interval"

# Run 1
echo "[$(date)] Run 1/2 - Starting"
python3 scrape_all_posts.py
if [ $? -eq 0 ]; then
    python3 ai_filter_all.py
    echo "[$(date)] Run 1/2 - Complete"
else
    echo "[$(date)] Run 1/2 - Failed"
fi

# Wait 5 minutes
echo "[$(date)] Waiting 5 minutes..."
sleep 300

# Run 2
echo "[$(date)] Run 2/2 - Starting"
python3 scrape_all_posts.py
if [ $? -eq 0 ]; then
    python3 ai_filter_all.py
    echo "[$(date)] Run 2/2 - Complete"
else
    echo "[$(date)] Run 2/2 - Failed"
fi

echo "[$(date)] Loop complete - 2 runs done"
