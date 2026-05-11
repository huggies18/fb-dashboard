#!/usr/bin/env python3
"""
Facebook Poster - โพสข้อความ + รูปไปเพจ Facebook
=========================================
ใช้ Playwright + Facebook session cookies ที่มีอยู่
"""

import sys
sys.path.insert(0, '.')

import json, time, os, random
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

THAI_OFFSET = timedelta(hours=7)
LOG_FILE = '/root/.openclaw/workspace/highsolar/poster/post.log'

def log(msg):
    ts = (datetime.now() + THAI_OFFSET).strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def load_cookies():
    try:
        with open('fb_session.json', 'r') as f:
            session = json.load(f)
        # Handle both list format and dict format
        if isinstance(session, list):
            return session
        return session.get('cookies', [])
    except Exception as e:
        log(f"❌ โหลด cookies ล้มเหลว: {e}")
        return []

def post_to_facebook(page, message, image_path=None, target="me"):
    """
    โพสไป Facebook
    - target="me" = โพส personal
    - target="PAGE_ID" = โพสเพจ
    - target="GROUP_ID" = โพสกลุ่ม
    """
    
    log(f"📤 เริ่มโพส...")
    
    # 1. เปิด Facebook
    page.goto("https://www.facebook.com", timeout=30000)
    time.sleep(random.uniform(2, 4))
    
    # 2. ไปที่เป้าหมาย
    if target == "me":
        page.goto("https://www.facebook.com/", timeout=30000)
    else:
        page.goto(f"https://www.facebook.com/{target}", timeout=30000)
    
    time.sleep(random.uniform(3, 5))
    
    # 3. หาช่องโพส (อาจเปลี่ยนได้ตาม Facebook version)
    selectors = [
        "div[contenteditable='true'][role='presentation']",
        "div[contenteditable='true']",
        "div[aria-label*='คุณกำลังคิด']",
        "span[aria-label*='คุณกำลังคิด']",
        "div[role='presentation'] textarea",
        "div[aria-label='สร้างโพส'] textarea",
        "div[data-testid='message'] textarea",
        "textarea[name='message']",
        "[contenteditable='true'][role='button']"
    ]
    
    textbox = None
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                textbox = el
                log(f"✅ พบช่องโพส: {sel}")
                break
            else:
                log(f"⚠️ เจอแต่ไม่ visible: {sel}")
        except Exception as e:
            log(f"⚠️ ลอง {sel}: {e}")
            continue
    
    if not textbox:
        log("❌ ไม่พบช่องโพส - Facebook UI อาจเปลี่ยนแล้ว")
        return False
    
    # 4. พิมพ์ข้อความ
    textbox.click()
    time.sleep(1)
    textbox.fill(message)
    log("✅ พิมพ์ข้อความเสร็จ")
    
    # 5. ถ้ามีรูป ให้แนบ
    if image_path and os.path.exists(image_path):
        time.sleep(1)
        # หาปุ่มแนบรูป
        attach_selectors = [
            "div[aria-label='แนบไฟล์']",
            "[data-testid='media-attachment-add-photo']",
            "div[role='button'][aria-label*='photo']"
        ]
        
        for sel in attach_selectors:
            try:
                btn = page.query_selector(sel)
                if btn:
                    btn.click()
                    time.sleep(1)
                    # ใส่ไฟล์
                    page.set_input_files('input[type="file"]', image_path)
                    log(f"✅ แนบรูป: {image_path}")
                    time.sleep(2)
                    break
            except:
                continue
    
    # 6. กดโพส
    post_selectors = [
        "div[role='button'][aria-label='โพส']",
        "[data-testid='submit']",
        "div[role='button'][aria-label='Post']",
        "span[data-testid='fb-ellipsis-item']"
    ]
    
    for sel in post_selectors:
        try:
            btn = page.query_selector(sel)
            if btn:
                btn.click()
                log("✅ กดโพสแล้ว")
                time.sleep(3)
                log("📤 โพสเสร็จสิ้น!")
                return True
        except:
            continue
    
    log("❌ ไม่พบปุ่มโพส")
    return False

def main():
    import sys
    
    # รับ target จาก command line
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = input("ใส่ Page ID หรือ Group ID: ").strip()
    
    # รับข้อความจาก command line
    if len(sys.argv) > 2:
        message = sys.argv[2]
    else:
        message = input("ใส่ข้อความที่จะโพส: ").strip()
    
    # รับรูปจาก command line (optional)
    image_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    log(f"📤 โพสไป: {target}")
    log(f"📝 ข้อความ: {message}")
    if image_path:
        log(f"🖼️ รูป: {image_path}")
    
    result = None
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', 
                  '--disable-dev-shm-usage', '--disable-gpu']
        )
        
        ctx = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        cookies = load_cookies()
        if not cookies:
            log("❌ ไม่มี cookies")
            return
        
        ctx.add_cookies(cookies)
        page = ctx.new_page()
        
        result = post_to_facebook(page, message, image_path, target)
        
        browser.close()
    
    if result:
        log("✅ โพสสำเร็จ!")
    else:
        log("❌ โพสล้มเหลว")

if __name__ == "__main__":
    # รันตรงๆ = ทดสอบ
    main()
    
    # ถ้าอยากใช้เป็น function ใน script อื่น:
    # from fb_poster import post_to_facebook
    # post_to_facebook(page, "ข้อความ", "/path/to/image.jpg", "PAGE_ID")