#!/bin/bash
#
# Facebook Scraper - Setup Script
# Run this on your Windows machine (with Python installed)
#

echo "=================================="
echo "🤖 Facebook Group Scraper Setup"
echo "=================================="

# Check Python
echo ""
echo "📌 Checking Python..."
python --version || python3 --version

# Install requirements
echo ""
echo "📌 Installing Playwright..."
pip install playwright

echo ""
echo "📌 Installing Chromium browser..."
playwright install chromium

echo ""
echo "📌 Installing other dependencies..."
pip install pyyaml

echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit config.json - add your Facebook Group IDs"
echo "2. Edit fb_session.json - leave as-is for first run"
echo "3. Run: python scraper.py"
echo ""
echo "For cron job (every 3 hours):"
echo "0 */3 * * * cd /path/to/facebook-scraper && python scraper.py >> bot.log 2>&1"
echo ""