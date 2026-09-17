"""AI Chatbox — Flask app entry point."""
import logging
import os
import secrets
import warnings

from flask import Flask
from flask_session import Session as FlaskSession

warnings.filterwarnings("ignore", message=".*Accessing .*__path__.*")

from src.config import (  # noqa: E402
    APP_DEBUG,
    APP_HOST,
    APP_PORT,
    MAX_CONTENT_LENGTH_MB,
    SECRET_KEY,
    SESSION_CLEANUP_INTERVAL,
)
from src.utils.logging_setup import setup_logging  # noqa: E402

setup_logging()
logger = logging.getLogger(__name__)


def _ensure_secret_key() -> str:
    """Return SECRET_KEY from config, or auto-generate and persist to .env."""
    if SECRET_KEY:
        return SECRET_KEY
    generated = secrets.token_hex(32)
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    try:
        with open(env_path, encoding="utf-8") as f:
            content = f.read()
        if "SECRET_KEY=" in content:
            # Handle both CRLF and LF .env files (CRLF files would otherwise
            # get a duplicate SECRET_KEY line appended instead of replaced)
            content = content.replace("SECRET_KEY=\r\n", f"SECRET_KEY={generated}\r\n", 1)
            content = content.replace("SECRET_KEY=\n", f"SECRET_KEY={generated}\n", 1)
        else:
            content += f"\nSECRET_KEY={generated}\n"
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("Auto-generated SECRET_KEY and saved to .env")
    except Exception as e:
        logger.warning(f"Could not persist SECRET_KEY to .env: {e}")
    return generated

# Global performance tracker (accessible from routes)
perf_middleware = None


def _cleanup_old_sessions():
    """Delete session files older than PERMANENT_SESSION_LIFETIME."""
    from datetime import datetime, timedelta

    session_dir = ".flask_sessions"
    if not os.path.isdir(session_dir):
        return
    cutoff = datetime.now() - timedelta(days=7)
    count = 0
    for f in os.listdir(session_dir):
        path = os.path.join(session_dir, f)
        if os.path.isfile(path):
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(path))
                if mtime < cutoff:
                    os.remove(path)
                    count += 1
            except OSError:
                pass
    if count:
        logger.info("Session cleanup: removed %d expired sessions", count)


def _cleanup_stale_caches():
    """One-shot cleanup of stale disk caches on app startup."""
    from src.utils.cache import CACHE_DIR

    if not CACHE_DIR.exists():
        return
    for subdir in CACHE_DIR.iterdir():
        if subdir.is_dir():
            count = 0
            cutoff_ts = __import__("time").time() - 5 * 86400  # 5 days
            for p in subdir.glob("*.json"):
                try:
                    if os.path.getmtime(p) < cutoff_ts:
                        p.unlink(missing_ok=True)
                        count += 1
                except OSError:
                    pass
            # Also enforce max_entries=300
            files = sorted(subdir.glob("*.json"), key=os.path.getmtime)
            while len(files) > 300:
                files.pop(0).unlink(missing_ok=True)
                count += 1
            if count:
                logger.info("Startup cache cleanup: %s removed %d files", subdir.name, count)


def create_app() -> Flask:
    global perf_middleware

    app = Flask(__name__)
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.config["SECRET_KEY"] = _ensure_secret_key()
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_FILE_DIR"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".flask_sessions")
    from datetime import timedelta
    app.config["SESSION_PERMANENT"] = True
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH_MB * 1024 * 1024
    FlaskSession(app)

    # Startup cache cleanup
    try:
        _cleanup_stale_caches()
    except Exception as e:
        logger.warning("Startup cache cleanup failed: %s", e)

    # Session cleanup scheduler (background thread, every N hours)
    # + Customer Excel report (every N minutes, single overwritten file)
    import atexit
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        _scheduler = BackgroundScheduler(daemon=True)
        _scheduler.add_job(_cleanup_old_sessions, "interval", hours=SESSION_CLEANUP_INTERVAL)
        try:
            from src.config import CUSTOMER_EXCEL_ENABLED, CUSTOMER_EXCEL_INTERVAL_MINUTES
            from src.services.customer_excel_export import run_scheduled_export
            if CUSTOMER_EXCEL_ENABLED:
                interval_min = max(1, min(int(CUSTOMER_EXCEL_INTERVAL_MINUTES), 1440))
                _scheduler.add_job(
                    run_scheduled_export, "interval", minutes=interval_min,
                    id="customer_excel_export", replace_existing=True,
                )
                logger.info("Customer Excel scheduler started (every %d min)", interval_min)
        except Exception as e:
            logger.warning("Customer Excel scheduler not started: %s", e)
        _scheduler.start()
        atexit.register(lambda: _scheduler.shutdown(wait=False))
        logger.info("Session cleanup scheduler started (every %dh)", SESSION_CLEANUP_INTERVAL)
    except ImportError:
        logger.warning("apscheduler not installed — session cleanup disabled. Install: pip install apscheduler")

    # Xuat Excel lan dau ngay khi khoi dong (delay nhe de DB init xong)
    try:
        from src.config import CUSTOMER_EXCEL_ENABLED  # noqa: N811
        if CUSTOMER_EXCEL_ENABLED:
            import threading as _th

            def _first_excel_export():
                try:
                    from src.services.customer_excel_export import run_scheduled_export
                    run_scheduled_export()
                except Exception as e:
                    logger.warning("Initial Excel export failed: %s", e)

            _th.Timer(10.0, _first_excel_export).start()
    except Exception:
        pass

    # Performance monitoring
    from src.utils.performance import PerformanceMiddleware
    perf_middleware = PerformanceMiddleware(app, window_seconds=300)

    # Register Admin Blueprint
    from admin import admin_bp
    app.register_blueprint(admin_bp)

    # Register API routes
    from src.routes import api_bp, init_routes
    app.register_blueprint(api_bp)

    # Register SAG routes
    from src.config import settings as app_settings
    if app_settings.sag_enabled:
        from src.routes.sag_api import init_sag_routes, sag_bp
        app.register_blueprint(sag_bp)
        init_sag_routes()
        logger.info("SAG routes registered")

    # Initialize RAGChatbot and inject into routes
    from src.services import RAGChatbot
    rag = RAGChatbot()
    init_routes(rag)

    # Store RAG in app extensions for SAG routes
    app.extensions["rag"] = rag

    # Initialize ModelDiscovery and inject into routers
    from src.config import settings
    if settings.model_discovery_enabled:
        _start_model_discovery(rag, app)

    return app


def _start_model_discovery(rag, app):
    """Create ModelDiscovery and inject it into LLM and Embedding routers."""
    from src.config import settings
    from src.utils.model_discovery import ModelDiscovery

    # Collect all endpoint URLs
    all_urls = []
    if settings.llm_endpoints:
        for ep in settings.llm_endpoints.split(","):
            parts = ep.strip().split("|")
            if parts:
                all_urls.append(parts[0].strip())
    if settings.embedding_endpoints:
        for ep in settings.embedding_endpoints.split(","):
            parts = ep.strip().split("|")
            if parts:
                all_urls.append(parts[0].strip())

    # Also add the default LM Studio host if not already included
    default_host = settings.lm_studio_host.removesuffix("/v1").rstrip("/")
    if default_host and default_host not in all_urls:
        all_urls.append(default_host)

    if not all_urls:
        return

    discovery = ModelDiscovery(all_urls, poll_interval=settings.model_discovery_poll_interval)
    discovery.start()

    # Inject into LLM router
    if hasattr(rag, "llm_client") and hasattr(rag.llm_client, "router"):
        rag.llm_client.router.set_model_discovery(discovery)
        logger.info("ModelDiscovery: injected into LLM router")

    # Inject into embedding router
    if hasattr(rag, "embedding_manager"):
        em = rag.embedding_manager
        if hasattr(em, "_router") and em._router is not None:
            em._router.set_model_discovery(discovery)
            logger.info("ModelDiscovery: injected into embedding router")

    # Store reference for status endpoint
    app.extensions["model_discovery"] = discovery


app = create_app()

if __name__ == "__main__":
    app.run(host=APP_HOST, port=APP_PORT, debug=APP_DEBUG, threaded=True)
