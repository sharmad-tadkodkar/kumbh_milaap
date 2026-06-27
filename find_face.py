#!/usr/bin/env python3
"""
find_face.py — Find whether a given face (from a photo) appears in a video
(e.g. CCTV mp4) and report the timestamps where it shows up.

Uses OpenCV's built-in models (no dlib / heavy ML frameworks required):
  - YuNet  : fast face DETECTION
  - SFace  : face RECOGNITION (128-d embedding + cosine similarity)

Example:
  python3 find_face.py --photo assets/obama.jpg --video assets/sample_cctv.mp4
  python3 find_face.py --photo me.jpg --video cctv.mp4 --interval 0.5 --annotate out.mp4
"""

import argparse
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DETECTOR_PATH = os.path.join(HERE, "models", "face_detection_yunet_2023mar.onnx")
RECOGNIZER_PATH = os.path.join(HERE, "models", "face_recognition_sface_2021dec.onnx")

# SFace cosine similarity: higher = more similar. OpenCV's reference
# decision threshold for "same person" is 0.363. We default a touch higher
# to keep false positives down; lower it if you miss real appearances.
DEFAULT_THRESHOLD = 0.40


def load_models(score_threshold=0.8):
    if not os.path.exists(DETECTOR_PATH) or not os.path.exists(RECOGNIZER_PATH):
        sys.exit(
            "Model files missing under ./models. Expected:\n"
            f"  {DETECTOR_PATH}\n  {RECOGNIZER_PATH}"
        )
    detector = cv2.FaceDetectorYN.create(
        DETECTOR_PATH, "", (320, 320),
        score_threshold=score_threshold, nms_threshold=0.3, top_k=5000,
    )
    recognizer = cv2.FaceRecognizerSF.create(RECOGNIZER_PATH, "")
    return detector, recognizer


def detect_faces(detector, img):
    """Return the YuNet face rows (each is a 15-value array) for an image."""
    h, w = img.shape[:2]
    detector.setInputSize((w, h))
    _, faces = detector.detect(img)
    return faces if faces is not None else np.empty((0, 15), dtype=np.float32)


def embed(recognizer, img, face_row):
    """Align/crop a detected face and return its normalized feature vector."""
    aligned = recognizer.alignCrop(img, face_row)
    return recognizer.feature(aligned)


def reference_embedding(detector, recognizer, photo_path):
    img = cv2.imread(photo_path)
    if img is None:
        sys.exit(f"Could not read photo: {photo_path}")
    faces = detect_faces(detector, img)
    if len(faces) == 0:
        sys.exit(f"No face found in the reference photo: {photo_path}")
    # If several faces, use the largest (by box area).
    largest = max(faces, key=lambda f: f[2] * f[3])
    return embed(recognizer, img, largest)


def fmt_ts(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def merge_hits(hits, max_gap):
    """Group individual frame hits into continuous appearance intervals.

    hits: list of (timestamp_seconds, score). Returns list of dicts.
    """
    if not hits:
        return []
    hits = sorted(hits)
    intervals = []
    start, last, best = hits[0][0], hits[0][0], hits[0][1]
    for ts, score in hits[1:]:
        if ts - last <= max_gap:
            last = ts
            best = max(best, score)
        else:
            intervals.append({"start": start, "end": last, "best": best})
            start, last, best = ts, ts, score
    intervals.append({"start": start, "end": last, "best": best})
    return intervals


def search_video(detector, recognizer, ref, video_path,
                 threshold=DEFAULT_THRESHOLD, interval=0.5,
                 annotate=None, verbose=True):
    """Search one video for the reference face.

    Returns a list of appearance intervals (dicts with start/end/best), or
    raises IOError if the video can't be opened. Reusable by the chained
    runner (search_missing_person.py) as well as this script's CLI.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = total / fps if total else 0
    frame_skip = max(1, int(round(fps * interval)))
    if verbose:
        print(f"[*] Video: {video_path}  fps={fps:.2f}  frames={total}  "
              f"duration={fmt_ts(duration)}")
        print(f"[*] Sampling every {frame_skip} frame(s) (~{interval}s); "
              f"threshold={threshold}\n")

    writer = None
    if annotate:
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        writer = cv2.VideoWriter(
            annotate, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    hits = []
    frame_idx = -1
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_idx += 1
        if frame_idx % frame_skip != 0:
            continue

        ts = frame_idx / fps
        faces = detect_faces(detector, frame)
        best_score = -1.0
        for f in faces:
            score = recognizer.match(
                ref, embed(recognizer, frame, f), cv2.FaceRecognizerSF_FR_COSINE)
            if score > best_score:
                best_score = score
            if score >= threshold and writer is not None:
                x, y, bw, bh = f[:4].astype(int)
                cv2.rectangle(frame, (x, y), (x + bw, y + bh), (0, 255, 0), 2)
                cv2.putText(frame, f"MATCH {score:.2f}", (x, max(0, y - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        if best_score >= threshold:
            hits.append((ts, float(best_score)))
            if verbose:
                print(f"  [HIT ] {fmt_ts(ts)}  cosine={best_score:.3f}")

        if writer is not None:
            writer.write(frame)

    cap.release()
    if writer is not None:
        writer.release()

    # An appearance is a run of hits; allow a small gap so brief misses
    # (occlusion, blur) don't split one appearance into many.
    return merge_hits(hits, max_gap=interval * 4)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--photo", required=True, help="Reference face image")
    ap.add_argument("--video", required=True, help="Video file (e.g. CCTV .mp4)")
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                    help=f"Cosine match threshold (default {DEFAULT_THRESHOLD}; "
                         "OpenCV same-person reference is 0.363)")
    ap.add_argument("--interval", type=float, default=0.5,
                    help="Seconds between sampled frames (default 0.5)")
    ap.add_argument("--annotate", metavar="OUT.mp4",
                    help="Optional: write a copy of the video with match boxes drawn")
    args = ap.parse_args()

    detector, recognizer = load_models()
    ref = reference_embedding(detector, recognizer, args.photo)
    print(f"[*] Reference face loaded from {args.photo}")

    try:
        intervals = search_video(
            detector, recognizer, ref, args.video,
            threshold=args.threshold, interval=args.interval,
            annotate=args.annotate)
    except IOError as e:
        sys.exit(str(e))

    print("\n" + "=" * 60)
    if not intervals:
        print("RESULT: face NOT found in the video.")
        sys.exit(1)

    print(f"RESULT: face FOUND in {len(intervals)} appearance(s):")
    for i, iv in enumerate(intervals, 1):
        if iv["end"] - iv["start"] < 1e-3:
            when = f"at {fmt_ts(iv['start'])}"
        else:
            when = f"{fmt_ts(iv['start'])} -> {fmt_ts(iv['end'])}"
        print(f"  {i}. {when}  (peak cosine {iv['best']:.3f})")
    if args.annotate:
        print(f"\nAnnotated video written to: {args.annotate}")


if __name__ == "__main__":
    main()
