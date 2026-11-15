"""Detection (F-03, F-04): chat spikes, audio spikes, viewer clips -> candidates.

Signals, cheapest first. A moment qualifies on any of them; ranking (rank.py)
decides the order. All pure helpers are stdlib-only and testable.
"""
import math
import os
import re
import statistics
from urllib.parse import urlparse

# Bots / system accounts that must never move the chat needle.
KNOWN_BOTS = {
    "nightbot", "streamelements", "streamlabs", "moobot", "fossabot",
    "wizebot", "nightbot_", "sery_bot", "streamlabsbot", "commanderroot",
    "pretzelrocks", "soundalerts", "kofistreambot",
}
# One user can contribute at most this many messages per 10s window.
USER_CAP_PER_WINDOW = 3
WINDOW_SEC = 10.0
# Chat lags the moment: viewers watch on a delayed stream, then react and
# type, so a chat spike sits well AFTER the action. Clips cut from a chat
# spike start 20s early (ai.with.raiyan GTA 6 Part 2 reel: "chat reacts
# after the moment"). Audio spikes and viewer clips ARE the moment, so they
# only get a small lead-in for context.
CHAT_OFFSET_SEC = 20.0
LEAD_IN_SEC = 3.0
MIN_CLIP_SEC = 15.0
MAX_CLIP_SEC = 60.0


def chat_windows(messages: list, duration: float) -> list:
    """Per-10s windows: [{start, msg_count, velocity_ratio}].

    Baseline is the channel's own median window (small chats count).
    velocity_ratio = count / baseline. Bots filtered, one spammer capped.
    """
    n_windows = max(1, math.ceil(duration / WINDOW_SEC))
    counts = [0] * n_windows
    for m in messages or []:
        author = str(m.get("author") or "").lower()
        if author in KNOWN_BOTS:
            continue
        t = float(m.get("t") or 0)
        if t < 0 or t >= duration:
            continue
        idx = min(n_windows - 1, int(t // WINDOW_SEC))
        counts[idx] += 1
    # Per-user cap: recount with the cap applied.
    per_user: dict = {}
    capped = [0] * n_windows
    for m in messages or []:
        author = str(m.get("author") or "").lower()
        if author in KNOWN_BOTS:
            continue
        t = float(m.get("t") or 0)
        if t < 0 or t >= duration:
            continue
        idx = min(n_windows - 1, int(t // WINDOW_SEC))
        key = (idx, author)
        if per_user.get(key, 0) >= USER_CAP_PER_WINDOW:
            continue
        per_user[key] = per_user.get(key, 0) + 1
        capped[idx] += 1
    baseline = statistics.median(capped) if capped else 0
    baseline = max(baseline, 1.0)
    return [
        {"start": round(i * WINDOW_SEC, 1), "msg_count": capped[i],
         "velocity_ratio": round(capped[i] / baseline, 2)}
        for i in range(n_windows)
    ]


def audio_spikes(wav_path, duration: float) -> list:
    """Energy-envelope spikes from the 16 kHz mono WAV.

    RMS per 0.5s window vs a rolling median. Returns [{t, type, ratio}]:
    type 'loud' (shout/laughter) or 'silence' (sudden drop). No deps
    beyond numpy (already installed).
    """
    import wave
    import numpy as np

    with wave.open(str(wav_path), "rb") as w:
        n = w.getnframes()
        rate = w.getframerate()
        raw = w.readframes(n)
    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    win = int(rate * 0.5)
    if win <= 0 or len(audio) < win:
        return []
    n_win = len(audio) // win
    rms = np.sqrt(np.mean(audio[: n_win * win].reshape(n_win, win) ** 2, axis=1))
    med = float(np.median(rms)) or 1e-6
    spikes = []
    for i, r in enumerate(rms):
        t = round(i * 0.5, 2)
        if r > 2.0 * med:
            spikes.append({"t": t, "type": "loud", "ratio": round(float(r) / med, 2)})
        elif r < 0.12 * med:
            spikes.append({"t": t, "type": "silence", "ratio": round(float(r) / med, 2)})
    # Merge adjacent spike windows into one event each.
    merged = []
    for s in spikes:
        if merged and s["t"] - merged[-1]["t"] <= 1.0 and s["type"] == merged[-1]["type"]:
            merged[-1]["ratio"] = max(merged[-1]["ratio"], s["ratio"])
        else:
            merged.append(dict(s))
    return merged


def parse_vod_id(url: str):
    """Numeric Twitch VOD id from a twitch.tv/videos/<id> link, else None."""
    try:
        parsed = urlparse(str(url or "").strip())
    except ValueError:
        return None
    if (parsed.hostname or "").lower() not in ("twitch.tv", "www.twitch.tv", "m.twitch.tv"):
        return None
    m = re.match(r"^/(?:[^/]+/)?(?:videos?|v)/(\d+)/?$", parsed.path or "")
    return m.group(1) if m else None


def fetch_viewer_clips(url: str, duration: float) -> list:
    """Viewer-made clips for a Twitch VOD (Helix app token, public data).

    Adapted from OpenShorts' twitch_signals.py (MIT): each clip records
    where in the VOD it starts and how many views it got — the scream-and-
    silence moments a transcript ranks low. Best effort: [] without
    credentials or on any failure.
    """
    import httpx

    vod_id = parse_vod_id(url)
    cid = os.environ.get("TWITCH_CLIENT_ID", "").strip()
    secret = os.environ.get("TWITCH_CLIENT_SECRET", "").strip()
    if not vod_id or not cid or not secret:
        return []
    try:
        with httpx.Client(timeout=15) as client:
            tok = client.post("https://id.twitch.tv/oauth2/token", data={
                "client_id": cid, "client_secret": secret,
                "grant_type": "client_credentials"}).json().get("access_token")
            if not tok:
                return []
            headers = {"Client-Id": cid, "Authorization": f"Bearer {tok}"}
            r = client.get("https://api.twitch.tv/helix/videos",
                           params={"id": vod_id}, headers=headers)
            data = (r.json() or {}).get("data") or []
            if not data:
                return []
            from datetime import datetime, timezone, timedelta
            created = datetime.fromisoformat(
                str(data[0].get("created_at", "")).replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            fmt = lambda d: d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            params = {"broadcaster_id": data[0].get("user_id"), "first": 100,
                      "started_at": fmt(created),
                      "ended_at": fmt(min(now, created + timedelta(days=60)))}
            out, cursor = [], None
            for _ in range(5):
                if cursor:
                    params["after"] = cursor
                r = client.get("https://api.twitch.tv/helix/clips",
                               params=params, headers=headers)
                if r.status_code != 200:
                    break
                body = r.json() or {}
                for c in body.get("data") or []:
                    if str(c.get("video_id") or "") != str(vod_id):
                        continue
                    if c.get("vod_offset") is None:
                        continue
                    out.append({"start": float(c["vod_offset"]),
                                "duration": float(c.get("duration") or 0),
                                "views": int(c.get("view_count") or 0)})
                cursor = (body.get("pagination") or {}).get("cursor")
                if not cursor:
                    break
    except Exception as e:
        print(f"   ℹ️ Twitch viewer clips unavailable ({type(e).__name__}).")
        return []
    return sorted(out, key=lambda c: -c["views"])


def snap_to_words(start: float, end: float, words: list, duration: float) -> tuple:
    """Snap clip edges to word boundaries so cuts land in pauses, not
    mid-word. Simplified from OpenShorts' snap_clip_to_words."""
    if not words:
        return max(0.0, start), min(duration, end)
    starts = [w["s"] for w in words]
    ends = [w["e"] for w in words]
    near = [s for s in starts if abs(s - start) <= 1.5]
    if near:
        start = min(near, key=lambda s: abs(s - start)) - 0.2
    near = [e for e in ends if abs(e - end) <= 1.5]
    if near:
        end = min(near, key=lambda e: abs(e - end)) + 0.2
    start = max(0.0, start)
    end = min(duration, end)
    if end - start < MIN_CLIP_SEC:
        end = min(duration, start + MIN_CLIP_SEC)
    if end - start > MAX_CLIP_SEC:
        end = start + MAX_CLIP_SEC
    return round(start, 2), round(end, 2)


def candidate_moments(transcript: dict, chat: list, audio: list,
                      viewer_clips: list, duration: float,
                      scene_cuts: list | None = None) -> list:
    """Merge all signals into candidate moments with a signals dict.

    Chat windows with ratio >= 2.5, loud audio spikes, and viewer-clip
    positions each open a candidate (chat spikes start 20s early, audio /
    viewer moments start 3s early, ~45s long, snapped to words, then to
    the nearest scene cut so clips never start mid-cut). Overlapping
    candidates merge; the strongest signals win. Sorted by signal
    strength, best first.
    """
    words = transcript.get("words", [])
    raw = []

    for w in chat or []:
        if w["velocity_ratio"] >= 2.5 and w["msg_count"] >= 3:
            raw.append({
                "start": max(0.0, w["start"] - CHAT_OFFSET_SEC),
                "end": w["start"] + 45,
                "signals": {"chat_ratio": w["velocity_ratio"],
                            "chat_count": w["msg_count"]},
            })
    for s in audio or []:
        if s["type"] == "loud":
            raw.append({
                "start": max(0.0, s["t"] - LEAD_IN_SEC),
                "end": s["t"] + 45,
                "signals": {"audio_spike": s["ratio"]},
            })
    for c in viewer_clips or []:
        raw.append({
            "start": max(0.0, c["start"] - LEAD_IN_SEC),
            "end": c["start"] + max(15.0, c["duration"]),
            "signals": {"viewer_clips": 1, "viewer_views": c["views"]},
        })

    # Merge overlaps (keep the union, merge the signals).
    raw.sort(key=lambda c: c["start"])
    merged = []
    for c in raw:
        if merged and c["start"] < merged[-1]["end"] - 5:
            m = merged[-1]
            m["end"] = max(m["end"], c["end"])
            for k, v in c["signals"].items():
                if isinstance(v, (int, float)):
                    m["signals"][k] = max(m["signals"].get(k, 0), v)
                else:
                    m["signals"][k] = v
        else:
            merged.append({"start": c["start"], "end": c["end"],
                           "signals": dict(c["signals"])})

    # Fallback: no signal at all (quiet VOD) — take the loudest audio
    # windows so the job still returns something to review.
    if not merged and duration >= MIN_CLIP_SEC:
        loud = sorted(audio or [], key=lambda s: -s.get("ratio", 0))[:3]
        for s in loud:
            merged.append({"start": max(0.0, s["t"] - LEAD_IN_SEC),
                           "end": s["t"] + 45, "signals": {"audio_spike": s["ratio"]}})
        merged.sort(key=lambda c: c["start"])

    out = []
    for c in merged:
        s, e = snap_to_words(c["start"], c["end"], words, duration)
        if e - s < 10:
            continue
        # Snap to the nearest scene cut (PySceneDetect) so the clip opens
        # and closes on a hard cut, never mid-shot. Then re-clamp length:
        # the end snap can push the clip past the 60s cap.
        if scene_cuts:
            from . import scenes as scenes_mod
            s, e, cut_info = scenes_mod.snap_to_scene_cuts(s, e, scene_cuts)
            for k, v in cut_info.items():
                if v is not None:
                    c["signals"][k] = v
            if e - s > MAX_CLIP_SEC:
                e = s + MAX_CLIP_SEC
            if e - s < 10:
                continue
        c = {"start": s, "end": e, "signals": c["signals"]}
        # Transcript snippet for the ranker.
        seg_text = " ".join(
            seg["text"] for seg in transcript.get("segments", [])
            if seg["end"] >= s and seg["start"] <= e
        )
        c["transcript"] = seg_text[:800]
        out.append(c)
    return out
