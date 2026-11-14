"""Credits + auth (F-11).

P0 local auth: a single dev user, auto-provisioned from DEV_USER_EMAIL
(default dev@hookclip.local). The API identifies the user by the
X-User-Id header in local dev; Supabase Auth replaces this at deploy
time (users.id = auth.users id, same table). Every spend is a ledger row.
"""
import os
import uuid

from . import config, db

DEV_USER_EMAIL = os.environ.get("DEV_USER_EMAIL", "dev@hookclip.local").strip()


def get_or_create_user(email: str | None = None) -> dict:
    email = (email or DEV_USER_EMAIL).strip().lower()
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if row:
            return dict(row)
        user_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO users (id, email, plan, credits, created_at) "
            "VALUES (?, ?, 'free', ?, ?)",
            (user_id, email, config.PLANS["free"]["minutes_per_month"], db.now_iso()),
        )
        conn.execute(
            "INSERT INTO credit_ledger (user_id, delta, reason, created_at) "
            "VALUES (?, ?, 'free tier grant', ?)",
            (user_id, config.PLANS["free"]["minutes_per_month"], db.now_iso()),
        )
        conn.commit()
        return {"id": user_id, "email": email, "plan": "free",
                "credits": config.PLANS["free"]["minutes_per_month"]}


def get_credits(user_id: str) -> dict:
    with db.connect() as conn:
        row = conn.execute(
            "SELECT plan, credits FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        return {"plan": "free", "credits": 0}
    return {"plan": row["plan"], "credits": row["credits"]}


def spend(user_id: str, minutes: int, reason: str) -> bool:
    """Deduct `minutes` credits if affordable. Returns False if not."""
    if minutes <= 0:
        return True
    with db.connect() as conn:
        row = conn.execute(
            "SELECT credits FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row or row["credits"] < minutes:
            return False
        conn.execute("UPDATE users SET credits = credits - ? WHERE id = ?",
                     (minutes, user_id))
        conn.execute(
            "INSERT INTO credit_ledger (user_id, delta, reason, created_at) "
            "VALUES (?, ?, ?, ?)", (user_id, -minutes, reason, db.now_iso()))
        conn.commit()
    return True


def refund(user_id: str, minutes: int, reason: str) -> None:
    if minutes <= 0:
        return
    with db.connect() as conn:
        conn.execute("UPDATE users SET credits = credits + ? WHERE id = ?",
                     (minutes, user_id))
        conn.execute(
            "INSERT INTO credit_ledger (user_id, delta, reason, created_at) "
            "VALUES (?, ?, ?, ?)", (user_id, minutes, reason, db.now_iso()))
        conn.commit()


def plan_for(user_id: str) -> dict:
    return config.PLANS[get_credits(user_id)["plan"]]


def current_user_id(request) -> str:
    """Local dev: X-User-Id header, else the dev user. Deploy: replace
    with Supabase JWT validation."""
    header_id = (request.headers.get("X-User-Id") or "").strip()
    if header_id:
        with db.connect() as conn:
            row = conn.execute(
                "SELECT id FROM users WHERE id = ?", (header_id,)).fetchone()
        if row:
            return header_id
    return get_or_create_user()["id"]
