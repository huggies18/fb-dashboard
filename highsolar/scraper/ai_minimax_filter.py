#!/usr/bin/env python3
"""
MiniMax AI Filter - ใช้ MiniMax API วิเคราะห์โพส
=========================================
ใช้ API จริงของ MiniMax (OpenClaw config)
"""

import sys
sys.path.insert(0, '.')

import json, os, urllib.request

# ==================== CONFIG ====================
MINIMAX_API_KEY = "sk-cp-A_RP19hNeTy4d_Z8AcSJIy61Ex3T8nAXExChoYAQ9VygDDqaBx5jgmsVeihAoIhIC2JsQIDgQYCNpb4GNqyn6BFAGX2sA455sHIVKBBw1ygU2ZLFx_kxI-A"
MINIMAX_ENDPOINT = "https://api.minimax.io/anthropic/v1/messages"
MODEL = "MiniMax-M2.7"

# ==================== PROMPT ====================
BUYER_PROMPT = """You are a solar cell lead analyzer. Reply ONLY JSON. {"is_lead": true/false, "score": 0-10, "reason": "thai reason"}

Rules - ตัดทิ้ง (NOT BUYER):
- แชร์ความรู้/ประสบการณ์ หรือ เล่าสู่กันฟัง
- ถามเรื่องขั้นตอน/เอกสาร/กฎหมาย (เช่น แจ้งการไฟฟ้า, ขออนุญาต, ขั้นตอนติดตั้ง)
- ถามตำแหน่งทั่วไป (ตรงไหน, ติดที่ไหน)
- ถามพื้นฐาน (คืออะไร, ทำไม, วิธีใช้)
- คำถามเทคนิคที่ไม่มีความต้องการซื้อ (เช่น ต่ออนุกรมกี่แผง, Voc, Isc)
- ข้อความสั้นไม่ชัดเจน (น้อยกว่า 30 ตัวอักษร)

Rules - เก็บ (IS BUYER):
- ต้องการซื้อ/ติดตั้ง ชัดเจน
- ถามราคา หรือ ขอใบเสนอราคา
- มีความต้องการเฉพาะ (ขนาด, ยี่ห้อ, จำนวน)
- "หาซื้อ" "ตามหา" "ต้องการติดตั้ง" "กำลังจะติด"
- ถามค่าไฟ เพื่อประเมินขนาดระบบ

Score: 0-10 (higher = more ready to buy)

Post: """

# ==================== MINIMAX API CALL ====================
def minimax_analyze(post_text, post_url="unknown", group_id="unknown"):
    """วิเคราะห์โพสด้วย MiniMax API"""
    
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
                    'content': BUYER_PROMPT + post_text
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
        
        with urllib.request.urlopen(req, timeout=25) as response:
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
                return json.loads(json_str)
            else:
                return {
                    'is_lead': False,
                    'score': 0,
                    'reason': 'Parse error'
                }
                
    except Exception as e:
        return {
            'is_lead': False,
            'score': 0,
            'reason': f'Error: {str(e)[:30]}'
        }

# ==================== TEST ====================
if __name__ == '__main__':
    test_posts = [
        'บ้านเดี่ยว 2 ชั้น ต้องการหาช่างติดตั้งทั้งระบบครับ',
        'สนใจติดโซล่าเซลล์ ขอราคาหน่อยครับ',
        '#ขาดผู้ติดตามอีก700คนจะติดตามกลับทุกบ้านค่ะ',
        'ขายแผงโซล่า 400W ราคาถูก'
    ]
    
    print("="*60)
    print("MiniMax AI Filter - Test")
    print("="*60)
    
    for i, post in enumerate(test_posts, 1):
        result = minimax_analyze(post)
        emoji = "🟢" if result['is_lead'] else "🔴"
        print(f"{emoji} [{i}] {post}")
        print(f"   is_lead={result['is_lead']}, score={result['score']}")
        print(f"   reason: {result['reason']}")
    
    print("\n" + "="*60)
