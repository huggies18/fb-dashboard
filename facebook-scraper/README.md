# Facebook Group Scraper

ระบบเก็บคอมเมนต์จาก Facebook Group อัตโนมัติ

## 📋 สิ่งที่ต้องมี

- Python 3.8+
- Windows/macOS/Linux
- Facebook Account

## 🚀 วิธีติดตั้ง

### 1. ติดตั้ง Python
```bash
# Windows: ไปที่ https://python.org/downloads
# macOS: brew install python3
# Linux: sudo apt-get install python3 python3-pip
```

### 2. ติดตั้ง Dependencies
```bash
cd facebook-scraper
pip install -r requirements.txt
playwright install chromium
```

### 3. แก้ไข Config
```json
// config.json
{
    "groups": ["1248346110734837"],  // ใส่ Group ID ของคุณ
    "keywords": ["solar", "โซล่า", "ค่าไฟ"],
    "min_comment_length": 10,
    "headless": false  // true = ซ่อน browser, false = เห็น browser
}
```

### 4. รันครั้งแรก
```bash
python scraper.py
```

- ระบบจะเปิด Chrome browser
- Login Facebook ตามปกติ
- Session จะถูกบันทึกใน `fb_session.json` (ครั้งต่อไปไม่ต้อง login ใหม่)

## 📁 ไฟล์ในโปรเจค

| ไฟล์ | รายละเอียด |
|------|------------|
| `scraper.py` | Script หลัก |
| `database.py` | จัดการ SQLite |
| `config.json` | ตั้งค่า Group, Keywords |
| `fb_session.json` | เก็บ Session (auto) |
| `comments.db` | ฐานข้อมูล SQLite |
| `bot.log` | Log การทำงาน |

## ⏰ ตั้ง Cron Job (ทุก 3 ชั่วโมง)

### Windows (Task Scheduler)
```powershell
# เปิด Task Scheduler
# สร้าง Task ใหม่
# Action: python "C:\path\to\scraper.py"
# Trigger: Every 3 hours
```

### Linux/macOS
```bash
# เปิด crontab
crontab -e

# เพิ่มบรรทัดนี้
0 */3 * * * cd /path/to/facebook-scraper && python3 scraper.py >> bot.log 2>&1
```

## 📊 ดูผลลัพธ์

```bash
# ดูจำนวนคอมเมนต์ในฐานข้อมูล
python -c "from database import get_comment_count; print(get_comment_count())"

# Export เป็น CSV
python scraper.py --export

# ดู log
type bot.log   # Windows
cat bot.log    # Linux/macOS
```

## 🔍 ค้นหาคอมเมนต์

```python
from database import get_comments_by_keyword

# หาคอมเมนต์ที่มีคำว่า "solar"
results = get_comments_by_keyword("solar")
for r in results:
    print(r[1])  # text
```

## ⚠️ คำเตือน

1. **Facebook อาจ Ban** - ถ้าใช้บ่อยเกินไป
2. ใช้ **Account สำรอง** แทน Account หลัก
3. ควรมี **delay** ระหว่างการ scrape

## 🛠️ แก้ปัญหา

| ปัญหา | วิธีแก้ |
|-------|--------|
| Chrome ไม่เปิด | `playwright install chromium` |
| Login ล้มเหลว | ลบ `fb_session.json` แล้วรันใหม่ |
| ไม่เจอคอมเมนต์ | เช็ค Group ID ใน config.json |
| Error database | ลบ `comments.db` แล้วรันใหม่ |