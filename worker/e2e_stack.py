"""End-to-end verification of the clip-stack integration (Nov 15, 2026).

Runs the full pipeline in-process on the 458s GTA V VOD used for the
Nov 14 P0 E2E (YouTube SH9jVCyxPk0), reusing the already-downloaded
source in data/sources/<project>/ so no re-download is needed, and
prints per-tool evidence:

- WhisperX: backend used, word count, a sample word with timestamps.
- PySceneDetect: cut count, runtime, and whether a moment snapped.
- Auto-Editor: trim result on the exported clip.
- Remotion: backend used for the exported clip (remotion vs ffmpeg).
- FFmpeg: still the backbone (download/audio/reframe/encode).

Run: .venv/bin/python e2e_stack.py
No GROQ/GEMINI keys are needed (and none are set in the sandbox): the
local paths are what this script verifies. No HTTP server is involved
(sandbox POSTs hang); everything is direct in-process calls.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Force the local transcription chain (no Groq key in the sandbox anyway).
os.environ.pop("GROQ_API_KEY", None)
os.environ.pop("GEMINI_API_KEY", None)

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import detect, ingest, rank, render, scenes, transcribe  # noqa: E402

WORKER = Path(__file__).resolve().parent
PROJECT_DIR = WORKER / "data" / "sources" / "377693eb-f86e-4fe8-913d-1f1b0bcd12d3"
SOURCE_URL = "https://www.youtube.com/watch?v=SH9jVCyxPk0"
OUT_DIR = WORKER / "data" / "e2e-stack"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _ffprobe(path: Path) -> dict:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height",
         "-show_entries", "format=duration",
         "-of", "json", str(path)],
        capture_output=True, text=True, timeout=60)
    try:
        body = json.loads(r.stdout or "{}")
        stream = (body.get("streams") or [{}])[0]
        return {"width": stream.get("width"), "height": stream.get("height"),
                "duration": float(body.get("format", {}).get("duration") or 0)}
    except Exception:
        return {}


def main() -> dict:
    evidence: dict = {"source": SOURCE_URL, "tools": {}}
    source = PROJECT_DIR / "source.mp4"
    audio = PROJECT_DIR / "audio.wav"
    assert source.exists(), f"missing {source}"
    assert audio.exists(), f"missing {audio}"
    duration = 457.954
    print(f"== source: {source} ({duration:.0f}s, "
          f"{source.stat().st_size // 1024 // 1024} MB)")

    # 1. Transcription (WhisperX expected; faster-whisper is the fallback).
    t0 = time.time()
    result = transcribe.transcribe(audio)
    dt = time.time() - t0
    backend = result.get("backend", "?")
    words = result.get("words", [])
    evidence["tools"]["whisperx"] = {
        "backend": backend, "model": result.get("model"),
        "seconds": round(dt, 1), "words": len(words),
        "segments": len(result.get("segments", [])),
        "speakers": result.get("speakers"),
        "sample_word": words[len(words) // 2] if words else None,
    }
    print(f"== transcribe [{backend}] {len(words)} words in {dt:.0f}s "
          f"(sample: {evidence['tools']['whisperx']['sample_word']})")

    # 2. Chat + audio spikes (same inputs as Nov 14).
    # Chat fetch gets a short timeout here: in the sandbox the YouTube
    # chat-replay request stalls on the egress proxy (observed Nov 15 —
    # 6+ min, zero CPU, connection never completes). fetch_chat returns
    # [] on timeout and detection falls back to audio + transcript.
    chat = ingest.fetch_chat(SOURCE_URL, timeout=120)
    windows = detect.chat_windows(chat, duration)
    spikes = detect.audio_spikes(audio, duration)
    viewer = detect.fetch_viewer_clips(SOURCE_URL, duration)
    print(f"== signals: {len(chat)} chat msgs, {len(spikes)} audio spikes, "
          f"{len(viewer)} viewer clips")

    # 3. Scene cuts (PySceneDetect, downscaled 2x).
    t0 = time.time()
    cuts = scenes.detect_scene_cuts(source)
    dt = time.time() - t0
    evidence["tools"]["scenedetect"] = {
        "cuts": len(cuts), "seconds": round(dt, 1),
        "first_cuts": [round(c, 2) for c in cuts[:10]],
    }
    print(f"== scenes: {len(cuts)} cuts in {dt:.0f}s "
          f"(first: {evidence['tools']['scenedetect']['first_cuts']})")

    # 4. Candidates with scene snapping.
    candidates = detect.candidate_moments(result, windows, spikes, viewer,
                                          duration, scene_cuts=cuts)
    snapped = [c for c in candidates
               if "scene_start" in c["signals"] or "scene_end" in c["signals"]]
    evidence["tools"]["scenedetect"]["moments_snapped"] = len(snapped)
    print(f"== candidates: {len(candidates)} "
          f"({len(snapped)} snapped to a scene cut)")

    # 5. Ranking (heuristic — no Gemini key in the sandbox).
    ranked = rank.rank_moments(candidates)
    top = ranked[0] if ranked else None
    print(f"== ranked: {len(ranked)} moments "
          f"(top score: {top['score'] if top else '-'})")
    if not top:
        print("!! no moments — nothing to render")
        evidence["tools"]["render"] = {"backend": None, "reason": "no moments"}
        (OUT_DIR / "evidence.json").write_text(json.dumps(evidence, indent=2))
        return evidence

    # 6. Render the top moment via the smart path (Remotion first,
    # ffmpeg+ASS fallback, auto-editor trim last).
    hook = (top["hooks"][0]["text"] if top.get("hooks") else "")
    out_path = OUT_DIR / "clip-top.mp4"
    facecam = None
    cache = PROJECT_DIR / "facecam.json"
    if cache.exists():
        try:
            facecam = json.loads(cache.read_text()).get("box")
        except Exception:
            facecam = None
    t0 = time.time()
    out_path, backend = render.render_clip_smart(
        source, float(top["start"]), float(top["end"]), hook, "bold",
        True, out_path, facecam, result["words"])
    dt = time.time() - t0
    probe = _ffprobe(out_path)
    evidence["tools"]["render"] = {
        "backend": backend, "seconds": round(dt, 1),
        "start": top["start"], "end": top["end"], "score": top["score"],
        "hook": hook, "path": str(out_path),
        "size_kb": out_path.stat().st_size // 1024,
        "probe": probe,
    }
    evidence["tools"]["auto_editor"] = {
        "note": "trim runs inside render_clip_smart; see its log lines "
                "above (ran + seconds trimmed, or 'no silence worth cutting').",
    }
    print(f"== render [{backend}] {out_path} "
          f"({probe.get('width')}x{probe.get('height')}, "
          f"{probe.get('duration', 0):.1f}s, "
          f"{out_path.stat().st_size // 1024} KB) in {dt:.0f}s")
    print(f"== top moment: {top['start']}s–{top['end']}s score {top['score']} "
          f"signals={top['signals']}")

    (OUT_DIR / "evidence.json").write_text(json.dumps(evidence, indent=2))
    print(f"== evidence written to {OUT_DIR / 'evidence.json'}")
    return evidence


if __name__ == "__main__":
    main()
