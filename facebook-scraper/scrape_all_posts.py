#!/usr/bin/env python3
"""
Scraper - ดึงทุกโพสที่เจอ (ไม่ filter)
==================================
Output to file instead of stdout
"""

import sys
sys.path.insert(0, '.')

import json, time, os, random
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

THAI_OFFSET = timedelta(hours=7)
LOG_FILE = '/root/.openclaw/workspace/facebook-scraper/scrape_all.log'
OUTPUT_FILE = '/root/.openclaw/workspace/facebook-scraper/all_posts.json'

def log(msg):
    """Log to file"""
    ts = (datetime.now() + THAI_OFFSET).strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def load_cookies():
    try:
        with open('fb_session.json', 'r') as f:
            session = json.load(f)
            return session.get('cookies', [])
    except:
        return []

GROUPS = [
    '1925997401002801',
    '383849116272497',
    '2317142971864047',
    'thaisolarcell',
    '1671213103178339',
    '429829328127055'
]

def scrape_group_all_posts(page, group_id, all_posts):
    """ดึงทุกโพสที่เจอ"""
    
    page.goto(f"https://www.facebook.com/groups/{group_id}", timeout=45000)
    time.sleep(random.uniform(3, 6))  # Wait before scroll like human
    
    scrolls = random.randint(3, 5)
    log(f"📂 Group: {group_id} | Scrolls: {scrolls}")
    
    for scroll_num in range(scrolls):
        page.mouse.wheel(0, random.randint(500, 1000))
        time.sleep(random.uniform(2, 5))  # Human-like wait between scrolls
        
        posts = page.query_selector_all("div[role='article']")
        log(f"    📜 Scroll {scroll_num+1}/{scrolls} → Found {len(posts)} posts")
        
        for post in posts:
            try:
                post_url = None
                links = post.query_selector_all('a[href]')
                for link in links:
                    href = link.get_attribute('href')
                    if href and '/posts/' in href:
                        post_url = href.split('?')[0]
                        break
                
                if not post_url:
                    continue
                
                msg = ""
                for sel in ['div[data-ad-preview="message"]', 'div[dir="auto"]', 'span[dir="auto"]']:
                    try:
                        el = post.query_selector(sel)
                        if el:
                            txt = el.inner_text()
                            if len(txt) > 10:
                                msg = txt[:200]
                                break
                    except:
                        continue
                
                if not msg:
                    continue
                
                post_time = ""
                try:
                    spans = post.query_selector_all('span')
                    for span in spans:
                        text = span.inner_text()
                        if any(x in text for x in ['ชั่วโมง', 'นาที', 'วัน', 'hour', 'min', 'day', 'ago']):
                            post_time = text.replace('\n·', '').strip()
                            break
                except:
                    pass
                
                all_posts.append({
                    'url': post_url,
                    'message': msg,
                    'group': group_id,
                    'time': post_time,
                    'scraped_at': (datetime.now() + THAI_OFFSET).strftime('%Y-%m-%d %H:%M:%S')
                })
                
            except Exception as e:
                continue
        
        time.sleep(random.uniform(1, 2))
    
    return all_posts

def main():
    # Clear log
    with open(LOG_FILE, 'w') as f:
        f.write('')
    
    log("="*60)
    log("🚀 SCRAPER - ดึงทุกโพส (ไม่ filter)")
    log("="*60)
    
    cookies = load_cookies()
    if not cookies:
        log("❌ No cookies found")
        return
    
    all_posts = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
        )
        
        ctx = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        ctx.add_cookies(cookies)
        page = ctx.new_page()
        
        page.goto("https://www.facebook.com", timeout=30000)
        time.sleep(2)
        
        for group_id in GROUPS:
            log(f"📂 Loading: {group_id}")
            try:
                scrape_group_all_posts(page, group_id, all_posts)
                log(f"    ✅ Total so far: {len(all_posts)} posts")
            except Exception as e:
                log(f"    ❌ Error: {e}")
            
            time.sleep(random.uniform(2, 4))
        
        browser.close()
    
    # Save all posts
    if all_posts:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_posts, f, ensure_ascii=False, indent=2)
        
        log(f"\n" + "="*60)
        log(f"📊 TOTAL: {len(all_posts)} posts")
        log(f"💾 Saved to: {OUTPUT_FILE}")
        log("="*60)
    else:
        log(f"\n❌ ไม่เจอโพสเลย!")

if __name__ == "__main__":
    main()
