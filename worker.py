import sqlite3
import time
import os
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'kanban.db')

POLL_INTERVAL = 10

def claim_task(conn, task):
    now = datetime.utcnow().isoformat()
    cur = conn.cursor()
    cur.execute('UPDATE tasks SET status=?, updated_at=? WHERE id=?', ('in_progress', now, task['id']))
    cur.execute('INSERT INTO audit (task_id,event,payload,created_at) VALUES (?,?,?,?)',
                (task['id'],'claimed_by_jarvis','',now))
    conn.commit()
    print(f"[worker] Claimed task {task['id']} - {task['title']}")
    # TODO: Post to Discord channel via assistant (we will send a message when processing)

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
