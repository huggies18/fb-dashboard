#!/usr/bin/env python3
"""
Parallel Filter - ใช้ MiniMax AI วิเคราะห์หลายโพสพร้อมกัน
=======================================================
- Load all_posts.json
- วิเคราะห์ด้วย MiniMax API แบบ parallel (max 5 threads)
- ลดเวลาจาก ~5 นาที → ~1 นาที
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/highsolar/scraper')

import json, os, time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request

# Config
ALL_POSTS_FILE = '/root/.openclaw/workspace/highsolar/scraper/all_posts.json'
RESULT_FILE = '/root/.openclaw/workspace/highsolar/scraper/filter_result.json'
MINIMAX_API_KEY = "sk-cp-A_RP19hNeTy4d_Z8AcSJIy61Ex3T8nAXExChoYAQ9VygDDqaBx5jgmsVeihAoIhIC2JsQIDgQYCNpb4GNqyn6BFAGX2sA455sHIVKBBw1ygU2ZLFx_kxI-A"
MINIMAX_ENDPOINT = "https://api.minimax.io/anthropic/v1/messages"
MODEL = "MiniMax-M2.7"
MAX_WORKERS = 5  # Max parallel threads
THAI_OFFSET = timedelta(hours=7)

BUYER_PROMPT = """You are a solar cell lead analyzer. Reply ONLY JSON. {"is_lead": true/false, "score": 0-10, "reason": "thai reason"}

Rules:
- is_lead=true if person wants to BUY/INSTALL solar
- is_lead=false if person is SELLER or unrelated
- Score 0-10 (higher = more ready to buy)
- "ติดตาม" means "follow" not "install" → NOT BUYER

Post: """

def thai_time_str():
    return (datetime.now() + THAI_OFFSET).strftime("%H:%M:%S")

def analyze_post(post):
    """วิเคราะห์โพสเดียวด้วย MiniMax API"""
    msg = post.get('message', '')
    url = post.get('url', '')
    group = post.get('group', '')
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': MINIMAX_API_KEY,
            'anthropic-version': '2023-06-01',
        }
        
        payload = {
            'model': MODEL,
            'max_tokens': 1000,
            'temperature': 0.0,
            'messages': [
                {
                    'role': 'user',
                    'content': BUYER_PROMPT + msg
                }
            ]
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            MINIMAX_ENDPOINT,
            data=data,
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            # Extract text from content blocks
            text_response = ""
            for block in result.get('content', []):
                if block.get('type') == 'text':
                    text_response = block.get('text', '')
                    break
            
            # Parse JSON from response
            if text_response and '{' in text_response and '}' in text_response:
                start = text_response.index('{')
                end = text_response.rindex('}') + 1
                json_str = text_response[start:end]
                parsed = json.loads(json_str)
                
                return {
                    'url': url,
                    'message': msg[:200],
                    'group': group,
                    'time': post.get('time', ''),
                    'scraped_at': post.get('scraped_at', ''),
                    'score': parsed.get('score', 0),
                    'is_lead': parsed.get('is_lead', False),
                    'reason': parsed.get('reason', '')[:80]
                }
            else:
                return {
                    'url': url,
                    'message': msg[:200],
                    'group': group,
                    'time': post.get('time', ''),
                    'scraped_at': post.get('scraped_at', ''),
                    'score': 0,
                    'is_lead': False,
                    'reason': 'Parse error'
                }
                
    except Exception as e:
        return {
            'url': url,
            'message': msg[:200],
            'group': group,
            'time': post.get('time', ''),
            'scraped_at': post.get('scraped_at', ''),
            'score': 0,
            'is_lead': False,
            'reason': f'Error: {str(e)[:30]}'
        }

def main():
    print(f"[{thai_time_str()}] 🚀 Parallel Filter - เริ่มวิเคราะห์...")
    
    # Load posts
    if not os.path.exists(ALL_POSTS_FILE):
        print(f"❌ ไม่พบ {ALL_POSTS_FILE}")
        return None, None
    
    with open(ALL_POSTS_FILE, 'r', encoding='utf-8') as f:
        posts = json.load(f)
    
    print(f"📥 โหลด {len(posts)} โพสแล้ว")
    print(f"🔢 ใช้ {MAX_WORKERS} threads พร้อมกัน")
    
    leads = []
    not_leads = []
    
    # Process with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_post = {executor.submit(analyze_post, post): post for post in posts}
        
        for i, future in enumerate(as_completed(future_to_post), 1):
            result = future.result()
            
            if result.get('is_lead'):
                leads.append(result)
                emoji = "🟢"
            else:
                not_leads.append(result)
                emoji = "🔴"
            
            print(f"{emoji} [{i}/{len(posts)}] score={result.get('score')} | {result.get('message','')[:40]}...")
            
            # Small delay to avoid rate limit
            if i % MAX_WORKERS == 0:
                time.sleep(1)
    
    print(f"\n{'='*60}")
    print(f"✅ วิเคราะห์เสร็จ: {len(leads)} leads / {len(not_leads)} rejected")
    print(f"{'='*60}")
    
    # Save results
    result_data = {
        'leads': leads,
        'not_leads': not_leads,
        'total': len(posts),
        'timestamp': thai_time_str()
    }
    
    with open(RESULT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 บันทึกไป {RESULT_FILE}")
    
    return leads, not_leads

if __name__ == "__main__":
    start = time.time()
    leads_count, not_leads_count = main()
    elapsed = time.time() - start
    print(f"\n⏱️ ใช้เวลา: {elapsed:.1f} วินาที")