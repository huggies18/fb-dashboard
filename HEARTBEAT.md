# HEARTBEAT.md - 2026-04-23

## Facebook Lead Scraper - ⚠️ ISSUES

### Status: ✅ Proxy Working - No buyer leads found (2026-04-23)

### Active Files:
- `scraper_hybrid.py` - ✅ /fbuyer (uses Keyword Filter)
- `ai_minimax_filter.py` - ⚠️ MiniMax Cloud API (reserved)
- `ai_buyer_filter.py` - ✅ Keyword-based filter
- `wbuyer_hybrid.py` - ✅ /wbuyer
- `rbuyer.py` - ✅ /rbuyer

### Commands:
- `/fbuyer` → scraper_hybrid.py (3 workers, 6 groups, **Keyword Filter** + Dedup)
- `/wbuyer` → wbuyer_hybrid.py (2 messages: count → CSV file)
- `/rbuyer` → clear leads folder

### Features:
- ✅ **Keyword-based AI** for lead analysis (ai_buyer_filter.py)
- ✅ Deduplication (load existing URLs before scrape)
- ✅ Post time in format "เวลาโพสเมื่อ X นาทีก่อน"
- ✅ Color emoji: 🟢 for high intent, 🟡 for others
- ✅ Random delay 2-5 seconds

### MiniMax API Config:
- API Key: sk-cp-A_RP19hNeTy4d_Z8AcSJIy61Ex3T8nAXExChoYAQ9VygDDqaBx5jgmsVeihAoIhIC2JsQIDgQYCNpb4GNqyn6BFAGX2sA455sHIVKBBw1ygU2ZLFx_kxI-A
- Endpoint: https://api.minimax.io/anthropic/v1/messages
- Model: MiniMax-M2.7

### Groups (6):
1. `1925997401002801`
2. `383849116272497`
3. `2317142971864047`
4. `thaisolarcell`
5. `1671213103178339`
6. `429829328127055`

### Telegram Format (/wbuyer) & Admin Alert (/fbuyer):
⚠️ **ห้ามเปลี่ยนรูปแบบนี้ถ้า Tibodin ไม่ได้บอก!**

```
🟢 พบ Buyer Leads ใหม่!
⏰ เมื่อ: HH:MM (UTC+7)
📊 พบ: X โพส
👥 Workers: 3 ตัว

💡 พิมพ์ /wbuyer เพื่อ export CSV

━━━━━━━━━━━━━━━━━━━━━━
1. 🟢 [Reason] score:X / เวลาโพสเมื่อ X นาที
 📝 "message preview..."
 🔗 url

2. 🟢 ...
```

### Keyword Filter (ai_buyer_filter.py):
- คำว่า "หาช่าง" → MEDIUM (+3)
- Score 0-10 based on buyer intent

### Dataimpulse Proxy (2026-04-23):
- Type: SOCKS5
- Server: gw.dataimpulse.com:10000
- Status: ✅ Working - Found posts in all 6 groups
- Lead count: 0 (no buyer leads found)

### Scroll: Random 8-20 scrolls per group (upgraded!)

### New Features:
- ✅ admin_alerts.py - Telegram alert system for admin
  - alert_cookie_expired() - Cookie หมดอายุ
  - alert_proxy_expired() - Proxy หมดอายุ
  - alert_login_failed() - Login ล้มเหลว
  - alert_scraper_error() - Error ทั่วไป
  - alert_fbuyer_result() - แจ้งผล /fbuyer ทุกครั้ง
- ✅ cron_fbuyer.sh - Loop script
  - Usage: ./cron_fbuyer.sh X.Y
  - X.Y = X hours Y minutes (e.g., 0.10 = 10 min, 1.0 = 1 hour)
  - รัน /fbuyer ทุก 5 นาที → จบ → /wbuyer

---

## 🆕 Local LLM (Ollama) - Ready

### Installed: 2026-04-22
- Ollama installed at `/usr/local/bin/ollama`
- Ollama server running on port 11434

### Available Models:
| Model | Size | Status |
|-------|------|--------|
| qwen2.5:7b | 4.7GB | ✅ Ready |
| qwen2.5:14b | 9.0GB | ✅ Ready |
| deepseek-coder:6.7b | 3.8GB | ✅ Ready |
| llama3.1:8b | 4.9GB | ✅ Ready (NEW!) |

### API Endpoint:
```
http://localhost:11434
```