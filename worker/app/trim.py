"""Silence trim (Auto-Editor): strip dead/silent portions from an exported
clip via the `auto-editor` CLI (audio-based edit, silent sections cut).

Best effort by design: if auto-editor is missing or fails, or if it
would remove less than 0.5s, the clip ships untrimmed — the job never
fails because of trimming. Trimming runs AFTER captions are burned in,
so the remaining captions stay in sync with the picture (they move with
the frames, not with a separate stream).
"""
import shutil
import subprocess
import sys
from pathlib import Path

MIN_TRIM_SEC = 0.5


def _bin() -> str | None:
    venv_bin = Path(sys.executable).parent / "auto-editor"
    if venv_bin.exists():
        return str(venv_bin)
    return shutil.which("auto-editor")


def _duration(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, timeout=60,
    )
    try:
        return float((r.stdout or "").strip())
    except ValueError:
        return 0.0


def trim_silence(clip_path: Path, margin: str = "0.4s") -> dict:
    """Trim silent sections out of `clip_path` in place.

    Returns {"ran": bool, "trimmed_sec": float}. ran=False means the
    clip is untouched (tool missing, failed, or nothing worth cutting).
    """
    bin_path = _bin()
    if not bin_path:
        print("   ℹ️ auto-editor not installed — clip ships untrimmed.")
        return {"ran": False, "trimmed_sec": 0.0}
    before = _duration(clip_path)
    if before <= 0:
        return {"ran": False, "trimmed_sec": 0.0}
    tmp_out = clip_path.with_name(clip_path.stem + ".trimmed.mp4")
    try:
        r = subprocess.run(
            [bin_path, str(clip_path), "--edit", "audio",
             "--margin", margin, "--no-open", "-o", str(tmp_out)],
            capture_output=True, text=True, timeout=1200,
        )
    except Exception as e:
        print(f"   ℹ️ auto-editor trim skipped ({type(e).__name__}: {e})")
        return {"ran": False, "trimmed_sec": 0.0}
    if r.returncode != 0 or not tmp_out.exists():
        print(f"   ℹ️ auto-editor trim failed ({(r.stderr or '').strip()[-200:]})")
        if tmp_out.exists():
            tmp_out.unlink(missing_ok=True)
        return {"ran": False, "trimmed_sec": 0.0}
    after = _duration(tmp_out)
    trimmed = before - after
    if trimmed < MIN_TRIM_SEC:
        # Nothing worth cutting — keep the original, avoid a pointless
        # re-encode (quality loss for zero gain).
        tmp_out.unlink(missing_ok=True)
        print(f"   ✂️ auto-editor: no silence worth cutting "
              f"({trimmed:.2f}s) — clip kept as-is.")
        return {"ran": True, "trimmed_sec": 0.0}
    tmp_out.replace(clip_path)
    print(f"   ✂️ auto-editor: trimmed {trimmed:.1f}s of silence "
          f"({before:.1f}s -> {after:.1f}s).")
    return {"ran": True, "trimmed_sec": round(trimmed, 2)}
