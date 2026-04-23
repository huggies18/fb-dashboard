# เอกสารทางเทคนิค
## ระบบ Facebook Lead Scraper

---

## 1. สภาพแวดล้อม (Environment)

| รายการ | รุ่น/เวอร์ชัน |
|--------|---------------|
| OS | Debian/Linux |
| Python | 3.11+ |
| Node.js | v22 |
| Playwright | 1.58.0 |
| Chrome | 145.0.7632 |
| SQLite | 3.x |

---

## 2. โครงสร้างไฟล์

```
/root/.openclaw/workspace/facebook-scraper/
├── scraper_v3.py          # Script scraping หลัก
├── ai_analyzer.py         # AI วิเคราะห์
├── database.py            # จัดการ SQLite
├── config.json            # ตั้งค่า groups & keywords
├── fb_session.json       # Facebook session cookies
├── comments.db            # SQLite database
├── bot.log               # Log การทำงาน
└── requirements.txt      # Dependencies
```

---

## 3. Dependencies

```txt
playwright>=1.40.0
pyyaml>=6.0
```

ติดตั้งด้วย:
```bash
pip install -r requirements.txt
playwright install chromium
```

---

## 4. การทำงานของ scraper_v3.py

### 4.1 Flow หลัก

```
1. โหลด config จาก config.json
2. โหลด session จาก fb_session.json
3. สร้าง Playwright browser (headless)
4. เพิ่ม cookies เข้า context
5. วน loop ตาม groups ใน config
   5.1 เปิดหน้า group
   5.2 scroll 25 ครั้ง
   5.3 click "ดูเพิ่มเติม" buttons
   5.4 ค้นหา div[role="article"]
   5.5 กรอง text ที่มี keywords
   5.6 เก็บลง database
6. ปิด browser
```

### 4.2 Selectors ที่ใช้

| วัตถุ | Selector |
|-------|----------|
| Posts | `div[role="article"]` |
| See more | `span:text-is("ดูเพิ่มเติม")` |
| Message | `[data-ad-preview="message"]` |

### 4.3 Config

```json
{
    "groups": ["163583739075033", "383849116272497", "1175667799741067"],
    "keywords": ["solarcell", "solar cell", "โซล่าเซลล์", "โซล่าเซล", "โซล่า", "โซลาร์", "เซลล์แสงอาทิตย์", "ค่าไฟ", "ติดตั้ง", "หาร้าน", "ขอราคา"],
    "min_comment_length": 10,
    "max_scrolls": 25,
    "min_delay": 5,
    "max_delay": 15,
    "headless": true
}
```

---

## 5. การทำงานของ ai_analyzer.py

### 5.1 Intent Detection Patterns

```python
INTENT_PATTERNS = {
    "ซื้อ": [r"อยากได้", r"ต้องการ", r"สนใจ", r"ซื้อ", ...],
    "ราคา": [r"ราคา", r"เท่าไหร่", r"กี่บาท", ...],
    "ถามวิธี": [r"ทำไง", r"วิธี", r"ติดตั้งยังไง", ...],
    "เปรียบเทียบ": [r"เปรียบ", r"เทียบ", r"ดีกว่า", ...],
    "ขาย": [r"ขาย", r"มีขาย", ...],
    "แชร์ประสบการณ์": [r"ใช้แล้ว", r"มาแชร์", ...],
}
```

### 5.2 Lead Scoring Algorithm

```python
def calculate_lead_score(text):
    score = 0
    # Base: solar-related = +20
    # Intent: ซื้อ=40, ราคา=30, ถามวิธี=20
    # Sentiment: positive=+10, negative=-5
    # Urgency: high=20, medium=10, low=0
    # Has contact = +10
    # Specific patterns = +15 each
    return min(100, max(0, score))
```

### 5.3 Products Detection

```python
PRODUCT_TERMS = {
    "แผงโซล่า": ["แผง", "แผงโซล่า", "pv module", ...],
    "อินเวอร์เตอร์": ["inverter", "อินเวอร์เตอร์", ...],
    "แบตเตอรี่": ["แบต", "แบตเตอรี่", "battery", ...],
    "ชาร์จเจอร์": ["ชาร์จ", "charge", ...],
    "สายไฟ": ["สาย", "สายไฟ", "cable", ...],
}
```

---

## 6. การทำงานของ database.py

### 6.1 Schema

```sql
CREATE TABLE comments (
    id TEXT PRIMARY KEY,        -- MD5 hash ของ text
    text TEXT NOT NULL,
    author TEXT,
    post_url TEXT,
    group_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- AI analysis fields
    lead_score INTEGER,
    intent TEXT,
    products_mentioned TEXT,
    key_info TEXT,
    response_suggestion TEXT,
    is_competitor INTEGER DEFAULT 0,
    competitor_info TEXT,
    ai_analyzed INTEGER DEFAULT 0
);
```

### 6.2 Key Functions

| Function | ทำหน้าที่ |
|----------|-----------|
| `init_database()` | สร้าง table ถ้ายังไม่มี |
| `generate_comment_id(text)` | สร้าง ID จาก MD5 hash |
| `insert_comment()` | เพิ่ม comment กัน duplicate |
| `get_all_comments()` | ดึง comments ทั้งหมด |
| `export_to_csv() | Export เป็น CSV |

---

## 7. Session Management

### 7.1 Facebook Cookies

```json
{
    "cookies": [
        {"name": "c_user", "value": "100039634382957"},
        {"name": "xs", "value": "36%3Al0h_chyghd1kgA%3A..."},
        {"name": "datr", "value": "YYOaacerubUf_bofZVm5hA97"}
    ]
}
```

### 7.2 วิธีได้มา
1. เปิด Chrome บนเครื่อง user
2. Login Facebook
3. เปิด DevTools (F12) → Application → Cookies
4. Copy c_user, xs, datr

---

## 8. การตั้ง Cron Job

```bash
# แก้ crontab
crontab -e

# เพิ่มบรรทัด (รันทุก 3 ชั่วโมง)
0 */3 * * * cd /root/.openclaw/workspace/facebook-scraper && python3 scraper_v3.py >> bot.log 2>&1
```

---

## 9. Log Files

```bash
# ดู log
tail -f /root/.openclaw/workspace/facebook-scraper/bot.log

# ดู errors
grep ERROR /root/.openclaw/workspace/facebook-scraper/bot.log
```

---

## 10. Troubleshooting

| ปัญหา | วิธีแก้ |
|-------|---------|
| Browser ไม่เปิด | `playwright install chromium` |
| Login ล้มเหลว | Refresh cookies ใหม่ |
| ไม่เจอโพส | เช็ค Group ID ถูกต้องไหม |
| Scroll ไม่เพิ่ม content | Facebook limit แล้ว |

---

## 11. API Reference

### scraper_v3.py
```bash
python3 scraper_v3.py          # รัน scraping
python3 scraper_v3.py --export # export CSV
python3 scraper_v3.py --config # ดู config
```

### ai_analyzer.py
```python
from ai_analyzer import AIContextAnalyzer

analyzer = AIContextAnalyzer()
result = analyzer.analyze("text to analyze")
```

---

## 12. Security

- Session cookies เก็บในไฟล์ JSON
- ไม่เก็บ password
- ควรใช้ Facebook Account สำรอง
- HTTPS tunnel สำหรับดาวน์โหลดไฟล์

---

## 13. Performance

| Metric | ค่า |
|--------|-----|
| Scroll ต่อ group | 25 ครั้ง |
| Delay ระหว่าง actions | 5-15 วินาที (random) |
| เวลา scraping 1 กลุ่ม | ~3-5 นาที |
| Memory usage | ~500MB |

---

**อัปเดต:** 11 เมษายน 2569
**เวอร์ชัน:** 1.0