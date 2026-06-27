#!/usr/bin/env python3
"""
server.py — HTTP wrapper around the missing-person search.

Exposes the same flow as search_missing_person.py over HTTP so the Next.js
frontend (deployed separately, e.g. on Vercel) can call it directly:

    POST /api/search   (multipart: photo, lat, lon[, threshold])
        -> { found, cameras: [{ id, zone, distance, firstAppears }], summary }
    GET  /health       -> { ok: true }

Reuses the existing logic — no algorithm rewrite:
  - select_cctvs.{load_mapping, resolve_zone, select_cameras}
  - find_face.{load_models, reference_embedding, search_video, fmt_ts}

The face models are loaded once at startup and reused across requests.
"""

import os
import tempfile

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import find_face
import select_cctvs

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FOOTAGE_DIR = os.path.join(HERE, "assets", "footage")

app = FastAPI(title="Milaap Search API", version="1.0.0")

# Demo backend — allow any origin so the Vercel frontend can call it directly.
# Tighten `allow_origins` to your Vercel domain for a real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the CCTV mapping and face models once, at process start.
_mapping = select_cctvs.load_mapping()
_detector, _recognizer = find_face.load_models()


def _footage_path(footage_dir, camera_id, ext):
    return os.path.join(footage_dir, f"{camera_id}.{ext.lstrip('.')}")


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/api/search")
async def search(
    photo: UploadFile = File(...),
    lat: float = Form(...),
    lon: float = Form(...),
    threshold: float = Form(find_face.DEFAULT_THRESHOLD),
    interval: float = Form(0.5),
    batch: int = Form(10),
    max_cameras: int = Form(30),
    ext: str = Form("mp4"),
):
    """Mirror search_missing_person.main(): select nearest cameras, scan each in
    order, stop at the first match, and report camera id + first-appearance."""
    # Persist the uploaded photo so OpenCV can read it from disk.
    suffix = os.path.splitext(photo.filename or "upload.jpg")[1] or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await photo.read())
        photo_path = tmp.name

    try:
        zone_key, inside = select_cctvs.resolve_zone(_mapping, lat, lon)
        ref = find_face.reference_embedding(_detector, _recognizer, photo_path)

        limit = None if max_cameras == 0 else max_cameras
        cameras = select_cctvs.select_cameras(
            _mapping, lat, lon, batch=batch, max_cameras=limit)

        checked = skipped = 0
        found = []
        for cam in cameras:
            path = _footage_path(DEFAULT_FOOTAGE_DIR, cam["id"], ext)
            if not os.path.exists(path):
                skipped += 1
                continue
            checked += 1
            try:
                intervals = find_face.search_video(
                    _detector, _recognizer, ref, path,
                    threshold=threshold, interval=interval, verbose=False)
            except IOError:
                continue
            if intervals:
                found.append({
                    "id": cam["id"],
                    "zone": str(cam["zone"]),
                    "distance": round(cam["distance_m"]),
                    "firstAppears": find_face.fmt_ts(intervals[0]["start"]),
                })
                break  # stop at first camera with a match

        summary = (f"Checked {checked} camera(s), skipped {skipped} "
                   f"(no footage). Last seen → Zone {zone_key} "
                   f"({'inside' if inside else 'nearest'}).")
        return {"found": bool(found), "cameras": found, "summary": summary}
    finally:
        try:
            os.unlink(photo_path)
        except OSError:
            pass
