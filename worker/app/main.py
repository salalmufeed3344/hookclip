"""Hookclip worker API (FastAPI).

P0 routes: health, waitlist (Milestone 0), auth/credits stubs, Paddle stub.
Pipeline routes (projects/jobs/moments/clips/export) live in app/pipeline.py
and are registered here when the build reaches that milestone.
"""
import csv
import io
import re
import secrets
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, field_validator

from . import config, db, jobs
from .api import router as api_router

app = FastAPI(title="Hookclip worker", version=config.VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(api_router)

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
VALID_ROLES = {"streamer", "clipper", "both", "other"}


@app.on_event("startup")
def _startup():
    db.init_db()
    jobs.start_worker_thread()


@app.get("/health")
def health():
    with db.connect() as conn:
        queued = conn.execute(
            "SELECT COUNT(*) AS n FROM jobs WHERE stage IN ('queued','downloading',"
            "'transcribing','detecting','ranking','rendering')"
        ).fetchone()["n"]
        waitlist_n = conn.execute("SELECT COUNT(*) AS n FROM waitlist").fetchone()["n"]
    return {
        "status": "ok",
        "version": config.VERSION,
        "queue_depth": queued,
        "waitlist_count": waitlist_n,
        "integrations": {
            "groq": bool(config.GROQ_API_KEY),
            "gemini": bool(config.GEMINI_API_KEY),
            "twitch": bool(config.TWITCH_CLIENT_ID and config.TWITCH_CLIENT_SECRET),
            "supabase": bool(config.SUPABASE_URL),
            "r2": bool(config.R2_ENDPOINT),
            "paddle": bool(config.PADDLE_API_KEY),
        },
    }


# ---------------------------------------------------------------- waitlist
class WaitlistSignup(BaseModel):
    email: str
    role: str | None = None

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("not a valid email address")
        return v

    @field_validator("role")
    @classmethod
    def _role(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().lower()
        return v if v in VALID_ROLES else "other"


@app.post("/api/waitlist")
def waitlist_signup(body: WaitlistSignup):
    """Milestone 0: capture an email. Never loses a signup: the row is
    committed to SQLite before we answer. Duplicate email = same success
    response (no info leak, no error for the user)."""
    with db.connect() as conn:
        row = conn.execute(
            "SELECT id FROM waitlist WHERE email = ?", (body.email,)
        ).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO waitlist (email, role, created_at) VALUES (?, ?, ?)",
                (body.email, body.role, db.now_iso()),
            )
            conn.commit()
        position = conn.execute("SELECT COUNT(*) AS n FROM waitlist").fetchone()["n"]
    return {"ok": True, "position": position}


@app.get("/api/waitlist/count")
def waitlist_count():
    with db.connect() as conn:
        n = conn.execute("SELECT COUNT(*) AS n FROM waitlist").fetchone()["n"]
    return {"count": n}


@app.get("/api/waitlist/export", response_class=PlainTextResponse)
def waitlist_export(token: str = Query("")):
    """Owner export: GET /api/waitlist/export?token=<WAITLIST_ADMIN_TOKEN>.
    Returns CSV (email, role, created_at). No token configured -> 503."""
    if not config.WAITLIST_ADMIN_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="Waitlist export is not configured: set WAITLIST_ADMIN_TOKEN.",
        )
    if not token or not secrets.compare_digest(token, config.WAITLIST_ADMIN_TOKEN):
        raise HTTPException(status_code=401, detail="Invalid token.")
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT email, role, created_at FROM waitlist ORDER BY id"
        ).fetchall()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["email", "role", "created_at"])
    for r in rows:
        writer.writerow([r["email"], r["role"] or "", r["created_at"]])
    return PlainTextResponse(
        buf.getvalue(),
        headers={"Content-Disposition": "attachment; filename=hookclip-waitlist.csv"},
        media_type="text/csv",
    )


# ---------------------------------------------------------------- billing (stub)
@app.get("/api/billing/status")
def billing_status():
    """P0: Paddle is STUBBED. Checkout needs the owner's Paddle onboarding
    (business verification + price IDs). The credits ledger is real; only the
    money movement is stubbed."""
    return {
        "paddle_configured": bool(config.PADDLE_API_KEY),
        "checkout": "stubbed",
        "reason": "Paddle onboarding needs the owner's ID/business verification.",
        "plans": {
            name: {"minutes_per_month": p["minutes_per_month"]}
            for name, p in config.PLANS.items()
        },
        "credit_pack_minutes": config.CREDIT_PACK_MINUTES,
    }


@app.post("/api/billing/paddle-webhook")
async def paddle_webhook(request: Request):
    """Accepts Paddle webhooks only when configured; otherwise tells the
    caller plainly instead of silently dropping money events."""
    if not config.PADDLE_API_KEY or not config.PADDLE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Paddle is not configured (PADDLE_API_KEY / PADDLE_WEBHOOK_SECRET).",
        )
    # Full signature verification + ledger crediting is wired at deploy time
    # once the owner supplies Paddle keys and price IDs.
    body = await request.body()
    return {"ok": True, "received_bytes": len(body), "note": "stub: no keys in P0"}
