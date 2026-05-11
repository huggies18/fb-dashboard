#!/usr/bin/env python3
"""
/rbuyer - Clear leads folder
===========================
ล้างโพสที่เก็บมาของ Buyer จาก leads folder
"""

import sys
sys.path.insert(0, '.')

import os, asyncio
from datetime import datetime, timedelta
from telegram import Bot

THAI_OFFSET = timedelta(hours=7)
LEADS_DIR = "/root/.openclaw/workspace/highsolar/leads"
PENDING_DIR = "/root/.openclaw/workspace/highsolar/pending"

BOT_TOKEN = '8774902841:AAFveLJDs-Bf02cPkBhZVPU5JBw_sdLIhNw'
USER_ID = '6780942246'

def thai_time_str():
    return (datetime.now() + THAI_OFFSET).strftime("%H:%M:%S")

def log(msg):
    print(f"[{thai_time_str()}] {msg}")

async def send_notify(count):
    bot = Bot(token=BOT_TOKEN)
    thai_now = datetime.now() + THAI_OFFSET
    
    msg = f"🗑️ <b>ล้าง Leads แล้ว!</b>\n\n"
    msg += f"⏰ เมื่อ: {thai_now.strftime('%H:%M')} (UTC+7)\n"
    msg += f"🗑️ ลบไฟล์: {count} files\n\n"
    msg += f"✅ Leads folder ว่างแล้ว\n"
    msg += f"💡 พิมพ์ /fbuyer เพื่อหา leads ใหม่\n"
    
    await bot.send_message(chat_id=USER_ID, text=msg, parse_mode='HTML')

def main():
    log("="*50)
    log("🗑️ CLEAR LEADS")
    log("="*50)
    
    # Clear leads folder
    lead_files = [f for f in os.listdir(LEADS_DIR) if f.startswith('lead_')]
    pending_files = [f for f in os.listdir(PENDING_DIR) if f.startswith('pending_')]
    
    total_files = len(lead_files) + len(pending_files)
    
    if not total_files:
        log("❌ ไม่มีไฟล์ที่ต้องลบ")
        log("💡 Leads folder ว่างอยู่แล้ว")
        return
    
    log(f"📁 Found {len(lead_files)} lead files + {len(pending_files)} pending files")
    
    deleted_count = 0
    
    # Delete lead files
    for fname in lead_files:
        fpath = os.path.join(LEADS_DIR, fname)
        try:
            os.remove(fpath)
            deleted_count += 1
            log(f"   🗑️ Deleted: {fname}")
        except Exception as e:
            log(f"   ❌ Failed to delete {fname}: {e}")
    
    # Delete pending files
    for fname in pending_files:
        fpath = os.path.join(PENDING_DIR, fname)
        try:
            os.remove(fpath)
            deleted_count += 1
            log(f"   🗑️ Deleted: {fname}")
        except Exception as e:
            log(f"   ❌ Failed to delete {fname}: {e}")
    
    log(f"\n✅ ลบสำเร็จ {deleted_count}/{total_files} files")
    
    # Notify Telegram
    asyncio.run(send_notify(deleted_count))
    
    log("="*50)

if __name__ == "__main__":
    main()