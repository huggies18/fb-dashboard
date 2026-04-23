#!/usr/bin/env python3
"""
AI Buyer Filter - DeepSeek Coder 6.7b via Ollama
=============================================
ใช้ Local LLM (DeepSeek Coder 6.7b) วิเคราะห์โพสจาก Facebook
"""

import sys
import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timedelta

THAI_OFFSET = timedelta(hours=7)

# ==================== OLLAMA CONFIG ====================
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "deepseek-coder:6.7b"
TIMEOUT = 90  # seconds per request

# ==================== PROMPT ====================
BUYER_PROMPT = '''คุณเป็น AI ที่วิเคราะห์โพสจาก Facebook เกี่ยวกับโซล่าเซลล์

ตอบเฉพาะ JSON ตามกฎด้านล่างเท่านั้น

กฎ:
- is_lead = true ก็ต่อเมื่อ เจ้าของโพสต้องการซื้อ/ติดตั้งเอง
- is_lead = false ถ้า: เป็นผู้ขาย, ให้ความรู้, รีวิว, สอน, ถามเกี่ยวกับสินค้าที่จะขาย

score:
- 10 = กำลังจะซื้อ/ติดทันที
- 8-9 = พร้อมสนใจมาก
- 5-7 = สนใจธรรมดา
- 1-4 = ถาม/สอบถาม
- 0 = ไม่ใช่ lead

โพส: {}

JSON ที่ถูกต้อง: '''

def analyze_with_deepseek(post_text, post_url, group_id):
    """วิเคราะห์โพสด้วย DeepSeek Coder 6.7b"""
    
    try:
        prompt = BUYER_PROMPT.format(post_text[:500])
        
        data = json.dumps({
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 150
            }
        }).encode('utf-8')
        
        req = urllib.request.Request(
            OLLAMA_URL,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            result_data = json.loads(response.read().decode('utf-8'))
            ai_text = result_data.get('response', '').strip()
        
        # Clean response - remove markdown and extra text
        ai_text = ai_text.replace('```json', '').replace('```', '').replace('\n', '').strip()
        
        # Try to extract JSON from response
        # Find { and }
        start = ai_text.find('{')
        end = ai_text.rfind('}') + 1
        
        if start != -1 and end != 0:
            json_str = ai_text[start:end]
            analysis = json.loads(json_str)
            return {
                'is_lead': analysis.get('is_lead', False),
                'score': analysis.get('score', 0),
                'reason': analysis.get('reason', 'ไม่ทราบ'),
                'ai_used': 'deepseek-coder:6.7b',
                'ai_raw': ai_text
            }
        else:
            # Fallback - try direct parse
            try:
                analysis = json.loads(ai_text)
                return {
                    'is_lead': analysis.get('is_lead', False),
                    'score': analysis.get('score', 0),
                    'reason': analysis.get('reason', 'ไม่ทราบ'),
                    'ai_used': 'deepseek-coder:6.7b',
                    'ai_raw': ai_text
                }
            except:
                return {
                    'is_lead': False,
                    'score': 0,
                    'reason': f'Parse error: {ai_text[:50]}',
                    'ai_used': 'deepseek-coder:6.7b',
                    'ai_raw': ai_text
                }
            
    except urllib.error.URLError as e:
        return {
            'is_lead': False,
            'score': 0,
            'reason': f'URL Error: {str(e)}',
            'ai_used': 'deepseek-coder:6.7b',
            'ai_raw': ''
        }
    except Exception as e:
        return {
            'is_lead': False,
            'score': 0,
            'reason': f'Exception: {str(e)}',
            'ai_used': 'deepseek-coder:6.7b',
            'ai_raw': ''
        }

# ==================== TEST ====================
if __name__ == "__main__":
    test_cases = [
        "อยากติดโซล่าเซลล์ที่บ้าน ต้องใช้งบประมาณเท่าไหร่คะ",
        "ขาย Solar Panel 500W ราคาพิเศษ ติดต่อได้เลย",
        "ใครติดโซล่าแล้วบ้าง บริการดีไหม ราคาเท่าไหร่",
        "Hybrid Solar 10kw มีแบต 7kw ขอเปลี่ยนมิเตอร์เป็น tou จะดีกว่าไหม"
    ]
    
    print("="*60)
    print("🧪 DEEPSEEK CODER 6.7B AI BUYER FILTER TEST")
    print("="*60)
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n[{i}] Testing: {text[:50]}...")
        result = analyze_with_deepseek(text, f'test_{i}', 'test')
        print(f"    Result: is_lead={result['is_lead']}, score={result['score']}")
        print(f"    Reason: {result['reason']}")
        print(f"    AI: {result['ai_used']}")
    
    print("\n" + "="*60)
    print("✅ Test complete!")