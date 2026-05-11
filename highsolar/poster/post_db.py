#!/usr/bin/env python3
"""
Post Queue System - ระบบจัดการคิวโพสต์
- ป้องกันโพสซ้ำ
- คิวโพสต์ลำดับ
- รองรับ Cronjob
- เก็บ Engagement
"""
import sqlite3, json, time, sys
from datetime import datetime, timedelta

DB_FILE = '/root/.openclaw/workspace/highsolar/poster/post_db.sqlite'

def get_conn():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    
    # ตารางรูปภาพ
    c.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT UNIQUE NOT NULL,
            prompt TEXT,
            style TEXT,
            hash TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ตารางโพสต์ (เก็บ history)
    c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER UNIQUE NOT NULL,
            page_id TEXT,
            content TEXT,
            image_path TEXT,
            content_hash TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ตารางคิวโพสต์ (รอโพส)
    c.execute('''
        CREATE TABLE IF NOT EXISTS post_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            image_path TEXT,
            page_id TEXT,
            priority INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            scheduled_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            started_at TEXT,
            completed_at TEXT,
            error_message TEXT
        )
    ''')
    
    # ตาราง Engagement
    c.execute('''
        CREATE TABLE IF NOT EXISTS engagements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            page_id TEXT,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            fetched_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(post_id)
        )
    ''')
    
    # Index สำหรับความเร็ว
    c.execute('CREATE INDEX IF NOT EXISTS idx_queue_status ON post_queue(status)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_queue_priority ON post_queue(priority DESC, created_at)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_posts_hash ON posts(content_hash)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_engagement_post ON engagements(post_id)')
    
    conn.commit()
    conn.close()

# ==================== IMAGE ====================

def save_image(image_path, prompt=None, style=None):
    """บันทึกรูปภาพ"""
    import hashlib
    with open(image_path, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute(
            'INSERT OR IGNORE INTO images (image_path, prompt, style, hash) VALUES (?, ?, ?, ?)',
            (image_path, prompt, style, file_hash)
        )
        conn.commit()
        image_id = c.lastrowid
        conn.close()
        return image_id
    except Exception as e:
        conn.close()
        return None

def image_exists(image_path):
    """เช็คว่ารูปภาพเคยเจนไปหรือยัง"""
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT id FROM images WHERE image_path = ?', (image_path,))
    result = c.fetchone()
    conn.close()
    return result is not None

def find_similar_image(prompt_keyword, limit=5):
    """ค้นหารูปภาพคล้ายๆ กัน"""
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'SELECT id, image_path, prompt, created_at FROM images WHERE prompt LIKE ? ORDER BY created_at DESC LIMIT ?',
        (f'%{prompt_keyword}%', limit)
    )
    results = c.fetchall()
    conn.close()
    return results

def get_all_images(limit=50):
    """ดึงรูปภาพทั้งหมด"""
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT id, image_path, prompt, style, hash, created_at FROM images ORDER BY created_at DESC LIMIT ?', (limit,))
    results = c.fetchall()
    conn.close()
    return results

# ==================== CONTENT HASH ====================

def hash_content(content):
    """สร้าง hash จาก content เพื่อเช็คซ้ำ"""
    import hashlib
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def is_duplicate_content(content):
    """เช็คว่า content นี้เคยโพสไปหรือยัง"""
    h = hash_content(content)
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT post_id FROM posts WHERE content_hash = ?', (h,))
    result = c.fetchone()
    conn.close()
    return result is not None, result[0] if result else None

# ==================== QUEUE ====================

def add_to_queue(content, image_path=None, page_id='61588849713937', priority=0, scheduled_at=None):
    """เพิ่มโพสต์เข้าคิว"""
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute(
            '''INSERT INTO post_queue (content, image_path, page_id, priority, scheduled_at) 
               VALUES (?, ?, ?, ?, ?)''',
            (content, image_path, page_id, priority, scheduled_at)
        )
        conn.commit()
        queue_id = c.lastrowid
        conn.close()
        return queue_id
    except Exception as e:
        conn.close()
        return None

def get_next_in_queue():
    """ดึงโพสต์ถัดไปจากคิว (priority สูงสุด ก่อน)"""
    conn = get_conn()
    c = conn.cursor()
    
    # ดึงโพสต์ที่ status='pending' และ scheduled_at <= now หรือไม่มี scheduled_at
    c.execute('''
        SELECT id, content, image_path, page_id, priority, scheduled_at, created_at
        FROM post_queue 
        WHERE status = 'pending' 
          AND (scheduled_at IS NULL OR scheduled_at <= datetime('now'))
        ORDER BY priority DESC, created_at ASC
        LIMIT 1
    ''')
    result = c.fetchone()
    conn.close()
    return result

def mark_queue_started(queue_id):
    """标记队列项目已开始"""
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "UPDATE post_queue SET status='in_progress', started_at=datetime('now') WHERE id=?",
        (queue_id,)
    )
    conn.commit()
    conn.close()

def mark_queue_completed(queue_id, post_id=None):
    """标记队列项目已完成"""
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "UPDATE post_queue SET status='completed', completed_at=datetime('now') WHERE id=?",
        (queue_id,)
    )
    conn.commit()
    conn.close()

def mark_queue_failed(queue_id, error):
    """标记队列项目失败"""
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "UPDATE post_queue SET status='failed', error_message=? WHERE id=?",
        (error, queue_id)
    )
    conn.commit()
    conn.close()

def get_queue_stats():
    """ดูสถิติคิว"""
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        SELECT status, COUNT(*) FROM post_queue GROUP BY status
    ''')
    results = c.fetchall()
    stats = {row[0]: row[1] for row in results}
    conn.close()
    return stats

def get_queue_list(status='all', limit=50):
    """ดูรายการคิว"""
    conn = get_conn()
    c = conn.cursor()
    if status == 'all':
        c.execute('SELECT id, content[:50], page_id, priority, status, scheduled_at, created_at FROM post_queue ORDER BY priority DESC, created_at DESC LIMIT ?', (limit,))
    else:
        c.execute('SELECT id, content[:50], page_id, priority, status, scheduled_at, created_at FROM post_queue WHERE status=? ORDER BY priority DESC, created_at DESC LIMIT ?', (status, limit))
    results = c.fetchall()
    conn.close()
    return results

def remove_from_queue(queue_id):
    """ลบโพสต์ออกจากคิว"""
    conn = get_conn()
    c = conn.cursor()
    c.execute('DELETE FROM post_queue WHERE id=?', (queue_id,))
    conn.commit()
    conn.close()
    return True

# ==================== POSTS HISTORY ====================

def save_post(post_id, page_id, content, image_path=None):
    """บันทึกโพสต์ที่เคยโพส (history)"""
    content_hash = hash_content(content)
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute(
            'INSERT INTO posts (post_id, page_id, content, image_path, content_hash) VALUES (?, ?, ?, ?, ?)',
            (post_id, page_id, content, image_path, content_hash)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        return False

def get_all_posts(limit=50):
    """ดึงโพสต์ทั้งหมด"""
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT post_id, page_id, content, image_path, content_hash, created_at FROM posts ORDER BY created_at DESC LIMIT ?', (limit,))
    results = c.fetchall()
    conn.close()
    return results

def search_posts(keyword):
    """ค้นหาโพสต์"""
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT post_id, page_id, content, image_path, created_at FROM posts WHERE content LIKE ? ORDER BY created_at DESC', (f'%{keyword}%',))
    results = c.fetchall()
    conn.close()
    return results

# ==================== ENGAGEMENT ====================

def save_engagement(post_id, page_id, likes=0, comments=0, shares=0, views=0):
    """บันทึก engagement ของโพสต์"""
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'INSERT INTO engagements (post_id, page_id, likes, comments, shares, views) VALUES (?, ?, ?, ?, ?, ?)',
        (post_id, page_id, likes, comments, shares, views)
    )
    conn.commit()
    conn.close()

def get_engagement(post_id):
    """ดึง engagement ของโพสต์"""
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'SELECT post_id, likes, comments, shares, views, fetched_at FROM engagements WHERE post_id=? ORDER BY fetched_at DESC LIMIT 1',
        (post_id,)
    )
    result = c.fetchone()
    conn.close()
    return result

def get_all_engagements(limit=50):
    """ดึง engagement ทั้งหมด"""
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        SELECT e.post_id, e.likes, e.comments, e.shares, e.views, e.fetched_at, p.content
        FROM engagements e
        LEFT JOIN posts p ON e.post_id = p.post_id
        ORDER BY e.fetched_at DESC LIMIT ?
    ''', (limit,))
    results = c.fetchall()
    conn.close()
    return results

def get_top_posts(limit=10, by='likes'):
    """ดึงโพสต์ยอดนิยม"""
    conn = get_conn()
    c = conn.cursor()
    c.execute(f'''
        SELECT e.post_id, e.likes, e.comments, e.shares, e.views, p.content, e.fetched_at
        FROM engagements e
        LEFT JOIN posts p ON e.post_id = p.post_id
        ORDER BY e.{by} DESC LIMIT ?
    ''', (limit,))
    results = c.fetchall()
    conn.close()
    return results

# ==================== STATS ====================

def get_stats():
    """ดูสถิติทั้งหมด"""
    conn = get_conn()
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM images')
    img_count = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM posts')
    post_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM post_queue WHERE status='pending'")
    queue_pending = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM post_queue WHERE status='completed'")
    queue_completed = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM engagements')
    engagement_count = c.fetchone()[0]
    
    conn.close()
    return {
        'images': img_count,
        'posts': post_count,
        'queue_pending': queue_pending,
        'queue_completed': queue_completed,
        'engagements': engagement_count
    }

# ==================== CLI ====================

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('=== Post Queue System ===')
        print('Commands:')
        print('  python3 post_db.py stats                    - ดูสถิติทั้งหมด')
        print('  python3 post_db.py list_queue              - ดูคิวโพสต์')
        print('  python3 post_db.py list_posts             - ดูโพสต์ทั้งหมด')
        print('  python3 post_db.py add_queue <content>     - เพิ่มคิว')
        print('  python3 post_db.py next_queue             - ดึงโพสต์ถัดไป')
        print('  python3 post_db.py top_posts              - โพสต์ยอดนิยม')
        print('  python3 post_db.py search <keyword>       - ค้นหาโพสต์')
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == 'stats':
        s = get_stats()
        print(f'รูปภาพ: {s["images"]} รูป')
        print(f'โพสต์ที่เคยโพส: {s["posts"]} โพสต์')
        print(f'คิวรอโพส: {s["queue_pending"]} รายการ')
        print(f'คิวเสร็จแล้ว: {s["queue_completed"]} รายการ')
        print(f'Engagement records: {s["engagements"]} รายการ')
        
        qs = get_queue_stats()
        print(f'\\n=== Queue Status ===')
        for status, count in qs.items():
            print(f'  {status}: {count}')
    
    elif cmd == 'list_queue':
        items = get_queue_list()
        print(f'=== คิวโพสต์ ({len(items)} รายการ) ===')
        for item in items:
            print(f"[{item[0]}] Status: {item[4]} | Priority: {item[3]}")
            print(f"    Content: {item[1]}...")
            print(f"    Created: {item[6]}")
            print()
    
    elif cmd == 'list_posts':
        posts = get_all_posts()
        print(f'=== โพสต์ทั้งหมด ({len(posts)} โพสต์) ===')
        for p in posts:
            eng = get_engagement(p[0])
            print(f"[#{p[0]}] Page: {p[1]} | Likes: {eng[1] if eng else 0} | Comments: {eng[2] if eng else 0}")
            print(f"    Content: {p[2][:80]}...")
            print(f"    สร้าง: {p[5]}")
            print()
    
    elif cmd == 'add_queue' and len(sys.argv) > 2:
        content = sys.argv[2].replace('\\n', '\n')
        qid = add_to_queue(content)
        print(f'เพิ่มเข้าคิวสำเร็จ: #{qid}')
    
    elif cmd == 'next_queue':
        item = get_next_in_queue()
        if item:
            print(f'=== โพสต์ถัดไปในคิว ===')
            print(f'Queue ID: {item[0]}')
            print(f'Content: {item[1][:100]}...')
            print(f'Image: {item[2]}')
            print(f'Page: {item[3]}')
            print(f'Priority: {item[4]}')
            print(f'Scheduled: {item[5]}')
        else:
            print('ไม่มีโพสต์ในคิว')
    
    elif cmd == 'top_posts':
        posts = get_top_posts(limit=10, by='likes')
        print('=== โพสต์ยอดนิยม (by likes) ===')
        for p in posts:
            print(f'[#{p[0]}] Likes: {p[1]} | Comments: {p[2]} | Shares: {p[3]} | Views: {p[4]}')
            print(f'    Content: {p[5][:80]}...')
            print()
    
    elif cmd == 'search' and len(sys.argv) > 2:
        kw = sys.argv[2]
        posts = search_posts(kw)
        print(f'=== ผลการค้นหา: "{kw}" ({len(posts)} ผลลัพธ์) ===')
        for p in posts:
            print(f'[#{p[0]}] {p[2][:100]}...')
    
    else:
        print('ไม่รู้จักคำสั่ง:', cmd)