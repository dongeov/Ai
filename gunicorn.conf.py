"""Gunicorn configuration for AI Chatbox production deployment.

NOTE: gunicorn requires fcntl (Unix-only). On Windows, use waitress instead:
    python -m waitress --host=0.0.0.0 --port=5000 app:app

For Linux/Docker production: gunicorn with gevent (recommended).
For Windows production: waitress (auto-selected by run_production.py).
"""
import multiprocessing
import os
import sys

# Server socket
bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:5000")

# Worker processes
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))

# Worker class selection:
# - Windows: gthread (gevent requires libev, gunicorn fcntl requires Unix)
# - Linux: gevent (best async I/O concurrency)
if sys.platform == "win32":
    worker_class = "gthread"
    threads = int(os.environ.get("GUNICORN_THREADS", "8"))
else:
    worker_class = "gevent"
    worker_connections = 500

worker_tmp_dir = "/dev/shm" if os.path.exists("/dev/shm") else None

# Timeouts
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "300"))
graceful_timeout = 30
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info").lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "ai-chatbox"

# Server mechanics
preload_app = False
daemon = False
tmp_upload_dir = None


def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("AI Chatbox starting with %d workers (class=%s)", workers, worker_class)


def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)
