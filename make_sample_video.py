#!/usr/bin/env python3
"""
make_sample_video.py — Build a small CCTV-style test video with KNOWN
ground truth, so find_face.py can be verified.

Timeline (10s @ 15fps, 640x480):
  0-3s : empty scene (timestamp overlay only)        -> no face
  3-6s : Obama appears (assets/obama2.jpg)           -> SHOULD match obama.jpg
  6-7s : empty scene                                 -> no face
  7-10s: Biden appears (assets/biden.jpg)            -> should NOT match obama.jpg
"""

import os
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
OUT = os.path.join(ASSETS, "sample_cctv.mp4")

W, H, FPS, DURATION = 640, 480, 15, 10


def face_crop(path):
    """Load an image and crop roughly to the head/upper body for a CCTV look."""
    img = cv2.imread(path)
    if img is None:
        raise SystemExit(f"Missing asset: {path}")
    h, w = img.shape[:2]
    side = min(h, w)
    img = img[:side, :side]  # square-ish crop from top
    return cv2.resize(img, (220, 220))


def paste(frame, patch, cx, cy):
    ph, pw = patch.shape[:2]
    x, y = cx - pw // 2, cy - ph // 2
    frame[y:y + ph, x:x + pw] = patch


def main():
    obama = face_crop(os.path.join(ASSETS, "obama2.jpg"))
    biden = face_crop(os.path.join(ASSETS, "biden.jpg"))

    writer = cv2.VideoWriter(OUT, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
    if not writer.isOpened():
        raise SystemExit("VideoWriter failed to open (codec issue).")

    total = FPS * DURATION
    for i in range(total):
        t = i / FPS
        # faux-CCTV gray background with light noise
        frame = np.full((H, W, 3), 60, np.uint8)
        frame += (np.random.rand(H, W, 3) * 12).astype(np.uint8)

        if 3 <= t < 6:
            paste(frame, obama, W // 2, H // 2)
        elif 7 <= t < 10:
            paste(frame, biden, W // 2, H // 2)

        # timestamp overlay, like a CCTV stamp
        cv2.putText(frame, f"CAM-01  t={t:05.2f}s", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        writer.write(frame)

    writer.release()
    print(f"Wrote {OUT}  ({DURATION}s @ {FPS}fps, {W}x{H})")
    print("Ground truth: target (Obama) visible 3.0s-6.0s; Biden 7.0s-10.0s.")


if __name__ == "__main__":
    main()
