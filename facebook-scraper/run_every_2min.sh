#!/bin/bash
# Run scraper every 2 minutes
cd /root/.openclaw/workspace/facebook-scraper
while true; do
    echo "=== $(date) - Running scraper ===" >> bot.log
    python3 scraper_v3.py >> bot.log 2>&1
    echo "=== Done. Sleeping 2 minutes ===" >> bot.log
    sleep 120
done