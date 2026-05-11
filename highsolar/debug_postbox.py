#!/usr/bin/env python3
import json, time
from playwright.sync_api import sync_playwright

with open('fb_session.json', 'r') as f:
    session = json.load(f)
    cookies = session.get('cookies', [])

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
    )
    ctx = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    )
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    
    page.goto('https://www.facebook.com/61588849713937', timeout=30000)
    time.sleep(4)
    
    page.evaluate('window.scrollTo(0, 0)')
    time.sleep(2)
    
    texts_to_find = [
        'คุณกำลังคิดอะไรอยู่',
        'What',
        'Create',
        'โพส'
    ]
    
    for text in texts_to_find:
        result = page.evaluate('''(t) => {
            let found = null;
            document.querySelectorAll("*").forEach(e => {
                if (e.innerText && e.innerText.includes(t)) {
                    found = e.tagName + " [" + e.getAttribute("role") + "] " + e.innerText.substring(0,80).replace(/\\n/g," ");
                }
            });
            return found;
        }''', text)
        print(f'Search "{text}": {result}')
    
    page.screenshot(path='/root/.openclaw/workspace/content/debug_fb5.png')
    print('Screenshot 5 saved')
    
    browser.close()