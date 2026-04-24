#!/usr/bin/env python3
"""
AI Buyer Filter - Ultra Accurate (v6)
=====================================
ใช้ Keyword วิเคราะห์โพสจาก Facebook ให้แม่นที่สุด

4 Categories (ตาม Tibodin Spec):
- 🔥 HIGH (9-10): สนใจ/ซื้อ - ปิดการขายทันที
- 🟢 MEDIUM (7-8): สนใจโซล่าเซลล์ - มุ่งหวังสูง
- 🟡 EVAL (5-6): กำลังพิจารณา - เปรียบเทียบราคา
- 🔵 COLD (1-4): สอบถาม - หาความรู้/ข้อมูล
"""

import sys
sys.path.insert(0, '.')

import json, os, re
from datetime import datetime, timedelta

THAI_OFFSET = timedelta(hours=7)
LEADS_DIR = "/root/.openclaw/workspace/facebook-scraper/leads"
PENDING_DIR = "/root/.openclaw/workspace/facebook-scraper/pending"

# ==================== BUYER SCORING (Ultra Accurate v6) ====================
def ultra_analyze(post_text, post_url, group_id):
    """
    วิเคราะห์แบบ Ultra Accurate v6:
    1. HIGH intent → ตรวจก่อนเสมอ
    2. MEDIUM → ถ้าไม่มี HIGH
    3. COLD → ถ้าไม่มี HIGH/MEDIUM  
    4. SELLER → ตรวจสุดท้าย (ถ้าไม่มี buyer signals)
    """
    
    text = post_text.strip()
    lower = text.lower()
    
    # ==================== STEP 0: STRONG SELLER SIGNALS (check BEFORE buyer) ====================
    # Some seller phrases are so strong they should override buyer signals
    strong_seller = [
        'ประกาศขาย', 'ขออนุญาตลงขาย', 'ลงขาย inverter', 'ประกาศขาย inverter',
        'ขายอินเวอร์เตอร์', 'พร้อมส่ง', 'ติดตั้งฟรี', 'รับสมัครแอดมิน',
        'โปรโมชั่น', 'ส่วนลด', 'ลดราคา',
        # ขาย/ปล่อย
        'ขาย', 'ส่งต่อ', 'ปล่อย', 'บอกราคา', 'ตั้งราคา', '฿', 'บาท', 'รวมส่ง',
        # ติดต่อ
        'สนใจ เบอร์', 'สนใจไลน์', 'ไลน์',
        # ช่องทางติดต่อ
        'ib', 'inbox', 'ทักแชท', 'แชท',
        # ลิ้ง/สั่ง
        'ลิ้ง', 'shopee', 'กดสั่ง', 'สั่งในช้อปี้', 'กดลิ้งสั่ง',
        # โฆษณาสินค้า (seller promotional)
        'ของดี', 'ราคาประหยัด', 'มาแล้ว', 'เข้ามาเลย', 'ด่วนจำนน',
        # ลูกค้าอุดหนุน (seller พูดถึงลูกค้า)
        'อุดหนุนสินค้า', 'จัดอีกสักตู้', 'ลูกค้านะครับที่อุดหนุน'
    ]
    
    for phrase in strong_seller:
        if phrase in lower:
            return {
                'is_lead': False,
                'score': 0,
                'reason': "❌ โฆษณาขาย",
                'intent_type': "seller",
                'all_reasons': ["❌ " + phrase]
            }
    
    # ==================== STEP 0.5: CONSULTATION QUESTIONS (before HIGH) ====================
    consultation_phrases = [
        'ขอสอบถาม', 'สอบถามผู้รู้', 'ดีไหม', 
        'เป็นไง', 'ควรเลือก', 'เลือกยังไง', 'ช่วยดู', 'ช่วยตรวจ', 'ช่วยเช็ค',
        'ขอดู', 'ดูหน่อย', 'มีดูไหม', 'รีวิว', 'ขอรีวิว',
        'ใครเคย', 'มีใครรู้บ้าง', 'วิธีการ', 'ขั้นตอน',
        'ขอความเห็น', 'ขอคำปรึกษา',
        'สอบถาม', 'รบกวนถาม', 'อยากสอบถาม',
        'ต้องขออนุญาตไหม', 'รับไหวไหม', 'ตัดได้ไหม'
    ]
    
    for phrase in consultation_phrases:
        if phrase in lower:
            return {
                'is_lead': True,
                'score': 3,
                'reason': "🔵 สอบถาม",
                'intent_type': "buyer",
                'all_reasons': ["🔵 " + phrase]
            }
    
    # ==================== STEP 1: HIGH INTENT ====================
    high_intent = [
        # ตัดสินใจ/นัด
        'เอาจริง', 'ตกลงติด', 'มัดจำ', 'โอนจอง',
        'มาดูหน้างาน', 'ขอคิวติดตั้ง', 'ขอเบอร์ติดต่อ', 'ขอพิกัดร้าน', 'นัดวัน',
        # สัญลักษณ์
        'สนใจ++', 'สนคับ', 'สนค่ะ', '+1', 'สนใจมาก',
        # ตามหา/ถามหาร้าน = สนใจ
        'ตามหา', 'ตามหาบริษัท', 'หาสินค้า', 'หาแผง', 'หาช่าง', 'หาร้าน',
        'ถามหาร้าน', 'แนะนำบริษัท', 'แนะนำหน่อย', 'ช่วยแนะนำ',
        # ขอรายละเอียด = อยากได้
        'ขอรายละเอียด', 'ขอคำแนะนำ', 'ขอข้อมูล', 'ขอโปรไฟล์',
        # อยาก/พร้อม
        'พร้อมติด', 'พร้อมซื้อ', 'ตัดสินใจ', 'จะติด', 'จะซื้อ', 'ติดด่วน', 'อยากจบงาน',
        'อยากติด', 'อยากได้', 'อยากมี', 'อยากสอบถาม',
        # ติดตั้งโซลาร์เซลล์
        'ติดตั้งโซลาร์เซลล์', 'อยากติด solar', 'อยากติดโซล่า',
        'ติดโซล่าบ้าน', 'ติด solar บ้าน', 'สนใจโซลาร์เซลล์',
        'สนใจ solar roof', 'หาโซลาร์เซลล์', 'หาช่างติด solar',
        'บริษัทติดตั้งโซลาร์เซลล์แนะนำ', 'solar cell ราคา',
        'ติดโซลาร์กี่บาท', 'solar roof ราคา',
        # ถามราคา (HIGH intent - เป็น buyer ที่สนใจ)
        'ราคา', 'เท่าไหร่',  # ถามราคา = ราคา + เท่าไหร่/กี่บาท
        'ราคาแพงไหม', 'ราคาถูกไหม', 'ราคากี่บาท', 'ราคากี่',
        'ราคาที่', 'ราคาต่อ', 'ราคาค่ะ', 'ราคาครับ', 'ราคาหรือ',
        # Hybrid/On-grid
        'hybrid', 'on grid', 'off grid', 'on-grid', 'off-grid',
        'hybrid on grid', 'hybrid off grid',
        # บริการหลังการขาย (ไม่ใช่ seller!)
        'บริการหลังการขาย'
    ]
    
    for phrase in high_intent:
        if phrase in lower:
            return {
                'is_lead': True,
                'score': 9,
                'reason': "🔥 สนใจ/ซื้อ",
                'intent_type': "buyer",
                'all_reasons': ["🔥 " + phrase]
            }
    
    # ==================== STEP 2: MEDIUM INTENT ====================
    medium_intent = [
        # เปรียบเทียบ
        'เจ้าอื่น', 'เทียบกับ', 'ออนกริด', 'ไฮบริด', 'micro inverter', 'battery', 'กันย้อน',
        # ยี่ห้อ
        # ความคุ้มค่า
        'คืนทุนกี่ปี', 'ลดค่าไฟ', 'คุ้มไหม', 'ผ่อนได้กี่เดือน',
        # สถานะ/สนใจ
        'สนใจติด', 'ต้องการติด', 'ต้องการซื้อ', 'ดูไว้อยู่', 'กำลังเลือก', 'ยังลังเล'
    ]
    
    for phrase in medium_intent:
        if phrase in lower:
            return {
                'is_lead': True,
                'score': 7,
                'reason': "🟢 สนใจโซล่าเซลล์",
                'intent_type': "buyer",
                'all_reasons': ["🟢 " + phrase]
            }
    
    # ==================== STEP 3: COLD/QUESTIONS (legacy - ลบออกแล้ว ใช้ STEP 0.5 แทน) ====================
    # cold_phrases ย้ายไป STEP 0.5 แล้ว
    eval_intent = [
        # อุปกรณ์/Spec
        'แผง n-type', 'แผง p-type', 'n-type', 'p-type',
        'inverter', 'อินเวอร์เตอร์', 'ไมโครอินเวอร์เตอร์',
        'แบตเตอรี่', 'ตู้ไฟ', 'สมาร์ทมิเตอร์',
        # เงื่อนไขบ้าน
        'หลังคาซีแพค', 'หลังคาเมทัลชีท', 'บ้านเดี่ยว', 'ทาวน์โฮม',
        'แอร์กี่ตัว', 'ตู้เย็นกี่เครื่อง', 'ชาร์จรถไฟฟ้า', 'ev',
        'ไฟตกบ่อย', 'พื้นที่น้อย',
        # ราคา
        'กี่บาท', 'งบเท่าไหร่', 'ขอราคา', 'ราคาเท่าไหร่', 'ค่าติดตั้ง', 'ใบเสนอราคา'
    ]
    
    for phrase in eval_intent:
        if phrase in lower:
            return {
                'is_lead': True,
                'score': 5,
                'reason': "🟡 กำลังพิจารณา",
                'intent_type': "buyer",
                'all_reasons': ["🟡 " + phrase]
            }
    
    # ==================== STEP 5: SELLER (ตรวจสุดท้าย) ====================
    seller_phrases = [
        # ขาย/โฆษณา - ใช้คำเฉพาะเจาะจง (ไม่ใช้ 'ขาย' อย่างเดียว)
        'ขออนุญาตลงขาย', 'ประกาศขาย inverter', 'ขายอินเวอร์เตอร์',
        'พร้อมส่ง', 'พร้อมติดตั้ง', 'ติดตั้งฟรี',
        # ขายออนไลน์/ช้อปี้
        'สั่งในช้อปี้', 'กดลิ้งสั่ง', 'ซื้อขาย', 'ขายตรง', 'ขายตรงจากโรงงาน',
        # รับงาน (ไม่ใช่ buyer)
        'รับงาน', 'รับสมัคร', 'รับจ้าง',
        # ลูกค้าอุดหนุน (seller พูดถึงลูกค้า)
        'อุดหนุนสินค้า', 'จัดอีกสักตู้', 'ลูกค้านะครับที่อุดหนุน',
        # ร้านค้า/ผู้ขาย
        'ร้านขายอินเวอร์เตอร์', 'ร้านขายแผง', 'ร้านขายโซล่า',
        # ข่าว/ข้อมูล (ไม่ใช่ buyer intent)
        'ด่วน! ค่าไฟ', 'ค่าไฟรอบใหม่', 'ค่า ft', 'มติ กกพ.',
        'ปรับขึ้น', 'ปรับลง', 'ผันผ่าน',
        # ตัวแทนจำหน่าย
        'ตัวแทนจำหน่าย', 'จำหน่าย', 'ตัวแทน', 'รีบจับจอง',
        'ขนกอง', 'กองทัพ', 'แผงมา', 'มาไว้ที่นี่',
        'รับสมัครแอดมิน', 'ทำงานออนไลน์', 'ฝากร้าน',
        'โปรโมชั่น', 'ส่วนลด', 'ลดราคา'
    ]
    
    for phrase in seller_phrases:
        if phrase in lower:
            return {
                'is_lead': False,
                'score': 0,
                'reason': "❌ โฆษณาขาย",
                'intent_type': "seller",
                'all_reasons': ["❌ " + phrase]
            }
    
    # ==================== STEP 6: NOTHING MATCHED ====================
    return {
        'is_lead': False,
        'score': 0,
        'reason': "ไม่มี signals",
        'intent_type': "unknown",
        'all_reasons': []
    }

def extract_contact(post_text):
    """ดึงข้อมูลติดต่อจากโพส"""
    contacts = []
    text = post_text.lower()
    
    import re
    phone_pattern = r'[\d]{9,10}'
    phones = re.findall(phone_pattern, text)
    for phone in phones:
        if len(phone) >= 9:
            contacts.append('โทร: ' + phone)
    
    fb_pattern = r'facebook\.com/(\w+)'
    fb_links = re.findall(fb_pattern, text)
    for fb in fb_links[:2]:
        contacts.append('FB: ' + fb)
    
    return contacts
