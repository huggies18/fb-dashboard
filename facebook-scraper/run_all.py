#!/usr/bin/env python3
"""
Run All - รัน scrape + filter + report ต่อกัน
=============================================
1. scrape_all_posts.py - ดึงโพสทั้งหมด
2. ai_filter_all.py - Filter + ส่ง CSV ให้ Admin
"""

import sys
import os
import re
import json
from datetime import datetime, timedelta
from telegram import Bot
import asyncio

# Config
LEADS_DIR = '/root/.openclaw/workspace/facebook-scraper/leads/'
PENDING_DIR = '/root/.openclaw/workspace/facebook-scraper/pending/'
ALL_POSTS_FILE = '/root/.openclaw/workspace/facebook-scraper/all_posts.json'
SCRAPER_LOG = '/root/.openclaw/workspace/facebook-scraper/scrape_all.log'
THAI_OFFSET = timedelta(hours=7)

TELEGRAM_TOKEN = '8774902841:AAFveLJDs-Bf02cPkBhZVPU5JBw_sdLIhNw'
ADMIN_USER_ID = 6780942246

sys.path.insert(0, '/root/.openclaw/workspace/facebook-scraper')
from ai_minimax_filter import minimax_analyze

def thai_time_str():
    return (datetime.now() + THAI_OFFSET).strftime("%H:%M:%S")

def thai_now():
    return (datetime.now() + THAI_OFFSET).strftime("%Y-%m-%d %H:%M:%S")

async def send_telegram(msg):
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=ADMIN_USER_ID, text=msg)

async def send_document(caption, filepath, filename):
    bot = Bot(token=TELEGRAM_TOKEN)
    with open(filepath, 'rb') as f:
        await bot.send_document(
            chat_id=ADMIN_USER_ID,
            document=f,
            filename=filename,
            caption=caption
        )

def load_all_posts():
    if not os.path.exists(ALL_POSTS_FILE):
        return []
    with open(ALL_POSTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def filter_posts(posts):
    leads = []
    rejected = []
    seen_urls = set()
    
    for post in posts:
        msg = post.get('message', '')
        url = post.get('url', '')
        group = post.get('group', '')
        post_time = post.get('time', '')
        
        # Skip duplicates
        if url in seen_urls:
            continue
        seen_urls.add(url)
        
        result = minimax_analyze(msg, url, group)
        
        post_data = {
            'url': url,
            'message': msg[:200],
            'group': group,
            'time': post_time,
            'score': result['score'],
            'reason': result['reason'],
            'is_lead': result['is_lead'],
            'scraped_at': post.get('scraped_at', '')
        }
        
        if result['is_lead']:
            leads.append(post_data)
        else:
            rejected.append(post_data)
    
    return leads, rejected

def create_csv(leads, rejected):
    csv_filename = f'all_posts_{(datetime.now() + THAI_OFFSET).strftime("%Y%m%d_%H%M%S")}.csv'
    csv_filepath = f'/root/.openclaw/workspace/facebook-scraper/csv_exports/{csv_filename}'
    os.makedirs(os.path.dirname(csv_filepath), exist_ok=True)
    
    import re
    scraped_at = thai_now()
    
    # Combine and sort all posts
    all_posts = []
    for p in leads:
        p['_status'] = '✅ Lead'
        all_posts.append(p)
    for p in rejected:
        p['_status'] = '❌ Rejected'
        all_posts.append(p)
    
    with open(csv_filepath, 'w', encoding='utf-8') as f:
        f.write('No,Status,Group,Post URL,Message,Score,Reason,PostDate (UTC+7),Contact,ScrapedAt (UTC+7)\n')
        
        for i, post in enumerate(all_posts, 1):
            msg_text = post['message'].replace('"', '""')
            reason_clean = re.sub(r'[🟢🟡🔵🔥💬📢✅❌⚠️🎉]+', '', post['reason']).strip()
            status = post.get('_status', '❌ Rejected')
            
            # Calculate post time
            post_time_str = post.get('time', '')
            match = re.match(r'(\d+)\s*(นาที|ชั่วโมง|วัน)', post_time_str)
            if match:
                value = int(match.group(1))
                unit = match.group(2)
                if unit == 'นาที':
                    delta = timedelta(minutes=value)
                elif unit == 'ชั่วโมง':
                    delta = timedelta(hours=value)
                else:
                    delta = timedelta(days=value)
                
                scraped_dt = datetime.strptime(scraped_at, '%Y-%m-%d %H:%M:%S')
                post_dt = scraped_dt - delta
                post_time_formatted = post_dt.strftime('%Y-%m-%d %H:%M')
            else:
                post_time_formatted = post_time_str
            
            f.write(f'{i},"{status}","{post["group"]}","{post["url"]}","{msg_text}",{post["score"]},"{reason_clean}","{post_time_formatted}","","{scraped_at}"\n')
    
    return csv_filepath, csv_filename

async def main():
    print(f"[{thai_time_str()}] 🚀 RUN ALL - Scrape + Filter + Report")
    
    # Step 1: Scrape all posts
    print(f"[{thai_time_str()}] 📥 Step 1: Scrape all posts...")
    await send_telegram(f"🔄 เริ่มรัน /runall ที่ {thai_time_str()} (UTC+7)\n⏳ กำลังดึงโพส...")
    
    os.system('cd /root/.openclaw/workspace/facebook-scraper && nohup python3 scrape_all_posts.py > /dev/null 2>&1 &')
    
    # Wait for scrape to complete (check log file)
    max_wait = 300  # 5 minutes
    waited = 0
    while waited < max_wait:
        await asyncio.sleep(5)
        waited += 5
        
        if os.path.exists(SCRAPER_LOG):
            with open(SCRAPER_LOG, 'r') as f:
                content = f.read()
                if 'TOTAL:' in content and 'Saved to:' in content:
                    break
    
    print(f"[{thai_time_str()}] ✅ Scrape completed")
    
    # Step 2: Load and filter posts
    print(f"[{thai_time_str()}] 🔍 Step 2: Filter posts...")
    await send_telegram(f"🔍 กำลัง Filter โพส...")
    
    posts = load_all_posts()
    if not posts:
        await send_telegram(f"❌ ไม่พบโพสที่ดึงมา")
        return
    
    print(f"📥 โหลด {len(posts)} โพสแล้ว")
    
    leads, rejected = filter_posts(posts)
    print(f"📊 พบ {len(leads)} leads, {len(rejected)} rejected")
    
    # Save rejected to pending/
    os.makedirs(PENDING_DIR, exist_ok=True)
    for i, post in enumerate(rejected, 1):
        fname = f"rejected_runall_{(datetime.now() + THAI_OFFSET).strftime('%Y%m%d_%H%M%S')}_{i}.json"
        fpath = os.path.join(PENDING_DIR, fname)
        with open(fpath, 'w', encoding='utf-8') as f:
            json.dump(post, f, ensure_ascii=False, indent=2)
    
    # Always create CSV (leads + rejected)
    print(f"[{thai_time_str()}] 📊 Step 3: Create CSV...")
    csv_filepath, csv_filename = create_csv(leads, rejected)
    
    if not leads:
        await send_telegram(f"📭 ไม่พบ Lead ใหม่วันนี้\n━━━━━━━━━━━━━━━━━━━━━━\n📝 วิเคราะห์: {len(posts)} โพส\n🔴 Rejected: {len(rejected)}\n📋 CSV ส่งให้แล้วด้านล่าง\n✅ /runall เสร็จสิ้น!")
        await send_document(f"📋 CSV: {len(rejected)} rejected posts (ไม่มี leads)", csv_filepath, csv_filename)
        return
    
    # Step 4: Send report + CSV
    print(f"[{thai_time_str()}] 📤 Step 4: Send report...")
    
    # Summary message
    high = sum(1 for l in leads if l['score'] >= 5)
    med = sum(1 for l in leads if 3 <= l['score'] < 5)
    low = sum(1 for l in leads if l['score'] < 3)
    
    msg = f"""🟢 พบ Buyer Leads ใหม่!
⏰ เมื่อ: {thai_time_str()} (UTC+7)
📊 วิเคราะห์: {len(posts)} โพส
📋 Lead ที่เจอ: {len(leads)} ราย

📈 สรุป:
 🟢 สนใจ/ซื้อ: {high} ราย
 🟡 กำลังพิจารณา: {med} ราย
 🔵 สอบถาม: {low} ราย

━━━━━━━━━━━━━━━━━━━━━━"""
    
    for i, lead in enumerate(leads, 1):
        emoji = "🔵"
        if lead['score'] >= 5:
            emoji = "🟢"
        elif lead['score'] >= 3:
            emoji = "🟡"
        reason_clean = re.sub(r'[🟢🟡🔵🔥💬📢✅❌⚠️🎉]+', '', lead['reason']).strip()
        msg += f"""
{i}. {emoji} {reason_clean} score:{lead['score']}
 📝 \"{lead['message'][:60]}...\"
 🔗 {lead['url']}"""
    
    # Send CSV file with caption
    await send_document(msg, csv_filepath, csv_filename)
    
    print(f"[{thai_time_str()}] ✅ เสร็จสิ้น!")
    await send_telegram(f"✅ /runall เสร็จสิ้น!\n📋 Lead ที่ส่งให้: {len(leads)} ราย")

if __name__ == "__main__":
    asyncio.run(main())
