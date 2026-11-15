"""Transcription (F-02): word-level timestamps for the whole VOD.

Primary: Groq Whisper Large v3 Turbo ($0.04/hr, free tier 8 hrs/day).
Audio is chunked to stay under Groq's 100 MB file cap.
Local: WhisperX (word alignment + optional diarization), falling back to
faster-whisper (tiny model, CPU) if WhisperX is missing or fails.
Returns {"segments": [{start, end, text}], "words": [{w, s, e}],
"text": str, "backend": str}.
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


def transcribe_whisperx(wav_path: Path) -> dict:
    """WhisperX on CPU: precise word timestamps (alignment model) +
    optional speaker diarization (pyannote, needs an HF token).

    Model size from $WHISPERX_MODEL (default "base"). Raises on any
    failure — the caller falls back to faster-whisper. Diarization is
    best effort inside this function: a failure there never loses the
    transcript, it just leaves "speakers" out.
    """
    import whisperx

    model_size = os.environ.get("WHISPERX_MODEL", "base").strip() or "base"
    try:
        import torch
        torch.set_num_threads(2)
    except Exception:
        pass
    model = whisperx.load_model(model_size, "cpu", compute_type="int8")
    audio = whisperx.load_audio(str(wav_path))
    result = model.transcribe(audio, batch_size=4)
    lang = (result.get("language") or "en").split("-")[0]
    model_a, metadata = whisperx.load_align_model(
        language_code=lang, device="cpu")
    result = whisperx.align(result["segments"], model_a, metadata,
                            audio, "cpu", return_char_alignments=False)
    # Diarization: only with an HF token (pyannote models are gated).
    token = (os.environ.get("HF_TOKEN", "")
             or os.environ.get("HUGGING_FACE_HUB_TOKEN", ""))
    if token:
        try:
            diarize_model = whisperx.DiarizationPipeline(
                use_auth_token=token, device="cpu")
            diarize_segments = diarize_model(audio)
            result = whisperx.assign_word_speakers(
                diarize_segments, result)
            speakers = sorted({w.get("speaker") for s in result["segments"]
                               for w in (s.get("words") or [])
                               if w.get("speaker")})
            print(f"   🗣️ WhisperX diarization: {len(speakers)} speaker(s).")
        except Exception as e:
            print(f"   ℹ️ WhisperX diarization skipped "
                  f"({type(e).__name__}: {e})")
    segments, words, texts = [], [], []
    for seg in result.get("segments", []):
        segments.append({"start": float(seg["start"]), "end": float(seg["end"]),
                         "text": (seg.get("text") or "").strip()})
        texts.append((seg.get("text") or "").strip())
        for w in seg.get("words") or []:
            if (w.get("word") or "").strip():
                entry = {"w": w["word"].strip(), "s": float(w["start"]),
                         "e": float(w["end"])}
                if w.get("speaker"):
                    entry["speaker"] = str(w["speaker"])
                words.append(entry)
    return {"segments": segments, "words": words, "text": " ".join(texts),
            "backend": "whisperx", "model": f"whisperx-{model_size}"}


def transcribe(wav_path: Path) -> dict:
    """Groq when a key is set, WhisperX locally, faster-whisper last.

    Order: Groq (cheap/fast, primary) -> WhisperX (precise word timings
    + diarization, no API cost) -> faster-whisper tiny (the old fallback).
    Each step degrades to the next on failure; a job never crashes here.
    """
    if config.GROQ_API_KEY:
        print("   🎙️ Transcribing via Groq Whisper (turbo)…")
        result = transcribe_groq(wav_path)
        result["backend"] = "groq"
        return result
    if not os.environ.get("WHISPERX_DISABLE"):
        try:
            print("   🎙️ No GROQ_API_KEY — transcribing locally (WhisperX)…")
            return transcribe_whisperx(wav_path)
        except Exception as e:
            print(f"   ⚠️ WhisperX failed ({type(e).__name__}: {e}) — "
                  f"falling back to faster-whisper.")
    print("   🎙️ Transcribing locally (faster-whisper tiny)…")
    result = transcribe_local(wav_path)
    result["backend"] = "faster-whisper"
    return result
