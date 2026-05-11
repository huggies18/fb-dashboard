#!/usr/bin/env python3
"""Debug - after clicking ถัดไป v2"""
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

    # Step 1: Click composer
    page.get_by_text("คุณกำลังคิดอะไรอยู่", exact=True).first.click()
    time.sleep(2)
    print("Clicked composer")

    # Step 2: Type directly on page
    page.locator('[contenteditable="true"]').first.fill(message)
    time.sleep(1)
    print("Typed message")

    # Step 3: Find and click image button
    img_btn = page.locator('[aria-label="เพิ่มรูปภาพ"]').first
    if img_btn.is_visible():
        img_btn.click()
        time.sleep(2)
        print("Clicked เพิ่มรูปภาพ")
        
        # Upload
        file_input = page.locator('input[type="file"]').first
        file_input.set_input_files(image_path)
        time.sleep(3)
        print("Uploaded image")

    # Step 4: Click ถัดไป
    next_btn = page.get_by_text("ถัดไป", exact=True).first
    if next_btn.is_enabled():
        next_btn.click(force=True)
        time.sleep(3)
        print("Clicked ถัดไป")
    else:
        print("ถัดไป disabled")

    # Step 5: List ALL visible buttons
    print("\n--- ALL visible buttons after ถัดไป ---")
    buttons = page.locator('[role="button"]').all()
    for btn in buttons:
        try:
            if btn.is_visible():
                label = btn.get_attribute('aria-label') or ''
                text = btn.inner_text()[:80].replace('\n', ' ') or ''
                if label or text:
                    print(f"  role=button: label='{label}', text='{text}'")
        except:
            pass

    # Find any button with "โพสต์" text
    print("\n--- Looking for โพสต์ ---")
    post_btns = page.get_by_text("โพสต์").all()
    for btn in post_btns:
        try:
            if btn.is_visible():
                print(f"  Found: label={btn.get_attribute('aria-label')}, text={btn.inner_text()[:50]}")
        except:
            pass

    # Screenshot
    page.screenshot(path='/root/.openclaw/workspace/highsolar/poster/debug_final.png')
    print("\nScreenshot saved!")

    browser.close()