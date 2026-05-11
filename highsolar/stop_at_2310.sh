#!/bin/bash
# Stop scraper at 23:10 Thai time
sleep 1020  # 17 minutes from now
pkill -f "run_every_2min"
echo "Stopped at $(date)" >> /root/.openclaw/workspace/facebook-scraper/stop.log