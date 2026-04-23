#!/usr/bin/env python3
"""
AI Buyer Filter - Qwen 2.5:7b via Ollama
========================================
ใช้ Local LLM (Qwen 2.5:7b) วิเคราะห์โพสจาก Facebook
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
MODEL = "qwen2.5:7b"
TIMEOUT = 30  # seconds per request

# ==================== PROMPT ====================
BUYER_PROMPT = """คุณเป็น AI ที่วิเคราะห์โพสจาก Facebook เกี่ยวกับโซล่าเซลล์

วิเคราะห์โพสต์ต่อไปนี้แล้วตอบเฉพาะ JSON:
{{"is_lead": true/false, "score": 0-10, "reason": "เหตุผลสั้นๆ"}}

กฎสำคัญ:
- is_lead = true ก็ต่อเมื่อ เจ้าของโพส ต้องการซื้อ/ติดตั้ง โซล่าเซลล์ สำหรับตัวเอง
- is_lead = false ถ้า:
  * เป็นผู้ขาย/ร้าน/ช่าง
  * เป็นคนให้ความรู้/สอน/แนะนำ โดยไม่ได้อยากซื้อ
  * ถามเกี่ยวกับสินค้าที่จะขาย ไม่ใช่อยากซื้อ
  * โพสต์รีวิว/แชร์ประสบการณ์ โดยไม่ได้อยากซื้อ
- score 10 = กำลังจะซื้อ, score 8-9 = สนใจมาก, score 5-7 = สนใจ, score 1-4 = ถาม/สอบถาม

โพส: {post_text}

ตอบเฉพาะ JSON เท่านั้น"""

def analyze_with_qwen(post_text, post_url, group_id):
    """วิเคราะห์โพสด้วย Qwen 2.5:7b"""
    
    try:
        prompt = BUYER_PROMPT.format(post_text=post_text[:500])
        
        data = json.dumps({
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1}
        }).encode('utf-8')
        
        req = urllib.request.Request(
            OLLAMA_URL,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            result_data = json.loads(response.read().decode('utf-8'))
            ai_text = result_data.get('response', '').strip()
        
        # Parse JSON response
        # Remove markdown code blocks if present
        ai_text = ai_text.replace('```json', '').replace('```', '').strip()
        
        try:
            analysis = json.loads(ai_text)
            return {
                'is_lead': analysis.get('is_lead', False),
                'score': analysis.get('score', 0),
                'reason': analysis.get('reason', 'ไม่ทราบ'),
                'ai_used': 'qwen2.5:7b',
                'ai_raw': ai_text
            }
        except json.JSONDecodeError:
            # Fallback to simple parsing
            return {
                'is_lead': 'ซื้อ' in ai_text or 'สนใจ' in ai_text,
                'score': 5,
                'reason': ai_text[:100],
                'ai_used': 'qwen2.5:7b',
                'ai_raw': ai_text
            }
            
    except urllib.error.URLError as e:
        return {
            'is_lead': False,
            'score': 0,
            'reason': f'URL Error: {str(e)}',
            'ai_used': 'qwen2.5:7b',
            'ai_raw': ''
        }
    except Exception as e:
        return {
            'is_lead': False,
            'score': 0,
            'reason': f'Exception: {str(e)}',
            'ai_used': 'qwen2.5:7b',
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
    print("🧪 QWEN 2.5:7b AI BUYER FILTER TEST")
    print("="*60)
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n[{i}] Testing: {text[:50]}...")
        result = analyze_with_qwen(text, f'test_{i}', 'test')
        print(f"    Result: is_lead={result['is_lead']}, score={result['score']}")
        print(f"    Reason: {result['reason']}")
        print(f"    AI: {result['ai_used']}")
    
    print("\n" + "="*60)
    print("✅ Test complete!")