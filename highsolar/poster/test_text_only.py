#!/usr/bin/env python3
"""Poster - text only, no image"""
import sys, json, time
sys.path.insert(0, '.')

from playwright.sync_api import sync_playwright

PAGE_ID = '61588849713937'
message = "ทดสอบโพสเท็กซ์ครับ"

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
    ctx.add_cookies(session.get('cookies', []))
    page = ctx.new_page()

    page.goto(f"https://www.facebook.com/{PAGE_ID}", timeout=30000)
    time.sleep(5)

    # Click composer
    page.evaluate('''() => {
        const els = document.querySelectorAll('[role="button"]');
        for (const el of els) {
            if (el.textContent.includes("คุณกำลังคิดอะไรอยู่")) {
                el.click();
                break;
            }
        }
    }''')
    print("✅ Clicked composer")
    time.sleep(2)

    # Type message
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
    print(f"✅ Typed: {message}")
    time.sleep(2)

    # Click "ไม่ใช่ตอนนี้" (WhatsApp)
    page.evaluate('''() => {
        const els = document.querySelectorAll('[role="button"]');
        for (const el of els) {
            if (el.textContent.includes("ไม่ใช่ตอนนี้")) {
                el.click();
                break;
            }
        }
    }''')
    print("✅ Clicked: ไม่ใช่ตอนนี้")
    time.sleep(1)

    # Click "สร้างโพสต์"
    page.evaluate('''() => {
        const els = document.querySelectorAll('[role="button"]');
        for (const el of els) {
            if (el.textContent === "สร้างโพสต์") {
                el.click();
                break;
            }
        }
    }''')
    print("✅ Clicked: สร้างโพสต์")
    time.sleep(3)
    print("✅ Posted!")

    browser.close()
    print("Done")