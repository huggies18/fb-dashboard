#!/usr/bin/env python3
"""Test poster - full flow with Playwright"""
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

    # Try to find and click the main composer
    composer_selectors = [
        'div[contenteditable="true"]',
        '[role="button"][aria-label*="Create"]',
        'div[aria-label*="What"]',
        'span[aria-label*="Create"]'
    ]

    for sel in composer_selectors:
        try:
            el = page.locator(sel).first
            if el and el.is_visible():
                print(f"Clicking: {sel}")
                el.click(timeout=5000)
                time.sleep(2)
                print("Clicked!")
                break
        except Exception as e:
            print(f"ERR {sel}: {e}")

    # Type message
    time.sleep(1)
    try:
        editable = page.locator('div[contenteditable="true"]').first
        if editable.is_visible():
            editable.click()
            time.sleep(0.5)
            editable.fill(message)
            print(f"Typed: {message}")
            time.sleep(1)
    except Exception as e:
        print(f"Type err: {e}")

    # Find Post button
    post_selectors = [
        '[role="button"][aria-label*="Post"]',
        '[aria-label="Post"]',
        'div[aria-label*="Post"]',
        'span[aria-label="Post"]'
    ]

    post_btn = None
    for sel in post_selectors:
        try:
            el = page.locator(sel).first
            if el and el.is_visible():
                print(f"Found Post button: {sel}")
                post_btn = el
                break
        except:
            pass

    if post_btn:
        try:
            post_btn.click(timeout=5000)
            print("✅ Posted!")
            time.sleep(3)
        except Exception as e:
            print(f"Post err: {e}")
    else:
        print("❌ No Post button found")

    browser.close()
    print("Done")