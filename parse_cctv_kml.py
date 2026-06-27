#!/usr/bin/env python3
"""
parse_cctv_kml.py — Build a CCTV -> coordinate mapping from the KML.

Reads "CCTV Dataset.kml" and extracts the zoned camera network whose
placemark names encode zone + camera number ("Z<zone>-C<cam>"), together
with the matching "Zone Area <n>" boundary polygons. Writes cctv_zones.json:

  zones["1"] = {
    "zone": 1,
    "boundary": [[lon, lat], ...],   # polygon outer ring
    "centroid": [lon, lat],          # used as a fallback zone resolver
    "cameras": [{"id": "Z1-C1", "cam_no": 1, "lat": ..., "lon": ...}, ...]
  }

Stdlib only — no external dependencies. Coordinates are WGS84 (lon, lat).
"""

import json
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
KML_PATH = os.path.join(HERE, "CCTV Dataset.kml")
OUT_PATH = os.path.join(HERE, "cctv_zones.json")

KML_NS = "http://www.opengis.net/kml/2.2"

CAMERA_RE = re.compile(r"^Z(\d+)-C(\d+)$")
ZONE_AREA_RE = re.compile(r"^Zone Area (\d+)$")

EXPECTED_ZONES = 32
EXPECTED_CAMS_PER_ZONE = 40


def q(tag):
    """Namespace-qualified tag name for findall/find."""
    return f"{{{KML_NS}}}{tag}"


def parse_coord_list(text):
    """Parse a KML <coordinates> blob 'lon,lat,alt lon,lat,alt ...'.

    Returns a list of [lon, lat] pairs (altitude dropped).
    """
    points = []
    for token in text.split():
        parts = token.split(",")
        if len(parts) >= 2:
            points.append([float(parts[0]), float(parts[1])])
    return points


def polygon_centroid(ring):
    """Area-weighted centroid of a polygon outer ring ([[lon, lat], ...]).

    Falls back to the vertex average for degenerate (zero-area) rings.
    """
    n = len(ring)
    if n == 0:
        return None
    area = cx = cy = 0.0
    for i in range(n):
        x0, y0 = ring[i]
        x1, y1 = ring[(i + 1) % n]
        cross = x0 * y1 - x1 * y0
        area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    area *= 0.5
    if abs(area) < 1e-12:
        avg_x = sum(p[0] for p in ring) / n
        avg_y = sum(p[1] for p in ring) / n
        return [avg_x, avg_y]
    return [cx / (6 * area), cy / (6 * area)]


def main():
    if not os.path.exists(KML_PATH):
        sys.exit(f"KML not found: {KML_PATH}")

    tree = ET.parse(KML_PATH)
    root = tree.getroot()

    zones = {}  # zone_no -> {"cameras": [...], "boundary": [...], "centroid": [...]}

    def zone(no):
        return zones.setdefault(no, {"cameras": [], "boundary": None, "centroid": None})

    for pm in root.iter(q("Placemark")):
        name_el = pm.find(q("name"))
        if name_el is None or not name_el.text:
            continue
        name = name_el.text.strip()

        cam = CAMERA_RE.match(name)
        if cam:
            coord_el = pm.find(f"./{q('Point')}/{q('coordinates')}")
            if coord_el is None or not coord_el.text:
                continue
            lon, lat = parse_coord_list(coord_el.text)[0]
            zone_no, cam_no = int(cam.group(1)), int(cam.group(2))
            zone(zone_no)["cameras"].append(
                {"id": name, "cam_no": cam_no, "lat": lat, "lon": lon})
            continue

        area = ZONE_AREA_RE.match(name)
        if area:
            coord_el = pm.find(
                f"./{q('Polygon')}/{q('outerBoundaryIs')}/"
                f"{q('LinearRing')}/{q('coordinates')}")
            if coord_el is None or not coord_el.text:
                continue
            ring = parse_coord_list(coord_el.text)
            z = zone(int(area.group(1)))
            z["boundary"] = ring
            z["centroid"] = polygon_centroid(ring)

    # Order cameras within each zone by camera number (stable, query-time
    # reordering by proximity happens in select_cctvs.py).
    out_zones = {}
    total_cams = 0
    for zone_no in sorted(zones):
        z = zones[zone_no]
        z["cameras"].sort(key=lambda c: c["cam_no"])
        total_cams += len(z["cameras"])
        out_zones[str(zone_no)] = {
            "zone": zone_no,
            "boundary": z["boundary"],
            "centroid": z["centroid"],
            "cameras": z["cameras"],
        }

    # Sanity checks before writing.
    bad = [zn for zn, z in out_zones.items()
           if len(z["cameras"]) != EXPECTED_CAMS_PER_ZONE]
    missing_boundary = [zn for zn, z in out_zones.items() if not z["boundary"]]
    if len(out_zones) != EXPECTED_ZONES or bad:
        print(f"WARNING: expected {EXPECTED_ZONES} zones x "
              f"{EXPECTED_CAMS_PER_ZONE} cams; got {len(out_zones)} zones, "
              f"off-count zones={bad}", file=sys.stderr)
    if missing_boundary:
        print(f"WARNING: zones missing a boundary polygon: {missing_boundary}",
              file=sys.stderr)

    payload = {
        "source": os.path.basename(KML_PATH),
        "crs": "WGS84 (lon, lat)",
        "zone_count": len(out_zones),
        "camera_count": total_cams,
        "zones": out_zones,
    }
    with open(OUT_PATH, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"Parsed {total_cams} cameras across {len(out_zones)} zones.")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
