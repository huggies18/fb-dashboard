#!/usr/bin/env python3
"""
Cron Manager - จัดการ Cronjobs สำหรับ Facebook Scraper
=======================================================
Commands:
  /cron list          - แสดง cronjobs ปัจจุบัน
  /cron add X.Y       - เพิ่ม cronjob ทุก X ชั่วโมง Y นาที
  /cron remove        - ลบ cronjob ทั้งหมด
  /cron status        - แสดงสถานะ cronjob ล่าสุน
"""

import sys
import os
import json
import asyncio
from datetime import datetime, timedelta
from telegram import Bot

sys.path.insert(0, '.')

# Config
TELEGRAM_TOKEN = '8774902841:AAFveLJDs-Bf02cPkBhZVPU5JBw_sdLIhNw'
ADMIN_USER_ID = 6780942246
CRON_STATE_FILE = '/root/.openclaw/workspace/facebook-scraper/cron_state.json'

THAI_OFFSET = timedelta(hours=7)

def thai_time_str():
    return (datetime.now() + THAI_OFFSET).strftime("%Y-%m-%d %H:%M:%S")

def load_state():
    if os.path.exists(CRON_STATE_FILE):
        with open(CRON_STATE_FILE, 'r') as f:
            return json.load(f)
    return {'active': False, 'interval_minutes': 0, 'last_run': None, 'total_runs': 0}

def save_state(state):
    with open(CRON_STATE_FILE, 'w') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def get_cron_jobs():
    """Get current cronjobs for this script"""
    result = os.popen('crontab -l 2>/dev/null | grep runall_cron').read()
    return result.strip()

def add_cronjob(interval_minutes):
    """Add a cronjob to run every X minutes"""
    script_path = '/root/.openclaw/workspace/facebook-scraper/runall_cron.sh'
    
    # Remove existing cron first
    os.system('crontab -l 2>/dev/null | grep -v runall_cron | crontab - 2>/dev/null')
    
    # Add new cron (run every X minutes)
    cron_line = f"*/{interval_minutes} * * * * bash {script_path} >> {os.path.dirname(script_path)}/cron.log 2>&1"
    os.system(f'(crontab -l 2>/dev/null; echo "{cron_line}") | crontab -')
    
    state = load_state()
    state['active'] = True
    state['interval_minutes'] = interval_minutes
    save_state(state)
    
    return True

def remove_cronjob():
    """Remove all cronjobs for this script"""
    os.system('crontab -l 2>/dev/null | grep -v runall_cron | crontab - 2>/dev/null')
    
    state = load_state()
    state['active'] = False
    state['interval_minutes'] = 0
    save_state(state)
    
    return True

async def send_message(text):
    bot = Bot(token=TELEGRAM_TOKEN)
    try:
        msg = await bot.send_message(chat_id=ADMIN_USER_ID, text=text)
        print(f"[DEBUG] Sent message {msg.message_id}")
    except Exception as e:
        print(f"[ERROR] Failed to send: {e}")
    await bot.close()
    return

async def handle_cron_command(args):
    """Handle /cron command"""
    if not args:
        await send_message("📋 Cron Manager\n\nCommands:\n/cron list - แสดง cronjobs\n/cron add X.Y - เพิ่ม cronjob (X ชม Y นาที)\n/cron remove - ลบ cronjob ทั้งหมด\n/cron status - สถานะ")
        return
    
    cmd = args[0].lower()
    
    if cmd == 'list':
        jobs = get_cron_jobs()
        state = load_state()
        status = "✅ เปิดอยู่" if state['active'] else "❌ ปิดอยู่"
        msg = f"📋 Cron Jobs\n\nสถานะ: {status}"
        if state['active']:
            msg += f"\n⏰ ทุก {state['interval_minutes']} นาที"
        if state['last_run']:
            msg += f"\n🕐 รันล่าสุด: {state['last_run']}"
        msg += f"\n📊 รันไปแล้ว: {state['total_runs']} ครั้ง"
        if jobs:
            msg += f"\n\nCronjobs:\n{jobs}"
        else:
            msg += "\n\n(ไม่มี cronjobs)"
        await send_message(msg)
    
    elif cmd == 'add':
        if len(args) < 2:
            await send_message("❌ ระบุเวลา\nExample: /cron add 0.5 (30 นาที) หรือ /cron add 1.0 (1 ชม)")
            return
        
        try:
            hours = float(args[1])
            total_minutes = int(hours * 60)
            if total_minutes < 1:
                await send_message("❌ ต้องมากกว่า 1 นาที")
                return
            
            add_cronjob(total_minutes)
            h = int(hours)
            m = int((hours - h) * 60)
            time_str = ""
            if h > 0:
                time_str += f"{h} ชั่วโมง"
            if m > 0:
                time_str += f" {m} นาที"
            await send_message(f"✅ เพิ่ม cronjob แล้ว!\n⏰ ทุก{time_str}\n🗑️ พิมพ์ /cron remove เพื่อลบ")
        except ValueError:
            await send_message("❌ รูปแบบไม่ถูกต้อง\nExample: /cron add 0.5 หรือ /cron add 1.0")
    
    elif cmd == 'remove':
        remove_cronjob()
        await send_message("✅ ลบ cronjob ทั้งหมดแล้ว!")
    
    elif cmd == 'status':
        state = load_state()
        jobs = get_cron_jobs()
        status = "✅ เปิดอยู่" if state['active'] else "❌ ปิดอยู่"
        msg = f"📊 Cron Status\n\nสถานะ: {status}"
        if state['active']:
            msg += f"\n⏰ ทุก {state['interval_minutes']} นาที"
        if state['last_run']:
            msg += f"\n🕐 รันล่าสุด: {state['last_run']}"
        msg += f"\n📊 รันไปแล้ว: {state['total_runs']} ครั้ง"
        await send_message(msg)
    
    else:
        await send_message("❌ คำสั่งไม่ถูกต้อง\n\nCommands:\n/cron list\n/cron add X.Y\n/cron remove\n/cron status")


if __name__ == '__main__':
    args = sys.argv[1:]
    
    async def main():
        await handle_cron_command(args)
        print("✅ Cron command executed")
    
    asyncio.run(main())
