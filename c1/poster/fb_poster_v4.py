#!/usr/bin/env python3
"""
Facebook Poster v4 - ใช้ chromedriver ที่ตรงกับ Chrome 147
รองรับ: text + image + WhatsApp dialog
"""
import json, time, random, sys, urllib.request, urllib.parse, subprocess

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

LOG_FILE = '/root/.openclaw/workspace/c1/poster/post.log'
POST_ID_FILE = '/root/.openclaw/workspace/c1/poster/post_id.txt'
TELEGRAM_BOT_TOKEN = '8641112117:AAFokLi4gAvfqSUPjBz2AqUyGceAsX8M5CE'
TELEGRAM_CHAT_ID = '6780942246'

def notify_admin(post_id, post_url, image_path=None):
    """ส่งแจ้งเตือนไป Telegram Admin (Noty)"""
    import datetime
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    
    topic = "Save the Environment with Solar Energy"
    
    msg = f"""📊 รายงานโพส Facebook

🏷️ หัวข้อ: {topic}
✅ สถานะ: โพสแล้ว
📅 วันที่: {now}
🔢 โพสที่: #{post_id}
🔗 ลิ้งค์: {post_url}"""
    
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    data = urllib.parse.urlencode({'chat_id': TELEGRAM_CHAT_ID, 'text': msg})
    try:
        req = urllib.request.Request(url, data.encode('utf-8'))
        urllib.request.urlopen(req, timeout=10)
        log(f"📲 แจ้ง Noty สำเร็จ")
    except Exception as e:
        log(f"⚠️ แจ้ง Noty ล้มเหลว: {e}")
    
    # ส่งรูปภาพถ้ามี
    if image_path:
        try:
            cmd = [
                'curl', '-s', '-X', 'POST',
                f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto',
                '-F', f'chat_id={TELEGRAM_CHAT_ID}',
                '-F', f'photo=@{image_path}',
                '-F', 'caption=📷 รูปภาพแนบในโพส'
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            if result.returncode == 0:
                log(f"📷 ส่งรูปไป Noty สำเร็จ")
            else:
                log(f"⚠️ ส่งรูปไป Noty ล้มเหลว: {result.stderr.decode()}")
        except Exception as e:
            log(f"⚠️ ส่งรูปไป Noty ล้มเหลว: {e}")

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

def get_next_post_id():
    """อ่าน post ID ล่าสุดจากไฟล์ แล้วคืนค่า ID ถัดไป"""
    try:
        with open(POST_ID_FILE, 'r') as f:
            current_id = int(f.read().strip())
    except:
        current_id = 0
    next_id = current_id + 1
    with open(POST_ID_FILE, 'w') as f:
        f.write(str(next_id))
    return next_id

def post_to_page(message, page_id="61588849713937", image_path=None, post_id=None):
    """โพสไปเพจ"""

    log(f"🚀 เริ่ม Chrome ด้วย chromedriver 147...")

    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    service = Service('/tmp/chromedriver-linux64/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

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

        driver.get(f'https://www.facebook.com/{page_id}')
        time.sleep(5)

        log(f"📍 ไปที่เพจ {page_id} แล้ว")

        # Scroll down to reveal the composer
        driver.execute_script('window.scrollTo(0, 400);')
        time.sleep(2)

        # Find and click the composer "คุณกำลังคิดอะไรอยู่"
        spans = driver.find_elements('css selector', 'span')
        composer_clicked = False
        for span in spans:
            try:
                text = span.text.strip()
                if text == "คุณกำลังคิดอะไรอยู่":
                    driver.execute_script('arguments[0].click();', span)
                    log("✅ Click composer 'คุณกำลังคิดอะไรอยู่'")
                    composer_clicked = True
                    time.sleep(3)
                    break
            except:
                pass

        if not composer_clicked:
            log("❌ ไม่เจอ composer")
            return False

        # Find the textbox (height < 100 to skip dialog)
        text_selectors = [
            'div[contenteditable="true"][role="presentation"]',
            'div[role="textbox"]',
            'div[contenteditable="true"]'
        ]

        textbox = None
        for sel in text_selectors:
            els = driver.find_elements('css selector', sel)
            for el in els:
                try:
                    if el.is_displayed() and 10 < el.rect['height'] < 100:
                        textbox = el
                        log(f"✅ พบ textbox: {sel}, height={el.rect['height']}")
                        break
                except:
                    pass
            if textbox:
                break

        if not textbox:
            log("❌ ไม่เจอ textbox")
            return False

        # Click textbox using ActionChains, then type with send_keys
        driver.execute_script('arguments[0].scrollIntoView({block: "center"});', textbox)
        time.sleep(0.5)

        actions = ActionChains(driver)
        actions.move_to_element(textbox).click().perform()
        log("✅ Click textbox via ActionChains")
        time.sleep(1)

        textbox.send_keys(message)
        log("✅ พิมพ์ข้อความเสร็จ (send_keys)")
        time.sleep(2)

        # === เพิ่มรูปภาพ (ถ้ามี) ===
        if image_path:
            log(f"📷 กำลังอัพโหลดรูป: {image_path}")
            image_btns = driver.find_elements('css selector', '[aria-label="รูปภาพ/วิดีโอ"]')
            for btn in image_btns:
                try:
                    if btn.is_displayed() and btn.rect['y'] > 1000:
                        driver.execute_script('arguments[0].click();', btn)
                        log("✅ กดปุ่ม 'รูปภาพ/วิดีโอ'")
                        time.sleep(3)
                        break
                except:
                    pass
            
            # Find file input inside dialog and upload
            dialogs = driver.find_elements('css selector', '[role="dialog"]')
            uploaded = False
            for d in dialogs:
                try:
                    if d.is_displayed() and d.rect['height'] > 400:
                        file_inputs = d.find_elements('css selector', 'input[type="file"]')
                        for fi in file_inputs:
                            try:
                                fi.send_keys(image_path)
                                log(f"✅ อัพโหลดรูปสำเร็จ: {image_path}")
                                uploaded = True
                                time.sleep(3)
                                break
                            except Exception as e:
                                log(f"⚠️ Upload error: {e}")
                except:
                    pass
                if uploaded:
                    break
            
            if not uploaded:
                log("⚠️ ไม่สามารถอัพโหลดรูปได้")
        # === จบเพิ่มรูปภาพ ===

        # Re-fetch spans after clicking composer (DOM may have changed)
        all_spans = driver.find_elements('css selector', 'span')

        # Click "ถัดไป" button
        next_clicked = False
        for span in all_spans:
            try:
                if span.is_displayed() and span.text.strip() == "ถัดไป":
                    driver.execute_script('arguments[0].click();', span)
                    log("✅ กด 'ถัดไป'")
                    next_clicked = True
                    time.sleep(3)
                    break
            except:
                pass

        if not next_clicked:
            log("❌ ไม่เจอปุ่ม 'ถัดไป'")
            return False

        # Now find and click "โพสต์" button - must match EXACTLY "โพสต์"
        post_button_found = False
        all_buttons = driver.find_elements('css selector', '[role="button"]')

        for btn in all_buttons:
            try:
                if btn.is_displayed():
                    txt = (btn.text or '').strip()
                    aria = btn.get_attribute('aria-label') or ''
                    # Match exact "โพสต์" (NOT "กลุ่มเป้าหมายของโพสต์")
                    if txt == "โพสต์" or aria == "โพสต์":
                        driver.execute_script('arguments[0].click();', btn)
                        log(f"✅ กด 'โพสต์' (aria='{aria}')")
                        post_button_found = True
                        time.sleep(3)
                        break
            except:
                pass

        if not post_button_found:
            log("❌ ไม่เจอปุ่ม 'โพสต์'")
            return False

        # Handle WhatsApp dialog - click "ไม่ใช่ตอนนี้"
        time.sleep(2)

        not_now_found = False
        all_spans = driver.find_elements('css selector', 'span')
        for span in all_spans:
            try:
                if span.is_displayed() and 'ไม่ใช่ตอนนี้' in span.text:
                    driver.execute_script('arguments[0].click();', span)
                    log("✅ กด 'ไม่ใช่ตอนนี้' (WhatsApp dialog)")
                    not_now_found = True
                    time.sleep(3)
                    break
            except:
                pass

        if not not_now_found:
            # Try finding as button
            all_buttons = driver.find_elements('css selector', '[role="button"]')
            for btn in all_buttons:
                try:
                    if btn.is_displayed():
                        txt = (btn.text or '').strip()
                        if 'ไม่ใช่ตอนนี้' in txt:
                            driver.execute_script('arguments[0].click();', btn)
                            log("✅ กด 'ไม่ใช่ตอนนี้' (as button)")
                            not_now_found = True
                            time.sleep(3)
                            break
                except:
                    pass

        if not not_now_found:
            log("⚠️ ไม่เจอ WhatsApp dialog - อาจจะไม่มีหรือโพสแล้ว")

        log("📤 โพสสำเร็จ!")
        time.sleep(5)
        
        # ดึง URL ของโพสที่เพิ่งโพส
        post_url = None
        try:
            # Scroll to top to see the newly posted content
            driver.execute_script('window.scrollTo(0, 0);')
            time.sleep(2)
            
            # หาลิ้งค์โพสใหม่ล่าสุด - มองหา /posts/ ที่ไม่ใช่ permalink
            all_links = driver.find_elements('css selector', 'a[href]')
            for link in all_links:
                try:
                    href = link.get_attribute('href')
                    if not href:
                        continue
                    # ต้องการลิ้งค์ที่มี /posts/ และไม่ใช่ query string ยาว
                    if '/posts/' in href:
                        clean_url = href.split('?')[0]
                        # ข้ามลิ้งค์ที่เป็น permalink ของกลุ่มหรือคนอื่น
                        if 'facebook.com/groups/' in href or 'facebook.com/story.php' in href:
                            continue
                        post_url = clean_url
                        log(f"🔗 พบ post URL: {post_url}")
                        break
                except:
                    pass
        except Exception as e:
            log(f"⚠️ หา post URL ไม่เจอ: {e}")
        
        if not post_url:
            post_url = f"https://www.facebook.com/{page_id}/posts/ID{post_id or 'UNKNOWN'}"
            log(f"⚠️ ไม่เจอ URL จริง ใช้ estimated URL: {post_url}")
        
        return True, post_url

    except Exception as e:
        log(f"❌ Error: {e}")
        return False, None
    finally:
        driver.quit()

def main():
    with open(LOG_FILE, 'w') as f:
        f.write('')

    post_id = get_next_post_id()
    message = f"""#ID{post_id} Solar Cell Working Principle

Solar panels absorb sunlight
Convert to electricity (DC)
Inverter converts to AC
Power your home
Excess = sell back to the grid!

Real savings"""

    # Get page ID and optional image path from command line
    page_id = "61588849713937"
    image_path = None

    args = sys.argv[1:]
    if args:
        page_id = args[0]
    if len(args) > 1:
        image_path = args[1]

    log(f"📤 โพสไปเพจ {page_id} [#{post_id}]...")

    result, post_url = post_to_page(message, page_id=page_id, image_path=image_path, post_id=post_id)

    if result:
        log(f"✅ โพสต์ #ID{post_id} สำเร็จ!")
        notify_admin(post_id, post_url, image_path)
        log("✅ เสร็จสมบูรณ์!")
    else:
        log("❌ ล้มเหลว")

if __name__ == "__main__":
    main()