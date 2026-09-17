"""Waitress configuration for Windows production deployment.

Waitress is a pure-Python WSGI server that works on Windows without
requiring fcntl or Unix-specific modules.

Usage:
    python -m waitress --host=0.0.0.0 --port=5000 app:app
    # Or use this config:
    waitress-serve --host=0.0.0.0 --port=5000 app:app
"""
import os

# Server settings
host = os.environ.get("WAITRESS_HOST", "0.0.0.0")
port = int(os.environ.get("WAITRESS_PORT", "5000"))

# Thread settings (waitress uses its own thread pool)
# 1000 concurrent users: each SSE chat stream holds a thread for its lifetime
# (5-30s), so the pool must be large. 200 threads ≈ 200 concurrent streams
# per instance; run 2-4 instances behind nginx for more.
threads = int(os.environ.get("WAITRESS_THREADS", "200"))
channel_timeout = int(os.environ.get("WAITRESS_CHANNEL_TIMEOUT", "300"))
cleanup_interval = 30

# Buffer settings
recv_bytes = 65536
send_bytes = 72000
map_size = 16777216
