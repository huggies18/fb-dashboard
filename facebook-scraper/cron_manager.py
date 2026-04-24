#!/usr/bin/env python3
"""
Cron Manager - จัดการ Cronjobs สำหรับ Facebook Scraper
=======================================================
รองรับ 2 Users:
  - Primary Admin (6780942246): สั่งได้ทุกคำสั่ง
  - Secondary User: สั่งได้เฉพาะ /cron add, /cron status, /cron list, /cron remove

Commands:
  /cron list          - แสดง cronjobs ปัจจุบัน
  /cron add X.Y       - เพิ่ม cronjob ทุก X ชั่วโมง Y นาที
  /cron remove        - ลบ cronjob ทั้งหมด
  /cron status        - แสดงสถานะ cronjob ล่าสุด
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
PRIMARY_ADMIN = 6780942246  # Tibodin
SECONDARY_USER = 8698062232  # First Nick
ALLOWED_USERS = [PRIMARY_ADMIN, SECONDARY_USER]  # Users ที่สามารถรับคำสั่งได้ทั้งหมด
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

async def send_message(text, user_id):
    """ส่งข้อความไปยัง user ที่ระบุ"""
    import asyncio
    bot = Bot(token=TELEGRAM_TOKEN)
    try:
        msg = await bot.send_message(chat_id=user_id, text=text)
        print(f"[DEBUG] Sent message {msg.message_id} to {user_id}")
    except Exception as e:
        print(f"[ERROR] Failed to send to {user_id}: {e}")
    finally:
        await asyncio.sleep(1)
    return

async def handle_cron_command(args, user_id):
    """Handle /cron command with permission check"""
    
    # Check permission - only PRIMARY_ADMIN can use full commands
    is_primary_admin = (user_id == PRIMARY_ADMIN)
    is_secondary_user = (user_id == SECONDARY_USER)
    
    # Limited commands for secondary user
    limited_commands = ['add', 'status', 'list', 'remove']
    
    # All users can use cron commands
    cron_commands = ['list', 'add', 'remove', 'status']
    
    if not args:
        if is_primary_admin:
            await send_message(
                "📋 Cron Manager\n\n"
                "Commands:\n"
                "/cron list - แสดง cronjobs\n"
                "/cron add X.Y - เพิ่ม cronjob (X ชม Y นาที)\n"
                "/cron remove - ลบ cronjob ทั้งหมด\n"
                "/cron status - สถานะ", user_id
            )
        else:
            await send_message(
                "📋 Cron Manager (Limited)\n\n"
                "Commands:\n"
                "/cron list - แสดง cronjobs\n"
                "/cron add X.Y - เพิ่ม cronjob\n"
                "/cron status - สถานะ", user_id
            )
        return
    
    cmd = args[0].lower()
    
    # Check if command is allowed for this user
    if not is_primary_admin and cmd not in limited_commands:
        await send_message("❌ คุณไม่มีสิทธิ์ใช้คำสั่งนี้", user_id)
        return
    
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
        await send_message(msg, user_id)
    
    elif cmd == 'add':
        if len(args) < 2:
            await send_message(
                "❌ ระบุเวลา\n"
                "Example: /cron add 0.5 (30 นาที)\n"
                "หรือ /cron add 1.0 (1 ชม)\n"
                "หรือ /cron add 2.30 (2 ชม 30 นาที)", user_id
            )
            return
        
        try:
            hours = float(args[1])
            total_minutes = int(hours * 60)
            if total_minutes < 1:
                await send_message("❌ ต้องมากกว่า 1 นาที", user_id)
                return
            
            add_cronjob(total_minutes)
            h = int(hours)
            m = int((hours - h) * 60)
            time_str = ""
            if h > 0:
                time_str += f"{h} ชั่วโมง"
            if m > 0:
                time_str += f" {m} นาที"
            
            msg = f"✅ ตั้ง cronjob สำเร็จ!\n"
            msg += f"⏰ ทำงานทุก {time_str}\n"
            msg += f"📊 ทุก {total_minutes} นาที\n\n"
            msg += f"🗑️ พิมพ์ /cron remove เพื่อยกเลิก\n"
            msg += f"📋 พิมพ์ /cron status เพื่อดูสถานะ"
            await send_message(msg, user_id)
            
            # Also notify primary admin
            if user_id != PRIMARY_ADMIN:
                await send_message(
                    f"🔔 แจ้งเตือน: User {user_id} ตั้ง cronjob ทุก {time_str} ({total_minutes} นาที)", 
                    PRIMARY_ADMIN
                )
        except ValueError:
            await send_message(
                "❌ รูปแบบไม่ถูกต้อง\n"
                "Example: /cron add 0.5 หรือ /cron add 1.0 หรือ /cron add 2.30", 
                user_id
            )
    
    elif cmd == 'remove':
        if not is_primary_admin and not is_secondary_user:
            await send_message("❌ คุณไม่มีสิทธิ์ลบ cronjob", user_id)
            return
        
        state = load_state()
        old_interval = state.get('interval_minutes', 0)
        h = old_interval // 60
        m = old_interval % 60
        old_time_str = f"{h} ชั่วโมง {m} นาที" if h > 0 else f"{m} นาที"
        
        remove_cronjob()
        msg = f"✅ ลบ cronjob ทั้งหมดแล้ว!\n"
        msg += f"⏰ ลบการทำงานทุก {old_time_str}"
        await send_message(msg, user_id)
        
        # Notify primary admin
        if user_id != PRIMARY_ADMIN:
            await send_message(
                f"🔔 แจ้งเตือน: User {user_id} ลบ cronjob", 
                PRIMARY_ADMIN
            )
    
    elif cmd == 'status':
        state = load_state()
        status = "✅ เปิดอยู่" if state['active'] else "❌ ปิดอยู่"
        
        msg = f"📊 Cron Status\n\nสถานะ: {status}\n"
        
        if state['active']:
            total_min = state['interval_minutes']
            h = total_min // 60
            m = total_min % 60
            time_str = f"{h} ชั่วโมง {m} นาที" if h > 0 else f"{m} นาที"
            msg += f"⏰ ทำงานทุก {time_str}\n"
            msg += f"📊 ทุก {total_min} นาที\n"
        
        if state['last_run']:
            msg += f"🕐 รันล่าสุด: {state['last_run']}\n"
        
        msg += f"📊 รันไปแล้ว: {state['total_runs']} ครั้ง\n\n"
        msg += f"📋 พิมพ์ /cron list เพื่อดูรายละเอียดเพิ่มเติม"
        await send_message(msg, user_id)
    
    else:
        await send_message("❌ คำสั่งไม่ถูกต้อง", user_id)

if __name__ == '__main__':
    args = sys.argv[1:]
    user_id = int(sys.argv[2]) if len(sys.argv) > 2 else PRIMARY_ADMIN
    
    async def main():
        await handle_cron_command(args, user_id)
        print("✅ Cron command executed")
    
    asyncio.run(main())
