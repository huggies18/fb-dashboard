#!/usr/bin/env python3
"""
Admin Notification System
==========================
ส่งแจ้งเตือนไป Telegram เมื่อเกิดปัญหา หรือ ผล /fbuyer
"""

import sys
sys.path.insert(0, '.')

import json, os, urllib.request, urllib.error
from datetime import datetime, timedelta

# ==================== CONFIG ====================
THAI_OFFSET = timedelta(hours=7)
TELEGRAM_BOT_TOKEN = "8774902841:AAFveLJDs-Bf02cPkBhZVPU5JBw_sdLIhNw"
TELEGRAM_USER_ID = "6780942246"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

def thai_now():
    return datetime.now() + THAI_OFFSET

# ==================== SEND MESSAGE ====================
def send_admin_alert(title, message, emoji="⚠️"):
    """ส่งแจ้งเตือนไป Telegram Admin"""
    
    full_message = f"{emoji} {title}\n\n{message}\n\n⏰ เวลา: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    payload = {
        'chat_id': TELEGRAM_USER_ID,
        'text': full_message,
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        TELEGRAM_API_URL,
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('ok', False)
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        return False
    except Exception as e:
        print(f"Failed to send alert: {e}")
        return False

# ==================== SPECIFIC ALERTS ====================
def alert_cookie_expired():
    """แจ้งเตือน Cookie หมดอายุ"""
    return send_admin_alert(
        title="🍪 Cookie หมดอายุ!",
        message="Facebook Cookie หมดอายุแล้ว\nกรุณาอัพเดต Cookie ใหม่\n\nไฟล์: fb_session.json",
        emoji="🍪"
    )

def alert_proxy_expired():
    """แจ้งเตือน Proxy หมดอายุ"""
    return send_admin_alert(
        title="🌐 Proxy หมดอายุ!",
        message="Proxy หมดอายุหรือไม่ทำงาน\nกรุณาตรวจสอบ Proxy config\n\nไฟล์: proxy_config.json",
        emoji="🌐"
    )

def alert_login_failed(reason="ไม่ทราบสาเหตุ"):
    """แจ้งเตือน Login ล้มเหลว"""
    return send_admin_alert(
        title="🔐 Login Facebook ล้มเหลว!",
        message=f"ไม่สามารถ login Facebook ได้\n\nสาเหตุ: {reason}\n\nกรุณาตรวจสอบ Cookie",
        emoji="🔐"
    )

def alert_scraper_error(error_type, details):
    """แจ้งเตือน Scraper Error ทั่วไป"""
    return send_admin_alert(
        title="⚠️ Scraper Error!",
        message=f"เกิดข้อผิดพลาด: {error_type}\n\nรายละเอียด: {details}",
        emoji="⚠️"
    )

# ==================== FBUYER RESULT ALERT ====================
def get_intent_emoji(score, reason):
    """Get emoji based on intent/reason"""
    reason_lower = reason.lower() if reason else ''
    
    if 'กำลังจะซื้อ' in reason_lower or 'กำลังจะติด' in reason_lower:
        return '🟢'
    elif 'สนใจ' in reason_lower or 'พร้อม' in reason_lower:
        return '🟢'
    elif 'ขอราคา' in reason_lower or 'ถามราคา' in reason_lower:
        return '🟡'
    elif 'สอบถาม' in reason_lower or 'ขอคำแนะนำ' in reason_lower:
        return '🟡'
    elif 'ถามเกี่ยวกับ' in reason_lower:
        return '🟢'
    else:
        return '🟢'

def format_reason_for_display(reason):
    """Format reason for display"""
    if not reason:
        return 'ไม่ระบุ'
    
    # Shorten common reasons
    reason_map = {
        'กำลังจะซื้อ/ติด': 'กำลังจะซื้อ/ติด',
        'สนใจ/กำลังพิจารณา': 'สนใจ/กำลังพิจารณา',
        'สอบถาม/ขอคำแนะนำ': 'สอบถาม/ขอคำแนะนำ',
        'ถามเกี่ยวกับโซล่า': 'ถามเกี่ยวกับโซล่า',
        'กำลังจะติดตั้ง': 'กำลังจะติดตั้ง',
        'พร้อมซื้อ/ติด': 'พร้อมซื้อ/ติด',
    }
    
    for key, value in reason_map.items():
        if key in reason:
            return value
    
    return reason[:30] if len(reason) > 30 else reason

def truncate_message(message, max_len=80):
    """Truncate message for preview"""
    if not message:
        return ''
    msg = ' '.join(message.split())
    if len(msg) > max_len:
        return msg[:max_len] + '...'
    return msg

def send_fbuyer_result_alert(leads_found, total_leads, leads=None):
    """ส่งแจ้งผล /fbuyer แบบละเอียด"""
    thai_now_dt = thai_now()
    
    if leads_found > 0 and leads:
        # Header with leads details
        header = f"""🟢 พบ Buyer Leads ใหม่!
⏰ เมื่อ: {thai_now_dt.strftime('%H:%M')} (UTC+7)
📊 พบ: {leads_found} โพส
👥 Workers: 3 ตัว

💡 พิมพ์ /wbuyer เพื่อ export CSV

━━━━━━━━━━━━━━━━━━━━━━
"""
        
        lead_items = []
        for i, lead in enumerate(leads[:10], 1):  # Max 10 leads in alert
            emoji = get_intent_emoji(lead.get('score', 0), lead.get('reason', ''))
            reason = format_reason_for_display(lead.get('reason', ''))
            score = lead.get('score', 0)
            post_time = lead.get('post_time', '')
            message = truncate_message(lead.get('message', ''))
            url = lead.get('url', '')
            
            item = f"""{i}. {emoji} {reason} score:{score} / เวลาโพสเมื่อ {post_time}
 📝 "{message}"
 🔗 {url}"""
            lead_items.append(item)
        
        report = header + '\n\n'.join(lead_items)
        
        # Add note if more than 10 leads
        if len(leads) > 10:
            report += f"\n\n📝 ...และอีก {len(leads) - 10} โพส (ดูทั้งหมดใน /wbuyer)"
    else:
        report = f"""🟡 /fbuyer ไม่พบ leads ใหม่!
⏰ เมื่อ: {thai_now_dt.strftime('%H:%M')} (UTC+7)
📊 พบ: 0 โพส
👥 Workers: 3 ตัว

💡 รวมทั้งหมด: {total_leads} ราย"""
    
    # Send via Telegram directly
    payload = {
        'chat_id': TELEGRAM_USER_ID,
        'text': report,
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        TELEGRAM_API_URL,
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('ok', False)
    except Exception as e:
        print(f"Failed to send alert: {e}")
        return False
