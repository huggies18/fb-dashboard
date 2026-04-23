#!/bin/bash
# Simple HTTP server to serve CSV files
cd /root/.openclaw/workspace/facebook-scraper/csv_exports
python3 -m http.server 8080