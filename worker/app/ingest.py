"""Ingest (F-01): Twitch/YouTube VOD download + chat replay (best effort).

- yt-dlp downloads the video (<=1080p, merged mp4) and reports duration.
- chat-downloader fetches chat replay (Twitch + YouTube) as timestamped
  messages; any failure degrades to [] — detection falls back to
  transcript + audio (architecture §10).
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

from . import config


def _bin(name: str) -> str:
    """Tool binaries live in the venv (same dir as this Python) or on PATH."""
    venv_bin = Path(sys.executable).parent / name
    if venv_bin.exists():
        return str(venv_bin)
    found = shutil.which(name)
    if found:
        return found
    return name  # let subprocess raise a clear error

TWITCH_VOD_RE = re.compile(r"^/(?:[^/]+/)?(?:videos?|v)/(\d+)/?$")
YOUTUBE_RE = re.compile(
    r"(?:youtube\.com/(?:watch\?.*v=|live/|shorts/)|youtu\.be/)([\w-]{6,})"
)

MAX_DURATION_SEC = config.MAX_SOURCE_HOURS * 3600


def parse_url(url: str):
    """-> (source_type, video_id) or (None, None) for an unrecognised URL."""
    url = (url or "").strip()
    try:
        parsed = urlparse(url)
    except ValueError:
        return None, None
    host = (parsed.hostname or "").lower()
    if host in ("twitch.tv", "www.twitch.tv", "m.twitch.tv"):
        m = TWITCH_VOD_RE.match(parsed.path or "")
        return ("twitch_vod", m.group(1)) if m else (None, None)
    if host in ("youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com"):
        m = YOUTUBE_RE.search(url)
        return ("youtube", m.group(1)) if m else (None, None)
    return None, None


def _yt_dlp_base_args() -> list:
    """yt-dlp defaults to certifi's CA bundle, which lacks the sandbox
    egress proxy's CA (system bundle has it). `--compat-options no-certifi`
    makes it use the system certificates instead. Harmless on DeployXA."""
    return [_bin("yt-dlp"), "--compat-options", "no-certifi",
            "--extractor-args", "youtube:player_client=android,ios,tv_embedded"]


def probe(url: str) -> dict:
    """Duration/title via yt-dlp without downloading. Raises on failure."""
    r = subprocess.run(
        _yt_dlp_base_args() + ["--dump-json", "--no-download", "--no-playlist", url],
        capture_output=True, text=True, timeout=120,
    )
    if r.returncode != 0:
        raise RuntimeError(f"yt-dlp probe failed: {(r.stderr or '').strip()[-300:]}")
    info = json.loads(r.stdout)
    duration = float(info.get("duration") or 0)
    if duration <= 0:
        # A probe that cannot read the length must fail here: accepting it
        # charges 1 credit for an unknown-length source and lets the worker
        # download blindly (a multi-hour VOD ties it up for hours).
        raise RuntimeError("Could not read the VOD length — try another link.")
    if duration > MAX_DURATION_SEC:
        raise RuntimeError(
            f"Source is {duration / 3600:.1f}h — capped at {config.MAX_SOURCE_HOURS}h.")
    return {
        "title": info.get("title") or "Untitled VOD",
        "duration_sec": duration,
        "uploader": info.get("uploader") or info.get("channel") or "",
    }


def download(url: str, dest_dir: Path) -> Path:
    """Download video (<=1080p) + audio merged to mp4. Returns the file."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    out_tmpl = str(dest_dir / "source.%(ext)s")
    r = subprocess.run(
        _yt_dlp_base_args() + ["-f", "bv*[height<=1080]+ba/b[height<=1080]",
         "--merge-output-format", "mp4", "--no-playlist",
         "-o", out_tmpl, url],
        capture_output=True, text=True, timeout=3600,
    )
    if r.returncode != 0:
        raise RuntimeError(f"yt-dlp download failed: {(r.stderr or '').strip()[-500:]}")
    files = sorted(dest_dir.glob("source.*"))
    if not files:
        raise RuntimeError("yt-dlp finished but no source file was written.")
    return files[0]


def extract_audio(video_path: Path, wav_path: Path) -> Path:
    """16 kHz mono WAV for transcription + audio-energy analysis."""
    r = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(video_path),
         "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(wav_path)],
        capture_output=True, text=True, timeout=1800,
    )
    if r.returncode != 0 or not wav_path.exists():
        raise RuntimeError(f"audio extraction failed: {(r.stderr or '').strip()[-300:]}")
    return wav_path


def fetch_chat(url: str, timeout: int = 600) -> list:
    """Chat replay messages [{t, author, text}] in video seconds.

    Uses chat-downloader (Twitch + YouTube). Best effort: [] on any failure.
    """
    import os
    # chat-downloader runs on requests -> certifi; point it at the system CA.
    env = dict(os.environ)
    bundle = config.ca_bundle_path()
    if bundle:
        env["REQUESTS_CA_BUNDLE"] = bundle
    try:
        r = subprocess.run(
            [_bin("chat_downloader"), url, "--output", "-", "--format", "json"],
            capture_output=True, text=True, timeout=timeout, env=env,
        )
    except Exception as e:
        print(f"   ℹ️ chat replay unavailable ({type(e).__name__}: {e})")
        return []
    if r.returncode != 0 or not (r.stdout or "").strip():
        return []
    messages = []
    for line in r.stdout.splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            continue
        try:
            t = float(item.get("time_in_seconds", 0))
        except (TypeError, ValueError):
            continue
        author = str(item.get("author", {}).get("name") or item.get("author") or "")
        text = str(item.get("message") or "")
        if text:
            messages.append({"t": t, "author": author, "text": text})
    messages.sort(key=lambda m: m["t"])
    return messages
