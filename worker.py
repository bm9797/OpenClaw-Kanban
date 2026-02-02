import sqlite3
import time
import os
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'kanban.db')

POLL_INTERVAL = 10
DISCORD_WEBHOOK = os.environ.get('DISCORD_WEBHOOK')  # set locally if desired

def post_discord(message):
    url = DISCORD_WEBHOOK
    if not url:
        return
    try:
        # import requests lazily so missing package doesn't crash container at startup
        import requests
        requests.post(url, json={"content": message}, timeout=5)
    except Exception as e:
        print(f"[worker] Discord post failed: {e}")

def claim_task(conn, task):
    now = datetime.utcnow().isoformat()
    cur = conn.cursor()
    cur.execute('UPDATE tasks SET status=?, updated_at=? WHERE id=?', ('in_progress', now, task['id']))
    cur.execute('INSERT INTO audit (task_id,event,payload,created_at) VALUES (?,?,?,?)',
                (task['id'],'claimed_by_jarvis','',now))
    conn.commit()
    msg = f"Jarvis claimed task #{task['id']}: {task['title']}"
    print(f"[worker] {msg}")
    post_discord(msg)

def poll_loop():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    print("Worker started, polling for tasks...")
    try:
        while True:
            cur = conn.cursor()
            rows = cur.execute("SELECT * FROM tasks WHERE status='todo' ORDER BY id ASC").fetchall()
            for r in rows:
                task = dict(r)
                claim_task(conn, task)
            time.sleep(POLL_INTERVAL)
    finally:
        conn.close()

if __name__=='__main__':
    poll_loop()
