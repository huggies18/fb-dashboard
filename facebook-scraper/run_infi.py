#!/usr/bin/env python3
"""
/run_infi - Continuous workflow: /run every 2-3 minutes
======================================================
- Run /run workflow
- Wait 2-3 minutes
- Repeat forever
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/facebook-scraper')
import subprocess
import time
import asyncio
from datetime import datetime, timedelta
from telegram import Bot

BOT_TOKEN = '8774902841:AAFveLJDs-Bf02cPkBhZVPU5JBw_sdLIhNw'
ADMIN_USER_IDS = [6780942246, 8698062232]  # Tibodin, Nick
THAI_OFFSET = timedelta(hours=7)

def thai_time_str():
    return (datetime.now() + THAI_OFFSET).strftime("%H:%M:%S")

async def send_telegram(msg):
    bot = Bot(token=BOT_TOKEN)
    for uid in ADMIN_USER_IDS:
        await bot.send_message(chat_id=uid, text=msg)

async def main():
    print("="*60)
    print(f"[{thai_time_str()}] 🚀 /run_infi - Continuous Workflow")
    print("="*60)
    
    await send_telegram(f"🔄 /run_infi เริ่มทำงาน\n⏰ เริ่ม: {thai_time_str()}\n🔁 รันทุก 2-3 นาที")
    
    count = 0
    while True:
        count += 1
        print(f"\n[{thai_time_str()}] === รอบที่ {count} ===")
        
        # Run /run workflow
        try:
            result = subprocess.run(
                ['python3', 'run_workflow.py'],
                cwd='/root/.openclaw/workspace/facebook-scraper',
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                print(f"[{thai_time_str()}] ✅ รอบที่ {count} เสร็จ")
                await send_telegram(f"✅ รอบที่ {count} เสร็จ")
            else:
                print(f"[{thai_time_str()}] ❌ รอบที่ {count} ผิดพลาด")
                await send_telegram(f"❌ รอบที่ {count} ผิดพลาด")
        
        except Exception as e:
            print(f"[{thai_time_str()}] ❌ Error: {e}")
            await send_telegram(f"❌ รอบที่ {count} ผิดพลาด: {str(e)[:100]}")
        
        # Wait 2-3 minutes (random)
        wait_min = 2
        wait_max = 3
        wait = (wait_min * 60) + (wait_max - wait_min) * 60 * (time.time() % 1)
        print(f"[{thai_time_str()}] ⏳ พัก {wait_min}-{wait_max} นาที...")
        time.sleep(wait * 60 / 60)  # Simplified: 2-3 minutes

if __name__ == "__main__":
    asyncio.run(main())