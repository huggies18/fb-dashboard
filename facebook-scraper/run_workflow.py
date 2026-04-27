#!/usr/bin/env python3
"""
/run - Full Workflow: Scrape → Filter → Report to Telegram
==========================================================
Step 1: Scrape all posts from 6 groups → CSV
Step 2: Filter with MiniMax AI → CSV with leads/rejected
Send results to NotiBot (Telegram)
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/facebook-scraper')

import os, json, csv, time, asyncio
from datetime import datetime, timedelta
from telegram import Bot

# Config
SCRAPER_LOG = '/root/.openclaw/workspace/facebook-scraper/scrape_all.log'
ALL_POSTS_FILE = '/root/.openclaw/workspace/facebook-scraper/all_posts.json'
RESULT_FILE = '/root/.openclaw/workspace/facebook-scraper/filter_result.json'
CSV_DIR = '/root/.openclaw/workspace/facebook-scraper/csv_exports'
BOT_TOKEN = '8774902841:AAFveLJDs-Bf02cPkBhZVPU5JBw_sdLIhNw'
ADMIN_USER_IDS = [6780942246, 8698062232]  # Tibodin, Nick

# Override via environment variable (set by run_infi.py)
import os
_target = os.environ.get('TARGET', '')
if _target == 'Tibodin':
    ADMIN_USER_IDS = [6780942246]
elif _target == 'Nick':
    ADMIN_USER_IDS = [8698062232]
THAI_OFFSET = timedelta(hours=7)

from ai_minimax_filter import minimax_analyze

def thai_time_str():
    return (datetime.now() + THAI_OFFSET).strftime("%H:%M:%S")

def thai_now():
    return (datetime.now() + THAI_OFFSET).strftime("%Y-%m-%d %H:%M:%S")

async def send_telegram(msg):
    bot = Bot(token=BOT_TOKEN)
    for uid in ADMIN_USER_IDS:
        await bot.send_message(chat_id=uid, text=msg)

async def send_csv(caption, filepath, filename):
    bot = Bot(token=BOT_TOKEN)
    for uid in ADMIN_USER_IDS:
        with open(filepath, 'rb') as f:
            await bot.send_document(
                chat_id=uid,
                document=f,
                filename=filename,
                caption=caption
            )

async def step1_scrape():
    """Step 1: Scrape all posts"""
    print(f"[{thai_time_str()}] 📥 ขั้นตอน 1 - Scrape ทุกโพส...")
    await send_telegram(f"🔄 ขั้นตอน 1 เวลา {thai_time_str()} UTC+7 - กำลัง scrape โพสจาก 6 กลุ่ม...")
    
    # Clean old data
    if os.path.exists(ALL_POSTS_FILE):
        os.remove(ALL_POSTS_FILE)
    
    # Run scraper in background
    os.system('cd /root/.openclaw/workspace/facebook-scraper && nohup python3 scrape_all_posts.py > /dev/null 2>&1 &')
    
    # Wait for scrape to complete
    max_wait = 600  # 10 minutes
    waited = 0
    while waited < max_wait:
        await asyncio.sleep(5)
        waited += 5
        
        if os.path.exists(SCRAPER_LOG):
            with open(SCRAPER_LOG, 'r') as f:
                content = f.read()
                if 'TOTAL:' in content and 'Saved to:' in content:
                    break
    
    # Load posts
    if not os.path.exists(ALL_POSTS_FILE):
        print(f"[{thai_time_str()}] ❌ Scrape failed - no posts file")
        await send_telegram("❌ ขั้นตอน 1 ล้มเหลว - ไม่พบไฟล์โพส")
        return None
    
    with open(ALL_POSTS_FILE, 'r', encoding='utf-8') as f:
        posts = json.load(f)
    
    print(f"[{thai_time_str()}] ✅ Scrape เสร็จ - ได้ {len(posts)} โพส")
    
    # Save Step 1 CSV
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_path = f'{CSV_DIR}/step1_scrape_{ts}.csv'
    os.makedirs(CSV_DIR, exist_ok=True)
    
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['No', 'Group', 'Post URL', 'Message', 'PostTime (UTC+7)', 'ScrapeAt (UTC+7)'])
        for i, p in enumerate(posts, 1):
            w.writerow([i, p.get('group',''), p.get('url',''), p.get('message','')[:200], p.get('time',''), p.get('scraped_at','')])
    
    # Send Step 1 CSV
    await send_csv(f"📥 ขั้นตอน 1 - เก็บทุกโพส: {len(posts)} โพส (ไม่ filter)", csv_path, f'step1_scrape_{ts}.csv')
    await send_telegram(f"✅ ขั้นตอน 1 เวลา {thai_time_str()} UTC+7 - เก็บได้ {len(posts)} โพส\n\n🔄 กำลังดำเนินขั้นตอน 2...")
    
    return posts

async def step2_filter(posts):
    """Step 2: Filter posts with MiniMax AI (Parallel)"""
    print(f"[{thai_time_str()}] 🔍 ขั้นตอน 2 - กรองด้วย MiniMax AI (Parallel)...")
    
    # Save current posts to all_posts.json for parallel_filter
    with open(ALL_POSTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    
    # Run parallel_filter.py as subprocess
    import subprocess
    result = subprocess.run(
        ['python3', 'parallel_filter.py'],
        cwd='/root/.openclaw/workspace/facebook-scraper',
        capture_output=True,
        text=True,
        timeout=300
    )
    
    if result.returncode != 0:
        print(f"❌ Parallel filter failed: {result.stderr}")
        await send_telegram(f"❌ ขั้นตอน 2 ล้มเหลว")
        return [], []
    
    # Load results
    with open(RESULT_FILE, 'r', encoding='utf-8') as f:
        filter_result = json.load(f)
    
    leads = filter_result.get('leads', [])
    not_leads = filter_result.get('not_leads', [])
    
    print(f"[{thai_time_str()}] ✅ Filter เสร็จ - Lead: {len(leads)}, Rejected: {len(not_leads)}")
    
    # Save Step 2 CSV
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_path = f'{CSV_DIR}/step2_filter_{ts}.csv'
    
    all_posts = leads + not_leads
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['No', 'Status', 'Group', 'Post URL', 'Message', 'Score', 'Reason', 'PostDate (UTC+7)', 'ScrapeAt (UTC+7)'])
        for i, p in enumerate(all_posts, 1):
            status = '✅ Lead' if p.get('is_lead') else '❌ Rejected'
            w.writerow([i, status, p.get('group',''), p.get('url',''), p.get('message','')[:200], p.get('score',0), p.get('reason',''), p.get('time',''), p.get('scraped_at','')])
    
    # Send Step 2 results
    summary = f"✅ ขั้นตอน 2 - กรอง Buyer ได้ {len(leads)} โพส (จาก {len(posts)} โพส)\n\n"
    summary += f"📋 CSV แนบด้านล่าง\n\n"
    summary += f"📈 สรุป:\n"
    summary += f" 🟢 Lead: {len(leads)}\n"
    summary += f" ❌ Rejected: {len(not_leads)}"
    
    await send_telegram(summary)
    await send_csv(f"📋 ขั้นตอน 2 - Lead {len(leads)} โพส, Rejected {len(not_leads)} โพส", csv_path, f'step2_filter_{ts}.csv')
    
    # List leads in detail format (single message)
    if leads:
        lead_lines = []
        for i, p in enumerate(leads[:10], 1):
            score = p.get('score', 0)
            reason = p.get('reason', '')
            msg_text = p.get('message', '')[:80].replace('"', '')
            url = p.get('url', '')
            
            lead_lines.append(f"{i}. {reason} score:{score}\n 📝 \"{msg_text}...\"\n 🔗 {url}")
        
        combined = "✅ Leads ที่เจอ (9 ราย):\n\n" + "\n\n".join(lead_lines)
        if len(leads) > 10:
            combined += f"\n\n...และอีก {len(leads)-10} ราย (ดูใน CSV)"
        await send_telegram(combined)
    
    return leads, not_leads

async def main():
    print("="*60)
    print(f"[{thai_time_str()}] 🚀 /run - Full Workflow")
    print("="*60)
    
    # Step 1: Scrape
    posts = await step1_scrape()
    if not posts:
        print("❌ หยุดการทำงาน - Scrape ล้มเหลว")
        return
    
    # Step 2: Filter
    leads, not_leads = await step2_filter(posts)
    
    print("="*60)
    print(f"[{thai_time_str()}] ✅ /run เสร็จสิ้น!")
    print(f"   โพสทั้งหมด: {len(posts)}")
    print(f"   Lead: {len(leads)}")
    print(f"   Rejected: {len(not_leads)}")
    print("="*60)
    
    await send_telegram(f"✅ /run เสร็จสิ้น!\n📊 สรุป: {len(posts)} โพส → {len(leads)} leads")

if __name__ == "__main__":
    asyncio.run(main())
