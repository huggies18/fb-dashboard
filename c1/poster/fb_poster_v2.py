#!/usr/bin/env python3
"""
Facebook Poster v2 - ใช้ span text "คุณกำลังคิดอะไรอยู่" เป็น anchor
"""
import json, time, random
from playwright.sync_api import sync_playwright

LOG_FILE = '/root/.openclaw/workspace/c1/poster/post.log'

def log(msg):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def load_cookies():
    with open('fb_session.json', 'r') as f:
        session = json.load(f)
        return session.get('cookies', [])

def post_to_page(page, message, image_path=None):
    """โพสไปเพจ"""
    
    # 1. ไปเพจ
    page.goto('https://www.facebook.com/61588849713937', timeout=30000)
    time.sleep(random.uniform(3, 5))
    
    # 2. Scroll to top
    page.evaluate('window.scrollTo(0, 0)')
    time.sleep(2)
    
    # 3. หา span ที่มี text "คุณกำลังคิดอะไรอยู่"
    log("🔍 หาปุ่ม 'คุณกำลังคิดอะไรอยู่'...")
    
    try:
        # วิธีที่ 1: หา span แล้วคลิก parent
        span = page.query_selector('span:text("คุณกำลังคิดอะไรอยู่")')
        if span:
            log(f"✅ พบ span: {span.inner_text()}")
            # ลองหา parent ที่ clickable
            parent = span.evaluate('el => el.parentElement.parentElement')
            log(f"📍 Parent tag: {parent.tagName}")
            
            # Click ที่ span โดยตรง
            span.click()
            time.sleep(2)
            log("✅ คลิกแล้ว")
        else:
            log("❌ ไม่พบ span 'คุณกำลังคิดอะไรอยู่'")
            
    except Exception as e:
        log(f"❌ Error: {e}")
    
    # 4. ถ้ามี composer เปิดขึ้น หา textarea
    time.sleep(3)
    
    # หา textarea หรือ contenteditable
    textarea_selectors = [
        'div[contenteditable="true"][role="presentation"]',
        'div[aria-label*="โพส"]',
        'textarea[name="message"]',
        'div[role="textbox"]'
    ]
    
    textbox = None
    for sel in textarea_selectors:
        try:
            el = page.query_selector(sel)
            if el:
                textbox = el
                log(f"✅ พบ composer: {sel}")
                break
        except:
            pass
    
    if not textbox:
        # Debug: ดูว่ามีอะไรเกิดขึ้น
        page.screenshot(path='/root/.openclaw/workspace/content/debug_after_click.png')
        log("❌ ไม่พบ composer - ถ่ายรูป debug แล้ว")
        return False
    
    # 5. พิมพ์ข้อความ
    textbox.click()
    time.sleep(1)
    textbox.fill(message)
    log("✅ พิมพ์ข้อความเสร็จ")
    
    # 6. แนบรูปถ้ามี
    if image_path:
        try:
            attach_btn = page.query_selector('div[aria-label="แนบไฟล์"]')
            if attach_btn:
                attach_btn.click()
                time.sleep(1)
                page.set_input_files('input[type="file"]', image_path)
                log(f"✅ แนบรูป: {image_path}")
        except Exception as e:
            log(f"⚠️ แนบรูปล้มเหลว: {e}")
    
    time.sleep(2)
    
    # 7. กดโพส
    post_buttons = [
        'div[role="button"][aria-label="โพส"]',
        'div[role="button"][aria-label="Post"]',
        'div[data-testid="submit"]'
    ]
    
    for sel in post_buttons:
        try:
            btn = page.query_selector(sel)
            if btn:
                btn.click()
                log("✅ กดโพสแล้ว")
                time.sleep(3)
                log("📤 โพสสำเร็จ!")
                return True
        except:
            pass
    
    log("❌ ไม่พบปุ่มโพส")
    return False

def main():
    with open(LOG_FILE, 'w') as f:
        f.write('')
    
    message = "🧐 How does Solar Cell work?\n\n☀️ Solar panels absorb sunlight\n⚡ Convert to electricity (DC)\n🔄 Inverter converts to AC\n🏠 Power your home\n💡 Excess = sell back to the grid!\n\nReal savings ✅"
    image_path = None
    
    log("📤 เริ่มโพสไปเพจ 61588849713937...")
    
    cookies = load_cookies()
    if not cookies:
        log("❌ ไม่มี cookies")
        return
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
        )
        ctx = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        ctx.add_cookies(cookies)
        page = ctx.new_page()
        
        result = post_to_page(page, message, image_path)
        
        browser.close()
    
    if result:
        log("✅ เสร็จสมบูรณ์!")
    else:
        log("❌ ล้มเหลว")

if __name__ == "__main__":
    main()