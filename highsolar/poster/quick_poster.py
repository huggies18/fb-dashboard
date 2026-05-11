#!/usr/bin/env python3
"""Quick poster using existing Playwright setup"""
import sys
import json
import time
import random
sys.path.insert(0, '.')

from playwright.sync_api import sync_playwright

LOG_FILE = '/root/.openclaw/workspace/highsolar/poster/post.log'
PAGE_ID = '61588849713937'

def log(msg):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def load_session():
    with open('fb_session.json', 'r') as f:
        return json.load(f)

message = """🏠 ก่อน vs หลังติดโซลาร์เซลล์

❌ ก่อนติด:
• ค่าไฟเดือนละ 5,000-8,000 บาท
• ใช้แอร์ไม่อิสระ ต้องประหยัด
• กังวลเรื่องค่าไฟทุกเดือน

✅ หลังติด:
• ค่าไฟเหลือ 1,000-2,000 บาท
• ใช้ไฟได้สบายใจ
• ติดแล้วอยากติดเพิ่ม!

💡 ถ้าบ้านของคุณโดนแดดเยอะ ยิ่งคุ้มค่า
ทักแชทมาคุยกันได้เลย 👇"""

image_path = '/root/.openclaw/media/tool-image-generation/image-1---29c77929-b75d-46c8-8e6f-757080ff0f10.png'

log("📤 เริ่มโพสด้วย Playwright...")

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox',
              '--disable-dev-shm-usage', '--disable-gpu',
              '--disable-blink-features=AutomationControlled']
    )
    ctx = browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )

    session = load_session()
    cookies = session if isinstance(session, list) else session.get('cookies', [])
    ctx.add_cookies(cookies)
    page = ctx.new_page()

    # Go to page
    page.goto(f"https://www.facebook.com/{PAGE_ID}", timeout=30000)
    time.sleep(random.uniform(3, 5))
    log("✅ เปิดเพจแล้ว")

    # Find composer
    time.sleep(2)
    page.evaluate('window.scrollTo(0, 300)')
    time.sleep(2)

    # Try to find and click the composer
    try:
        composer = page.locator('span:text-is("คุณกำลังคิดอะไรอยู่")').first
        if composer.is_visible():
            composer.click()
            log("✅ กด composer แล้ว")
            time.sleep(2)
    except Exception as e:
        log(f"⚠️ หา composer: {e}")

    # Find textbox
    selectors = [
        'div[contenteditable="true"][role="presentation"]',
        'div[role="textbox"]',
        'div[contenteditable="true"]'
    ]

    textbox = None
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if el.is_visible():
                bb = el.bounding_box()
                if bb and bb['height'] > 30 and bb['height'] < 150:
                    textbox = el
                    log(f"✅ พบ textbox: {sel}, height={bb['height']}")
                    break
        except:
            pass

    if not textbox:
        log("❌ ไม่เจอ textbox")
        browser.close()
        sys.exit(1)

    textbox.click()
    time.sleep(1)
    textbox.fill(message)
    log("✅ พิมพ์ข้อความเสร็จ")
    time.sleep(2)

    # Upload image if present
    if image_path:
        try:
            # Click photo button
            photo_btn = page.locator('[aria-label="รูปภาพ/วิดีโอ"]').first
            if photo_btn.is_visible():
                photo_btn.click()
                log("✅ กดปุ่มรูปภาพ")
                time.sleep(2)

            # Upload via file input
            file_input = page.locator('input[type="file"]').first
            file_input.set_input_files(image_path)
            log(f"✅ อัพโหลดรูป: {image_path}")
            time.sleep(4)
        except Exception as e:
            log(f"⚠️ อัพโหลดรูปล้มเหลว: {e}")

    # Click Next
    try:
        next_btn = page.locator('span:text-is("ถัดไป")').first
        if next_btn.is_visible():
            next_btn.click()
            log("✅ กด 'ถัดไป'")
            time.sleep(2)
    except Exception as e:
        log(f"⚠️ หา Next: {e}")

    # Click Post
    try:
        post_btn = page.locator('[role="button"]:text-is("โพสต์")').first
        if post_btn.is_visible():
            post_btn.click()
            log("✅ กด 'โพสต์'")
            time.sleep(3)
            log("📤 โพสสำเร็จ!")
        else:
            log("❌ ไม่เจอปุ่มโพสต์")
    except Exception as e:
        log(f"⚠️ โพส: {e}")

    browser.close()

log("✅ เสร็จสมบูรณ์!")