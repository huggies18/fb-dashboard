#!/usr/bin/env python3
"""Test poster - full flow"""
import sys, json, time
sys.path.insert(0, '.')

from playwright.sync_api import sync_playwright

PAGE_ID = '61588849713937'
message = "ทดสอบโพสจาก Playwright - ครับทำงานได้ไหม?"

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
        what_on_mind = page.locator('[aria-label="คุณกำลังคิดอะไรอยู่"]')
        if what_on_mind.is_visible():
            what_on_mind.click()
            print("✅ Clicked: คุณกำลังคิดอะไรอยู่")
            time.sleep(2)
        else:
            print("❌ ไม่เจอ: คุณกำลังคิดอะไรอยู่")
    except Exception as e:
        print(f"ERR click: {e}")

    # Step 2: Type message in the editable area inside dialog
    try:
        # Find the editable area inside dialog
        editable = page.locator('div[role="dialog"] div[contenteditable="true"]').first
        if editable.is_visible():
            editable.click()
            time.sleep(0.5)
            editable.fill(message)
            print(f"✅ Typed: {message}")
            time.sleep(1)
        else:
            print("❌ ไม่เจอ editable ใน dialog")
    except Exception as e:
        print(f"ERR type: {e}")

    # Step 3: Click "ถัดไป" button
    try:
        next_btn = page.locator('[aria-label="ถัดไป"]')
        if next_btn.is_visible():
            next_btn.click()
            print("✅ Clicked: ถัดไป")
            time.sleep(2)
        else:
            print("❌ ไม่เจอ: ถัดไป")
    except Exception as e:
        print(f"ERR next: {e}")

    # Step 4: Click "โพส" button
    try:
        post_btn = page.locator('[aria-label="โพส"]')
        if post_btn.is_visible():
            post_btn.click()
            print("✅ Clicked: โพส")
            time.sleep(3)
            print("✅ Posted successfully!")
        else:
            print("❌ ไม่เจอ: โพส")
    except Exception as e:
        print(f"ERR post: {e}")

    browser.close()
    print("Done")