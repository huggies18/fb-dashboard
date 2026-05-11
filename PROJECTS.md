# Project Structure - Client Tracking

## สำคัญ: ทุกครั้งที่ทำงานกับไฟล์ ต้องระบุว่าเป็นของบริษัทไหน

---

## Clients

| ชื่อ | หน้าที่ | Folder |
|------|---------|--------|
| **HighSolar** | Scraper + Poster สำหรับโซลาร์เซลล์ | `/workspace/highsolar/` |
| **C1** | Scraper + Poster (รอ config) | `/workspace/c1/` |

---

## HighSolar (21 MB)

### scraper/
| ไฟล์ | หน้าที่ |
|------|---------|
| scrape_all_posts.py | ดึงโพสจาก 13 กลุ่ม Facebook |
| scraper_hybrid.py | Scraper hybrid version |
| parallel_filter.py | Filter ด้วย AI (MiniMax) |
| ai_minimax_filter.py | AI engine |
| run_workflow.py | Full workflow: Scrape → Filter → Report |
| run_infi.py | Loop workflow ทุก 2-3 นาที |
| config.json | Config กลุ่ม + keywords |
| fb_session.json | Facebook cookie |
| all_posts.json | โพสที่ scrape ได้ |
| seen_urls.json | URL ซ้ำ (กันดึงซ้ำ) |
| filter_result.json | Lead + Rejected |
| scrape_all.log | Log การ scrape |
| csv_exports/ | CSV ผลลัพธ์ทุกรอบ |

### poster/
| ไฟล์ | หน้าที่ |
|------|---------|
| fb_poster_v4.py | โพสต์หลัก |
| fb_poster_v3.py | เวอร์ชันเก่า |
| fb_poster_v2.py | เวอร์ชันเก่า |
| fb_poster.py | เวอร์ชันแรก |
| quick_poster.py | โพสต์เร็ว |
| post_db.py | Database |
| debug_poster.py | Debug |
| content/ | Content templates |

---

## C1 (180 KB)

### scraper/
| ไฟล์ | หน้าที่ |
|------|---------|
| scrape_all_posts.py | ดึงโพสจาก Facebook |
| scraper_hybrid.py | Scraper hybrid |
| parallel_filter.py | Filter ด้วย AI |
| ai_minimax_filter.py | AI engine |
| run_workflow.py | Full workflow |
| run_infi.py | Loop workflow |
| config.json | Config (ยังเป็นของ HighSolar) |
| fb_session.json | Cookie (ยังเป็นของ HighSolar) |

### poster/
| ไฟล์ | หน้าที่ |
|------|---------|
| fb_poster_v4.py | โพสต์หลัก |
| fb_poster_v3.py | เวอร์ชันเก่า |
| fb_poster_v2.py | เวอร์ชันเก่า |
| fb_poster.py | เวอร์ชันแรก |
| quick_poster.py | โพสต์เร็ว |
| post_db.py | Database |
| debug_poster.py | Debug |
| content/ | Content templates |

---

## หลักการทำงาน

1. **ก่อนแก้ไขไฟล์** → ตรวจสอบว่าเป็นของบริษัทไหน
2. **หลังแก้ไขเสร็จ** → บันทึกลงไฟล์นี้ด้วยว่าแก้อะไร

---

## Changelog

| วันที่ | บริษัท | รายละเอียด |
|--------|-------|-----------|
| 2026-05-07 | HighSolar | แก้ "6 กลุ่ม" → "13 กลุ่ม", hardcode lead count → dynamic |
| 2026-05-07 | HighSolar | แบ่งโฟลเดอร์ scraper/ + poster/ |
| 2026-05-07 | C1 | สร้างโครงสร้างใหม่ ก็อปจาก HighSolar |
| 2026-05-07 | C1 | อัปเดต GROUPS เป็น 6 กลุ่ม เช่าคอมออนไลน์ (ddcth, 720017303421089, 1753091335118215, 581287844115057, 467924334931584, 747581198744495) |
| 2026-05-07 | C1 | อัปเดต AI prompt เป็นบริบท "เช่าคอมออนไลน์" (เดิมเป็น solar cell) |
| 2026-05-07 | ALL | Poster: Facebook UI เปลี่ยน selector composer ไม่เจอ → ต้อง debug ใหม่ |
