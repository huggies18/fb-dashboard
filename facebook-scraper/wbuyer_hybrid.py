#!/usr/bin/env python3
"""
/wbuyer - Export all leads to CSV with Detailed Report
=====================================================
Compatible with scraper_hybrid.py (Hybrid + MiniMax AI)
Send detailed lead report to Telegram in the format:
🟢 พบ Buyer Leads ใหม่!
⏰ เมื่อ: HH:MM (UTC+7)
📊 พบ: X โพส
👥 Workers: 3 ตัว

💡 พิมพ์ /wbuyer เพื่อ export CSV

━━━━━━━━━━━━━━━━━━━━━━
1. 🟢 [Reason] score:X / เวลาโพสเมื่อ X นาที
 📝 "message preview..."
 🔗 url

... (more leads)
"""

import sys
sys.path.insert(0, '.')

import json, csv, os, asyncio
from datetime import datetime, timedelta
from telegram import Bot

THAI_OFFSET = timedelta(hours=7)
LEADS_DIR = "/root/.openclaw/workspace/facebook-scraper/leads"
PENDING_DIR = "/root/.openclaw/workspace/facebook-scraper/pending"
CSV_DIR = "/root/.openclaw/workspace/facebook-scraper/csv_exports"

BOT_TOKEN = '8774902841:AAFveLJDs-Bf02cPkBhZVPU5JBw_sdLIhNw'
USER_ID = '6780942246'

def thai_time_str():
    return (datetime.now() + THAI_OFFSET).strftime("%H:%M:%S")

def thai_now():
    return datetime.now() + THAI_OFFSET

def log(msg):
    print(f"[{thai_time_str()}] {msg}")

def get_intent_emoji(score, reason):
    """Get emoji based on intent/reason"""
    reason_lower = reason.lower() if reason else ''
    
    if 'กำลังจะซื้อ' in reason_lower or 'กำลังจะติด' in reason_lower:
        return '🟢'
    elif 'สนใจ' in reason_lower or 'พร้อม' in reason_lower:
        return '🟢'
    elif 'ขอราคา' in reason_lower or 'ถามราคา' in reason_lower:
        return '🟡'
    elif 'สอบถาม' in reason_lower or 'ขอคำแนะนำ' in reason_lower:
        return '🟡'
    elif 'ถามเกี่ยวกับ' in reason_lower:
        return '🟢'
    else:
        return '🟢'

def format_reason_for_display(reason):
    """Format reason for display"""
    if not reason:
        return 'ไม่ระบุ'
    
    # Shorten common reasons
    reason_map = {
        'กำลังจะซื้อ/ติด': 'กำลังจะซื้อ/ติด',
        'สนใจ/กำลังพิจารณา': 'สนใจ/กำลังพิจารณา',
        'สอบถาม/ขอคำแนะนำ': 'สอบถาม/ขอคำแนะนำ',
        'ถามเกี่ยวกับโซล่า': 'ถามเกี่ยวกับโซล่า',
        'กำลังจะติดตั้ง': 'กำลังจะติดตั้ง',
        'พร้อมซื้อ/ติด': 'พร้อมซื้อ/ติด',
    }
    
    for key, value in reason_map.items():
        if key in reason:
            return value
    
    return reason[:30] if len(reason) > 30 else reason

def truncate_message(message, max_len=80):
    """Truncate message for preview"""
    if not message:
        return ''
    # Remove extra whitespace
    msg = ' '.join(message.split())
    if len(msg) > max_len:
        return msg[:max_len] + '...'
    return msg

def export_csv():
    """Export leads + rejected posts to CSV"""
    os.makedirs(CSV_DIR, exist_ok=True)
    
    lead_files = sorted([f for f in os.listdir(LEADS_DIR) if f.startswith('lead_') and f.endswith('.json')])
    rejected_files = sorted([f for f in os.listdir(PENDING_DIR) if f.startswith('rejected_') and f.endswith('.json')])
    
    if not lead_files and not rejected_files:
        log("❌ No posts to export")
        log(f"💡 Run /fbuyer first")
        return None
    
    all_posts = []
    
    # Load leads
    for fname in lead_files:
        fpath = os.path.join(LEADS_DIR, fname)
        try:
            with open(fpath, 'r') as f:
                post = json.load(f)
                post['_source'] = 'lead'
                all_posts.append(post)
        except:
            continue
    
    # Load rejected
    for fname in rejected_files:
        fpath = os.path.join(PENDING_DIR, fname)
        try:
            with open(fpath, 'r') as f:
                post = json.load(f)
                post['_source'] = 'rejected'
                all_posts.append(post)
        except:
            continue
    
    if not all_posts:
        log("❌ No posts to export")
        return None
    
    # Sort by scraped_at (newest first)
    all_posts.sort(key=lambda x: x.get('scraped_at', ''), reverse=True)
    
    thai_now_dt = thai_now()
    timestamp = thai_now_dt.strftime("%Y%m%d_%H%M%S")
    csv_filename = f"all_posts_{timestamp}.csv"
    csv_filepath = os.path.join(CSV_DIR, csv_filename)
    
    with open(csv_filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['No', 'Status', 'Post URL', 'Message', 'Score', 'Reason', 'Group', 'PostDate', 'Contact', 'ScrapedAt'])
        
        for i, post in enumerate(all_posts, 1):
            # Convert scraped_at to Bangkok time
            scraped_at = post.get('scraped_at', '')
            if scraped_at:
                try:
                    dt = datetime.fromisoformat(scraped_at)
                    bkk_time = (dt + THAI_OFFSET).strftime("%Y-%m-%d %H:%M:%S")
                except:
                    bkk_time = scraped_at
            else:
                bkk_time = ''
            
            status = '✅ Lead' if post.get('is_lead') else '❌ Rejected'
            
            writer.writerow([
                i,
                status,
                post.get('url', ''),
                post.get('message', ''),
                post.get('score', ''),
                post.get('reason', ''),
                post.get('group', ''),
                post.get('post_time', ''),
                post.get('contact', ''),
                bkk_time
            ])
    
    lead_count = len([p for p in all_posts if p.get('is_lead')])
    rejected_count = len([p for p in all_posts if not p.get('is_lead')])
    
    return csv_filepath, lead_count, rejected_count, csv_filename, all_posts

def build_detailed_report(lead_count, rejected_count, all_posts):
    """Build detailed lead report message"""
    thai_now_dt = thai_now()
    total = lead_count + rejected_count
    
    # Header
    header = f"""🟢 พบ Buyer Leads ใหม่!
⏰ เมื่อ: {thai_now_dt.strftime('%H:%M')} (UTC+7)
📊 พบ: {lead_count} Leads | {rejected_count} Rejected (จาก {total} โพส)
👥 Workers: 3 ตัว

💡 พิมพ์ /wbuyer เพื่อ export CSV

━━━━━━━━━━━━━━━━━━━━━━
"""
    
    # Build lead list
    lead_items = []
    for i, lead in enumerate(leads, 1):
        emoji = get_intent_emoji(lead.get('score', 0), lead.get('reason', ''))
        reason = format_reason_for_display(lead.get('reason', ''))
        score = lead.get('score', 0)
        post_time = lead.get('post_time', '')
        message = truncate_message(lead.get('message', ''))
        url = lead.get('url', '')
        
        item = f"""{i}. {emoji} {reason} score:{score} / เวลาโพสเมื่อ {post_time}
 📝 "{message}"
 🔗 {url}"""
        lead_items.append(item)
    
    # Combine all
    report = header + '\n\n'.join(lead_items)
    
    return report

async def send_telegram_report(csv_filepath, lead_count, rejected_count, csv_filename, all_posts):
    """Send detailed report + CSV to Telegram"""
    bot = Bot(token=BOT_TOKEN)
    
    # Build detailed report
    report = build_detailed_report(lead_count, rejected_count, all_posts)
    
    # Send report (may need to split if too long)
    if len(report) > 4000:
        # Split into multiple messages
        parts = report.split('━━━━━━━━━━━━━━━━━━━━━━')
        await bot.send_message(chat_id=USER_ID, text=parts[0])
        
        remaining = '━━━━━━━━━━━━━━━━━━━━━━' + parts[1]
        if len(remaining) > 4000:
            # Split further
            lines = remaining.split('\n\n')
            msg = '\n\n'.join(lines[:5])
            await bot.send_message(chat_id=USER_ID, text=msg)
            for j in range(5, len(lines), 5):
                msg = '\n\n'.join(lines[j:j+5])
                if msg.strip():
                    await bot.send_message(chat_id=USER_ID, text=msg)
        else:
            await bot.send_message(chat_id=USER_ID, text=remaining)
    else:
        await bot.send_message(chat_id=USER_ID, text=report)
    
    # Send CSV file
    with open(csv_filepath, 'rb') as f:
        await bot.send_document(
            chat_id=USER_ID,
            document=f,
            filename=csv_filename,
            caption=f"📁 CSV: {lead_count} leads, {rejected_count} rejected"
        )

def main():
    log("="*50)
    log("📊 EXPORT ALL POSTS TO CSV (Leads + Rejected)")
    log("="*50)
    
    result = export_csv()
    
    if result:
        csv_filepath, lead_count, rejected_count, csv_filename, all_posts = result
        total = lead_count + rejected_count
        log(f"✅ Exported {lead_count} leads + {rejected_count} rejected = {total} posts to CSV")
        log(f"📁 {csv_filepath}")
        log(f"📋 Columns: No, Status, Post URL, Message, Score, Reason, Group, PostDate, Contact, ScrapedAt")
        
        # Send detailed report to Telegram
        asyncio.run(send_telegram_report(csv_filepath, lead_count, rejected_count, csv_filename, all_posts))
        log(f"✅ Sent detailed report to Telegram!")
    else:
        log("❌ Export failed")
    
    log("="*50)

if __name__ == "__main__":
    main()
