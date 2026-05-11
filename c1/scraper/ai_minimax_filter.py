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
BUYER_PROMPT = """You are a computer rental lead analyzer for C1 (เช่าคอมออนไลน์). Reply ONLY JSON. {"is_lead": true/false, "score": 0-10, "reason": "thai reason"}

Rules:
- is_lead=true if person WANTS TO RENT/BUY computer bot services (เช่าคอม, เช่าบอท, VPS, เครื่องเล่นเกม)
- is_lead=false if person is SELLER/PROVIDER or unrelated
- Score 0-10 (higher = more ready to rent/buy)
- ปล่อยเช่า = SELLER → NOT BUYER
- ต้องการเช่า/หาบอท/ขอราคา = BUYER → is_lead=true

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
        'หาบอทเล่น Fivem วันละ 10 ชม ราคาเท่าไหร่ครับ',
        'ขอราคาเช่าคอมบอท Roblox หน่อยครับ',
        'ปล่อยเช่า VPS เครื่องแรง ราคาถูก',
        'ขายบอทเกม เช่าบอท FiveM'
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
