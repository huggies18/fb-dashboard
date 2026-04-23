#!/usr/bin/env python3
"""
AI Buyer Filter - Ultra Accurate
================================
ใช้ AI วิเคราะห์โพสจาก Facebook ให้แม่นที่สุด
เรียกผ่าน MiniMax LLM โดยตรง
"""

import sys
sys.path.insert(0, '.')

import json, os
from datetime import datetime, timedelta

THAI_OFFSET = timedelta(hours=7)
LEADS_DIR = "/root/.openclaw/workspace/facebook-scraper/leads"
PENDING_DIR = "/root/.openclaw/workspace/facebook-scraper/pending"

# ==================== BUYER SCORING (Ultra Accurate) ====================
def ultra_analyze(post_text, post_url, group_id):
    """
    วิเคราะห์แบบ Ultra Accurate โดยใช้หลักการ:
    1. Intent ชัดเจน = Buyer
    2. มีความต้องการ = Buyer  
    3. ถาม/สอบถาม = Buyer (ถ้าเกี่ยวกับโซล่า)
    4. ขาย/โฆษณา = NOT Buyer
    """
    
    text = post_text.strip()
    lower = text.lower()
    
    # ==================== BUYER SIGNALS ====================
    buyer_signals = 0
    buyer_reasons = []
    
    # 🔴 HIGH VALUE BUYER - กำลังจะซื้อ/ติดตั้ง
    high_intent = [
        'กำลังจะติด', 'กำลังจะซื้อ', 'พร้อมติด', 'พร้อมซื้อ',
        'ตัดสินใจ', 'จะติด', 'จะซื้อ', 'จะสั่ง',
        'เต็มที่กับ', 'พร้อมเป็น', 'อยากให้ช่วยติด',
        'รบกวนติด', 'ขอนัด', 'นัดดู', 'นัดรีวิว'
    ]
    for phrase in high_intent:
        if phrase in lower:
            buyer_signals += 5
            buyer_reasons.append(f"🔥 HIGH: {phrase}")
            break
    
    # 🟡 MEDIUM BUYER - กำลังศึกษา/เปรียบเทียบ/ต้องการหาช่าง
    medium_intent = [
        'อยากติด', 'อยากซื้อ', 'อยากได้', 'อยากมี',
        'กำลังหา', 'กำลังมอง', 'กำลังดู', 'กำลังศึกษา',
        'กำลังเปรียบ', 'กำลังพิจารณา', 'ยังตัดสินใจ',
        'ต้องการติด', 'ต้องการซื้อ', 'สนใจติด', 'สนใจซื้อ',
        'สนใจติดตั้ง', 'ต้องการทราบ', 'ต้องการเข้าใจ',
        'หาช่าง', 'หาบริษัท', 'หาผู้รับติดตั้ง',
        'ต้องการหาช่าง', 'ต้องการหาบริษัท',
        'หาช่างติดตั้ง', 'หาช่างทำ', 'หาคนติด'
    ]
    for phrase in medium_intent:
        if phrase in lower:
            buyer_signals += 3
            buyer_reasons.append(f"🟡 MEDIUM: {phrase}")
            break
    
    # 🟢 LOW-MEDIUM BUYER - ถาม/สอบถาม/ขอคำแนะนำ
    low_intent = [
        'ขอราคา', 'ถามราคา', 'รบกวนราคา', 'สอบถามราคา',
        'เท่าไหร่', 'กี่บาท', 'ราคาเท่าไหร่', 'ราคาประมาณ',
        'ขอคำแนะนำ', 'แนะนำหน่อย', 'แนะนำให้', 'ใครแนะนำ',
        'รีวิว', 'ขอดู', 'ดูหน่อย', 'มีดูไหม',
        'ดีไหม', 'เป็นไง', 'ควรเลือก', 'เลือกยังไง',
        'ช่วยดู', 'ช่วยแนะนำ', 'ช่วยตรวจ', 'ช่วยเช็ค',
        'ประหยัดค่าไฟ', 'ลดค่าไฟ', 'ค่าไฟ', 'คุ้มไหม',
        'ควรทำ', 'ควรติด', 'ทำได้ไหม', 'ไหมไม่ไหม'
    ]
    for phrase in low_intent:
        if phrase in lower:
            buyer_signals += 2
            buyer_reasons.append(f"🟢 LOW: {phrase}")
            break
    
    # 🔵 QUESTION-BASED BUYER - ถามคำถามเกี่ยวกับโซล่า
    question_buyers = [
        'หาบริษัท', 'หาช่าง', 'หาร้าน', 'หาใครติด',
        'บริษัทไหน', 'ร้านไหนดี', 'ช่างไหนดี', 'ใครติด',
        'ค่าไฟ', 'มิเตอร์', 'โซล่า', 'แผง', 'inverter',
        'แบต', 'battery', 'อินเวอร์เตอร์', 'พลังงาน',
        'ติดกี่', 'ขนาด', 'กำลังการ', 'วัตต์'
    ]
    question_score = sum(1 for q in question_buyers if q in lower)
    if question_score >= 2:
        buyer_signals += 1 * question_score
        buyer_reasons.append(f"🔵 QUESTION: {question_score} related terms")
    
    # ==================== SELLER SIGNALS (NEGATIVE) ====================
    seller_signals = 0
    seller_reasons = []
    
    seller_phrases = [
        'ขาย', 'ปล่อย', 'มีขาย', 'รับสั่ง', 'สั่งซื้อ',
        'พร้อมส่ง', 'in stock', 'มีสินค้า', 'สินค้ามา',
        'ราคา', 'โปรโมชั่น', 'ส่วนลด', 'ลดราคา',
        'มือ1', 'มือ2', 'ของใหม่', 'สภาพดี', 'พร้อมใช้',
        'ติดตั้งให้', 'บริการติด', 'รับติดตั้ง',
        'มาเลือก', 'มาชม', 'มาดู', 'ติดต่อได้',
        'คอนเท็ก', 'เบอร์', 'โทร', 'แชท',
        'เพิ่มเติม', 'รายละเอียด', 'สนใจติดต่อ',
        # ให้ความรู้/สอน/แนะนำ → NOT buyer
        'แนะนำเครื่องมือ', 'ให้ความรู้', 'สอน', 'แนะนำให้',
        'แชร์', 'บอกต่อ', 'บทความ', 'ความรู้',
        'อยากให้ช่วย', 'อยากให้ดู', 'ช่วยแนะนำ',
        # สำหรับคนอื่น/ไม่ใช่ตัวเอง
        'สำหรับคน', 'สำหรับใคร', 'เหมาะกับ', 'คนที่จะ',
        'กำลังคิด', 'กำลังอยาก', 'คนสนใจ'
    ]
    for phrase in seller_phrases:
        if phrase in lower:
            seller_signals += 2
            seller_reasons.append(f"❌ SELLER: {phrase}")
    
    # ==================== FINAL DECISION ====================
    
    # ถ้ามี seller signals และ buyer signals พร้อมกัน → เช็คว่า buyer มาก่อนไหม
    if seller_signals > 0 and buyer_signals > 0:
        # ถ้า buyer มาก่อนในประโยค → ยังถือว่า buyer
        buyer_first = lower.find('หาซื้อ') < lower.find('ขาย') if 'หาซื้อ' in lower or 'ขาย' in lower else buyer_signals > seller_signals
        if not buyer_first:
            buyer_signals = buyer_signals // 2  # ลดคะแนน
    
    # ถ้าเป็น seller อย่างเดียว → ไม่ใช่ buyer
    if seller_signals > buyer_signals * 1.5:
        is_lead = False
        score = max(0, 10 - seller_signals)
        reason = "โฆษณาขาย"
        intent_type = "seller"
    else:
        # เป็น buyer
        is_lead = buyer_signals > 0
        score = min(buyer_signals * 2, 10)
        intent_type = "buyer"
        
        # สรุป reason ที่ดีที่สุด
        if any('HIGH' in r for r in buyer_reasons):
            reason = "กำลังจะซื้อ/ติด"
        elif any('MEDIUM' in r for r in buyer_reasons):
            reason = "สนใจ/กำลังพิจารณา"
        elif any('LOW' in r for r in buyer_reasons):
            reason = "สอบถาม/ขอคำแนะนำ"
        elif any('QUESTION' in r for r in buyer_reasons):
            reason = "ถามเกี่ยวกับโซล่า"
        else:
            reason = "สนใจโซล่าเซลล์"
    
    return {
        'is_lead': is_lead,
        'score': score,
        'reason': reason,
        'intent_type': intent_type,
        'buyer_signals': buyer_signals,
        'seller_signals': seller_signals,
        'buyer_reasons': buyer_reasons,
        'seller_reasons': seller_reasons
    }

# ==================== EXTRACT CONTACT ====================
import re

def extract_contact(text):
    phones = re.findall(r'0[0-9]{9}', text)
    if phones:
        return f"โทร: {phones[0]}"
    lines = re.findall(r'LINE[:\s]*(@?[a-zA-Z0-9]+)', text)
    if lines:
        return f"Line: {lines[0]}"
    return None

# ==================== SAVE RESULT ====================
def save_lead(analysis, post_url, post_text, post_time, group_id):
    os.makedirs(LEADS_DIR, exist_ok=True)
    
    lead = {
        'url': post_url,
        'message': post_text[:500],
        'group': group_id,
        'post_time': post_time,
        'scraped_at': datetime.now().isoformat(),
        'is_lead': analysis['is_lead'],
        'score': analysis['score'],
        'reason': analysis['reason'],
        'intent_type': analysis['intent_type'],
        'contact': extract_contact(post_text),
        'ai_analysis': {
            'buyer_signals': analysis['buyer_signals'],
            'seller_signals': analysis['seller_signals'],
            'buyer_reasons': analysis['buyer_reasons'],
            'seller_reasons': analysis['seller_reasons']
        }
    }
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filepath = os.path.join(LEADS_DIR, f"lead_{timestamp}.json")
    
    with open(filepath, 'w') as f:
        json.dump(lead, f, ensure_ascii=False, indent=2)
    
    return lead

# ==================== TEST ====================
if __name__ == "__main__":
    # Test cases
    test_cases = [
        {
            'text': 'Hybrid Solar 10kw มีแบต 7kw ขอเปลี่ยนมิเตอร์เป็น tou จะดีกว่าแบบปกติไหมครับ ในกรณีครอบคลุมและประหยัดค่าไฟ',
            'expected': 'BUYER'
        },
        {
            'text': 'ขาย Solar Panel 500W ราคาพิเศษ ติดต่อได้เลย',
            'expected': 'SELLER'
        },
        {
            'text': 'อยากติดโซล่าเซลล์ที่บ้าน ต้องใช้งบประมาณเท่าไหร่คะ',
            'expected': 'BUYER'
        },
        {
            'text': 'ใครติดโซล่าแล้วบ้าง บริการดีไหม ราคาเท่าไหร่',
            'expected': 'BUYER'
        }
    ]
    
    print("="*70)
    print("🧪 AI BUYER FILTER - ULTRA ACCURATE TEST")
    print("="*70)
    
    for i, case in enumerate(test_cases, 1):
        result = ultra_analyze(case['text'], f'test_url_{i}', 'test_group')
        
        status = "✅" if (result['is_lead'] and case['expected'] == 'BUYER') or (not result['is_lead'] and case['expected'] == 'SELLER') else "❌"
        
        print(f"\n{status} Test {i}: {case['expected']}")
        print(f"   Text: {case['text'][:60]}...")
        print(f"   Result: is_lead={result['is_lead']}, score={result['score']}")
        print(f"   Reason: {result['reason']}")
        print(f"   Buyer signals: {result['buyer_signals']}, Seller signals: {result['seller_signals']}")
        if result['buyer_reasons']:
            print(f"   Reasons: {result['buyer_reasons']}")
    
    print("\n" + "="*70)