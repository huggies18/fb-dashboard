#!/usr/bin/env python3
"""
Facebook Group Scraper for Windows
Automatically logs in and extracts posts from specified groups

Usage:
    pip install selenium
    python facebook-scraper.py
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import os
from datetime import datetime

# ============== SETTINGS ==============
TARGET_GROUPS = [
    "1248346110734837",  # Group ID or Name
]

KEYWORDS = [
    "โซล่า", "solar", "แผง", "ประหยัดไฟ", "ติดตั้ง",
    "ค่าไฟ", "เซลล์แสงอาทิตย์", "อินเวอร์เตอร์"
]

OUTPUT_FILE = f"facebook_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
# =====================================

def create_driver():
    """Create Chrome driver with settings"""
    chrome_options = Options()
    # Run in headless mode (no browser window) - comment out for debugging
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--lang=th-TH")
    chrome_options.add_argument("--start-maximized")
    # Fix Chrome/ChromeDriver compatibility on newer versions
    chrome_options.add_argument("--remote-allow-origins=*")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def login_facebook(driver, email, password):
    """Login to Facebook"""
    print("🔐 Logging in to Facebook...")
    driver.get("https://www.facebook.com")
    time.sleep(2)
    
    # Enter email
    email_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "email"))
    )
    email_input.send_keys(email)
    
    # Enter password
    password_input = driver.find_element(By.ID, "pass")
    password_input.send_keys(password)
    
    # Click login
    login_button = driver.find_element(By.NAME, "login")
    login_button.click()
    
    time.sleep(5)
    print("✅ Logged in!")

def get_group_posts(driver, group_id_or_name, keywords):
    """Extract posts from a group"""
    print(f"\n📂 Scanning group: {group_id_or_name}")
    
    # Navigate to group
    if group_id_or_name.isdigit():
        url = f"https://www.facebook.com/groups/{group_id_or_name}"
    else:
        url = f"https://www.facebook.com/groups/{group_id_or_name.replace(' ', '.')}"
    
    driver.get(url)
    time.sleep(3)
    
    posts_data = []
    
    # Scroll to load more posts
    for scroll in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
    
    # Find posts
    try:
        post_elements = driver.find_elements(By.CSS_SELECTOR, "[data-ad-preview='message']")
        
        for i, post in enumerate(post_elements):
            try:
                text = post.text
                
                # Check if post contains keywords
                matched_keywords = [kw for kw in keywords if kw.lower() in text.lower()]
                
                if matched_keywords:
                    # Find author
                    try:
                        author = post.find_element(By.XPATH, ".//..//..//strong").text
                    except:
                        author = "Unknown"
                    
                    posts_data.append({
                        "author": author,
                        "text": text[:500],  # Limit text length
                        "keywords_found": matched_keywords,
                        "timestamp": datetime.now().isoformat()
                    })
                    print(f"  ✅ Found: {text[:80]}...")
                    
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"  ❌ Error scanning: {e}")
    
    return posts_data

def save_results(posts):
    """Save results to JSON file"""
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Saved {len(posts)} posts to {OUTPUT_FILE}")

def main():
    print("=" * 50)
    print("🤖 Facebook Group Scraper")
    print("=" * 50)
    
    # Get credentials
    print("\n📧 Enter Facebook Email: ")
    email = input().strip()
    
    print("🔑 Enter Facebook Password: ")
    password = input().strip()
    
    # Get group to monitor
    print("\n📋 Enter Facebook Group ID or Name (e.g., 1248346110734837 or groupname): ")
    group_input = input().strip()
    
    if not group_input:
        group_input = "1248346110734837"
    
    try:
        driver = create_driver()
        login_facebook(driver, email, password)
        
        posts = get_group_posts(driver, group_input, KEYWORDS)
        save_results(posts)
        
        print("\n" + "=" * 50)
        print("✅ Scraping complete!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        
    finally:
        input("\nPress Enter to close browser...")
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    main()
