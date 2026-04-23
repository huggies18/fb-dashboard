#!/usr/bin/env python3
"""
Facebook Group Scraper - HYBRID + MiniMax AI
============================================
- Queue + Worker Pool (3 workers parallel)
- 1 job = 1 group
- Browser reuse limit: 2-3 groups
- AI Analysis: JSON format (is_lead, score, reason)
- Save to leads folder
- Notify Telegram on completion
"""

import sys
sys.path.insert(0, '.')

import json, time, random, os, asyncio, signal
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from telegram import Bot
from queue import Queue
from threading import Thread, Lock

# Import Ultra Accurate AI Filter
from ai_buyer_filter import ultra_analyze, extract_contact

# ==================== CONFIG ====================
THAI_OFFSET = timedelta(hours=7)
MAX_SCROLLS = 3
MAX_RETRIES = 2
BROWSER_REUSE_LIMIT = 2
WORKER_COUNT = 3
DELAY_MIN = 2
DELAY_MAX = 5
LEADS_DIR = "/root/.openclaw/workspace/facebook-scraper/leads"
PENDING_DIR = "/root/.openclaw/workspace/facebook-scraper/pending"

GROUPS = [
    "1925997401002801",
    "383849116272497",
    "2317142971864047",
    "thaisolarcell",
    "1671213103178339",
    "429829328127055"
]

BOT_TOKEN = '8774902841:AAFveLJDs-Bf02cPkBhZVPU5JBw_sdLIhNw'
USER_ID = '6780942246'

# ==================== STATE ====================
group_queue = Queue()
found_urls = set()
found_lock = Lock()
stats_lock = Lock()
stats = {'total_leads': 0, 'total_scraped': 0, 'groups_completed': 0}
cookies = None
shutdown_flag = False

# Load existing URLs from leads folder to prevent duplicates
def load_existing_urls():
    """Load URLs from existing lead files to prevent duplicates"""
    existing = set()
    if os.path.exists(LEADS_DIR):
        for fname in os.listdir(LEADS_DIR):
            if fname.startswith('lead_') and fname.endswith('.json'):
                fpath = os.path.join(LEADS_DIR, fname)
                try:
                    with open(fpath, 'r') as f:
                        lead = json.load(f)
                        if 'url' in lead:
                            existing.add(lead['url'])
                except:
                    pass
    return existing

# ==================== HELPERS ====================
def thai_time_str():
    return (datetime.now() + THAI_OFFSET).strftime("%H:%M:%S")

def log(msg, worker_id=0):
    prefix = f"[{thai_time_str()}]"
    if worker_id > 0:
        prefix += f" [Worker-{worker_id}]"
    print(f"{prefix} {msg}")

def random_delay():
    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

# ==================== AI ANALYSIS (MiniMax Format) ====================
def analyze_post(post_text, post_url, group_id):
    """
    AI วิเคราะห์โพสต์แบบ JSON สั้นที่สุด
    Format: {is_lead, score, reason}
    """
    post_lower = post_text.lower()
    
    # Keywords scoring
    # Keywords สำหรับ Buyer (จากการวิเคราะห์ MiniMax AI)
    buyer_kw = [
        # คำทั่วไป
        'หาบริษัท', 'หาร้าน', 'อยากติด', 'อยากได้', 'อยากซื้อ', 
        'ต้องการติด', 'ต้องการซื้อ', 'กำลังหา', 'กำลังมอง', 
        'สนใจติด', 'สนใจซื้อ', 'ขอราคา', 'รบกวนราคา', 
        'ถามราคา', 'เท่าไหร่', 'สอบถามราคา', 'อยากติดโซล่า', 
        'ติดตั้งโซล่า', 'ราคาโซล่า', 'ค่าไฟโซล่า', 'พร้อมติด', 
        'ติดกี่w', 'ติดกี่kw', 'แนะนำบริษัท', 'ใครติด', 'อยากได้',
        # คำเปรียบเทียบ/ถาม (สำคัญ!)
        'รีวิว', 'เปรียบเทียบ', 'ดีกว่า', 'เลือกไม่ถูก', 'ขอดู',
        'ดีไหม', 'เป็นไง', 'แนะนำหน่อย', 'ควรเลือก', 'ตัดสินใจ',
        'อยากทราบ', 'อยากเข้าใจ', 'มีคำแนะนำ', 'ขอคำแนะนำ',
        # คำเรื่องค่าใช้จ่าย/ประหยัด
        'ประหยัดค่าไฟ', 'ค่าไฟ', 'ลดค่าไฟ', 'กี่บาท', 'คุ้มไหม',
        'ค่าใช้จ่าย', 'งบประมาณ', 'ราคาเท่าไหร่',
        # คำถามก่อนซื้อ
        'ควรซื้อ', 'ควรติด', 'ควรเลือก', 'ซื้อดีไหม', 'ติดดีไหม',
        'เหมาะกับ', 'กำลังพิจารณา', 'กำลังศึกษา', 'อยากศึกษา'
    ]
    
    seller_kw = ['ขาย', 'ปล่อย', 'มีขาย', 'ราคา', 'โปรโมชั่น', 'ส่วนลด', 
                 'พร้อมส่ง', 'in stock', 'มีสินค้า', 'จำหน่าย', 'รับติดตั้ง',
                 'ติดตั้งให้', 'บริการติดตั้ง', 'มาเลือก', 'รับสั่ง', 'สั่งซื้อ',
                 'มือ1', 'มือ2', 'ของใหม่', 'สภาพดี', 'พร้อมใช้']
    
    buyer_score = sum(1 for w in buyer_kw if w in post_lower)
    seller_score = sum(1 for w in seller_kw if w in post_lower)
    
    # Determine is_lead and reason (5 คำ)
    if buyer_score > 0 and seller_score == 0:
        is_lead = True
        score = min(buyer_score * 2, 10)
        
        # Reason ที่ละเอียดกว่า (จากการวิเคราะห์ MiniMax AI)
        if 'ดีไหม' in post_lower or 'เป็นไง' in post_lower or 'ควรซื้อ' in post_lower or 'ควรติด' in post_lower:
            reason = "สอบถามก่อนซื้อ"
        elif 'ประหยัดค่าไฟ' in post_lower or 'ลดค่าไฟ' in post_lower or 'ค่าไฟ' in post_lower:
            reason = "สนใจเรื่องค่าไฟ/ประหยัด"
        elif 'เปรียบเทียบ' in post_lower or 'ดีกว่า' in post_lower or 'เลือกไม่ถูก' in post_lower:
            reason = "เปรียบเทียบ/เลือกระหว่าง"
        elif 'ขอราคา' in post_lower or 'ถามราคา' in post_lower or 'เท่าไหร่' in post_lower or 'กี่บาท' in post_lower:
            reason = "สอบถามราคา"
        elif 'อยากติด' in post_lower or 'ติดตั้ง' in post_lower or 'พร้อมติด' in post_lower:
            reason = "ต้องการติดตั้งโซล่า"
        elif 'หาบริษัท' in post_lower or 'หาช่าง' in post_lower or 'แนะนำบริษัท' in post_lower or 'ขอคำแนะนำ' in post_lower:
            reason = "หาบริษัท/ช่างติดตั้ง"
        elif 'รีวิว' in post_lower or 'ขอดู' in post_lower or 'มีคำแนะนำ' in post_lower:
            reason = "ต้องการรีวิว/คำแนะนำ"
        elif 'กำลังหา' in post_lower or 'กำลังมอง' in post_lower or 'กำลังพิจารณา' in post_lower:
            reason = "กำลังพิจารณาซื้อ"
        elif 'อยากศึกษา' in post_lower or 'อยากเข้าใจ' in post_lower:
            reason = "ศึกษาเพิ่มเติม"
        else:
            reason = "สนใจโซล่าเซลล์"
            
    elif seller_score > 0 and buyer_score == 0:
        is_lead = False
        score = seller_score
        reason = "โฆษณาขาย"
    else:
        is_lead = False
        score = 0
        reason = "ไม่เกี่ยวข้อง"
    
    return {
        'is_lead': is_lead,
        'score': score,
        'reason': reason
    }

def extract_contact(text):
    """ดึงช่องทางติดต่อ"""
    import re
    phones = re.findall(r'0[0-9]{9}', text)
    if phones:
        return f"โทร: {phones[0]}"
    lines = re.findall(r'LINE[:\s]*(@?[a-zA-Z0-9]+)', text)
    if lines:
        return f"Line: {lines[0]}"
    return None

def save_lead(analysis, post_url, post_text, post_time, group_id):
    """บันทึก lead ด้วย Ultra Accurate AI"""
    os.makedirs(LEADS_DIR, exist_ok=True)
    
    lead = {
        'url': post_url,
        'message': post_text[:500],
        'group': group_id,
        'post_time': post_time,
        'scraped_at': datetime.now().isoformat(),
        'is_lead': analysis['is_lead'],
        'score': analysis['score'],
        'reason': analysis['reason'],
        'intent_type': analysis.get('intent_type', 'buyer'),
        'contact': extract_contact(post_text)
    }
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filepath = os.path.join(LEADS_DIR, f"lead_{timestamp}.json")
    
    with open(filepath, 'w') as f:
        json.dump(lead, f, ensure_ascii=False, indent=2)
    
    return lead

# ==================== BROWSER MANAGEMENT ====================
def launch_browser(playwright):
    browser = playwright.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
    )
    return browser

def new_context(browser, cookies):
    ctx = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    ctx.add_cookies(cookies)
    return ctx

# ==================== SCRAPING ====================
def scrape_single_group(page, group_id: str, worker_id: int):
    """Scrape ONE group and return leads found"""
    log(f"📂 Loading group: {group_id}", worker_id)
    leads = []
    
    try:
        page.goto(f"https://www.facebook.com/groups/{group_id}", timeout=30000)
        random_delay()
        
        for scroll_num in range(MAX_SCROLLS):
            log(f"   📜 Scroll {scroll_num+1}/{MAX_SCROLLS}...", worker_id)
            
            page.mouse.wheel(0, random.randint(400, 800))
            random_delay()
            
            posts = page.query_selector_all("div[role='article']")
            log(f"      📰 Found {len(posts)} posts", worker_id)
            
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
                    
                    with found_lock:
                        if post_url in found_urls:
                            continue
                        found_urls.add(post_url)
                    
                    msg = ""
                    for sel in ['div[data-ad-preview="message"]', 'div[dir="auto"]', 'span[dir="auto"]']:
                        try:
                            el = post.query_selector(sel)
                            if el:
                                txt = el.inner_text()
                                if len(txt) > 20:
                                    msg = txt
                                    break
                        except:
                            continue
                    
                    if len(msg) < 20:
                        continue
                    
                    # AI Analysis (Ultra Accurate)
                    analysis = ultra_analyze(msg, post_url, group_id)
                    
                    # Get post time
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
                    
                    # Save if is_lead
                    if analysis['is_lead']:
                        lead = save_lead(analysis, post_url, msg, post_time, group_id)
                        leads.append(lead)
                        log(f"      🟢 LEAD | score:{analysis['score']} | {analysis['reason']}", worker_id)
                    
                    random_delay()
                    
                except Exception as e:
                    continue
            
            random_delay()
        
    except Exception as e:
        log(f"   ❌ Group error: {e}", worker_id)
    
    return leads

# ==================== WORKER ====================
def worker_loop(worker_id: int, groups_list: list):
    global stats, shutdown_flag
    
    log(f"🚀 Worker {worker_id} starting...", worker_id)
    
    groups_scraped = 0
    all_leads = []
    
    while not shutdown_flag:
        try:
            group_id = group_queue.get(timeout=2)
        except:
            if group_queue.empty():
                log(f"🏁 Worker {worker_id} queue empty, exiting", worker_id)
                break
            continue
        
        # Restart browser after reuse limit
        if groups_scraped >= BROWSER_REUSE_LIMIT:
            log(f"🔄 Worker {worker_id} restarting browser...", worker_id)
            groups_scraped = 0
        
        try:
            with sync_playwright() as p:
                browser = launch_browser(p)
                ctx = new_context(browser, cookies)
                page = ctx.new_page()
                
                page.goto("https://www.facebook.com", timeout=30000)
                time.sleep(2)
                
                # Retry logic
                for retry in range(MAX_RETRIES):
                    try:
                        leads = scrape_single_group(page, group_id, worker_id)
                        all_leads.extend(leads)
                        
                        with stats_lock:
                            stats['total_leads'] += len(leads)
                            stats['groups_completed'] += 1
                        
                        break
                    except Exception as e:
                        log(f"   ⚠️ Retry {retry+1}/{MAX_RETRIES}: {e}", worker_id)
                        if retry == MAX_RETRIES - 1:
                            log(f"   ❌ Failed after {MAX_RETRIES} retries", worker_id)
                        else:
                            random_delay()
                
                groups_scraped += 1
                browser.close()
                
        except Exception as e:
            log(f"❌ Worker {worker_id} browser error: {e}", worker_id)
            try:
                browser.close()
            except:
                pass
        
        group_queue.task_done()
        random_delay()
    
    log(f"🏁 Worker {worker_id} done. Total leads: {len(all_leads)}", worker_id)
    return all_leads

# ==================== NOTIFY ====================
async def send_notify(all_leads: list):
    if not all_leads:
        return
    
    bot = Bot(token=BOT_TOKEN)
    thai_now = datetime.now() + THAI_OFFSET
    
    msg = f"🟢 <b>พบ Buyer Leads ใหม่!</b>\n"
    msg += f"⏰ เมื่อ: {thai_now.strftime('%H:%M')} (UTC+7)\n"
    msg += f"📊 พบ: {len(all_leads)} โพส\n"
    msg += f"👥 Workers: {WORKER_COUNT} ตัว\n\n"
    msg += f"💡 พิมพ์ /wbuyer เพื่อ export CSV\n\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    
    for i, lead in enumerate(all_leads[:10], 1):
        # Format: number + emoji + reason + score + post time
        post_time = lead.get('post_time', '')
        time_str = f" / เวลาโพสเมื่อ {post_time}ก่อน" if post_time else ""
        
        # Green for HIGH intent, Yellow for others
        reason = lead.get('reason', '')
        if 'กำลังจะ' in reason or 'สนใจ' in reason:
            emoji = '🟢'
        else:
            emoji = '🟡'
        
        msg += f"{i}. {emoji} {reason} score:{lead['score']}{time_str}\n"
        msg += f" 📝 \"{lead['message'][:80]}...\"\n"
        msg += f" 🔗 {lead['url']}\n\n"
    
    await bot.send_message(chat_id=USER_ID, text=msg, parse_mode='HTML')

# ==================== MAIN ====================
def main():
    global cookies, shutdown_flag, stats
    
    print("="*60)
    print("🚀 FACEBOOK SCRAPER - HYBRID + MiniMax AI")
    print("="*60)
    log(f"📋 Groups: {len(GROUPS)}")
    log(f"👥 Workers: {WORKER_COUNT}")
    log(f"🔄 Browser reuse limit: {BROWSER_REUSE_LIMIT}")
    log(f"⏳ Delay: {DELAY_MIN}-{DELAY_MAX} seconds")
    log(f"🧠 AI: JSON format - is_lead, score, reason")
    print("="*60)
    
    # Load cookies
    try:
        with open("fb_cookies.json") as f:
            cookies = json.load(f)
        log(f"✅ Loaded {len(cookies)} cookies")
    except Exception as e:
        log(f"❌ Cannot load cookies: {e}")
        return
    
    # Setup queue
    for group in GROUPS:
        group_queue.put(group)
    
    log(f"📋 Queue filled with {group_queue.qsize()} groups")
    
    # Load existing URLs to prevent duplicates
    global found_urls
    found_urls = load_existing_urls()
    log(f"📁 Existing leads: {len(found_urls)} URLs")
    
    # Handle shutdown
    def shutdown_handler(sig, frame):
        log("⚠️ Shutdown signal received...")
        shutdown_flag = True
    
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    # Start workers
    threads = []
    all_leads = []
    
    log(f"🚀 Starting {WORKER_COUNT} workers...")
    
    for i in range(WORKER_COUNT):
        t = Thread(target=lambda wid: all_leads.extend(worker_loop(wid, GROUPS)), args=(i+1,))
        t.start()
        threads.append(t)
        time.sleep(1)
    
    for t in threads:
        t.join()
    
    # Final notification
    if all_leads:
        asyncio.run(send_notify(all_leads))
    
    leads_count = len([f for f in os.listdir(LEADS_DIR) if f.startswith('lead_')])
    
    print("="*60)
    print(f"✅ COMPLETE!")
    print(f"📊 Leads found this run: {len(all_leads)}")
    print(f"📁 Total in leads folder: {leads_count}")
    print(f"🏁 Groups completed: {stats['groups_completed']}")
    print(f"💡 Run /wbuyer to export CSV")
    print("="*60)

if __name__ == "__main__":
    main()