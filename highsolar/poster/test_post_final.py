#!/usr/bin/env python3
"""Test poster - full flow with image, find โพสต์"""
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

    print(f"Going to page {PAGE_ID}")
    page.goto(f"https://www.facebook.com/{PAGE_ID}", timeout=30000)
    time.sleep(5)
    print("Page loaded")

    # Step 1: Click "คุณกำลังคิดอะไรอยู่"
    try:
        what = page.get_by_text("คุณกำลังคิดอะไรอยู่", exact=True).first
        what.click()
        print("✅ Clicked: คุณกำลังคิดอะไรอยู่")
        time.sleep(2)
    except Exception as e:
        print(f"ERR click: {e}")

    # Step 2: Type message
    try:
        dialog = page.locator('[role="dialog"]').first
        editable = dialog.locator('[contenteditable="true"]').first
        editable.click()
        time.sleep(0.5)
        editable.fill(message)
        print(f"✅ Typed: {message}")
        time.sleep(1)
    except Exception as e:
        print(f"ERR type: {e}")

    # Step 3: Add image
    try:
        add_photo_btn = dialog.get_by_text("เพิ่มรูปภาพ", exact=True).first
        if add_photo_btn.is_visible():
            add_photo_btn.click()
            print("✅ Clicked: เพิ่มรูปภาพ")
            time.sleep(2)
            
            file_input = dialog.locator('input[type="file"]').first
            if file_input.is_visible():
                file_input.set_input_files(image_path)
                print(f"✅ Uploaded: {image_path}")
                time.sleep(3)
    except Exception as e:
        print(f"ERR image: {e}")

    # Step 4: Click "ถัดไป"
    try:
        time.sleep(2)
        next_btn = page.get_by_text("ถัดไป", exact=True).first
        if next_btn.is_enabled():
            next_btn.click()
            print("✅ Clicked: ถัดไป")
            time.sleep(2)
        else:
            print(f"❌ ถัดไป disabled")
    except Exception as e:
        print(f"ERR next: {e}")

    # Step 5: Click "โพสต์" (not โพส)
    try:
        time.sleep(1)
        # Try exact match
        post_btn = page.get_by_text("โพสต์", exact=True).first
        if post_btn.is_visible():
            post_btn.click(force=True)
            print("✅ Clicked: โพสต์")
            time.sleep(3)
            print("✅ Posted!")
        else:
            print("❌ ไม่เจอ: โพสต์")
            # Try partial match
            post_btn2 = page.get_by_text("โพสต์").first
            if post_btn2.is_visible():
                post_btn2.click()
                print("✅ Clicked: โพสต์ (partial)")
                time.sleep(3)
                print("✅ Posted!")
    except Exception as e:
        print(f"ERR post: {e}")

    browser.close()
    print("Done")