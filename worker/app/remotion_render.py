"""Remotion caption rendering (animated word-by-word captions + hook).

The worker renders the clip in two steps: ffmpeg reframes the source
into a clean 1080x1920 clip (no captions), then Remotion overlays the
animated captions and hook on top of it. Remotion renders through a
headless Chromium, so it needs Node.js + a Chromium binary — both are
optional: ANY failure here returns None and the caller falls back to
the ffmpeg + ASS caption path (render.py), which always works.

Chromium discovery: $REMOTION_CHROMIUM_PATH, the Playwright cache
(~/.cache/ms-playwright), then chromium/chrome on PATH. Without a
browser binary, Remotion is skipped without even trying (it would
otherwise try to download one).
"""
import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path

REMOTION_DIR = Path(__file__).resolve().parent.parent / "remotion"


def find_chromium() -> str | None:
    """A usable Chromium/Chrome executable, or None."""
    env_path = os.environ.get("REMOTION_CHROMIUM_PATH", "").strip()
    if env_path and Path(env_path).exists():
        return env_path
    # Playwright's cached browsers (the sandbox has these pre-installed).
    cache = Path.home() / ".cache" / "ms-playwright"
    if cache.exists():
        for pattern in ("chromium-*/chrome-linux64/chrome",
                        "chromium-*/chrome-linux/chrome",
                        "chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell",
                        "chromium_headless_shell-*/chrome-linux/headless_shell"):
            hits = sorted(cache.glob(pattern))
            if hits:
                return str(hits[-1])
    for name in ("chromium", "chromium-browser", "google-chrome",
                 "google-chrome-stable"):
        found = shutil.which(name)
        if found:
            return found
    return None


def remotion_available() -> bool:
    """Node project installed AND a Chromium binary present."""
    cli = REMOTION_DIR / "node_modules" / "@remotion" / "cli"
    return cli.exists() and find_chromium() is not None


def render_with_remotion(clean_clip: Path, words: list, start: float,
                         end: float, hook_text: str, watermark: bool,
                         out_path: Path, fps: int = 30) -> Path | None:
    """Render animated captions over `clean_clip` via Remotion.

    Returns out_path on success, None on any failure (caller falls back).
    `words` are absolute VOD times; they are shifted to clip-relative
    here. The staged input video is deleted afterwards.
    """
    if not remotion_available():
        print("   ℹ️ Remotion skipped (not installed or no Chromium found).")
        return None
    chromium = find_chromium()
    duration = max(1.0, end - start)
    tag = uuid.uuid4().hex[:8]
    public_dir = REMOTION_DIR / "public"
    public_dir.mkdir(exist_ok=True)
    staged = public_dir / f"input-{tag}.mp4"
    props_path = public_dir / f"props-{tag}.json"
    try:
        shutil.copyfile(clean_clip, staged)
        rel_words = [
            {"w": w["w"], "s": round(float(w["s"]) - start, 3),
             "e": round(float(w["e"]) - start, 3)}
            for w in words
            if float(w["e"]) > start and float(w["s"]) < end
        ]
        props = {
            "video": f"input-{tag}.mp4",
            "words": rel_words,
            "hook": hook_text or "",
            "watermark": bool(watermark),
            "durationSec": round(duration, 2),
        }
        props_path.write_text(json.dumps(props), encoding="utf-8")
        cmd = [
            "npx", "remotion", "render", "src/index.ts", "HookclipCaption",
            str(out_path), "--props", str(props_path),
            "--browser-executable", chromium,
            "--concurrency", "1",
        ]
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=1800,
            cwd=str(REMOTION_DIR),
            env={**os.environ, "NODE_OPTIONS": "--max-old-space-size=2048"},
        )
        if r.returncode != 0 or not out_path.exists():
            tail = ((r.stderr or "") + (r.stdout or "")).strip()[-400:]
            print(f"   ⚠️ Remotion render failed ({tail}) — ffmpeg fallback.")
            if out_path.exists():
                out_path.unlink(missing_ok=True)
            return None
        # Sanity: the output must actually be ~the right length.
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(out_path)],
            capture_output=True, text=True, timeout=60,
        )
        try:
            got = float((probe.stdout or "").strip())
        except ValueError:
            got = 0.0
        if got < duration * 0.5:
            print(f"   ⚠️ Remotion output too short ({got:.1f}s vs "
                  f"{duration:.1f}s) — ffmpeg fallback.")
            out_path.unlink(missing_ok=True)
            return None
        print(f"   🎞️ Remotion captions rendered ({got:.1f}s, "
              f"{len(rel_words)} words, hook + watermark).")
        return out_path
    except Exception as e:
        print(f"   ⚠️ Remotion render error ({type(e).__name__}: {e}) "
              f"— ffmpeg fallback.")
        if out_path.exists():
            out_path.unlink(missing_ok=True)
        return None
    finally:
        staged.unlink(missing_ok=True)
        props_path.unlink(missing_ok=True)
