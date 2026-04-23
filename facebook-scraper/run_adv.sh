#!/bin/bash
cd /root/.openclaw/workspace/facebook-scraper
python3 scraper_advanced.py > /tmp/scraper_output.log 2>&1
echo "Exit code: $?" >> /tmp/scraper_output.log