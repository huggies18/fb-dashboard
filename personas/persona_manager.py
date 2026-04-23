# ============================================================
# PERSONA MANAGER - รวมทุก Personas
# ============================================================

from programmer import PERSONA as PROGRAMMER, TRIGGER_KEYWORDS as PROGRAMMER_KEYS
from housewife import PERSONA as HOUSEWIFE, TRIGGER_KEYWORDS as HOUSEWIFE_KEYS
from employee100k import PERSONA as EMPLOYEE100K, TRIGGER_KEYWORDS as EMPLOYEE100K_KEYS
from manager300k import PERSONA as MANAGER300K, TRIGGER_KEYWORDS as MANAGER300K_KEYS
from government import PERSONA as GOVERNMENT, TRIGGER_KEYWORDS as GOVERNMENT_KEYS

PERSONAS = {
    "programmer": PROGRAMMER,
    "housewife": HOUSEWIFE,
    "employee100k": EMPLOYEE100K,
    "manager300k": MANAGER300K,
    "government": GOVERNMENT,
}

TRIGGER_MAP = {
    "programmer": PROGRAMMER_KEYS,
    "housewife": HOUSEWIFE_KEYS,
    "employee100k": EMPLOYEE100K_KEYS,
    "manager300k": MANAGER300K_KEYS,
    "government": GOVERNMENT_KEYS,
}

def get_persona(name):
    """ดึงข้อมูล persona ตามชื่อ"""
    return PERSONAS.get(name)

def get_all_personas():
    """ดึงรายชื่อทุก personas"""
    return list(PERSONAS.keys())

def match_persona(text):
    """ตรวจสอบว่า text ควรใช้ persona ไหน"""
    text_lower = text.lower()
    for persona_name, keywords in TRIGGER_MAP.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return persona_name
    return None

def generate_response(persona_name, context):
    """สร้าง response ตาม persona และ context"""
    persona = get_persona(persona_name)
    if not persona:
        return None
    
    # Context types: greeting, asking_spec, asking_price, buying, competitor, closing
    context_type = context.get("type", "greeting")
    return persona.get(context_type, persona["greeting"])
