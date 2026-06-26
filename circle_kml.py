#!/usr/bin/env python3
"""
circle_kml.py — Draw a circle of a chosen radius around each coordinate in
a CSV file, and save the result as two KML files — one with the circles,
one with just the center points — that you can open in Google Earth or
Google My Maps.

EASIEST WAY TO RUN IT
----------------------
Open a terminal in this folder and type:

    python3 circle_kml.py

Then just answer the two questions it asks you (the CSV file, and the
radius in meters). That's it — everything else is automatic.

FASTER WAY (if you're comfortable typing one line)
----------------------------------------------------
    python3 circle_kml.py points.csv 250

This reads points.csv, draws a 250-meter circle around each point, and
saves the results automatically as points_circles.kml and
points_centers.kml in the same folder.

See README.md for full instructions.
"""

import argparse
import csv
import math
import os
import sys

EARTH_RADIUS_M = 6371000.0
DEFAULT_RADIUS_M = 250.0
DEFAULT_SEGMENTS = 30   # points used to approximate each circle
DEFAULT_FILL = False    # outline only, no red fill, by default


# ---------------------------------------------------------------------
# Geometry: find a point a given distance/bearing from a lat/lon, then
# walk that all the way around a center point to approximate a circle.
# ---------------------------------------------------------------------

def destination_point(lat, lon, bearing_deg, distance_m):
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    brng = math.radians(bearing_deg)
    ang_dist = distance_m / EARTH_RADIUS_M

    lat2 = math.asin(
        math.sin(lat1) * math.cos(ang_dist)
        + math.cos(lat1) * math.sin(ang_dist) * math.cos(brng)
    )
    lon2 = lon1 + math.atan2(
        math.sin(brng) * math.sin(ang_dist) * math.cos(lat1),
        math.cos(ang_dist) - math.sin(lat1) * math.sin(lat2),
    )
    return math.degrees(lat2), math.degrees(lon2)


def make_circle_coords(lat, lon, radius_m, segments=DEFAULT_SEGMENTS):
    coords = []
    for i in range(segments + 1):  # +1 closes the loop
        bearing = (360.0 / segments) * i
        clat, clon = destination_point(lat, lon, bearing, radius_m)
        coords.append((clon, clat))
    return coords


# ---------------------------------------------------------------------
# KML building
# ---------------------------------------------------------------------

def escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def circles_kml_header(fill=DEFAULT_FILL):
    fill_flag = "1" if fill else "0"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
<name>Coordinate Circles</name>
<Style id="circleStyle">
  <LineStyle><color>ff0000ff</color><width>2</width></LineStyle>
  <PolyStyle><color>4d0000ff</color><fill>{fill_flag}</fill><outline>1</outline></PolyStyle>
</Style>
"""


def centers_kml_header():
    return """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
<name>Coordinate Centers</name>
<Style id="centerPoint">
  <IconStyle>
    <Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon>
    <scale>0.8</scale>
  </IconStyle>
</Style>
"""


def kml_footer():
    return "</Document>\n</kml>\n"


def placemark_point(name, lat, lon):
    return f"""<Placemark>
  <name>{escape(name)} (center)</name>
  <styleUrl>#centerPoint</styleUrl>
  <Point><coordinates>{lon},{lat},0</coordinates></Point>
</Placemark>
"""


def placemark_polygon(name, coords):
    coord_str = " ".join(f"{lon:.6f},{lat:.6f},0" for lon, lat in coords)
    return f"""<Placemark>
  <name>{escape(name)} (radius circle)</name>
  <styleUrl>#circleStyle</styleUrl>
  <Polygon>
    <outerBoundaryIs>
      <LinearRing>
        <coordinates>{coord_str}</coordinates>
      </LinearRing>
    </outerBoundaryIs>
  </Polygon>
</Placemark>
"""


def build_circles_kml(points, segments=DEFAULT_SEGMENTS, fill=DEFAULT_FILL):
    parts = [circles_kml_header(fill)]
    for name, lat, lon, radius_m in points:
        coords = make_circle_coords(lat, lon, radius_m, segments)
        parts.append(placemark_polygon(name, coords))
    parts.append(kml_footer())
    return "".join(parts)


def build_centers_kml(points):
    parts = [centers_kml_header()]
    for name, lat, lon, radius_m in points:
        parts.append(placemark_point(name, lat, lon))
    parts.append(kml_footer())
    return "".join(parts)


# ---------------------------------------------------------------------
# CSV reading — radius is always in meters
# ---------------------------------------------------------------------

def read_points_from_csv(path, default_radius_m):
    points = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("CSV file appears to be empty.")

        field_map = {fn.strip().lower(): fn for fn in reader.fieldnames}
        lat_key = field_map.get("latitude") or field_map.get("lat")
        lon_key = field_map.get("longitude") or field_map.get("lon") or field_map.get("lng")
        name_key = field_map.get("name")
        radius_key = field_map.get("radius") or field_map.get("radius_m") or field_map.get("radius_meters")

        if not lat_key or not lon_key:
            raise ValueError(
                "CSV must contain 'latitude' and 'longitude' columns (case-insensitive)."
            )

        for i, row in enumerate(reader, start=1):
            lat_raw = (row.get(lat_key) or "").strip()
            lon_raw = (row.get(lon_key) or "").strip()
            if not lat_raw or not lon_raw:
                continue  # skip blank rows

            try:
                lat = float(lat_raw)
                lon = float(lon_raw)
            except ValueError:
                print(f"  Skipping row {i}: invalid latitude/longitude ({lat_raw}, {lon_raw})")
                continue

            name = (row.get(name_key) or "").strip() if name_key else ""
            if not name:
                name = f"Point {i}"

            radius_m = default_radius_m
            if radius_key:
                r_raw = (row.get(radius_key) or "").strip()
                if r_raw:
                    try:
                        radius_m = float(r_raw)
                    except ValueError:
                        print(f"  Row {i}: invalid radius '{r_raw}', using default instead.")

            points.append((name, lat, lon, radius_m))

    return points


# ---------------------------------------------------------------------
# Small helpers that keep the human-facing parts simple
# ---------------------------------------------------------------------

def default_output_path(csv_path):
    folder = os.path.dirname(os.path.abspath(csv_path))
    base = os.path.splitext(os.path.basename(csv_path))[0]
    return os.path.join(folder, f"{base}_circles.kml")


def derive_centers_path(circles_path):
    base, ext = os.path.splitext(circles_path)
    if base.endswith("_circles"):
        base = base[: -len("_circles")]
    return f"{base}_centers{ext or '.kml'}"


def ask_for_radius():
    raw = input(f"Circle radius in meters (press Enter to use {int(DEFAULT_RADIUS_M)}): ").strip()
    if not raw:
        return DEFAULT_RADIUS_M
    try:
        return float(raw)
    except ValueError:
        print(f"  Not a number — using the default of {int(DEFAULT_RADIUS_M)}m instead.")
        return DEFAULT_RADIUS_M


def interactive_mode():
    print("=== Circle KML Generator ===")
    print("Just answer these two questions:\n")

    while True:
        csv_path = input("1. Path to your CSV file of coordinates: ").strip().strip('"')
        if os.path.isfile(csv_path):
            break
        print(f"   Couldn't find '{csv_path}'. Check the path and try again.\n")

    print()
    radius = ask_for_radius()
    out_path = default_output_path(csv_path)
    return csv_path, radius, out_path


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate two KML files — circles and center points — for each coordinate in a CSV file.",
        epilog=f"""
Easiest use — just run with no arguments and answer the two questions:
  python3 circle_kml.py

Or in one line:
  python3 circle_kml.py points.csv 250

This creates two files: points_circles.kml and points_centers.kml

CSV format (header row required):
  name,latitude,longitude,radius
  Warehouse A,40.7128,-74.0060,
  Warehouse B,34.0522,-118.2437,1000

Defaults: {DEFAULT_SEGMENTS}-point circle outline, no fill, radius in meters.
Advanced options below let you change those if you want to.
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input_csv", nargs="?", help="Path to your CSV file of coordinates")
    parser.add_argument("radius", nargs="?", type=float,
                         help="Circle radius in meters, used for any row that doesn't set its own")
    parser.add_argument("--output", help="Output KML file path for the circles (default: <csv name>_circles.kml). A matching <csv name>_centers.kml is always created alongside it.")
    parser.add_argument("--segments", type=int, default=DEFAULT_SEGMENTS,
                         help=f"(advanced) Points used to draw each circle. Default: {DEFAULT_SEGMENTS}")
    parser.add_argument("--fill", action="store_true",
                         help="(advanced) Fill circles with color instead of outline only")
    args = parser.parse_args()

    if args.input_csv is None:
        csv_path, radius, out_path = interactive_mode()
    else:
        csv_path = args.input_csv
        if not os.path.isfile(csv_path):
            print(f"Error: file not found: {csv_path}")
            sys.exit(1)
        radius = args.radius if args.radius is not None else ask_for_radius()
        out_path = args.output or default_output_path(csv_path)

    print(f"\nReading coordinates from {csv_path} ...")
    try:
        points = read_points_from_csv(csv_path, radius)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if not points:
        print("No valid coordinates found — check your CSV file's latitude/longitude columns.")
        sys.exit(1)

    print(f"Found {len(points)} point(s). Default radius: {radius:g}m. Building circles...")
    circles_path = out_path
    centers_path = derive_centers_path(circles_path)

    circles_kml = build_circles_kml(points, args.segments, args.fill)
    centers_kml = build_centers_kml(points)

    with open(circles_path, "w", encoding="utf-8") as f:
        f.write(circles_kml)
    with open(centers_path, "w", encoding="utf-8") as f:
        f.write(centers_kml)

    print(f"\nDone! Saved {len(points)} circle(s) to:")
    print(f"  {circles_path}")
    print(f"  {centers_path}")
    print("Open either file in Google Earth or Google My Maps to view it.\n")


if __name__ == "__main__":
    main()
