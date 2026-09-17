#!/usr/bin/env python
"""AI Chatbox Production Launcher — auto-selects the best WSGI server.

Windows:  waitress (pure-Python, no fcntl dependency)
Linux:    gunicorn with gevent (best performance)
Fallback: flask built-in (dev only)

Usage:
    python run_production.py
    # Or with custom host/port:
    python run_production.py --host 0.0.0.0 --port 8080
"""
import argparse
import os
import sys


def run_waitress(host: str, port: int, threads: int):
    """Run with waitress (Windows-compatible)."""
    try:
        from waitress import create_server
    except ImportError:
        print("ERROR: waitress not installed. Install it:")
        print("  pip install waitress")
        sys.exit(1)

    from app import app
    print(f"Starting Waitress server on {host}:{port} ({threads} threads)")
    server = create_server(
        app,
        host=host,
        port=port,
        threads=threads,
        channel_timeout=120,
        cleanup_interval=30,
    )
    server.run()


def run_gunicorn(host: str, port: int):
    """Run with gunicorn (Linux production)."""
    import subprocess
    bind = f"{host}:{port}"
    print(f"Starting Gunicorn on {bind}")
    cmd = [
        sys.executable, "-m", "gunicorn", "app:app",
        "-c", "gunicorn.conf.py",
        "--bind", bind,
    ]
    subprocess.run(cmd, check=True)


def run_flask(host: str, port: int, debug: bool = False):
    """Run with Flask built-in server (dev fallback)."""
    from app import app
    print(f"Starting Flask dev server on {host}:{port}")
    app.run(host=host, port=port, debug=debug, threaded=True)


def main():
    parser = argparse.ArgumentParser(description="AI Chatbox Production Launcher")
    parser.add_argument("--host", default=os.environ.get("APP_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("APP_PORT", "5000")))
    parser.add_argument(
        "--threads", type=int, default=int(os.environ.get("WAITRESS_THREADS", "200")),
        help="Worker threads (waitress only)",
    )
    parser.add_argument("--server", choices=["auto", "waitress", "gunicorn", "flask"], default="auto")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    if args.server == "auto":
        if sys.platform == "win32":
            args.server = "waitress"
        else:
            args.server = "gunicorn"
        print(f"Auto-detected platform: {sys.platform} -> using {args.server}")

    if args.server == "waitress":
        run_waitress(args.host, args.port, args.threads)
    elif args.server == "gunicorn":
        run_gunicorn(args.host, args.port)
    elif args.server == "flask":
        run_flask(args.host, args.port, args.debug)


if __name__ == "__main__":
    main()
