#!/usr/bin/env python3
"""
AI Filter All - วิเคราะห์โพสทั้งหมดแล้วส่งให้ Admin
===============================================
1. โหลดโพสจาก all_posts.json
2. Filter ด้วย Keyword (ai_buyer_filter)
3. ส่ง lead + CSV ให้ Admin
"""

import sys
sys.path.insert(0, '.')

import json, os, asyncio
from datetime import datetime, timedelta
import re
from telegram import Bot

LEADS_DIR = '/root/.openclaw/workspace/facebook-scraper/leads/'
ALL_POSTS_FILE = '/root/.openclaw/workspace/facebook-scraper/all_posts.json'
THAI_OFFSET = timedelta(hours=7)

# Import AI Filter
from ai_buyer_filter import ultra_analyze

# ==================== TELEGRAM CONFIG ====================
TELEGRAM_TOKEN = '8774902841:AAFveLJDs-Bf02cPkBhZVPU5JBw_sdLIhNw'
ADMIN_USER_ID = 6780942246

def thai_time_str():
    return (datetime.now() + THAI_OFFSET).strftime("%H:%M:%S")

def load_all_posts():
    if not os.path.exists(ALL_POSTS_FILE):
        print(f"❌ ไฟล์ {ALL_POSTS_FILE} ไม่มีอยู่")
        return []
    with open(ALL_POSTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def filter_posts(posts):
    leads = []
    seen_urls = set()  # Track URLs to avoid duplicates
    analyzed_posts = []  # Track all analyzed posts for counting
    
    print(f"{'='*60}")
    print(f"🔍 วิเคราะห์ {len(posts)} โพสด้วย Keyword Filter v2")
    print(f"{'='*60}")
    
    for i, post in enumerate(posts, 1):
        msg = post.get('message', '')
        url = post.get('url', '')
        group = post.get('group', '')
        post_time = post.get('time', '')
        
        url = post.get('url', '')
        
        # Check for duplicate URL
        if url in seen_urls:
            print(f"   ⚠️ ซ้ำ: {url}")
            continue
        seen_urls.add(url)
        
        result = ultra_analyze(msg, url, group)
        
        analyzed_posts.append({
            'url': url,
            'score': result['score'],
            'is_lead': result['is_lead'],
            'reason': result['reason']
        })
        
        if result['is_lead']:
            leads.append({
                'url': url,
                'message': msg[:200],
                'group': group,
                'time': post_time,
                'score': result['score'],
                'reason': result['reason']
            })
            emoji = "🔵"
            if result['score'] >= 5:
                emoji = "🟢"
            elif result['score'] >= 3:
                emoji = "🟡"
            print(f"{emoji} [{i}] {result['reason']} (score:{result['score']})")
        
        if i % 50 == 0:
            print(f"   ประมวลผล {i}/{len(posts)} โพส...")
    
    print(f"{'='*60}")
    print(f"📊 ผลลัพธ์: {len(leads)} leads / {len(posts) - len(leads)} ไม่ใช่ lead")
    print(f"{'='*60}")
    return leads, analyzed_posts

async def send_admin_alert(leads, total_posts, analyzed_posts):
    bot = Bot(token=TELEGRAM_TOKEN)
    
    # Count sellers and buyers (based on analyzed_posts, not raw total)
    analyzed_count = len(analyzed_posts)
    sellers = sum(1 for p in analyzed_posts if not p.get('is_lead', False))
    buyers = sum(1 for p in analyzed_posts if p.get('is_lead', False))
    leads_count = sum(1 for p in analyzed_posts if p.get('is_lead', False) and p.get('score', 0) > 0)
    
    if not leads:
        msg = f"📭 ไม่พบ Lead ใหม่วันนี้ ({thai_time_str()})\n━━━━━━━━━━━━━━━━━━━━━━\n📝 วิเคราะห์: {analyzed_count} โพส\n🔴 Seller: {sellers} | 🟢 Buyer: {buyers}\n🔍 Lead ที่เจอ: {leads_count}"
        await bot.send_message(chat_id=ADMIN_USER_ID, text=msg)
        return
    
    # Create CSV file
    csv_filename = f'all_leads_{(datetime.now() + THAI_OFFSET).strftime("%Y%m%d_%H%M%S")}.csv'
    csv_filepath = f'/root/.openclaw/workspace/facebook-scraper/csv_exports/{csv_filename}'
    
    os.makedirs(os.path.dirname(csv_filepath), exist_ok=True)
    
    with open(csv_filepath, 'w', encoding='utf-8') as f:
        f.write('No,Group,Post URL,Message,Score,Reason,PostDate (UTC+7),Contact,ScrapedAt (UTC+7)\n')
        for i, lead in enumerate(leads, 1):
            msg_text = lead['message'].replace('"', '""')
            scraped_at = (datetime.now() + THAI_OFFSET).strftime('%Y-%m-%d %H:%M:%S')
            # Calculate actual post time (in UTC+7)
            # scraped_at is already in UTC+7 (server local time)
            post_time_str = lead['time']  # e.g., "33 นาที"
            scraped_at_str = scraped_at  # e.g., "2026-04-23 06:10:49"
            
            # Parse time string like "33 นาที", "2 ชั่วโมง", "1 วัน"
            match = re.match(r'(\d+)\s*(นาที|ชั่วโมง|วัน)', post_time_str)
            if match:
                value = int(match.group(1))
                unit = match.group(2)
                if unit == 'นาที':
                    delta = timedelta(minutes=value)
                elif unit == 'ชั่วโมง':
                    delta = timedelta(hours=value)
                else:  # วัน
                    delta = timedelta(days=value)
                
                # scraped_at is already in UTC+7, no conversion needed
                scraped_dt = datetime.strptime(scraped_at_str, '%Y-%m-%d %H:%M:%S')
                post_dt = scraped_dt - delta
                post_time_formatted = post_dt.strftime('%Y-%m-%d %H:%M')
            else:
                post_time_formatted = post_time_str
            
            # Remove emoji from reason for CSV
            reason_clean = re.sub(r'[🟢🟡🔵🔥💬📢✅❌⚠️🎉]+', '', lead['reason']).strip()
            f.write(f'{i},"{lead["group"]}","{lead["url"]}","{msg_text}",{lead["score"]},"{reason_clean}","{post_time_formatted}","","{scraped_at}"\n')
    
    # Create message with seller/buyer count
    msg = f"🟢 พบ Buyer Leads ใหม่!\n⏰ เมื่อ: {thai_time_str()} (UTC+7)\n📊 พบ: {len(leads)} โพส\n🔴 Seller: {sellers} | 🟢 Buyer: {buyers}\n\n💡 พิมพ์ /wbuyer เพื่อ export CSV\n\n━━━━━━━━━━━━━━━━━━━━━━"
    
    for i, lead in enumerate(leads[:5], 1):
        emoji = "🔵"
        if lead['score'] >= 9:
            emoji = "🔥"
        elif lead['score'] >= 7:
            emoji = "🟢"
        elif lead['score'] >= 5:
            emoji = "🟡"
        reason_clean = re.sub(r'[🟢🟡🔵🔥💬📢✅❌⚠️🎉]+', '', lead['reason']).strip()
        msg += f"\n{i}. {emoji} {reason_clean} score:{lead['score']}\n 📝 \"{lead['message'][:40]}...\"\n 🔗 {lead['url']}"
    
    if len(leads) > 5:
        msg += f"\n...และอีก {len(leads) - 5} ราย (ดูทั้งหมดใน CSV)"
    
    # Send CSV file
    with open(csv_filepath, 'rb') as f:
        await bot.send_document(
            chat_id=ADMIN_USER_ID,
            document=f,
            filename=csv_filename,
            caption=msg
        )

def main():
    print(f"[{thai_time_str()}] 🚀 AI Filter All - วิเคราะห์โพสทั้งหมด")
    
    posts = load_all_posts()
    if not posts:
        print("❌ ไม่มีโพสที่ต้องวิเคราะห์")
        return
    
    print(f"📥 โหลด {len(posts)} โพสแล้ว")
    
    leads, analyzed_posts = filter_posts(posts)
    
    print(f"📤 ส่งแจ้งเตือนให้ Admin...")
    asyncio.run(send_admin_alert(leads, len(posts), analyzed_posts))
    
    for i, lead in enumerate(leads, 1):
        filename = f"lead_filtered_{(datetime.now() + THAI_OFFSET).strftime('%Y%m%d_%H%M%S')}_{i}.json"
        filepath = os.path.join(LEADS_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(lead, f, ensure_ascii=False, indent=2)
    
    print(f"✅ เสร็จสิ้น! บันทึก {len(leads)} leads")

if __name__ == "__main__":
    main()
