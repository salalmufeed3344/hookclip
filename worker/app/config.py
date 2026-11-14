"""Hookclip worker — config from environment, nothing hardcoded.

Every integration is optional in local dev: missing keys fall back to a
stub/local implementation and the app still runs. Deploy needs the keys
listed in .env.example.
"""
import os
import ssl
from pathlib import Path


def ca_bundle_path():
    """System CA bundle. The sandbox egress proxy MITMs TLS with a CA that
    lives in the system bundle but NOT in certifi's — yt-dlp / requests /
    httpx all default to certifi, so every outbound tool call must be
    pointed at this bundle explicitly. On DeployXA the system bundle is
    the normal one, so this is harmless there too."""
    for candidate in (
        os.environ.get("SSL_CERT_FILE", ""),
        "/etc/ssl/certs/ca-certificates.crt",
    ):
        if candidate and Path(candidate).exists():
            return candidate
    return None


def ssl_context():
    """An SSL context that trusts the system bundle (see ca_bundle_path)."""
    bundle = ca_bundle_path()
    return ssl.create_default_context(cafile=bundle) if bundle else ssl.create_default_context()


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


# Load a local .env file if present (dev convenience; deploy uses real env).
def _load_dotenv() -> None:
    path = Path(__file__).resolve().parent.parent / ".env"
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()

DATA_DIR = Path(_env("DATA_DIR", "./data")).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "hookclip.db"
SOURCE_DIR = DATA_DIR / "sources"
CLIP_DIR = DATA_DIR / "clips"
SOURCE_DIR.mkdir(parents=True, exist_ok=True)
CLIP_DIR.mkdir(parents=True, exist_ok=True)

WAITLIST_ADMIN_TOKEN = _env("WAITLIST_ADMIN_TOKEN")

GROQ_API_KEY = _env("GROQ_API_KEY")
GEMINI_API_KEY = _env("GEMINI_API_KEY")
GEMINI_MODEL = _env("GEMINI_MODEL", "gemini-2.5-flash-lite")

TWITCH_CLIENT_ID = _env("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = _env("TWITCH_CLIENT_SECRET")

SUPABASE_URL = _env("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = _env("SUPABASE_SERVICE_ROLE_KEY")

R2_ENDPOINT = _env("R2_ENDPOINT")
R2_ACCESS_KEY_ID = _env("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = _env("R2_SECRET_ACCESS_KEY")
R2_BUCKET = _env("R2_BUCKET", "hookclip")

PADDLE_API_KEY = _env("PADDLE_API_KEY")
PADDLE_WEBHOOK_SECRET = _env("PADDLE_WEBHOOK_SECRET")
PADDLE_STARTER_PRICE_ID = _env("PADDLE_STARTER_PRICE_ID")
PADDLE_PRO_PRICE_ID = _env("PADDLE_PRO_PRICE_ID")
PADDLE_PACK_PRICE_ID = _env("PADDLE_PACK_PRICE_ID")

RESEND_API_KEY = _env("RESEND_API_KEY")

CORS_ORIGINS = [o for o in _env(
    "CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",") if o]

# Plans (pricing.md) — credits are source-minutes.
PLANS = {
    "free": {"minutes_per_month": 60, "watermark": True, "max_height": 720},
    "starter": {"minutes_per_month": 150, "watermark": False, "max_height": 1080},
    "pro": {"minutes_per_month": 400, "watermark": False, "max_height": 1080},
}
CREDIT_PACK_MINUTES = 100

MAX_SOURCE_HOURS = 10
MAX_SOURCE_GB = 30

VERSION = "0.1.0-p0"
