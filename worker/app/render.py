"""Render (F-07, F-08, F-10): 9:16 reframe + animated captions + MP4 export.

- Facecam split: webcam crop on top, gameplay below (vstack). No webcam:
  action-tracked center crop (centered; the crop follows the loudest
  half of the clip when the energy moves — P0 keeps it centered).
- Captions: Remotion first (animated word-by-word highlight + hook
  animation over a clean ffmpeg reframe); ffmpeg + ASS karaoke is the
  always-working fallback. Hook text is over the first 3 seconds.
- Free tier: small "Hookclip" watermark, bottom-right. Paid: clean.
- After export, Auto-Editor trims silent sections best-effort.
- One ffmpeg call per clip. 1080x1920 H.264 + AAC.
"""
import glob
import subprocess
import textwrap
from pathlib import Path

OUT_W, OUT_H = 1080, 1920
HALF_H = OUT_H // 2


def _font_path() -> str:
    for pat in ("/usr/share/fonts/**/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/**/DejaVuSans.ttf"):
        hits = sorted(glob.glob(pat, recursive=True))
        if hits:
            return hits[0]
    return "sans-serif"


def _ass_time(t: float) -> str:
    t = max(0.0, t)
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


STYLES = {
    # name -> (font, size, primary, outline, highlight, bold)
    "bold": ("DejaVu Sans", 64, "&H00FFFFFF", "&H00000000", "&H0000CCFF", -1),
    "minimal": ("DejaVu Sans", 54, "&H00FFFFFF", "&H00000000", "&H00FFFFFF", 0),
    "pop": ("DejaVu Sans", 68, "&H0000CCFF", "&H00000000", "&H00FFFFFF", -1),
}


def build_ass(words: list, start: float, end: float, hook_text: str,
              style: str, out_path: Path) -> Path:
    """ASS file, times relative to the clip start."""
    font, size, primary, outline, highlight, bold = STYLES.get(style, STYLES["bold"])
    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {OUT_W}",
        f"PlayResY: {OUT_H}",
        "WrapStyle: 2",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Caption,{font},{size},{primary},{highlight},{outline},"
        f"&H80000000,{bold},0,0,0,100,100,0,0,1,4,0,2,40,40,150,1",
        f"Style: Hook,{font},76,&H0000CCFF,{highlight},{outline},"
        f"&H80000000,-1,0,0,0,100,100,0,0,1,5,0,8,60,60,260,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, "
        "Effect, Text",
    ]
    # Hook: first 3 seconds, top-centre. Pre-wrapped with explicit \N
    # breaks: libass did not wrap the single-line event on its own, so a
    # 34-char hook at 76pt overflowed both edges of the 1080px frame
    # (seen on the Nov 14 E2E clip). ~22 chars/line fits 960px at 76pt;
    # shrink to 64pt if it still needs more than 2 lines.
    if hook_text:
        hook = " ".join(hook_text.replace("\n", " ").split())
        wrapped = textwrap.wrap(hook, width=22)
        size = 76
        if len(wrapped) > 2:
            wrapped = textwrap.wrap(hook, width=27)
            size = 64
        if len(wrapped) > 2:
            wrapped = wrapped[:2]
            wrapped[1] = wrapped[1].rstrip(".!?,") + "…"
        hook = "\\N".join(wrapped)
        lines.append(
            f"Dialogue: 0,{_ass_time(0)},{_ass_time(3.0)},Hook,,0,0,0,,{hook}")
        # Hook style fontsize is set per-event via an override tag so the
        # 64pt fallback above actually applies.
        lines[-1] = lines[-1].replace(
            ",Hook,,0,0,0,,",
            f",Hook,,0,0,0,,{{\\fs{size}}}", 1) if size != 76 else lines[-1]

    # Captions: group words into lines of ~5 words / <= 3s, karaoke per word.
    clip_words = [w for w in words if w["e"] > start and w["s"] < end]
    group: list = []
    group_start = None
    for w in clip_words:
        if group_start is None:
            group_start = w["s"]
        group.append(w)
        last = group[-1]
        if len(group) >= 5 or (last["e"] - group_start) >= 2.5:
            _emit_caption(lines, group, start, end)
            group, group_start = [], None
    if group:
        _emit_caption(lines, group, start, end)

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def _emit_caption(lines: list, group: list, clip_start: float, clip_end: float):
    s = max(0.0, group[0]["s"] - clip_start - 0.05)
    e = min(clip_end - clip_start, group[-1]["e"] - clip_start + 0.25)
    if e <= s:
        return
    parts = []
    for w in group:
        dur_cs = max(1, int(round((w["e"] - w["s"]) * 100)))
        text = w["w"].replace("{", "").replace("}", "")
        parts.append(f"{{\\kf{dur_cs}}}{text}")
    lines.append(
        f"Dialogue: 0,{_ass_time(s)},{_ass_time(e)},Caption,,0,0,0,,{' '.join(parts)}")


def _probe_size(video_path: Path) -> tuple:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0",
         str(video_path)],
        capture_output=True, text=True, timeout=60,
    )
    w, h = (r.stdout.strip().split(",") + ["1920", "1080"])[:2]
    return int(w), int(h)


def _reframe_vf(source: Path, facecam_box: dict | None) -> str:
    """The 9:16 reframe filtergraph (facecam split or centre crop),
    ending at [vpre]. Shared by the ASS path and the Remotion path
    (Remotion needs the same reframe, without captions, as its input)."""
    src_w, src_h = _probe_size(source)
    if facecam_box:
        x, y, fw, fh = facecam_box
        # Facecam crop: box expanded a little, centred on the face.
        pad = 0.35
        cw = min(src_w, int(fw * (1 + pad * 2)))
        ch = min(src_h, int(fh * (1 + pad * 2)))
        cx = max(0, min(src_w - cw, int(x + fw / 2 - cw / 2)))
        cy = max(0, min(src_h - ch, int(y + fh / 2 - ch / 2)))
        cw -= cw % 2
        ch -= ch % 2
        # Gameplay crop: centre crop to the bottom-half aspect.
        gw = min(src_w, int(src_h * OUT_W / HALF_H))
        gw -= gw % 2
        gx = max(0, (src_w - gw) // 2)
        return (
            f"[0:v]split=2[ta][ba];"
            f"[ta]crop=w={cw}:h={ch}:x={cx}:y={cy},scale={OUT_W}:{HALF_H}[top];"
            f"[ba]crop=w={gw}:h={src_h}:x={gx}:y=0,scale={OUT_W}:{HALF_H}[bot];"
            f"[top][bot]vstack=inputs=2,setsar=1[vpre]"
        )
    cw = int(src_h * 9 / 16)
    cw -= cw % 2
    cx = max(0, (src_w - cw) // 2)
    return (f"[0:v]crop=w={cw}:h={src_h}:x={cx}:y=0,"
            f"scale={OUT_W}:{OUT_H},setsar=1[vpre]")


def _render_clean(source: Path, start: float, end: float,
                  facecam_box: dict | None, out_path: Path) -> Path:
    """Reframe only, no captions/watermark — the clean input clip that
    Remotion overlays its animated captions onto. Raises on failure."""
    duration = max(1.0, end - start)
    vf = _reframe_vf(source, facecam_box) + ";[vpre]null[vout]"
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-ss", str(round(start, 2)), "-t", str(round(duration, 2)),
        "-i", str(source),
        "-filter_complex", vf,
        "-map", "[vout]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart",
        str(out_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if r.returncode != 0 or not out_path.exists():
        raise RuntimeError(f"ffmpeg clean render failed: {(r.stderr or '').strip()[-500:]}")
    return out_path


def render_clip(source: Path, start: float, end: float, hook_text: str,
                caption_style: str, watermark: bool, out_path: Path,
                facecam_box: dict | None, words: list) -> Path:
    """Render one clip. Returns out_path. Raises RuntimeError on failure."""
    duration = max(1.0, end - start)
    ass_path = out_path.with_suffix(".ass")
    build_ass(words, start, end, hook_text, caption_style, ass_path)

    # Reframe filtergraph.
    vf = _reframe_vf(source, facecam_box)

    # ASS subtitles need an escaped path (colons break the filter parser).
    ass_escaped = str(ass_path).replace(":", "\\:").replace("'", "\\'")
    vf += f";[vpre]subtitles=filename='{ass_escaped}'[vsub]"
    last = "vsub"
    if watermark:
        font = _font_path()
        vf += (
            f";[{last}]drawtext=text='Hookclip':fontfile={font}:fontsize=30:"
            f"fontcolor=white@0.7:borderw=1:bordercolor=black@0.5:"
            f"x=w-tw-28:y=h-th-28[vout]"
        )
        last = "vout"
    else:
        vf += f";[{last}]null[vout]"

    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-ss", str(round(start, 2)), "-t", str(round(duration, 2)),
        "-i", str(source),
        "-filter_complex", vf,
        "-map", "[vout]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart",
        str(out_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if r.returncode != 0 or not out_path.exists():
        raise RuntimeError(f"ffmpeg render failed: {(r.stderr or '').strip()[-500:]}")
    return out_path


def render_clip_smart(source: Path, start: float, end: float, hook_text: str,
                      caption_style: str, watermark: bool, out_path: Path,
                      facecam_box: dict | None, words: list) -> tuple:
    """Remotion-first render; ffmpeg+ASS fallback; silence trim last.

    1. ffmpeg reframes the source into a clean clip (no captions).
    2. Remotion overlays animated word-by-word captions + hook on it.
       Any failure here -> the ffmpeg+ASS path above (always works).
    3. Auto-Editor trims silent sections best-effort (never fails the job).

    Returns (out_path, backend) with backend in {"remotion", "ffmpeg"}.
    Raises only if the ffmpeg fallback itself fails.
    """
    from . import remotion_render, trim

    clean = out_path.with_name(out_path.stem + ".clean.mp4")
    backend = "ffmpeg"
    try:
        _render_clean(source, start, end, facecam_box, clean)
        rem = remotion_render.render_with_remotion(
            clean, words, start, end, hook_text, watermark, out_path)
        if rem is not None:
            backend = "remotion"
    except Exception as e:
        print(f"   ⚠️ Remotion path failed ({type(e).__name__}: {e}) "
              f"— ffmpeg fallback.")
    finally:
        clean.unlink(missing_ok=True)
    if backend == "ffmpeg":
        render_clip(source, start, end, hook_text, caption_style,
                    watermark, out_path, facecam_box, words)
    try:
        trim.trim_silence(out_path)
    except Exception as e:
        print(f"   ℹ️ silence trim skipped ({type(e).__name__}: {e})")
    return out_path, backend
