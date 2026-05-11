#!/usr/bin/env python3
"""Debug poster - inspect Facebook UI"""
import sys, json, time
sys.path.insert(0, '.')

from playwright.sync_api import sync_playwright

LOG_FILE = '/root/.openclaw/workspace/highsolar/poster/debug_poster.log'
PAGE_ID = '61588849713937'

def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

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

    log(f"Going to page {PAGE_ID}")
    page.goto(f"https://www.facebook.com/{PAGE_ID}", timeout=30000)
    time.sleep(5)
    log("Page loaded")

    # Find composer area
    selectors = [
        '[role="composer"]',
        '[aria-label*="Create"]',
        '[aria-label*="Post"]',
        'div[aria-label*="What"]',
        'div[contenteditable="true"]',
        'div.x1n2wxh5',
        'div.x6s0dn4'
    ]

    for sel in selectors:
        try:
            els = page.locator(sel).all()
            if els:
                log(f"FOUND: {sel} = {len(els)} elements")
                for i, el in enumerate(els[:3]):
                    try:
                        visible = el.is_visible()
                        tag = el.evaluate('el => el.tagName')
                        text = el.inner_text()[:50] if visible else ''
                        log(f"  [{i}] tag={tag}, visible={visible}, text={text}")
                    except:
                        pass
        except Exception as e:
            log(f"ERR {sel}: {e}")

    log("Done")
    browser.close()