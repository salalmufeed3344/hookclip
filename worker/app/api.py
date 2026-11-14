"""Project / moment / clip API (F-01, F-09, F-10, F-12).

Auth in P0 is the local dev user (credits.current_user_id); Supabase Auth
replaces it at deploy time. Credits: 1 credit = 1 source minute, spent at
project creation, refunded if the job fails for good.
"""
import math
import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import config, credits, db, ingest

router = APIRouter()


class CreateProject(BaseModel):
    url: str


@router.post("/api/projects")
def create_project(body: CreateProject, request: Request):
    source_type, _vid = ingest.parse_url(body.url)
    if not source_type:
        raise HTTPException(
            status_code=400,
            detail="That link isn't a Twitch VOD or YouTube URL. "
                   "Paste a twitch.tv/videos/<id> or youtube.com/watch link.",
        )
    try:
        info = ingest.probe(body.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read that VOD: {e}")
    minutes = max(1, math.ceil(info["duration_sec"] / 60))
    user_id = credits.current_user_id(request)
    balance = credits.get_credits(user_id)
    if balance["credits"] < minutes:
        raise HTTPException(
            status_code=402,
            detail=f"This VOD needs {minutes} credits (1 per source minute) "
                   f"but you have {balance['credits']}. Free tier: 60/month.",
        )
    credits.spend(user_id, minutes, f"project {info['title'][:60]}")
    project_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO projects (id, user_id, source_url, source_type, title, "
            "duration_sec, status, created_at) VALUES (?, ?, ?, ?, ?, ?, 'queued', ?)",
            (project_id, user_id, body.url, source_type, info["title"],
             info["duration_sec"], db.now_iso()),
        )
        conn.execute(
            "INSERT INTO jobs (id, project_id, kind, stage, progress, attempts, "
            "created_at, updated_at) VALUES (?, ?, 'process', 'queued', 0, 0, ?, ?)",
            (job_id, project_id, db.now_iso(), db.now_iso()),
        )
        conn.commit()
    return {"project_id": project_id, "job_id": job_id,
            "title": info["title"], "duration_sec": info["duration_sec"],
            "credits_spent": minutes}


@router.get("/api/projects")
def list_projects(request: Request):
    user_id = credits.current_user_id(request)
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT p.*, j.stage, j.progress FROM projects p "
            "LEFT JOIN jobs j ON j.project_id = p.id AND j.kind = 'process' "
            "WHERE p.user_id = ? ORDER BY p.created_at DESC", (user_id,)).fetchall()
    return {"projects": [dict(r) for r in rows]}


@router.get("/api/projects/{project_id}")
def get_project(project_id: str, request: Request):
    user_id = credits.current_user_id(request)
    with db.connect() as conn:
        proj = conn.execute(
            "SELECT * FROM projects WHERE id = ? AND user_id = ?",
            (project_id, user_id)).fetchone()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found.")
        job = conn.execute(
            "SELECT * FROM jobs WHERE project_id = ? AND kind = 'process' "
            "ORDER BY created_at DESC LIMIT 1", (project_id,)).fetchone()
        n_moments = conn.execute(
            "SELECT COUNT(*) AS n FROM moments WHERE project_id = ?",
            (project_id,)).fetchone()["n"]
    out = dict(proj)
    out["job"] = dict(job) if job else None
    out["moments_count"] = n_moments
    return out


@router.get("/api/projects/{project_id}/moments")
def list_moments(project_id: str, request: Request):
    user_id = credits.current_user_id(request)
    with db.connect() as conn:
        proj = conn.execute(
            "SELECT id FROM projects WHERE id = ? AND user_id = ?",
            (project_id, user_id)).fetchone()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found.")
        moments = conn.execute(
            "SELECT * FROM moments WHERE project_id = ? ORDER BY score DESC",
            (project_id,)).fetchall()
        out = []
        for m in moments:
            d = dict(m)
            d["signals"] = db.from_json(m["signals_json"])
            d["hooks"] = [dict(h) for h in conn.execute(
                "SELECT text, rank FROM hooks WHERE moment_id = ? ORDER BY rank",
                (m["id"],)).fetchall()]
            d["clips"] = [dict(c) for c in conn.execute(
                "SELECT id, status, export_path FROM clips WHERE moment_id = ?",
                (m["id"],)).fetchall()]
            out.append(d)
    return {"moments": out,
            "note": "Scores rank clips; they do not guarantee views."}


class CreateClip(BaseModel):
    moment_id: str
    hook_text: str | None = None
    caption_style: str = "bold"
    trim_start: float | None = None
    trim_end: float | None = None


@router.post("/api/clips")
def create_clip(body: CreateClip, request: Request):
    user_id = credits.current_user_id(request)
    with db.connect() as conn:
        moment = conn.execute(
            "SELECT m.*, p.user_id FROM moments m JOIN projects p "
            "ON p.id = m.project_id WHERE m.id = ?", (body.moment_id,)).fetchone()
        if not moment or moment["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Moment not found.")
        hooks = conn.execute(
            "SELECT text FROM hooks WHERE moment_id = ? ORDER BY rank LIMIT 1",
            (body.moment_id,)).fetchone()
        clip_id = str(uuid.uuid4())
        hook_text = body.hook_text or (hooks["text"] if hooks else "")
        conn.execute(
            "INSERT INTO clips (id, moment_id, status, caption_style, hook_text, "
            "trim_start, trim_end, format, created_at) VALUES (?, ?, 'draft', ?, ?, ?, ?, '9:16', ?)",
            (clip_id, body.moment_id, body.caption_style, hook_text,
             body.trim_start, body.trim_end, db.now_iso()),
        )
        conn.commit()
    return {"clip_id": clip_id, "status": "draft", "hook_text": hook_text}


@router.get("/api/clips/{clip_id}")
def get_clip(clip_id: str, request: Request):
    user_id = credits.current_user_id(request)
    with db.connect() as conn:
        clip = conn.execute(
            "SELECT c.*, m.project_id, m.start_sec, m.end_sec, m.score, "
            "m.score_reason, p.user_id FROM clips c JOIN moments m "
            "ON m.id = c.moment_id JOIN projects p ON p.id = m.project_id "
            "WHERE c.id = ?", (clip_id,)).fetchone()
        if not clip or clip["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Clip not found.")
        job = conn.execute(
            "SELECT * FROM jobs WHERE clip_id = ? ORDER BY created_at DESC LIMIT 1",
            (clip_id,)).fetchone()
    out = dict(clip)
    out.pop("user_id", None)
    out["job"] = dict(job) if job else None
    return out


@router.post("/api/clips/{clip_id}/export")
def export_clip(clip_id: str, request: Request):
    user_id = credits.current_user_id(request)
    with db.connect() as conn:
        clip = conn.execute(
            "SELECT c.*, p.user_id, p.id AS project_id FROM clips c "
            "JOIN moments m ON m.id = c.moment_id "
            "JOIN projects p ON p.id = m.project_id WHERE c.id = ?",
            (clip_id,)).fetchone()
        if not clip or clip["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Clip not found.")
        existing = conn.execute(
            "SELECT id FROM jobs WHERE clip_id = ? AND stage IN "
            "('queued','claimed','rendering')", (clip_id,)).fetchone()
        if existing:
            return {"job_id": existing["id"], "status": "already queued"}
        job_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO jobs (id, project_id, kind, clip_id, stage, progress, "
            "attempts, created_at, updated_at) "
            "VALUES (?, ?, 'render', ?, 'queued', 0, 0, ?, ?)",
            (job_id, clip["project_id"], clip_id, db.now_iso(), db.now_iso()),
        )
        conn.execute("UPDATE clips SET status = 'rendering' WHERE id = ?", (clip_id,))
        conn.commit()
    return {"job_id": job_id, "status": "queued"}


@router.get("/api/clips/{clip_id}/download")
def download_clip(clip_id: str, request: Request):
    user_id = credits.current_user_id(request)
    with db.connect() as conn:
        clip = conn.execute(
            "SELECT c.*, p.user_id FROM clips c JOIN moments m "
            "ON m.id = c.moment_id JOIN projects p ON p.id = m.project_id "
            "WHERE c.id = ?", (clip_id,)).fetchone()
    if not clip or clip["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Clip not found.")
    if clip["status"] != "exported" or not clip["export_path"]:
        raise HTTPException(status_code=409, detail="Clip is not exported yet.")
    return FileResponse(
        clip["export_path"], media_type="video/mp4",
        filename=f"hookclip-{clip_id[:8]}.mp4")


@router.get("/api/me/credits")
def my_credits(request: Request):
    user_id = credits.current_user_id(request)
    info = credits.get_credits(user_id)
    return {"user_id": user_id, **info,
            "plan_minutes": config.PLANS[info["plan"]]["minutes_per_month"]}
