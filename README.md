Kanban MVP (headless)

Quick start (on the EC2 host)

1) Create a Python venv and install deps
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2) Initialize the DB and start the web server (localhost only)
   export FLASK_APP=app.py
   flask run --host=127.0.0.1 --port=8080

3) In another shell, run the background worker that watches for To-Do tasks
   source .venv/bin/activate
   python worker.py

Access
- The app runs on localhost:8080 on the EC2 host. Use SSH tunnel from your Mac:
  ssh -i ~/Downloads/openclaw-key.pem -L 8080:localhost:8080 ubuntu@18.221.162.206

- Open http://localhost:8080 in your browser.

Design notes
- SQLite DB at kanban.db tracks tasks, attachments, and audit events.
- Worker polls the DB every 10s and claims tasks moved to "todo" (status='todo'). It moves them to "in_progress" and creates a system comment.
- Attachments are stored in uploads/ and tracked in the DB.
- Notifications: the system writes notifications to the audit log; I will also post to Discord channel `pm-updates` when I process tasks (I will implement posting from the assistant side — you will see those posts in the channel).

Next steps
- If you want the service to run as a daemon, I can create a systemd service or docker-compose manifest.
- If you want HTTPS public access, we can add nginx + Let's Encrypt.

