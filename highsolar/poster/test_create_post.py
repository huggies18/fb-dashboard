#!/usr/bin/env python3
"""Debug - try สร้างโพสต์"""
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

    # Step 2: Type in the visible editable area
    for editable in page.locator('[contenteditable="true"]').all():
        if editable.is_visible():
            try:
                editable.fill(message)
                print(f"Typed: {message}")
                break
            except:
                continue

    time.sleep(1)

    # Step 3: Find image upload - click on "รูปภาพ/วิดีโอ" or similar
    photo_btn = page.locator('[aria-label="รูปภาพ/วิดีโอ"]').first
    if photo_btn.is_visible():
        photo_btn.click()
        print("Clicked: รูปภาพ/วิดีโอ")
        time.sleep(2)
        
        # Upload
        file_input = page.locator('input[type="file"]').first
        if file_input.is_visible():
            file_input.set_input_files(image_path)
            print("Uploaded image")
            time.sleep(4)

    # Step 4: Click ถัดไป
    time.sleep(1)
    next_btn = page.get_by_text("ถัดไป", exact=True).first
    if next_btn.is_enabled():
        next_btn.click(force=True)
        print("Clicked: ถัดไป")
        time.sleep(3)
    else:
        print(f"ถัดไป disabled: {next_btn.inner_text()}")

    # Step 5: Click "สร้างโพสต์"
    time.sleep(1)
    create_btn = page.get_by_text("สร้างโพสต์", exact=True).first
    if create_btn.is_visible():
        create_btn.click(force=True)
        print("Clicked: สร้างโพสต์")
        time.sleep(3)
        print("✅ Posted!")
    else:
        print("ไม่เจอ: สร้างโพสต์")

    browser.close()
    print("Done")