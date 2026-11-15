"""Job runner: the DB-backed queue (architecture §5.2, no Redis in P0).

One background thread claims the oldest queued job and runs its stages,
writing progress after each stage so the dashboard stays live. A failed
stage retries once, then marks the job failed with the stage + error —
never a silent hang.
"""
import json
import math
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

from . import config, credits, db, detect, ingest, rank, render, scenes, transcribe

POLL_SEC = 2


def _set_stage(job_id: str, stage: str, progress: float, error: str | None = None):
    with db.connect() as conn:
        conn.execute(
            "UPDATE jobs SET stage = ?, progress = ?, error = ?, updated_at = ? "
            "WHERE id = ?",
            (stage, progress, error, db.now_iso(), job_id),
        )
        conn.commit()


def _project_dir(project_id: str) -> Path:
    d = config.SOURCE_DIR / project_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _facecam_for(project_id: str, source: Path, moment_start: float, moment_end: float):
    """Facecam box for the project, detected once and cached."""
    cache = _project_dir(project_id) / "facecam.json"
    if cache.exists():
        try:
            return json.loads(cache.read_text()).get("box")
        except Exception:
            pass
    try:
        r = subprocess.run(
            [sys.executable, "-m", "app.facecam", str(source),
             str(moment_start), str(moment_end)],
            capture_output=True, text=True, timeout=300,
            cwd=str(Path(__file__).resolve().parent.parent),
        )
        box = (json.loads(r.stdout) or {}).get("box") if r.returncode == 0 else None
    except Exception as e:
        print(f"   ℹ️ facecam detection skipped ({e})")
        box = None
    cache.write_text(json.dumps({"box": box}))
    return box


def run_process_job(job_id: str, project_id: str):
    with db.connect() as conn:
        proj = conn.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    proj = dict(proj)
    pdir = _project_dir(project_id)
    source = pdir / "source.mp4"
    audio = pdir / "audio.wav"

    _set_stage(job_id, "downloading", 0.05)
    if not source.exists():
        source = ingest.download(proj["source_url"], pdir)
        if source.suffix != ".mp4":
            source = source.rename(pdir / "source.mp4")
    if not audio.exists():
        ingest.extract_audio(source, audio)

    _set_stage(job_id, "transcribing", 0.25)
    result = transcribe.transcribe(audio)
    print(f"   🎙️ transcript via {result.get('backend', '?')}: "
          f"{len(result['words'])} words, {len(result['segments'])} segments")
    with db.connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO transcripts (project_id, segments_json, words_json) "
            "VALUES (?, ?, ?)",
            (project_id, db.to_json(result["segments"]), db.to_json(result["words"])),
        )
        conn.commit()

    _set_stage(job_id, "detecting", 0.5)
    duration = float(proj["duration_sec"] or 0) or 0.0
    chat = ingest.fetch_chat(proj["source_url"])
    windows = detect.chat_windows(chat, duration)
    with db.connect() as conn:
        conn.execute("DELETE FROM chat_windows WHERE project_id = ?", (project_id,))
        for w in windows:
            conn.execute(
                "INSERT INTO chat_windows (project_id, window_start, msg_count, velocity_ratio) "
                "VALUES (?, ?, ?, ?)",
                (project_id, w["start"], w["msg_count"], w["velocity_ratio"]))
        conn.commit()
    spikes = detect.audio_spikes(audio, duration)
    viewer = detect.fetch_viewer_clips(proj["source_url"], duration)
    candidates = detect.candidate_moments(result, windows, spikes, viewer,
                                          duration)
    # Scene cuts (PySceneDetect), windowed: candidates snap to the nearest
    # cut so clips never start mid-shot. Only the span covering the
    # candidates is scanned — a whole-VOD scan costs ~3x realtime on CPU
    # (see scenes.py). Best effort — failure keeps old behaviour.
    if candidates:
        try:
            span_start = max(0.0, min(c["start"] for c in candidates) - 5.0)
            span_end = min(duration, max(c["end"] for c in candidates) + 5.0)
            scene_cuts = scenes.detect_scene_cuts(source, start=span_start,
                                                  end=span_end)
            print(f"   🎬 {len(scene_cuts)} scene cuts (PySceneDetect, "
                  f"{span_end - span_start:.0f}s window)")
            candidates = scenes.snap_candidates(
                candidates, scene_cuts, max_len=detect.MAX_CLIP_SEC)
        except Exception as e:
            print(f"   ℹ️ scene detection skipped ({type(e).__name__}: {e})")
    print(f"   🔍 {len(chat)} chat msgs, {len(spikes)} audio spikes, "
          f"{len(viewer)} viewer clips -> {len(candidates)} candidates")

    _set_stage(job_id, "ranking", 0.75)
    ranked = rank.rank_moments(candidates)
    with db.connect() as conn:
        conn.execute("DELETE FROM moments WHERE project_id = ?", (project_id,))
        for m in ranked:
            mid = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO moments (id, project_id, start_sec, end_sec, "
                "signals_json, score, score_reason, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (mid, project_id, m["start"], m["end"], db.to_json(m["signals"]),
                 m["score"], m["reason"], db.now_iso()))
            for h in m["hooks"]:
                conn.execute(
                    "INSERT INTO hooks (id, moment_id, text, rank) VALUES (?, ?, ?, ?)",
                    (str(uuid.uuid4()), mid, h["text"], h["rank"]))
        conn.execute("UPDATE projects SET status = 'ready' WHERE id = ?", (project_id,))
        conn.commit()
    print(f"   🏆 {len(ranked)} moments ranked "
          f"(top: {ranked[0]['score'] if ranked else '-'})")
    _set_stage(job_id, "ready", 1.0)


def run_render_job(job_id: str, clip_id: str):
    with db.connect() as conn:
        clip = conn.execute("SELECT * FROM clips WHERE id = ?", (clip_id,)).fetchone()
    clip = dict(clip)
    with db.connect() as conn:
        moment = conn.execute(
            "SELECT * FROM moments WHERE id = ?", (clip["moment_id"],)).fetchone()
        proj = conn.execute(
            "SELECT * FROM projects WHERE id = ?", (moment["project_id"],)).fetchone()
        trans = conn.execute(
            "SELECT words_json FROM transcripts WHERE project_id = ?",
            (moment["project_id"],)).fetchone()
        user = conn.execute(
            "SELECT plan FROM users WHERE id = ?", (proj["user_id"],)).fetchone()
    moment, proj = dict(moment), dict(proj)
    words = db.from_json(trans["words_json"]) if trans else []
    watermark = config.PLANS[user["plan"]]["watermark"] if user else True

    _set_stage(job_id, "rendering", 0.3)
    pdir = _project_dir(moment["project_id"])
    source = pdir / "source.mp4"
    start = float(clip["trim_start"] if clip["trim_start"] is not None else moment["start_sec"])
    end = float(clip["trim_end"] if clip["trim_end"] is not None else moment["end_sec"])
    facecam = _facecam_for(moment["project_id"], source, start, end)
    out_path = config.CLIP_DIR / f"{clip_id}.mp4"
    out_path, backend = render.render_clip_smart(
        source, start, end,
        clip["hook_text"] or "",
        clip["caption_style"] or "bold",
        watermark, out_path, facecam, words,
    )
    with db.connect() as conn:
        conn.execute(
            "UPDATE clips SET status = 'exported', export_path = ? WHERE id = ?",
            (str(out_path), clip_id))
        conn.commit()
    print(f"   🎬 exported {out_path} via {backend} "
          f"({out_path.stat().st_size // 1024} KB)")
    _set_stage(job_id, "ready", 1.0)


def _run_one(job: dict):
    job_id, kind = job["id"], job.get("kind", "process")
    try:
        if kind == "render":
            run_render_job(job_id, job["clip_id"])
        else:
            run_process_job(job_id, job["project_id"])
    except Exception as e:
        attempts = job["attempts"] + 1
        print(f"   ❌ job {job_id} failed at stage (attempt {attempts}): {e}")
        with db.connect() as conn:
            if attempts < 2:
                conn.execute(
                    "UPDATE jobs SET stage = 'queued', attempts = ?, "
                    "error = ?, updated_at = ? WHERE id = ?",
                    (attempts, str(e)[:500], db.now_iso(), job_id))
            else:
                conn.execute(
                    "UPDATE jobs SET stage = 'failed', attempts = ?, "
                    "error = ?, updated_at = ? WHERE id = ?",
                    (attempts, str(e)[:500], db.now_iso(), job_id))
                # Failed for good: refund the source-minutes spent.
                if job.get("kind", "process") == "process":
                    proj = conn.execute(
                        "SELECT user_id, duration_sec FROM projects WHERE id = ?",
                        (job["project_id"],)).fetchone()
                    if proj and proj["duration_sec"]:
                        import math
                        credits.refund(
                            proj["user_id"],
                            max(1, math.ceil(proj["duration_sec"] / 60)),
                            f"refund: job {job_id} failed")
            conn.commit()


def claim_next() -> dict | None:
    with db.connect() as conn:
        row = conn.execute(
            "SELECT * FROM jobs WHERE stage = 'queued' "
            "ORDER BY created_at LIMIT 1").fetchone()
        if not row:
            return None
        job = dict(row)
        conn.execute(
            "UPDATE jobs SET stage = 'claimed', updated_at = ? WHERE id = ?",
            (db.now_iso(), job["id"]))
        conn.commit()
    return job


def worker_loop(stop: threading.Event):
    db.init_db()
    # A restart mid-job used to leave the job stuck in a non-terminal stage
    # forever (claim_next only takes 'queued'). Fail stuck jobs fast so the
    # queue stays honest, and refund their spent minutes.
    with db.connect() as conn:
        stuck = conn.execute(
            "SELECT j.id, p.user_id, p.duration_sec FROM jobs j "
            "LEFT JOIN projects p ON p.id = j.project_id "
            "WHERE j.stage IN ('claimed','downloading','transcribing',"
            "'detecting','ranking','rendering')"
        ).fetchall()
        for s in stuck:
            conn.execute(
                "UPDATE jobs SET stage = 'failed', "
                "error = 'interrupted by worker restart - please retry', "
                "updated_at = ? WHERE id = ?",
                (db.now_iso(), s["id"]))
            if s["user_id"] and s["duration_sec"]:
                credits.refund(
                    s["user_id"],
                    max(1, math.ceil(float(s["duration_sec"]) / 60)),
                    "refund: job interrupted by restart")
        conn.commit()
    print("   ⚙️ worker loop started (DB queue, poll 2s)")
    while not stop.is_set():
        job = claim_next()
        if job:
            _run_one(job)
        else:
            stop.wait(POLL_SEC)


def start_worker_thread() -> threading.Event:
    stop = threading.Event()
    t = threading.Thread(target=worker_loop, args=(stop,), daemon=True)
    t.start()
    return stop
