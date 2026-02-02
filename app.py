import os
import sqlite3
from flask import Flask, g, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'kanban.db')
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    cur = db.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT NOT NULL DEFAULT 'backlog',
        labels TEXT,
        created_at TEXT,
        updated_at TEXT
    )''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER,
        filename TEXT,
        path TEXT,
        uploaded_at TEXT
    )''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER,
        event TEXT,
        payload TEXT,
        created_at TEXT
    )''')
    db.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tasks', methods=['GET','POST'])
def tasks():
    db = get_db()
    cur = db.cursor()
    if request.method == 'POST':
        data = request.json
        title = data.get('title')
        description = data.get('description','')
        labels = ','.join(data.get('labels',[])) if data.get('labels') else ''
        now = datetime.utcnow().isoformat()
        cur.execute('INSERT INTO tasks (title,description,labels,created_at,updated_at) VALUES (?,?,?,?,?)',
                    (title,description,labels,now,now))
        task_id = cur.lastrowid
        cur.execute('INSERT INTO audit (task_id,event,payload,created_at) VALUES (?,?,?,?)',
                    (task_id,'created','',now))
        db.commit()
        return jsonify({'id':task_id}), 201
    else:
        rows = cur.execute('SELECT * FROM tasks ORDER BY id DESC').fetchall()
        tasks = [dict(r) for r in rows]
        return jsonify(tasks)

@app.route('/api/tasks/<int:task_id>', methods=['GET','PUT'])
def task_detail(task_id):
    db = get_db(); cur = db.cursor()
    if request.method=='PUT':
        data = request.json
        status = data.get('status')
        labels = ','.join(data.get('labels',[])) if data.get('labels') else None
        now = datetime.utcnow().isoformat()
        if status:
            cur.execute('UPDATE tasks SET status=?, updated_at=? WHERE id=?', (status,now,task_id))
            cur.execute('INSERT INTO audit (task_id,event,payload,created_at) VALUES (?,?,?,?)',
                        (task_id,'status_change',status,now))
        if labels is not None:
            cur.execute('UPDATE tasks SET labels=?, updated_at=? WHERE id=?', (labels,now,task_id))
        db.commit()
        return jsonify({'ok':True})
    else:
        row = cur.execute('SELECT * FROM tasks WHERE id=?',(task_id,)).fetchone()
        if not row:
            return jsonify({'error':'not found'}),404
        attachments = cur.execute('SELECT id,filename,uploaded_at FROM attachments WHERE task_id=?',(task_id,)).fetchall()
        audits = cur.execute('SELECT event,payload,created_at FROM audit WHERE task_id=? ORDER BY id DESC',(task_id,)).fetchall()
        out = dict(row)
        out['attachments'] = [dict(a) for a in attachments]
        out['audit'] = [dict(a) for a in audits]
        return jsonify(out)

@app.route('/api/tasks/<int:task_id>/attach', methods=['POST'])
def attach(task_id):
    if 'file' not in request.files:
        return jsonify({'error':'no file'}),400
    f = request.files['file']
    fn = f.filename
    now = datetime.utcnow().isoformat()
    path = os.path.join(UPLOAD_DIR, f"{int(datetime.utcnow().timestamp())}_{fn}")
    f.save(path)
    db = get_db(); cur = db.cursor()
    cur.execute('INSERT INTO attachments (task_id,filename,path,uploaded_at) VALUES (?,?,?,?)', (task_id,fn,path,now))
    cur.execute('INSERT INTO audit (task_id,event,payload,created_at) VALUES (?,?,?,?)',
                (task_id,'attached',fn,now))
    db.commit()
    return jsonify({'ok':True})

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)

@app.route('/api/audit', methods=['GET'])
def audit_list():
    db = get_db(); cur = db.cursor()
    rows = cur.execute('SELECT * FROM audit ORDER BY id DESC LIMIT 200').fetchall()
    return jsonify([dict(r) for r in rows])

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=8080)
