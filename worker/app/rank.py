"""Ranking (F-05, F-06): score 0–99 + plain-words reason + 3 hooks per moment.

Primary: Gemini 2.5 Flash-Lite on candidate windows only (never the full
VOD) — ~1,000 input + ~300 output tokens per source minute.
Fallback (no key): a deterministic heuristic scorer + template hooks, so
the pipeline still works end to end. The score is a RANKING tool, not a
view guarantee — the UI says so.
"""
import json
import re

from . import config

# Words that mark excitement / payoff in a transcript. Heuristic only.
EXCITED = re.compile(
    r"\b(oh my god|omg|no way|what the|holy|insane|crazy|let'?s go|"
    r"wow|whoa|unbelievable|noooo+|yess+|come on|look at that|"
    r"did you see|that was)\b", re.I)


def _heuristic_score(c: dict) -> tuple:
    """(score 0–99, reason). Signal-weighted, capped, deterministic."""
    s = c.get("signals", {})
    score = 30.0  # every candidate starts watchable
    parts = []
    chat = float(s.get("chat_ratio", 0))
    if chat:
        score += min(30.0, (chat - 1) * 8)
        parts.append(f"chat spiked {chat:g}x")
    audio = float(s.get("audio_spike", 0))
    if audio:
        score += min(15.0, (audio - 1) * 5)
        parts.append("loud moment" if audio >= 2 else "raised voices")
    if s.get("viewer_clips"):
        score += 10
        parts.append(f"viewers clipped it ({s.get('viewer_views', 0):,} views)")
    text = c.get("transcript", "")
    hits = len(EXCITED.findall(text))
    if hits:
        score += min(10.0, hits * 3)
        parts.append("excited reaction")
    if "?" in text:
        score += 3
        parts.append("a question")
    if len(text) < 40:
        score -= 10
        parts.append("little dialogue")
    score = max(5, min(99, round(score)))
    reason = " + ".join(parts) if parts else "steady moment"
    return score, reason


def _template_hooks(c: dict) -> list:
    """Three hook options without an LLM: first strong line, a question,
    and a stakes line. Ranked by predicted 3-second hold (line > question
    > stakes is the usual order for gameplay clips)."""
    text = (c.get("transcript", "") or "").strip()
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    first = sentences[0] if sentences else "Watch what happens next."
    if len(first) > 90:
        first = first[:87].rsplit(" ", 1)[0] + "…"
    hooks = [first]
    # Question hook: turn a statement into a hook, or fall back.
    q = None
    for s in sentences:
        if s.endswith("?"):
            q = s
            break
    hooks.append(q if q else "What happens next? You have to see this.")
    hooks.append("This is the clip everyone will be talking about.")
    return [{"text": h, "rank": i + 1} for i, h in enumerate(hooks[:3])]


def _gemini_score(candidates: list) -> list | None:
    """One Gemini call for all candidates. Returns a list of dicts
    [{score, reason, hooks:[{text, rank}]}] or None on any failure."""
    try:
        from google import genai
        from google.genai import types as genai_types
        from pydantic import BaseModel

        class Hook(BaseModel):
            text: str
            rank: int

        class MomentScore(BaseModel):
            score: int
            reason: str
            hooks: list[Hook]

        class Answer(BaseModel):
            moments: list[MomentScore]

        client = genai.Client(api_key=config.GEMINI_API_KEY)
        payload = [
            {"i": i, "signals": c["signals"], "transcript": c.get("transcript", "")}
            for i, c in enumerate(candidates)
        ]
        prompt = (
            "You rank short clips from a gaming stream for TikTok/Reels/Shorts.\n"
            "For EACH candidate, score 0-99 on hook strength, emotional flow, "
            "value, and trend alignment. Give a plain-words reason (e.g. "
            "'chat spiked 8x + laughter + fail'). Write 3 hook options — the "
            "first 3 seconds of on-screen text — ranked by predicted hold.\n"
            "Score is a ranking tool, not a view guarantee. Answer JSON only.\n\n"
            + json.dumps(payload)
        )
        resp = client.models.generate_content(
            model=config.GEMINI_MODEL, contents=prompt,
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json", response_schema=Answer,
                max_output_tokens=4000,
            ),
        )
        answer = json.loads(resp.text)
        out = []
        for m in answer.get("moments", []):
            hooks = sorted(m.get("hooks", []), key=lambda h: h.get("rank", 99))[:3]
            out.append({
                "score": max(1, min(99, int(m.get("score", 50)))),
                "reason": str(m.get("reason", ""))[:200],
                "hooks": [{"text": h["text"][:120], "rank": i + 1}
                          for i, h in enumerate(hooks)] or None,
            })
        if len(out) != len(candidates):
            return None
        return out
    except Exception as e:
        print(f"   ⚠️ Gemini scoring failed ({type(e).__name__}: {e}) — heuristic fallback.")
        return None


def rank_moments(candidates: list) -> list:
    """Attach score, reason, hooks to each candidate; sort best first."""
    if not candidates:
        return []
    gemini = _gemini_score(candidates) if config.GEMINI_API_KEY else None
    out = []
    for i, c in enumerate(candidates):
        if gemini and gemini[i].get("hooks"):
            score, reason, hooks = (gemini[i]["score"], gemini[i]["reason"],
                                    gemini[i]["hooks"])
        else:
            score, reason = _heuristic_score(c)
            hooks = _template_hooks(c)
        out.append({**c, "score": score, "reason": reason, "hooks": hooks})
    out.sort(key=lambda m: -m["score"])
    return out
