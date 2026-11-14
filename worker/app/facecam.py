"""Facecam detection (F-07): find a persistent corner webcam in a clip window.

Runs as a subprocess (`python -m app.facecam <video> <start> <end>`) so the
heavy cv2 import never lives in the API process. Samples up to 8 frames,
runs a Haar cascade, and reports the median face box when the same corner
shows a face in >= 50% of readable frames. Prints JSON:
{"box": [x, y, w, h], "corner": "top-left"|"top-right"|"bottom-left"|"bottom-right"}
or {"box": null}. Never raises — no face just means center-crop.
"""
import json
import sys


def detect(video_path: str, start: float, end: float, samples: int = 8) -> dict:
    import cv2
    import numpy as np

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"box": None}
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    if cascade.empty():
        return {"box": None}

    times = np.linspace(start, max(start + 0.5, end), samples)
    corners: dict = {}
    try:
        for t in times:
            frame_no = int(t * fps)
            if total:
                frame_no = min(frame_no, total - 1)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = cascade.detectMultiScale(gray, 1.15, 5, minSize=(60, 60))
            for (x, y, fw, fh) in faces:
                cx, cy = x + fw / 2, y + fh / 2
                # Corner = face centre in the outer 40% on both axes.
                if cx < 0.4 * w and cy < 0.4 * h:
                    corner = "top-left"
                elif cx > 0.6 * w and cy < 0.4 * h:
                    corner = "top-right"
                elif cx < 0.4 * w and cy > 0.6 * h:
                    corner = "bottom-left"
                elif cx > 0.6 * w and cy > 0.6 * h:
                    corner = "bottom-right"
                else:
                    continue
                corners.setdefault(corner, []).append(
                    [int(x), int(y), int(fw), int(fh)])
    finally:
        cap.release()

    if not corners:
        return {"box": None}
    # The corner seen most; needs >= half the sampled frames.
    corner, boxes = max(corners.items(), key=lambda kv: len(kv[1]))
    if len(boxes) < max(2, samples // 2):
        return {"box": None}
    med = [int(np.median([b[i] for b in boxes])) for i in range(4)]
    return {"box": med, "corner": corner, "frames": len(boxes)}


if __name__ == "__main__":
    video, start, end = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
    print(json.dumps(detect(video, start, end)))
