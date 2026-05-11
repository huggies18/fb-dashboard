#!/usr/bin/env python3
"""
Facebook Poster - C1 - Computer Rental
=========================================
Flow: คุณกำลังคิดอะไรอยู่ → พิมพ์ → ถัดไป → โพสต์ → ไม่ใช่ตอนนี้
"""

import sys
sys.path.insert(0, '.')

import json, time, os, random
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

THAI_OFFSET = timedelta(hours=7)
LOG_FILE = '/root/.openclaw/workspace/c1/poster/post.log'

def log(msg):
    ts = (datetime.now() + THAI_OFFSET).strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def load_cookies():
    try:
        with open('fb_poster_session.json', 'r') as f:
            session = json.load(f)
        return session.get('cookies', [])
    except Exception as e:
        log(f"❌ โหลด cookies ล้มเหลว: {e}")
        return []

def post_to_facebook(page, message, page_id="me"):
    """
    โพสไป Facebook Page
    Flow: คุณกำลังคิดอะไรอยู่ → พิมพ์ → ถัดไป → โพสต์ → ไม่ใช่ตอนนี้
    """
    
    log(f"📤 เริ่มโพสไป {page_id}...")
    
    # 1. ไปที่เพจ
    if page_id == "me":
        page.goto("https://www.facebook.com/", timeout=30000)
    else:
        page.goto(f"https://www.facebook.com/{page_id}", timeout=30000)
    
    time.sleep(random.uniform(5, 8))
    
    # 2. Click composer "คุณกำลังคิดอะไรอยู่"
    try:
        page.get_by_text("คุณกำลังคิดอะไรอยู่", exact=True).click()
        log("✅ Click composer")
        time.sleep(3)
    except Exception as e:
        log(f"❌ Click composer ล้มเหลว: {e}")
        return False
    
    # 3. พิมพ์ข้อความ
    try:
        page.keyboard.type(message, delay=50)
        log("✅ พิมพ์ข้อความเสร็จ")
        time.sleep(2)
    except Exception as e:
        log(f"❌ พิมพ์ล้มเหลว: {e}")
        return False
    
    # 4. Click ถัดไป
    try:
        page.evaluate('''() => {
            const btns = document.querySelectorAll('[role="button"]');
            for (const btn of btns) {
                if (btn.textContent.trim() === "ถัดไป") {
                    btn.click();
                    return;
                }
            }
        }''')
        log("✅ Click ถัดไป")
        time.sleep(2)
    except Exception as e:
        log(f"❌ Click ถัดไป ล้มเหลว: {e}")
        return False
    
    # 5. Click โพสต์
    try:
        page.evaluate('''() => {
            const btns = document.querySelectorAll('[role="button"]');
            for (const btn of btns) {
                if (btn.textContent.trim() === "โพสต์") {
                    btn.click();
                    return;
                }
            }
        }''')
        log("✅ Click โพสต์")
        time.sleep(3)
    except Exception as e:
        log(f"❌ Click โพสต์ ล้มเหลว: {e}")
        return False
    
    # 6. Click ไม่ใช่ตอนนี้ (WhatsApp dialog)
    try:
        page.get_by_text("ไม่ใช่ตอนนี้", exact=True).click(force=True)
        log("✅ Click ไม่ใช่ตอนนี้ (WhatsApp)")
        time.sleep(3)
    except Exception as e:
        log(f"ℹ️ ไม่มี WhatsApp dialog: {e}")
    
    log("✅ โพสสำเร็จ!")
    return True

def main():
    import sys
    
    # รับ target จาก command line
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = input("ใส่ Page ID: ").strip()
    
    # รับข้อความจาก command line
    if len(sys.argv) > 2:
        message = sys.argv[2]
    else:
        message = input("ใส่ข้อความที่จะโพส: ").strip()
    
    log(f"📤 โพสไป: {target}")
    log(f"📝 ข้อความ: {message}")
    
    result = None
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', 
                  '--disable-dev-shm-usage', '--disable-gpu']
        )
        
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
        )
        
        cookies = load_cookies()
        if not cookies:
            log("❌ ไม่มี cookies")
            return
        
        ctx.add_cookies(cookies)
        page = ctx.new_page()
        
        result = post_to_facebook(page, message, target)
        
        browser.close()
    
    if result:
        log("✅ โพสสำเร็จ!")
    else:
        log("❌ โพสล้มเหลว")

if __name__ == "__main__":
    main()