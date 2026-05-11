#!/usr/bin/env python3
"""Debug poster - inspect Facebook UI"""
import sys
import json
import time
sys.path.insert(0, '.')

from playwright.sync_api import sync_playwright

LOG_FILE = '/root/.openclaw/workspace/c1/poster/post.log'
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

log("📤 Debug mode - ไปที่เพจแล้ว dump HTML...")

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox',
              '--disable-dev-shm-usage', '--disable-gpu',
              '--disable-blink-features=AutomationControlled']
    )
    ctx = browser.new_context(
        viewport={"width": 1280, "height": 900},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )

    session = load_session()
    cookies = session if isinstance(session, list) else session.get('cookies', [])
    ctx.add_cookies(cookies)
    page = ctx.new_page()

    page.goto(f"https://www.facebook.com/{PAGE_ID}", timeout=30000)
    time.sleep(5)
    log("✅ เปิดเพจแล้ว")

    # Scroll down a bit
    page.evaluate('window.scrollTo(0, 400)')
    time.sleep(3)

    # Click on the page body first to focus
    page.click('body')
    time.sleep(1)

    # Find any editable areas
    log("--- Looking for composer elements ---")

    # Try aria-label based
    try:
        labels = ['คุณกำลังคิดอะไรอยู่', 'What\\'s on your mind', 'สร้างโพส']
        for lbl in labels:
            els = page.locator(f'[aria-label="{lbl}"]').all()
            log(f"  aria-label '{lbl}': {len(els)} found")
            for i, el in enumerate(els[:3]):
                try:
                    log(f"    [{i}] visible={el.is_visible()}, tag={el.evaluate('el => el.tagName')}")
                except:
                    pass
    except Exception as e:
        log(f"aria-label search error: {e}")

    # Try text-based spans
    try:
        spans = page.locator('span').all()
        for span in spans[:20]:
            try:
                txt = span.text_content()
                if txt and len(txt) < 100 and span.is_visible():
                    tag = span.evaluate('el => el.tagName')
                    aria = span.get_attribute('aria-label') or ''
                    log(f"  span: '{txt[:50]}' tag={tag} aria='{aria[:30]}'")
            except:
                pass
    except Exception as e:
        log(f"span search error: {e}")

    # Try clicking any visible textbox-like div
    try:
        editable_divs = page.locator('div[contenteditable="true"]').all()
        log(f"contenteditable divs: {len(editable_divs)}")
        for i, d in enumerate(editable_divs[:5]):
            try:
                log(f"  [{i}] visible={d.is_visible()}, height={d.bounding_box()}")
            except:
                pass
    except Exception as e:
        log(f"editable divs error: {e}")

    # Take screenshot
    page.screenshot(path='/root/.openclaw/workspace/c1/poster/debug_composer.png')
    log("📸 บันทึก screenshot: debug_composer.png")

    browser.close()
    log("--- Debug done ---")