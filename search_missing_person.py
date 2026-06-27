#!/usr/bin/env python3
"""
search_missing_person.py — End-to-end missing-person search.

Given a photo of the missing person and the lat/lon where they were last seen,
this:
  1. picks the nearest CCTV cameras (via select_cctvs, zone-aware, batched),
  2. maps each camera id -> its footage file,
  3. runs the face matcher (find_face.search_video) on each in order,
  4. stops at the first camera where the face appears and reports the camera id
     + timestamp(s); keeps going through batches until found or cameras run out.

Footage convention (override with --footage-dir / --ext):
    <footage-dir>/<camera-id>.<ext>      e.g.  assets/footage/Z1-C1.mp4

Cameras with no footage file on disk are skipped (logged), so a partial
deployment still works.

Example:
  python3 search_missing_person.py \
      --photo assets/obama.jpg --lat 19.9837 --lon 73.7118 \
      --footage-dir assets/footage
"""

import argparse
import os
import sys

import find_face
import select_cctvs

HERE = os.path.dirname(os.path.abspath(__file__))


def footage_path(footage_dir, camera_id, ext):
    return os.path.join(footage_dir, f"{camera_id}.{ext.lstrip('.')}")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--photo", required=True, help="Photo of the missing person")
    ap.add_argument("--lat", type=float, required=True, help="Last-seen latitude")
    ap.add_argument("--lon", type=float, required=True, help="Last-seen longitude")
    ap.add_argument("--footage-dir", default=os.path.join(HERE, "assets", "footage"),
                    help="Directory of CCTV footage named <camera-id>.<ext>")
    ap.add_argument("--ext", default="mp4", help="Footage file extension (default mp4)")
    ap.add_argument("--batch", type=int, default=10, help="Cameras per batch (default 10)")
    ap.add_argument("--max", type=int, default=30, dest="max_cameras",
                    help="Max cameras to check before giving up (default 30; 0 = all)")
    ap.add_argument("--threshold", type=float, default=find_face.DEFAULT_THRESHOLD,
                    help="Face match cosine threshold")
    ap.add_argument("--interval", type=float, default=0.5,
                    help="Seconds between sampled frames")
    ap.add_argument("--all", action="store_true",
                    help="Don't stop at first match; check every selected camera")
    args = ap.parse_args()

    mapping = select_cctvs.load_mapping()
    zone_key, inside = select_cctvs.resolve_zone(mapping, args.lat, args.lon)
    note = "inside" if inside else "nearest (point outside all zones)"
    print(f"[*] Last seen ({args.lat}, {args.lon}) -> Zone {zone_key} ({note})")

    # Load the face models once and reuse across all videos.
    detector, recognizer = find_face.load_models()
    ref = find_face.reference_embedding(detector, recognizer, args.photo)
    print(f"[*] Reference face loaded from {args.photo}")
    print(f"[*] Footage: {args.footage_dir}/<id>.{args.ext}\n")

    limit = None if args.max_cameras == 0 else args.max_cameras
    cameras = select_cctvs.select_cameras(
        mapping, args.lat, args.lon, batch=args.batch, max_cameras=limit)

    checked = skipped = 0
    found = []
    current_batch = None
    for cam in cameras:
        if cam["batch"] != current_batch:
            current_batch = cam["batch"]
            print(f"--- Batch {current_batch} "
                  f"(cameras {(current_batch - 1) * args.batch + 1}"
                  f"-{current_batch * args.batch}) ---")

        path = footage_path(args.footage_dir, cam["id"], args.ext)
        tag = f"#{cam['sr_no']:>2} {cam['id']:<8} (zone {cam['zone']}, " \
              f"{cam['distance_m']:.0f}m)"
        if not os.path.exists(path):
            print(f"  {tag}: no footage on disk — skipped")
            skipped += 1
            continue

        print(f"  {tag}: scanning {os.path.basename(path)} ...")
        checked += 1
        try:
            intervals = find_face.search_video(
                detector, recognizer, ref, path,
                threshold=args.threshold, interval=args.interval, verbose=False)
        except IOError as e:
            print(f"      ! {e}")
            continue

        if intervals:
            stamps = ", ".join(find_face.fmt_ts(iv["start"]) for iv in intervals)
            peak = max(iv["best"] for iv in intervals)
            print(f"      >>> MATCH on {cam['id']} at {stamps} "
                  f"(peak cosine {peak:.3f})")
            found.append({"camera": cam, "intervals": intervals})
            if not args.all:
                break

    print("\n" + "=" * 60)
    print(f"Checked {checked} camera(s), skipped {skipped} (no footage).")
    if not found:
        print("RESULT: missing person NOT found in the checked footage.")
        sys.exit(1)

    print(f"RESULT: FOUND on {len(found)} camera(s):")
    for hit in found:
        cam = hit["camera"]
        first = hit["intervals"][0]
        when = find_face.fmt_ts(first["start"])
        print(f"  - {cam['id']} (zone {cam['zone']}, {cam['distance_m']:.0f}m "
              f"from last-seen): first appears at {when}")


if __name__ == "__main__":
    main()
