#!/usr/bin/env python3
"""
Analyze Facebook posts with Local LLM (llama3.1:8b)
Uses the 4-tier lead scoring system from Tibodin
"""

import sys
sys.path.insert(0, '.')

import json, subprocess, re, time
from datetime import datetime, timedelta

THAI_OFFSET = timedelta(hours=7)
LEADS_DIR = "/root/.openclaw/workspace/facebook-scraper/leads"

PROMPT_TEMPLATE = """ให้คะแนน lead โซล่าเซลล์ สำหรับช่างติดตั้ง:

ข้อความ: "{message}"

กติกา:
- 9-10 = สนใจ/ซื้อ (Hot): พร้อมติดตั้งทันที มีเจตนาชัดเจน
- 7-8 = สนใจโซล่าเซลล์ (Warm): สนใจแล้ว แต่ยังไม่แน่ใจ
- 5-6 = กำลังพิจารณา (Eval): กำลังเปรียบเทียบราคา
- 0-4 = สอบถาม (Cold): ถามข้อมูลเบื้องต้น

โฆษณาขาย = 0 คะแนน (ไม่นับ)

ตอบ JSON อย่างเดียว: {{"score": X, "reason": "เหตุผล"}}"""

def call_llama(prompt, timeout=60):
    """Call local LLM via Ollama API"""
    payload = {
        "model": "llama3.1:8b",
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 150}
    }
    
    try:
        result = subprocess.run(
            ['curl', '-s', 'http://localhost:11434/api/generate',
             '-d', json.dumps(payload)],
            capture_output=True, text=True, timeout=timeout
        )
        response = json.loads(result.stdout)
        return response.get('response', '').strip()
    except Exception as e:
        return f"Error: {e}"

def parse_response(response):
    """Parse LLM JSON response"""
    try:
        match = re.search(r'\{"score":\s*(\d+),\s*"reason":\s*"([^"]+)"\}', response)
        if match:
            score = int(match.group(1))
            reason = match.group(2)
            return score, reason
    except:
        pass
    return 0, 'Parse error'

def get_category(score):
    """Get category name from score"""
    if score >= 9:
        return "🔥 สนใจ/ซื้อ"
    elif score >= 7:
        return "🟢 สนใจโซล่าเซลล์"
    elif score >= 5:
        return "🟡 กำลังพิจารณา"
    else:
        return "🔵 สอบถาม"

def analyze_posts():
    """Analyze all posts with LLM"""
    with open('all_posts.json', 'r', encoding='utf-8') as f:
        posts = json.load(f)
    
    print(f"📋 วิเคราะห์ {len(posts)} โพสด้วย llama3.1:8b...")
    print("="*50)
    
    seen = set()
    leads = []
    cats = {"🔥 สนใจ/ซื้อ": 0, "🟢 สนใจโซล่าเซลล์": 0, "🟡 กำลังพิจารณา": 0, "🔵 สอบถาม": 0, "❌ โฆษณาขาย": 0}
    
    for i, post in enumerate(posts, 1):
        url = post.get('url', '')
        if url in seen:
            continue
        seen.add(url)
        
        msg = post.get('message', '')[:400]
        prompt = PROMPT_TEMPLATE.format(message=msg)
        
        print(f"[{i}/{len(posts)}] วิเคราะห์... ", end='', flush=True)
        
        response = call_llama(prompt)
        score, reason = parse_response(response)
        
        # Classify sellers
        if score == 0 and 'โฆษณา' not in reason:
            # Check for seller phrases
            seller_phrases = ['ขาย', 'ปล่อย', 'โฆษณา', 'พร้อมส่ง', 'ราคา']
            if any(p in msg.lower() for p in seller_phrases):
                cats["❌ โฆษณาขาย"] += 1
                print(f"❌ โฆษณา")
                time.sleep(2)
                continue
        
        cat = get_category(score)
        if score > 4:
            leads.append({
                'url': url,
                'message': msg[:150],
                'group': post.get('group', ''),
                'time': post.get('time', ''),
                'score': score,
                'reason': reason,
                'category': cat
            })
            cats[cat] += 1
            print(f"{cat} (score:{score})")
        else:
            cats["🔵 สอบถาม"] += 1
            print(f"🔵 Cold (score:{score})")
        
        time.sleep(2)  # Rate limiting
    
    print(f"\n{'='*50}")
    print(f"📊 ผลลัพธ์:")
    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"   {cat}: {count}")
    print(f"   รวม leads: {len(leads)}")
    
    print(f"\n📋 Leads:")
    for i, lead in enumerate(leads[:10], 1):
        print(f"\n{i}. {lead['category']} (score:{lead['score']})")
        print(f"   Reason: {lead['reason']}")
        print(f"   {lead['message'][:80]}...")
        print(f"   {lead['url']}")
    
    if len(leads) > 10:
        print(f"\n...และอีก {len(leads) - 10} ราย")

if __name__ == "__main__":
    analyze_posts()
