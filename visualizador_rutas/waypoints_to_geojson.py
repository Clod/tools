#!/usr/bin/env python3
"""
Waypoints to GeoJSON Converter

This script processes JSON files containing Sentiance event data and converts them into
GeoJSON format for easier visualization in geographic information systems (GIS) or web maps.

Key Features:
- Supports multiple Sentiance JSON structures:
    1. Standard export containing a 'userContext' object with an 'events' list.
    2. Single transport event objects (e.g., 'viaje.json' structure).
    3. Root objects directly containing 'waypoints'.
- Extracts 'LineString' geometries from sequences of waypoints.
- Preserves event metadata as GeoJSON properties:
    - Transport mode and tags
    - Distance and timestamps
    - Event index for tracking
- Generates a GeoJSON 'FeatureCollection' suitable for tools like geojson.io, QGIS, or Mapbox.

Usage:
    python waypoints_to_geojson.py <input_json> <output_geojson>
"""
import json
import sys
from pathlib import Path

def extract_waypoints_to_geojson(input_path, output_path):
    # Load input JSON
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error: Failed to process file '{input_path}'.")
        print(f"Details: {e}")
        sys.exit(1)

def convert_to_geojson_data(data):
    """
    Core logic to convert Sentiance JSON data to GeoJSON.
    Returns a dictionary representing the GeoJSON FeatureCollection.
    """
    events = []
    if "userContext" in data and "events" in data["userContext"]:
        # Standard Sentiance export
        events = data["userContext"]["events"]
    elif "transportEvent" in data:
        # Single transport event structure (like viaje.json)
        events = [data["transportEvent"]]
    elif "waypoints" in data:
        # Root object is the event (or list of waypoints)
        if isinstance(data["waypoints"], list):
            events = [data]
        else:
            events = []
    elif isinstance(data, list):
        # Maybe a list of events
        events = data

    features = []

    for idx, ev in enumerate(events):
        if not isinstance(ev, dict):
            continue
            
        waypoints = ev.get("waypoints")
        if not waypoints:
            continue

        # Build coordinates array [lon, lat]
        coords = []
        for wp in waypoints:
            lon = wp.get("longitude") or wp.get("lon")
            lat = wp.get("latitude") or wp.get("lat")
            if lon is None or lat is None:
                continue
            coords.append([lon, lat])

        if not coords:
            continue

        # Some useful props from the event if present
        props = {
            "event_index": idx,
            "type": ev.get("type"),
            "distance": ev.get("distance"),
            "transportMode": ev.get("transportMode"),
            "transportTags": ev.get("transportTags"),
            "startTime": ev.get("startTime"),
            "endTime": ev.get("endTime"),
        }

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": coords,
            },
            "properties": props,
        }
        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def extract_waypoints_to_geojson(input_path, output_path):
    # Load input JSON
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error: Failed to process file '{input_path}'.")
        print(f"Details: {e}")
        sys.exit(1)

    fc = convert_to_geojson_data(data)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False, indent=2)


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {Path(sys.argv[0]).name} input.json output.geojson")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    extract_waypoints_to_geojson(input_path, output_path)


if __name__ == "__main__":
    main()
