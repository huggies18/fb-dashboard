# Facebook Scraper - HighSolar

## สรุป
ระบบเก็บโพสจาก Facebook Groups แล้วกรองหา Buyer Leads ด้วย AI

## ไฟล์หลัก
- `scraper/run_workflow.py` - Workflow หลัก (Scrape → Filter → Telegram)
- `scraper/scrape_all_posts.py` - เก็บโพสจาก Facebook Groups
- `scraper/parallel_filter.py` - กรองด้วย AI
- `scraper/config.json` - กลุ่มและ keywords ที่ใช้

## การติดตั้ง

```bash
# 1. ติดตั้ง dependencies
pip install -r requirements.txt

# 2. ติดตั้ง Browser
playwright install chromium
```

## การตั้งค่าก่อนใช้

### 1. Cookie สำหรับ Facebook
Copy ไฟล์ `fb_session.json.example` เป็น `fb_session.json`
แล้วใส่ cookie จริงจาก Facebook

วิธีเอา cookie:
1. ล็อกอิน Facebook ใน Chrome
2. เปิด DevTools (F12) → Application → Cookies → facebook.com
3. Copy ค่า `c_user`, `datr`, `fr`, `sb`, `xs`

### 2. Proxy (ไม่บังคับ)
ถ้าต้องการใช้ proxy ให้ copy `proxy_config.json.example` เป็น `proxy_config.json`
แล้วใส่ข้อมูล proxy ของคุณ

## การรัน

```bash
# Full workflow (Scrape + Filter + Telegram)
cd highsolar/scraper
python3 run_workflow.py

# รัน Infinite loop (ทุก 2-3 นาที)
python3 run_infi.py
```

## ผลลัพธ์
- CSV files ใน `scraper/csv_exports/`
- Filter results ใน `scraper/filter_result.json`

## หมายเหตุ
- ต้องมี cookie ที่ยัง valid
- ถ้าโพสน้อยผิดปกติ แสดงว่า cookie หมด
- Proxy ช่วยให้ไม่โดน block