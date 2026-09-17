#!/usr/bin/env python3
"""AI Chatbox Launcher - Flask Backend"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_lm_studio():
    """Check if LM Studio is running."""
    print("Checking LM Studio connection...")
    try:
        import requests
        r = requests.get("http://localhost:1234/v1/models", timeout=5)
        if r.status_code == 200:
            print("  LM Studio: OK")
            return True
        else:
            print("  LM Studio: Not responding properly")
            return False
    except Exception:
        print("  WARNING: LM Studio is not running")
        print("  Please start LM Studio and load your models")
        return False


def main():
    print("=" * 50)
    print("AI Chatbox - RAG System Launcher")
    print("=" * 50)
    print()

    lm_ok = check_lm_studio()
    if not lm_ok:
        print()
        print("Continue anyway? (Ctrl+C to stop)")
        try:
            input("Press Enter to continue...")
        except KeyboardInterrupt:
            print("\nAborted.")
            sys.exit(0)

    print()

    # Detect mode: --prod flag or APP_ENV=production
    mode = os.environ.get("APP_ENV", "development")
    use_prod = "--prod" in sys.argv or mode == "production"

    if use_prod:
        print("Starting in PRODUCTION mode with Gunicorn...")
        print("Press Ctrl+C to stop")
        print()
        if sys.platform == "win32":
            import subprocess
            subprocess.run([sys.executable, "-m", "gunicorn", "-c", "gunicorn.conf.py", "app:app"])
        else:
            os.execvp(sys.executable, [sys.executable, "-m", "gunicorn", "-c", "gunicorn.conf.py", "app:app"])
    else:
        print("Starting in DEVELOPMENT mode (Flask dev server)...")
        print("Starting Flask app on http://localhost:5000")
        print("Press Ctrl+C to stop")
        print()
        if sys.platform == "win32":
            import subprocess
            subprocess.run([sys.executable, "app.py"])
        else:
            os.execvp(sys.executable, [sys.executable, "app.py"])


if __name__ == "__main__":
    main()
