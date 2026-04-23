#!/usr/bin/env python3
"""
/wbuyer - Export all leads to CSV
=================================
Compatible with scraper_hybrid.py (Hybrid + MiniMax AI)
Columns: No, Post URL, Message, Group, PostDate, Score, Reason, Contact, ScrapedAt
"""

import sys
sys.path.insert(0, '.')

import json, csv, os, asyncio
from datetime import datetime, timedelta
from telegram import Bot

THAI_OFFSET = timedelta(hours=7)
LEADS_DIR = "/root/.openclaw/workspace/facebook-scraper/leads"
CSV_DIR = "/root/.openclaw/workspace/facebook-scraper/csv_exports"

BOT_TOKEN = '8774902841:AAFveLJDs-Bf02cPkBhZVPU5JBw_sdLIhNw'
USER_ID = '6780942246'

def thai_time_str():
    return (datetime.now() + THAI_OFFSET).strftime("%H:%M:%S")

def log(msg):
    print(f"[{thai_time_str()}] {msg}")

def export_csv():
    """Export leads to CSV"""
    os.makedirs(CSV_DIR, exist_ok=True)
    
    lead_files = sorted([f for f in os.listdir(LEADS_DIR) if f.startswith('lead_') and f.endswith('.json')])
    
    if not lead_files:
        log("❌ No leads to export")
        log(f"💡 Run /fbuyer first")
        return None
    
    leads = []
    for fname in lead_files:
        fpath = os.path.join(LEADS_DIR, fname)
        try:
            with open(fpath, 'r') as f:
                lead = json.load(f)
                leads.append(lead)
        except:
            continue
    
    if not leads:
        log("❌ No leads to export")
        return None
    
    # Sort by scraped_at
    leads.sort(key=lambda x: x.get('scraped_at', ''))
    
    thai_now = datetime.now() + THAI_OFFSET
    timestamp = thai_now.strftime("%Y%m%d_%H%M%S")
    csv_filename = f"leads_{timestamp}.csv"
    csv_filepath = os.path.join(CSV_DIR, csv_filename)
    
    with open(csv_filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['No', 'Post URL', 'Message', 'Score', 'Reason', 'Group', 'PostDate', 'Contact', 'ScrapedAt'])
        
        for i, lead in enumerate(leads, 1):
            # Convert scraped_at to Bangkok time
            scraped_at = lead.get('scraped_at', '')
            if scraped_at:
                try:
                    dt = datetime.fromisoformat(scraped_at)
                    bkk_time = (dt + THAI_OFFSET).strftime("%Y-%m-%d %H:%M:%S")
                except:
                    bkk_time = scraped_at
            else:
                bkk_time = ''
            
            # Format: Score + Reason instead of Group name
            score = lead.get('score', '')
            reason = lead.get('reason', '')
            score_reason = f"Score:{score} | {reason}"
            
            writer.writerow([
                i,
                lead.get('url', ''),
                lead.get('message', ''),
                score,
                reason,
                lead.get('group', ''),  # Keep group but after Score/Reason
                lead.get('post_time', ''),
                lead.get('contact', ''),
                bkk_time
            ])
    
    return csv_filepath, len(leads), csv_filename

async def send_telegram(csv_filepath, count, csv_filename):
    """Send CSV file to Telegram - 2 messages only"""
    bot = Bot(token=BOT_TOKEN)
    thai_now = datetime.now() + THAI_OFFSET
    
    # Part 1: Count + CSV file
    msg1 = f"ดึง lead ได้ {count}\n"
    await bot.send_message(chat_id=USER_ID, text=msg1)
    
    # Part 2: CSV file attachment
    with open(csv_filepath, 'rb') as f:
        await bot.send_document(
            chat_id=USER_ID,
            document=f,
            filename=csv_filename,
            caption=f"Buyer CSV: {count} leads"
        )

def main():
    log("="*50)
    log("📊 EXPORT LEADS TO CSV")
    log("="*50)
    
    result = export_csv()
    
    if result:
        csv_filepath, count, csv_filename = result
        log(f"✅ Exported {count} leads to CSV")
        log(f"📁 {csv_filepath}")
        log(f"📋 Columns: No, Post URL, Message, Group, PostDate, Score, Reason, Contact, ScrapedAt")
        
        # Send to Telegram
        asyncio.run(send_telegram(csv_filepath, count, csv_filename))
        log(f"✅ Sent to Telegram!")
    else:
        log("❌ Export failed")
    
    log("="*50)

if __name__ == "__main__":
    main()