#!/usr/bin/env python3
"""Debug - JS click"""
import sys, json, time
sys.path.insert(0, '.')

from playwright.sync_api import sync_playwright

PAGE_ID = '61588849713937'
message = "ทดสอบโพส"
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

    # Click composer via JS
    page.evaluate('''() => {
        const els = document.querySelectorAll('[role="button"]');
        for (const el of els) {
            if (el.textContent.includes("คุณกำลังคิดอะไรอยู่")) {
                el.click();
                break;
            }
        }
    }''')
    print("Clicked composer via JS")
    time.sleep(2)

    # Type via JS
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
    print(f"Typed: {message}")
    time.sleep(1)

    # Click photo button via JS
    page.evaluate('''() => {
        const els = document.querySelectorAll('[role="button"]');
        for (const el of els) {
            if (el.textContent.includes("รูปภาพ/วิดีโอ")) {
                el.click();
                break;
            }
        }
    }''')
    print("Clicked photo button via JS")
    time.sleep(2)

    # Upload image
    page.evaluate(f'''() => {{
        const input = document.querySelector('input[type="file"]');
        if (input) {{
            // Create DataTransfer
            const dataTransfer = new DataTransfer();
            // Note: Can't set files via JS for security reasons
        }}
    }}''')
    
    # Try to upload via set_input_files
    try:
        file_input = page.locator('input[type="file"]').first
        if file_input.is_visible():
            file_input.set_input_files(image_path)
            print("Uploaded image")
            time.sleep(4)
    except Exception as e:
        print(f"Upload error: {e}")

    # Click ถัดไป via JS
    page.evaluate('''() => {
        const els = document.querySelectorAll('[role="button"]');
        for (const el of els) {
            if (el.textContent === "ถัดไป") {
                el.click();
                break;
            }
        }
    }''')
    print("Clicked ถัดไป via JS")
    time.sleep(3)

    # Click สร้างโพสต์ via JS
    page.evaluate('''() => {
        const els = document.querySelectorAll('[role="button"]');
        for (const el of els) {
            if (el.textContent === "สร้างโพสต์") {
                el.click();
                break;
            }
        }
    }''')
    print("Clicked สร้างโพสต์ via JS")
    time.sleep(3)
    print("Done")

    browser.close()