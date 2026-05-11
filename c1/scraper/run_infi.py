#!/usr/bin/env python3
"""
/run_infi scrap -c1 -[Tibodin|Noty|Nick] - Continuous workflow
=============================================================
- Run scrape workflow
- Wait 2-3 minutes
- Repeat forever
- Send to target based on argument
"""

import sys
import subprocess
import random
import asyncio
from datetime import datetime, timedelta
from telegram import Bot

THAI_OFFSET = timedelta(hours=7)

# Bot Tokens
BOT_TOKEN_OLD = '8774902841:AAFveLJDs-Bf02cPkBhZVPU5JBw_sdLIhNw'
BOT_TOKEN_NOTY = '8641112117:AAFokLi4gAvfqSUPjBz2AqUyGceAsX8M5CE'

# Admin IDs
ADMIN_IDS = {
    'Tibodin': 6780942246,
    'Nick': 8698062232,
    'Noty': 6780942246,  # ส่งไป Tibodin แต่ใช้ NotiBot
}

# Token per target
BOT_TOKEN = {
    'Tibodin': BOT_TOKEN_OLD,
    'Nick': BOT_TOKEN_OLD,
    'Noty': BOT_TOKEN_NOTY,
}

def thai_time_str():
    return (datetime.now() + THAI_OFFSET).strftime("%H:%M:%S")

async def send_telegram(msg, target):
    bot = Bot(token=BOT_TOKEN[target])
    uid = ADMIN_IDS[target]
    await bot.send_message(chat_id=uid, text=msg)

def main():
    # Get target from last argument
    # Format: /run_infi scrap -c1 -Noty
    target = 'Tibodin'
    for arg in sys.argv:
        if arg in ['Tibodin', 'Nick', 'Noty']:
            target = arg
            break
    
    print("="*60)
    print(f"[{thai_time_str()}] 🚀 /run_infi C1 - Continuous Workflow")
    print(f"📤 ส่งไป: {target}")
    print("="*60)
    
    async def run_loop():
        await send_telegram(f"🔄 /run_infi C1 เริ่มทำงาน\n📤 ส่งไป: {target}\n⏰ เริ่ม: {thai_time_str()} (UTC+7)\n🔁 รันทุก 2-3 นาที", target)
        
        count = 0
        while True:
            count += 1
            print(f"\n[{thai_time_str()}] 🔄 รอบที่ {count}")
            
            # Run workflow
            result = subprocess.run(
                [sys.executable, 'run_workflow.py', target],
                capture_output=True, text=True,
                cwd='/root/.openclaw/workspace/c1/scraper'
            )
            
            if result.returncode == 0:
                print(f"[{thai_time_str()}] ✅ จบรอบที่ {count}")
                await send_telegram(f"✅ จบรอบที่ {count}/{target}", target)
            else:
                print(f"[{thai_time_str()}] ❌ รอบที่ {count} failed")
                await send_telegram(f"❌ จบรอบที่ {count} - ผิดพลาด", target)
            
            # Wait 2-3 minutes
            wait = random.uniform(120, 180)
            print(f"[{thai_time_str()}] 💤 รอ {wait:.0f}วินาที ก่อนรอบต่อไป")
            await asyncio.sleep(wait)
    
    asyncio.run(run_loop())

if __name__ == "__main__":
    main()