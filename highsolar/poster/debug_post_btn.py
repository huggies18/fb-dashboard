#!/usr/bin/env python3
"""Debug Post button"""
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

    page.goto(f"https://www.facebook.com/{PAGE_ID}", timeout=30000)
    time.sleep(5)

    # Click composer
    try:
        page.locator('div[contenteditable="true"]').first.click()
        time.sleep(2)
    except:
        pass

    # Type
    try:
        page.locator('div[contenteditable="true"]').first.fill(message)
        time.sleep(2)
    except:
        pass

    # Save screenshot
    page.screenshot(path='/root/.openclaw/workspace/highsolar/poster/debug_post_btn.png')
    print("Screenshot saved!")

    # Find Post button
    print("\n--- Looking for Post button ---")
    selectors = [
        '[role="button"][tabindex="0"]',
        '[aria-label*="Post"]',
        '[aria-label*="โพส"]',
        '[data-tab-value="publish"]',
        'div[aria-label*="Post"]',
        'span:has-text("Post")',
        'div:has-text("Post")'
    ]

    for sel in selectors:
        try:
            els = page.locator(sel).all()
            if els:
                for el in els:
                    if el.is_visible():
                        tag = el.evaluate('el => el.tagName')
                        label = el.get_attribute('aria-label') or ''
                        text = el.inner_text()[:50] or ''
                        print(f"FOUND: {sel} -> tag={tag}, label={label}, text={text}")
        except Exception as e:
            pass

    # Check if dialog opened
    print("\n--- Check for dialog/composer ---")
    try:
        dialogs = page.locator('[role="dialog"]').all()
        print(f"Dialogs: {len(dialogs)}")
        for d in dialogs[:2]:
            print(f"  dialog: {d.is_visible()}")
    except:
        pass

    browser.close()