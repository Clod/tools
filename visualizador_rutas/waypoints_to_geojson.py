#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def extract_waypoints_to_geojson(input_path, output_path):
    # Load input JSON
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse JSON file '{input_path}'.")
            print(f"Details: {e}")
            sys.exit(1)

    events = data.get("userContext", {}).get("events", [])
    # Determine where the events/waypoints are located
    events = []
    if "userContext" in data and "events" in data["userContext"]:
        # Standard Sentiance export
        events = data["userContext"]["events"]
    elif "transportEvent" in data:
        # Single transport event structure (like viaje.json)
        events = [data["transportEvent"]]
    elif "waypoints" in data:
        # Root object is the event
        events = [data]

    features = []

    for idx, ev in enumerate(events):
        waypoints = ev.get("waypoints")
        if not waypoints:
            continue

        # Build coordinates array [lon, lat]
        coords = []
        for wp in waypoints:
            lon = wp.get("longitude")
            lat = wp.get("latitude")
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

    fc = {
        "type": "FeatureCollection",
        "features": features,
    }

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
