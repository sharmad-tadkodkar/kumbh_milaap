#!/usr/bin/env python3
"""
select_cctvs.py — Pick which CCTVs to check, nearest to the lost location first.

Given the coordinates where a missing person was last seen, this:
  1. resolves which zone the point falls in (point-in-polygon, with a
     nearest-centroid fallback if it's outside every zone),
  2. orders that zone's cameras by distance from the point (nearest first),
     assigning a dynamic Sr No 1..N,
  3. yields them in batches (default 10) so the search can "go further" if the
     face isn't found in the first batch, spilling into the next-nearest zone
     once a zone is exhausted.

The ordered camera ids are what feed footage retrieval / find_face.py.

CLI:
  python3 select_cctvs.py --lat 19.9837 --lon 73.7118
  python3 select_cctvs.py --lat 19.9837 --lon 73.7118 --batch 10 --max 30
"""

import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAPPING_PATH = os.path.join(HERE, "cctv_zones.json")


def load_mapping(path=MAPPING_PATH):
    if not os.path.exists(path):
        sys.exit(f"Mapping not found: {path}\nRun parse_cctv_kml.py first.")
    with open(path) as f:
        return json.load(f)


def haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance in metres between two WGS84 points."""
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def point_in_ring(lat, lon, ring):
    """Ray-casting point-in-polygon. ring is [[lon, lat], ...]."""
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]   # lon, lat
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > lat) != (yj > lat)) and \
           (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def resolve_zone(mapping, lat, lon):
    """Return the zone key the point lies in, else the nearest zone by centroid."""
    zones = mapping["zones"]
    for key, z in zones.items():
        if z.get("boundary") and point_in_ring(lat, lon, z["boundary"]):
            return key, True
    # Fallback: nearest centroid (centroid is [lon, lat]).
    nearest, best = None, float("inf")
    for key, z in zones.items():
        c = z.get("centroid")
        if not c:
            continue
        d = haversine(lat, lon, c[1], c[0])
        if d < best:
            nearest, best = key, d
    return nearest, False


def zone_order_by_proximity(mapping, lat, lon, start_zone):
    """Zone keys ordered: start_zone first, then others by centroid distance."""
    zones = mapping["zones"]
    others = [k for k in zones if k != start_zone]

    def cdist(k):
        c = zones[k].get("centroid")
        return haversine(lat, lon, c[1], c[0]) if c else float("inf")

    return [start_zone] + sorted(others, key=cdist)


def select_cameras(mapping, lat, lon, batch=10, max_cameras=None):
    """Yield cameras nearest-first with a dynamic sr_no.

    Starts in the resolved zone, then spills into the next-nearest zones.
    Each yielded dict: {sr_no, id, zone, lat, lon, distance_m, batch}.
    """
    start_zone, inside = resolve_zone(mapping, lat, lon)
    sr_no = 0
    for zone_key in zone_order_by_proximity(mapping, lat, lon, start_zone):
        cams = mapping["zones"][zone_key]["cameras"]
        ranked = sorted(
            cams, key=lambda c: haversine(lat, lon, c["lat"], c["lon"]))
        for c in ranked:
            sr_no += 1
            yield {
                "sr_no": sr_no,
                "id": c["id"],
                "zone": int(zone_key),
                "lat": c["lat"],
                "lon": c["lon"],
                "distance_m": round(haversine(lat, lon, c["lat"], c["lon"]), 1),
                "batch": (sr_no - 1) // batch + 1,
            }
            if max_cameras and sr_no >= max_cameras:
                return


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lat", type=float, required=True, help="Lost-location latitude")
    ap.add_argument("--lon", type=float, required=True, help="Lost-location longitude")
    ap.add_argument("--batch", type=int, default=10, help="Cameras per batch (default 10)")
    ap.add_argument("--max", type=int, default=20, dest="max_cameras",
                    help="Max cameras to list (default 20; 0 = all)")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of a table")
    args = ap.parse_args()

    mapping = load_mapping()
    start_zone, inside = resolve_zone(mapping, args.lat, args.lon)
    note = "inside" if inside else "nearest (point outside all zones)"
    # Info lines go to stderr so --json emits clean, pipeable JSON on stdout.
    print(f"[*] Lost location ({args.lat}, {args.lon}) -> Zone {start_zone} ({note})",
          file=sys.stderr)

    limit = None if args.max_cameras == 0 else args.max_cameras
    rows = list(select_cameras(mapping, args.lat, args.lon,
                               batch=args.batch, max_cameras=limit))

    if args.json:
        print(json.dumps(rows, indent=2))
        return

    print(f"[*] {len(rows)} camera(s), nearest first (batches of {args.batch}):\n")
    print(f"  {'Sr':>3}  {'Batch':>5}  {'Camera':<8}  {'Zone':>4}  {'Dist(m)':>8}")
    print("  " + "-" * 38)
    last_batch = None
    for r in rows:
        if last_batch is not None and r["batch"] != last_batch:
            print("  " + "-" * 38)
        last_batch = r["batch"]
        print(f"  {r['sr_no']:>3}  {r['batch']:>5}  {r['id']:<8}  "
              f"{r['zone']:>4}  {r['distance_m']:>8.1f}")


if __name__ == "__main__":
    main()
