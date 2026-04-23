#!/usr/bin/env python3
"""
Test Scraper - ดึงทุกโพสไม่ว่าจะเป็น lead ไหม
==============================================
ใช้ทดสอบว่า Facebook ยังให้ดึงโพสได้ไหม
"""

import sys
sys.path.insert(0, '.')

import json, time, os
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

THAI_OFFSET = timedelta(hours=7)

def thai_time_str():
    return (datetime.now() + THAI_OFFSET).strftime("%H:%M:%S")

def load_cookies():
    """Load cookies from fb_session.json"""
    try:
        with open('fb_session.json', 'r') as f:
            session = json.load(f)
            return session.get('cookies', [])
    except:
        print("❌ No cookies found")
        return []

def scrape_all_posts(group_id):
    """ดึงโพสทั้งหมดไม่ว่าจะเป็น lead ไหม"""
    cookies = load_cookies()
    if not cookies:
        print(f"   ❌ No cookies")
        return []
    
    with sync_playwright() as p:
        # Launch with context
        browser = p.chromium.launch(headless=True)
        
        # Create new context with cookies
        context = browser.new_context()
        for cookie in cookies:
            try:
                context.add_cookies([cookie])
            except Exception as e:
                print(f"   ⚠️ Cookie error: {e}")
        
        page = context.new_page()
        
        try:
            # Go to group
            print(f"   🔗 Opening group {group_id}...")
            page.goto(f"https://www.facebook.com/groups/{group_id}", timeout=30)
            time.sleep(3)
            
            posts = []
            
            # Scroll 3 times
            for scroll_num in range(3):
                print(f"   📜 Scroll {scroll_num+1}/3...")
                page.mouse.wheel(0, 2000)
                time.sleep(2)
                
                # Find posts
                selectors = [
                    'div[aria-posinset]',
                    'div[role="article"]',
                ]
                
                for selector in selectors:
                    try:
                        post_elements = page.query_selector_all(selector)
                        if post_elements and len(post_elements) > 0:
                            print(f"   📰 Found {len(post_elements)} elements ({selector})")
                            
                            for elem in post_elements[:15]:
                                try:
                                    text = ""
                                    for text_sel in ['span[dir]', 'div[dir="auto"]', 'div[dir]']:
                                        try:
                                            t = elem.query_selector(text_sel)
                                            if t:
                                                text = t.inner_text()[:150]
                                                break
                                        except:
                                            pass
                                    
                                    if len(text) > 30:
                                        posts.append({
                                            'message': text,
                                            'group': group_id,
                                            'scroll': scroll_num + 1
                                        })
                                except:
                                    continue
                            break
                    except:
                        continue
            
            print(f"   ✅ Total: {len(posts)} posts")
            return posts
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return []
        finally:
            page.close()
            context.close()
            browser.close()

def main():
    print("="*60)
    print("🚀 TEST SCRAPER - ดึงทุกโพส")
    print("="*60)
    
    # Test with thaisolarcell group
    test_group = "thaisolarcell"
    
    print(f"\n📂 Testing group: {test_group}")
    posts = scrape_all_posts(test_group)
    
    print(f"\n" + "="*60)
    print(f"📊 ผลลัพธ์: {len(posts)} posts")
    print("="*60)
    
    if posts:
        print(f"\n📝 ตัวอย่างโพส:")
        for i, post in enumerate(posts[:5], 1):
            print(f"\n{i}. {post['message'][:100]}...")
            print(f"   Group: {post['group']}, Scroll: {post['scroll']}")
    else:
        print(f"\n❌ ไม่เจอโพสเลย!")
    
    # Clean up cookies
    print(f"\n🗑️ Deleting cookies...")
    if os.path.exists('fb_session.json'):
        os.remove('fb_session.json')
        print(f"   Deleted!")

if __name__ == "__main__":
    main()
