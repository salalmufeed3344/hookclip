"""Re-verify scene detection + snapping after the PySceneDetect 0.7 fix.

The main E2E (e2e_stack.py) ran with the broken `VideoManager` import, so
its evidence.json says 0 cuts. This script re-runs steps 1-4 only
(transcribe -> scenes -> candidates -> rank) with the fixed scenes.py and
writes data/e2e-stack/evidence-scenes.json. The render evidence from the
main E2E still stands (render does not depend on scene cuts).
"""
import json
import os
import sys
import time
from pathlib import Path

os.environ.pop("GROQ_API_KEY", None)
os.environ.pop("GEMINI_API_KEY", None)
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import detect, ingest, rank, scenes, transcribe  # noqa: E402

WORKER = Path(__file__).resolve().parent
PROJECT_DIR = WORKER / "data" / "sources" / "377693eb-f86e-4fe8-913d-1f1b0bcd12d3"
SOURCE_URL = "https://www.youtube.com/watch?v=SH9jVCyxPk0"
OUT_DIR = WORKER / "data" / "e2e-stack"
source = PROJECT_DIR / "source.mp4"
audio = PROJECT_DIR / "audio.wav"
duration = 457.954

t0 = time.time()
result = transcribe.transcribe(audio)
print(f"== transcribe [{result.get('backend')}] {len(result.get('words', []))} "
      f"words in {time.time() - t0:.0f}s")

chat = ingest.fetch_chat(SOURCE_URL, timeout=120)
windows = detect.chat_windows(chat, duration)
spikes = detect.audio_spikes(audio, duration)
viewer = detect.fetch_viewer_clips(SOURCE_URL, duration)
print(f"== signals: {len(chat)} chat msgs, {len(spikes)} audio spikes, "
      f"{len(viewer)} viewer clips")

# Candidates first (word-snapped, no scene cuts yet), then windowed
# scene detection over the candidate span, then snap — mirrors jobs.py.
candidates = detect.candidate_moments(result, windows, spikes, viewer,
                                      duration)
print(f"== candidates (pre-snap): {len(candidates)}")

t0 = time.time()
cuts = []
if candidates:
    span_start = max(0.0, min(c["start"] for c in candidates) - 5.0)
    span_end = min(duration, max(c["end"] for c in candidates) + 5.0)
    cuts = scenes.detect_scene_cuts(source, start=span_start, end=span_end)
    dt = time.time() - t0
    print(f"== scenes: {len(cuts)} cuts in {dt:.0f}s "
          f"({span_end - span_start:.0f}s window, first: "
          f"{[round(c, 2) for c in cuts[:10]]})")
    candidates = scenes.snap_candidates(candidates, cuts,
                                        max_len=detect.MAX_CLIP_SEC)
else:
    dt = time.time() - t0
    print(f"== scenes: no candidates, skipped in {dt:.0f}s")

snapped = [c for c in candidates
           if "scene_start" in c["signals"] or "scene_end" in c["signals"]]
print(f"== candidates: {len(candidates)} ({len(snapped)} snapped)")
for c in candidates:
    print(f"   {c['start']}s-{c['end']}s signals={c['signals']}")
ranked = rank.rank_moments(candidates)
top = ranked[0] if ranked else None
print(f"== ranked: {len(ranked)} (top score: {top['score'] if top else '-'})")

evidence = {
    "source": SOURCE_URL,
    "scenedetect": {"cuts": len(cuts), "seconds": round(dt, 1),
                    "first_cuts": [round(c, 2) for c in cuts[:10]],
                    "moments_snapped": len(snapped)},
    "candidates": len(candidates),
    "top": {"start": top["start"], "end": top["end"], "score": top["score"],
            "signals": top["signals"]} if top else None,
}
(OUT_DIR / "evidence-scenes.json").write_text(json.dumps(evidence, indent=2))
print(f"== evidence written to {OUT_DIR / 'evidence-scenes.json'}")
