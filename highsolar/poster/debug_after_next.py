#!/usr/bin/env python3
"""Debug - after clicking ถัดไป"""
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

    # Step 2: Type
    dialog = page.locator('[role="dialog"]').first
    dialog.locator('[contenteditable="true"]').first.fill(message)
    time.sleep(1)

    # Step 3: Add image
    dialog.get_by_text("เพิ่มรูปภาพ", exact=True).first.click()
    time.sleep(2)
    dialog.locator('input[type="file"]').first.set_input_files(image_path)
    time.sleep(3)

    # Step 4: Click ถัดไป
    page.get_by_text("ถัดไป", exact=True).first.click()
    time.sleep(3)
    print("After clicking ถัดไป...")

    # Find all buttons with "โพส" or "Post"
    print("\n--- All buttons after ถัดไป ---")
    buttons = page.locator('[role="button"]').all()
    for btn in buttons:
        try:
            if btn.is_visible():
                label = btn.get_attribute('aria-label') or ''
                text = btn.inner_text()[:50] or ''
                if 'โพส' in label or 'โพส' in text or 'Post' in label or 'Post' in text:
                    print(f"  Button: label={label}, text={text}")
        except:
            pass

    # Save screenshot
    page.screenshot(path='/root/.openclaw/workspace/highsolar/poster/debug_after_next.png')
    print("\nScreenshot saved!")

    browser.close()