#!/usr/bin/env python3
"""Debug screenshot at each step"""
import sys, json, time
sys.path.insert(0, '.')

from playwright.sync_api import sync_playwright

PAGE_ID = '61588849713937'
message = "ทดสอบโพสจาก Playwright"
image_path = '/root/.openclaw/media/tool-image-generation/image-1---95f4a848-78dc-4d6c-814d-ad81dfc87c01.png'

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

    with open('fb_poster_session.json') as f:
        session = json.load(f)
    cookies = session.get('cookies', [])
    ctx.add_cookies(cookies)
    page = ctx.new_page()

    page.goto(f"https://www.facebook.com/{PAGE_ID}", timeout=30000)
    time.sleep(5)
    page.screenshot(path='/root/.openclaw/workspace/highsolar/poster/debug/01_page.png')
    print("1. Page loaded")

    # Step 1: Click composer
    page.evaluate('''() => {
        const els = document.querySelectorAll('[role="button"]');
        for (const el of els) {
            if (el.textContent.includes("คุณกำลังคิดอะไรอยู่")) {
                el.click();
                break;
            }
        }
    }''')
    time.sleep(2)
    page.screenshot(path='/root/.openclaw/workspace/highsolar/poster/debug/02_composer.png')
    print("2. Composer clicked")

    # Step 2: Type
    page.evaluate(f'''() => {{
        const els = document.querySelectorAll('[contenteditable="true"]');
        for (const el of els) {{
            if (el.offsetParent !== null) {{
                el.textContent = "{message}";
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                break;
            }}
        }}
    }}''')
    time.sleep(1)
    page.screenshot(path='/root/.openclaw/workspace/highsolar/poster/debug/03_typed.png')
    print("3. Typed")

    # Step 3: Click photo
    page.evaluate('''() => {
        const els = document.querySelectorAll('[role="button"]');
        for (const el of els) {
            if (el.textContent.includes("รูปภาพ/วิดีโอ")) {
                el.click();
                break;
            }
        }
    }''')
    time.sleep(2)
    page.screenshot(path='/root/.openclaw/workspace/highsolar/poster/debug/04_photo_dialog.png')
    print("4. Photo clicked")

    # Upload
    try:
        file_input = page.locator('input[type="file"]').first
        if file_input.is_visible():
            file_input.set_input_files(image_path)
            print("Uploaded")
            time.sleep(4)
            page.screenshot(path='/root/.openclaw/workspace/highsolar/poster/debug/05_uploaded.png')
    except Exception as e:
        print(f"Upload err: {e}")

    # Step 5: Click ถัดไป
    page.evaluate('''() => {
        const els = document.querySelectorAll('[role="button"]');
        for (const el of els) {
            if (el.textContent === "ถัดไป") {
                el.click();
                break;
            }
        }
    }''')
    time.sleep(3)
    page.screenshot(path='/root/.openclaw/workspace/highsolar/poster/debug/06_after_next.png')
    print("5. After ถัดไป")

    # Step 6: Click ไม่ใช่ตอนนี้
    page.evaluate('''() => {
        const els = document.querySelectorAll('[role="button"]');
        for (const el of els) {
            if (el.textContent.includes("ไม่ใช่ตอนนี้")) {
                el.click();
                break;
            }
        }
    }''')
    time.sleep(2)
    page.screenshot(path='/root/.openclaw/workspace/highsolar/poster/debug/07_after_whatsapp.png')
    print("6. After ไม่ใช่ตอนนี้")

    # Step 7: Click สร้างโพสต์
    page.evaluate('''() => {
        const els = document.querySelectorAll('[role="button"]');
        for (const el of els) {
            if (el.textContent === "สร้างโพสต์") {
                el.click();
                break;
            }
        }
    }''')
    time.sleep(3)
    page.screenshot(path='/root/.openclaw/workspace/highsolar/poster/debug/08_after_post.png')
    print("7. After click สร้างโพสต์")

    # Check URL
    print(f"Current URL: {page.url}")

    browser.close()
    print("Done - screenshots saved to debug/")