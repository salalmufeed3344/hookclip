"""Scene cuts (PySceneDetect): a new detection signal (F-04).

PySceneDetect's ContentDetector finds the hard cuts in the source video.
Candidate moments are then snapped to the nearest cut so a clip never
starts mid-cut — the cut is the natural edit point. All best effort:
[] on any failure (missing lib, unreadable file), so detection keeps
working exactly as before.
"""
from pathlib import Path


def detect_scene_cuts(video_path, threshold: float = 27.0,
                      min_scene_len: int = 15,
                      start: float | None = None,
                      end: float | None = None,
                      frame_skip: int = 1) -> list:
    """-> sorted list of cut timestamps in seconds (start of each scene
    after the first). Empty list on any failure.

    Windowed by default in production (jobs.py scans only the span
    covering the candidate moments): scanning a whole VOD costs ~3x
    realtime on CPU — the 458s test VOD (VP9, 60fps) needed 24 min of
    CPU and never finished in the time we gave it — because OpenCV must
    software-decode every frame and the 2x downscale only shrinks the
    detector's working frame, not the decode. A 3-hour VOD would take
    ~9 hours. So production passes start/end (the candidate span) and
    this seeks there first; whole-video scans are for short clips only.
    frame_skip=1 processes every 2nd frame (30fps effective): cuts land
    within ~33ms, plenty for the 5s snap tolerance, at half the cost.
    Cut timestamps are ABSOLUTE video seconds (seek + duration window)."""
    try:
        # PySceneDetect 0.7 API (pinned: scenedetect==0.7.3). NOTE: 0.7
        # REMOVED VideoManager entirely — `from scenedetect import
        # VideoManager` raises ImportError; the 0.7 way is open_video +
        # SceneManager.detect_scenes(video). Downscaling moved to the
        # SceneManager too (auto_downscale must be off for it to apply).
        from scenedetect import ContentDetector, SceneManager, open_video
    except Exception as e:
        print(f"   ℹ️ PySceneDetect unavailable ({type(e).__name__}: {e})")
        return []
    video = None
    try:
        video = open_video(str(video_path))
        scene_manager = SceneManager()
        scene_manager.auto_downscale = False
        scene_manager.downscale = 2
        scene_manager.add_detector(
            ContentDetector(threshold=threshold,
                            min_scene_len=min_scene_len))
        duration = None
        if start is not None:
            video.seek(start)
            if end is not None:
                duration = max(0.0, end - start)
        scene_manager.detect_scenes(video, duration=duration,
                                    frame_skip=frame_skip)
        scenes = scene_manager.get_scene_list()
    except Exception as e:
        print(f"   ℹ️ scene detection failed ({type(e).__name__}: {e})")
        return []
    finally:
        try:
            if video is not None:
                video.close()
        except Exception:
            pass
    # scenes are (start, end) Timecodes; cuts are the start of every
    # scene after the first.
    cuts = [round(s[0].get_seconds(), 2) for s in scenes[1:]]
    return sorted(c for c in cuts if c > 0)


def snap_to_scene_cuts(start: float, end: float, cuts: list,
                       tolerance: float = 5.0) -> tuple:
    """Snap clip edges to the nearest scene cut within `tolerance`.

    Start pulls BACK to the nearest cut at or before it (the cut is where
    the new shot begins, so the clip opens on it); end pushes FORWARD to
    the nearest cut at or after it. Returns (start, end, info) where info
    is {"scene_start": cut|None, "scene_end": cut|None}.
    """
    info = {"scene_start": None, "scene_end": None}
    if not cuts:
        return start, end, info
    before = [c for c in cuts if c <= start and start - c <= tolerance]
    if before:
        start = max(before)
        info["scene_start"] = start
    after = [c for c in cuts if c >= end and c - end <= tolerance]
    if after:
        end = min(after)
        info["scene_end"] = end
    return start, end, info


def snap_candidates(candidates: list, cuts: list,
                    max_len: float = 60.0) -> list:
    """Snap each candidate's edges to the nearest scene cut (same logic
    candidate_moments applies when it is given scene_cuts: record
    scene_start/scene_end in signals, re-clamp to max_len, drop clips
    under 10s). Returns the snapped list. No cuts -> unchanged."""
    if not cuts:
        return candidates
    out = []
    for c in candidates:
        s, e, cut_info = snap_to_scene_cuts(float(c["start"]),
                                            float(c["end"]), cuts)
        for k, v in cut_info.items():
            if v is not None:
                c["signals"][k] = v
        if e - s > max_len:
            e = s + max_len
        if e - s < 10:
            continue
        c = dict(c)
        c["start"] = s
        c["end"] = e
        out.append(c)
    return out
