#!/usr/bin/env python3
"""
Facebook Poster v3 - ใช้ undetected-chromedriver + webdriver-manager
"""
import json, time, random

try:
    import undetected_chromedriver as uc
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
except ImportError:
    print("ติดตั้งก่อน: pip install undetected-chromedriver webdriver-manager")
    exit(1)

LOG_FILE = '/root/.openclaw/workspace/c1/poster/post.log'

def log(msg):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def load_cookies():
    with open('fb_poster_session.json', 'r') as f:
        session = json.load(f)
        return session.get('cookies', [])

def post_to_page(message, image_path=None):
    """โพสไปเพจด้วย undetected-chromedriver"""
    
    log("🚀 เริ่ม undetected-chromedriver...")
    
    # Setup undetected chrome
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    # Use webdriver-manager to get correct chromedriver
    try:
        service = Service(ChromeDriverManager().install())
        driver = uc.Chrome(options=options, version_main=None, service=service)
    except Exception as e:
        log(f"⚠️ webdriver-manager failed: {e}")
        log("ลองใช้แบบปกติ...")
        driver = uc.Chrome(options=options, version_main=None)
    
    try:
        cookies = load_cookies()
        log(f"📂 โหลด {len(cookies)} cookies...")
        
        driver.get('https://www.facebook.com')
        time.sleep(3)
        
        for cookie in cookies:
            try:
                driver.add_cookie({
                    'name': cookie['name'],
                    'value': cookie['value'],
                    'domain': '.facebook.com',
                    'path': '/'
                })
            except Exception as e:
                log(f"⚠️ Cookie error: {e}")
        
        driver.refresh()
        time.sleep(4)
        
        log("✅ Login สำเร็จ")
        
        driver.get('https://www.facebook.com/61588849713937')
        time.sleep(5)
        
        log("📍 ไปที่เพจแล้ว")
        
        # Find post box
        selectors_to_try = [
            'span.x1lliihq.x6ikm8r.x10wlt62.x1n2onr6',
            'span:has-text("คุณกำลังคิดอะไรอยู่")',
            '[aria-label="คุณกำลังคิดอะไรอยู่"]',
        ]
        
        post_box_found = False
        for sel in selectors_to_try:
            try:
                elements = driver.find_elements('css selector', sel)
                for el in elements:
                    try:
                        text = el.text
                        if 'คุณกำลังคิด' in text or 'What' in text:
                            log(f"✅ พบ post box: {sel}")
                            el.click()
                            time.sleep(3)
                            post_box_found = True
                            break
                    except:
                        pass
                if post_box_found:
                    break
            except Exception as e:
                log(f"⚠️ Selector {sel} failed: {e}")
                continue
        
        if not post_box_found:
            log("❌ ไม่พบ post box")
        
        # Find text input area
        time.sleep(3)
        
        text_selectors = [
            'div[contenteditable="true"][role="presentation"]',
            'div[aria-label*="โพส"]',
            'div[role="textbox"]',
            'textarea[name="message"]'
        ]
        
        textbox = None
        for sel in text_selectors:
            try:
                els = driver.find_elements('css selector', sel)
                for el in els:
                    if el.is_displayed():
                        textbox = el
                        log(f"✅ พบ textbox: {sel}")
                        break
            except:
                pass
            if textbox:
                break
        
        if textbox:
            textbox.click()
            time.sleep(1)
            textbox.clear()
            textbox.send_keys(message)
            log("✅ พิมพ์ข้อความเสร็จ")
            
            time.sleep(2)
            
            post_btn_selectors = [
                'div[role="button"][aria-label="โพส"]',
                'div[role="button"][aria-label="Post"]',
                '[data-testid="submit"]'
            ]
            
            for sel in post_btn_selectors:
                try:
                    btns = driver.find_elements('css selector', sel)
                    for btn in btns:
                        if btn.is_displayed():
                            btn.click()
                            log("✅ กดโพสแล้ว!")
                            time.sleep(3)
                            log("📤 โพสสำเร็จ!")
                            return True
                except:
                    pass
        
        log("❌ ไม่สามารถโพสได้")
        return False
        
    finally:
        driver.quit()

def main():
    with open(LOG_FILE, 'w') as f:
        f.write('')
    
    message = """🧐 How does Solar Cell work?

☀️ Solar panels absorb sunlight
⚡ Convert to electricity (DC)
🔄 Inverter converts to AC
🏠 Power your home
💡 Excess = sell back to the grid!

Real savings ✅"""
    
    log("📤 โพสไปเพจ 61588849713937...")
    
    result = post_to_page(message)
    
    if result:
        log("✅ เสร็จสมบูรณ์!")
    else:
        log("❌ ล้มเหลว")

if __name__ == "__main__":
    main()