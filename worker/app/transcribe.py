"""Transcription (F-02): word-level timestamps for the whole VOD.

Primary: Groq Whisper Large v3 Turbo ($0.04/hr, free tier 8 hrs/day).
Audio is chunked to stay under Groq's 100 MB file cap.
Fallback: local faster-whisper (tiny model, CPU) — no API cost, slower.
Returns {"segments": [{start, end, text}], "words": [{w, s, e}], "text": str}.
"""
import io
import math
import os
import subprocess
from pathlib import Path

import httpx

from . import config

GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_MODEL = "whisper-large-v3-turbo"
# 16 kHz mono MP3 is ~16 KB/s; 20 MB chunks stay well under the 100 MB cap.
CHUNK_MB = 20


def _groq_chunk(mp3_bytes: bytes, offset: float) -> dict:
    headers = {"Authorization": f"Bearer {config.GROQ_API_KEY}"}
    files = {"file": ("audio.mp3", io.BytesIO(mp3_bytes), "audio/mpeg")}
    data = {
        "model": GROQ_MODEL,
        "response_format": "verbose_json",
        "timestamp_granularities[]": ["word", "segment"],
    }
    with httpx.Client(timeout=300, verify=config.ssl_context()) as client:
        r = client.post(GROQ_URL, headers=headers, files=files, data=data)
    if r.status_code != 200:
        raise RuntimeError(f"Groq Whisper failed ({r.status_code}): {r.text[:300]}")
    body = r.json()
    segments = [
        {"start": float(s["start"]) + offset, "end": float(s["end"]) + offset,
         "text": s.get("text", "").strip()}
        for s in body.get("segments", []) if s.get("text", "").strip()
    ]
    words = [
        {"w": w["word"].strip(), "s": float(w["start"]) + offset,
         "e": float(w["end"]) + offset}
        for w in body.get("words", []) if w.get("word", "").strip()
    ]
    return {"segments": segments, "words": words, "text": body.get("text", "")}


def transcribe_groq(wav_path: Path) -> dict:
    """Chunk the WAV to MP3 and transcribe each chunk via Groq."""
    size_mb = wav_path.stat().st_size / (1024 * 1024)
    # 16 kHz mono WAV is ~1.9 MB/min, so chunks are ~10 min each at 20 MB.
    chunk_sec = max(60, int(CHUNK_MB / max(size_mb, 0.01) * _wav_duration(wav_path)))
    tmp = wav_path.parent / "groq_chunks"
    tmp.mkdir(exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(wav_path),
         "-f", "segment", "-segment_time", str(chunk_sec),
         "-c:a", "libmp3lame", "-b:a", "32k", str(tmp / "chunk%03d.mp3")],
        check=True, timeout=1800,
    )
    out = {"segments": [], "words": [], "text": ""}
    offset = 0.0
    for chunk in sorted(tmp.glob("chunk*.mp3")):
        res = _groq_chunk(chunk.read_bytes(), offset)
        out["segments"].extend(res["segments"])
        out["words"].extend(res["words"])
        out["text"] += " " + res["text"]
        offset += chunk_sec
    out["text"] = out["text"].strip()
    return out


def _wav_duration(wav_path: Path) -> float:
    import wave
    with wave.open(str(wav_path), "rb") as w:
        return w.getnframes() / w.getframerate()


def transcribe_local(wav_path: Path) -> dict:
    """faster-whisper tiny on CPU. Slow but free; fine for short VODs."""
    from faster_whisper import WhisperModel

    model = WhisperModel("tiny", device="cpu", compute_type="int8", cpu_threads=2)
    segments_iter, _info = model.transcribe(
        str(wav_path), word_timestamps=True, vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
    )
    segments, words, texts = [], [], []
    for seg in segments_iter:
        segments.append({"start": float(seg.start), "end": float(seg.end),
                         "text": seg.text.strip()})
        texts.append(seg.text.strip())
        for w in seg.words or []:
            if w.word.strip():
                words.append({"w": w.word.strip(), "s": float(w.start), "e": float(w.end)})
    return {"segments": segments, "words": words, "text": " ".join(texts)}


def transcribe(wav_path: Path) -> dict:
    """Groq when a key is set, local faster-whisper otherwise."""
    if config.GROQ_API_KEY:
        print("   🎙️ Transcribing via Groq Whisper (turbo)…")
        return transcribe_groq(wav_path)
    print("   🎙️ No GROQ_API_KEY — transcribing locally (faster-whisper tiny)…")
    return transcribe_local(wav_path)
