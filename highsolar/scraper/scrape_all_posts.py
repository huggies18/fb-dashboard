#!/usr/bin/env python3
"""
Scraper - ดึงทุกโพสที่เจอ (ไม่ filter)
==================================
Output to file instead of stdout
"""

import sys
sys.path.insert(0, '.')

import json, time, os, random
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright

THAI_OFFSET = timedelta(hours=7)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, 'scrape_all.log')
OUTPUT_FILE = os.path.join(SCRIPT_DIR, 'all_posts.json')

def log(msg):
    """Log to file"""
    ts = (datetime.now(timezone.utc) + THAI_OFFSET).strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def load_cookies():
    try:
        with open(os.path.join(SCRIPT_DIR, 'fb_session.json'), 'r') as f:
            session = json.load(f)
            raw_cookies = session.get('cookies', [])
            
            # Normalize cookies for Playwright compatibility
            normalized_cookies = []
            for c in raw_cookies:
                nc = c.copy()
                # Playwright expects sameSite to be exactly Strict, Lax, or None (capitalized)
                same_site = nc.get('sameSite')
                if same_site:
                    same_site_str = str(same_site).strip().capitalize()
                    if same_site_str == 'No_restriction':
                        nc['sameSite'] = 'None'
                    elif same_site_str in ['Strict', 'Lax', 'None']:
                        nc['sameSite'] = same_site_str
                    else:
                        nc.pop('sameSite', None)
                normalized_cookies.append(nc)
            return normalized_cookies
    except:
        return []

def load_proxy_fallback():
    """Load fallback proxy from proxy_config.json"""
    try:
        with open(os.path.join(SCRIPT_DIR, 'proxy_config.json'), 'r') as f:
            config = json.load(f)
            proxies = config.get('proxies', [])
            for p in proxies:
                if p.get('status') == 'backup':
                    return {
                        'type': p.get('type', 'socks5'),
                        'server': p['server'],
                        'port': p['port'],
                        'username': p.get('username'),
                        'password': p.get('password')
                    }
    except:
        pass
    return None

def build_proxy_args(proxy_config):
    """Build proxy args dict from config"""
    proxy_args = {}
    if proxy_config:
        proxy_type = proxy_config.get('type', 'http')
        if proxy_type == 'socks5':
            server_url = f"socks5://{proxy_config['server']}:{proxy_config['port']}"
        elif proxy_type == 'socks4':
            server_url = f"socks4://{proxy_config['server']}:{proxy_config['port']}"
        else:
            server_url = f"http://{proxy_config['server']}:{proxy_config['port']}"
        
        proxy_args['proxy'] = {'server': server_url}
        if proxy_config.get('username') and proxy_config.get('password'):
            proxy_args['proxy']['username'] = proxy_config['username']
            proxy_args['proxy']['password'] = proxy_config['password']
    return proxy_args

SEEN_URLS_FILE = os.path.join(SCRIPT_DIR, 'seen_urls.json')

def load_seen_urls():
    """Load URLs that have been scraped before"""
    if os.path.exists(SEEN_URLS_FILE):
        with open(SEEN_URLS_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_seen_urls(urls):
    """Save scraped URLs to prevent duplicate scraping"""
    with open(SEEN_URLS_FILE, 'w') as f:
        json.dump(list(urls), f, ensure_ascii=False)

def save_seen_urls(urls):
    """Save scraped URLs to prevent duplicate scraping"""
    with open(SEEN_URLS_FILE, 'w') as f:
        json.dump(list(urls), f, ensure_ascii=False)

GROUPS = [
    '1925997401002801',
    '383849116272497',
    '2317142971864047',
    'thaisolarcell',
    '1671213103178339',
    '429829328127055',
    '1049914571763738',   # ซื้อ ขาย อุปกรณ์โซล่าเซลล์และรับติดตั้ง
    '278105266564882',   # โซล่าเซลล์ทำเองใช้งานจริง
    '763466071205875',   # แผงโซล่าเซลล์มือสองราคาถูก
    '473956404634218',   # กลุ่มโซล่าเซลล์ราคาถูก
    '300427817214285',   # โซล่าเซลล์ ส่งถึงบ้าน เก็บเงินปลายทาง
    '264965324013436',   # ชมรมผู้ค้าอุปกรณ์โซล่าเซลล์
    '185778725090915',   # โซล่าเซลล์ใช้งานจริง
    '242920475106307',   # HUAWEI INVERTER แชร์ความรู้ประสบการณ์
]

def scrape_group_all_posts(page, group_id, all_posts, seen_urls, stats, min_scrolls=8, max_scrolls=13, min_delay=1.0, max_delay=2.5):
    """ดึงทุกโพสที่เจอ"""
    
    page.goto(f"https://www.facebook.com/groups/{group_id}", timeout=45000)
    time.sleep(random.uniform(1.5, 3))  # Wait before scroll like human
    
    scrolls = random.randint(min_scrolls, max_scrolls)  # กำหนดช่วง scrolls จาก config
    log(f"📂 Group: {group_id} | Scrolls: {scrolls}")
    
    # Track new posts per scroll
    scroll_new_counts = []
    
    for scroll_num in range(scrolls):
        page.mouse.wheel(0, random.randint(500, 1000))
        time.sleep(random.uniform(1, 2.5))  # Human-like wait between scrolls
        
        # ลอง selector หลายแบบ
        selectors = [
            "div[role='article']",
            "div[aria-label='โพสต์']",
            "div[data-ad-preview='message']",
            "div.x1iyjq1x.x6ikm8r.x1liihqu.x1lzlqrn.x1n2wxh5",
            "div.x6s0dn4.x78zum5.xl56dj7.x1n2wxh5.x1vqgdjs"
        ]
        
        posts = []
        for sel in selectors:
            try:
                posts = page.query_selector_all(sel)
                if len(posts) > 0:
                    log(f"    📜 Scroll {scroll_num+1}/{scrolls} → Found {len(posts)} posts (selector: {sel[:30]})")
                    break
            except:
                continue
        
        new_in_scroll = 0
        dup_in_scroll = 0
        
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
                
                stats['total_found'] += 1
                
                # ✅ Skip URLs already seen in PREVIOUS scrape runs (cross-run dedup only)
                if post_url in seen_urls:
                    stats['duplicates'] += 1
                    dup_in_scroll += 1
                    continue
                seen_urls.add(post_url)  # เก็บไว้สำหรับข้ามรอบหน้า
                new_in_scroll += 1
                
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
                    'scraped_at': (datetime.now(timezone.utc) + THAI_OFFSET).strftime('%Y-%m-%d %H:%M:%S')
                })
                log(f"    ✨ Found post: {msg[:60].strip().replace('\n', ' ')}... ({post_url})")
                
            except Exception as e:
                continue
        
        scroll_new_counts.append(new_in_scroll)
        
        # 🔧 Smart scroll: ถ้าเจอแต่ duplicate → พยายาม scroll ต่อจนถึง max
        if new_in_scroll == 0 and dup_in_scroll > 0 and scroll_num < scrolls - 1:
            log(f"    ⚠️  Scroll {scroll_num+1}: เจอแต่ duplicate ({dup_in_scroll}) → พยายาม scroll ต่อ...")
        
        time.sleep(1)  # หลังดึงโพส
    
    # 📊 สรุป scroll ของกลุ่มนี้
    total_new = sum(scroll_new_counts)
    log(f"    📈 Group {group_id}: new={total_new}, scrolls={scrolls}")
    
    return all_posts

def main():
    # Clear log
    with open(LOG_FILE, 'w') as f:
        f.write('')
    
    log("="*60)
    log("🚀 SCRAPER - ดึงทุกโพส (ไม่ filter)")
    log("="*60)
    
    # Load config settings if available
    config = {}
    config_path = os.path.join(SCRIPT_DIR, 'config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            log(f"⚠️ Cannot load config: {e}")

    groups_to_scrape = config.get('groups', GROUPS)
    min_scrolls = config.get('min_scrolls', 8)
    max_scrolls = config.get('max_scrolls', 13)
    min_delay = config.get('min_delay', 5)
    max_delay = config.get('max_delay', 15)
    headless_setting = config.get('headless', True)

    cookies = load_cookies()
    if not cookies:
        log("❌ No cookies found")
        return
    
    # Try primary proxy first, fallback if primary fails
    primary_proxy = None
    try:
        with open(os.path.join(SCRIPT_DIR, 'proxy_config.json'), 'r') as f:
            config = json.load(f)
            proxies = config.get('proxies', [])
            for p in proxies:
                if p.get('status') == 'active':
                    primary_proxy = {
                        'type': p.get('type', 'socks5'),
                        'server': p['server'],
                        'port': p['port'],
                        'username': p.get('username'),
                        'password': p.get('password')
                    }
                    break
    except:
        pass
    
    # Load seen_urls for dedup
    seen_urls = load_seen_urls()
    log(f"📂 โหลด URL ที่เคย scrape แล้ว: {len(seen_urls)} URLs")
    
    stats = {'total_found': 0, 'duplicates': 0}
    all_posts = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless_setting,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
        )
        
        # Use primary proxy if available
        if primary_proxy:
            proxy_args = build_proxy_args(primary_proxy)
            log(f"Using primary proxy: {primary_proxy['server']}:{primary_proxy['port']}")
        
        # Load proxy from proxy_config.json
        proxy_config = None
        try:
            with open(os.path.join(SCRIPT_DIR, 'proxy_config.json'), 'r') as f:
                config = json.load(f)
                proxies = config.get('proxies', [])
                for p in proxies:
                    if p.get('status') == 'active':
                        proxy_config = {
                            'type': p.get('type', 'socks5'),
                            'server': p['server'],
                            'port': p['port'],
                            'username': p.get('username'),
                            'password': p.get('password')
                        }
                        break
        except Exception as e:
            print(f"Proxy load error: {e}")
        
        proxy_args = build_proxy_args(proxy_config)
        if proxy_config:
            print(f"Using proxy (primary): {proxy_config['server']}:{proxy_config['port']}")
        
        ctx = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            **proxy_args
        )
        ctx.add_cookies(cookies)
        page = ctx.new_page()
        
        page.goto("https://www.facebook.com", timeout=30000)
        time.sleep(1)
        
        for group_id in groups_to_scrape:
            log(f"📂 Loading: {group_id}")
            try:
                scrape_group_all_posts(
                    page, group_id, all_posts, seen_urls, stats,
                    min_scrolls=min_scrolls, max_scrolls=max_scrolls,
                    min_delay=min_delay/5.0, max_delay=max_delay/5.0
                )
                log(f"    ✅ Total so far: {len(all_posts)} posts")
            except Exception as e:
                log(f"    ❌ Error: {e}")
            
            time.sleep(random.uniform(min_delay/5.0, max_delay/5.0))
        
        # Fallback: check if we got very few posts - retry with fallback proxy
        if len(all_posts) < 3:
            fallback_proxy = load_proxy_fallback()
            if fallback_proxy:
                print(f"Few posts ({len(all_posts)}), retrying with fallback proxy...")
                browser.close()
                
                ctx = browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    **build_proxy_args(fallback_proxy)
                )
                ctx.add_cookies(cookies)
                page = ctx.new_page()
                
                page.goto(f"https://www.facebook.com/groups/{group_id}", timeout=45000)
                time.sleep(random.uniform(1.5, 3))
                
                # Re-scrape this group with fallback
                scrape_group_all_posts(page, group_id, all_posts, seen_urls, stats)
        
        browser.close()
    
    # Save all posts
    if all_posts:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_posts, f, ensure_ascii=False, indent=2)
        

        # Save seen URLs for next run
        save_seen_urls(seen_urls)
        
        log(f"\n" + "="*60)
        log(f"📥 ขั้นตอน 1 - เก็บทุกโพสจำนวน: {stats['total_found']} โพส ซ้ำ {stats['duplicates']} เหลือ {len(all_posts)}")
        log(f"📊 TOTAL: {len(all_posts)} posts")
        log(f"💾 Saved to: {OUTPUT_FILE}")
        log(f"📂 Seen URLs รวม: {len(seen_urls)} URLs")
        log("="*60)
    else:
        log(f"\n❌ ไม่เจอโพสเลย!")

if __name__ == "__main__":
    main()
