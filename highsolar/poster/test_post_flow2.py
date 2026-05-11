#!/usr/bin/env python3
"""Test poster - find by text"""
import sys, json, time
sys.path.insert(0, '.')

from playwright.sync_api import sync_playwright

PAGE_ID = '61588849713937'
message = "ทดสอบโพสจาก Playwright"

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

    # Step 1: Click by text "คุณกำลังคิดอะไรอยู่"
    try:
        # Use text selector
        what = page.get_by_text("คุณกำลังคิดอะไรอยู่", exact=True).first
        if what.is_visible():
            what.click()
            print("✅ Clicked: คุณกำลังคิดอะไรอยู่")
            time.sleep(2)
        else:
            print("❌ ไม่เจอ: คุณกำลังคิดอะไรอยู่")
    except Exception as e:
        print(f"ERR click: {e}")

    # Step 2: Type in dialog
    try:
        # Wait for dialog to appear
        time.sleep(2)
        dialog = page.locator('[role="dialog"]')
        if dialog.is_visible():
            print("✅ Dialog opened")
            
            # Find editable in dialog
            editable = dialog.locator('[contenteditable="true"]').first
            if editable.is_visible():
                editable.click()
                time.sleep(0.5)
                editable.fill(message)
                print(f"✅ Typed: {message}")
                time.sleep(1)
        else:
            print("❌ Dialog not visible")
    except Exception as e:
        print(f"ERR type: {e}")

    # Step 3: Click "ถัดไป"
    try:
        time.sleep(1)
        next_btn = page.get_by_text("ถัดไป", exact=True).first
        if next_btn.is_visible():
            next_btn.click()
            print("✅ Clicked: ถัดไป")
            time.sleep(2)
        else:
            print("❌ ไม่เจอ: ถัดไป")
    except Exception as e:
        print(f"ERR next: {e}")

    # Step 4: Click "โพส"
    try:
        post_btn = page.get_by_text("โพส", exact=True).first
        if post_btn.is_visible():
            post_btn.click()
            print("✅ Clicked: โพส")
            time.sleep(3)
            print("✅ Posted!")
        else:
            print("❌ ไม่เจอ: โพส")
    except Exception as e:
        print(f"ERR post: {e}")

    browser.close()
    print("Done")